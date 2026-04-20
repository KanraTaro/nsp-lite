"""Offline unit tests for the RohTalk core spine.

These tests exercise the conversation pipeline and early tool-loop
helpers without requiring any live LLM backend. The tests create a
temporary root directory for each run, so they do not interfere with
any real State/ or Config/ directories on disk.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Core.LLMClient.types import ChatResult, ToolCall, ToolDef
import Core.NSPL.NodeCTX as NodeCTX
from Core.NSPL.SkillCLI.ctx import SkillContext
from Core.RohTalk.conversations import append_message, create_conversation, list_conversations
from Core.RohTalk.tool_loop import run_tool_loop
from Core.RohTalk.tool_runner import execute_tool_call


class RohTalkCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)

        self.ctx = SkillContext(
            root=root,
            node_tag="testnode",
            instance_id="testinstance",
            global_scope=False,
            node_ctx=NodeCTX,
            debug=False,
            json=False,
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _mock_chat(self, reply_text: str) -> None:
        """Patch ``LLMClient.chat`` to return a fixed ChatResult."""
        patcher = patch("Core.RohTalk.conversations.LLMClient")
        mock_client = patcher.start()
        instance = mock_client.return_value
        instance.chat.return_value = ChatResult(
            text=reply_text,
            tool_calls=[],
            assistant_message={
                "role": "assistant",
                "content": reply_text,
            },
            raw={},
        )
        self.addCleanup(patcher.stop)

    def _conversation_dir(self) -> Path:
        node_ctx = self.ctx.node_ctx
        return node_ctx.build_state_dir(
            root=self.ctx.root,
            instance_id=self.ctx.instance_id,
            node_tag=self.ctx.node_tag,
            bucket="Workflow",
            domain="RohTalk",
            global_scope=self.ctx.global_scope,
            subpath="Conversations",
        )

    def test_create_conversation(self) -> None:
        node_ctx = self.ctx.node_ctx

        self._mock_chat("first reply")
        conv_id, reply = create_conversation(self.ctx, "hello", kind="conversation")

        self.assertEqual(reply, "first reply")

        conv_dir = self._conversation_dir()
        self.assertTrue(node_ctx.exists(conv_dir))
        self.assertTrue(node_ctx.is_dir(conv_dir))

        files = node_ctx.list_dir(conv_dir)
        self.assertEqual(len(files), 2)

        meta_files = node_ctx.list_files(conv_dir, suffix=".json")
        self.assertEqual(len(meta_files), 1)

        meta_path = meta_files[0]
        metadata = node_ctx.read_json(meta_path)
        self.assertEqual(metadata["id"], conv_id)
        self.assertEqual(metadata["kind"], "conversation")
        self.assertEqual(len(metadata["messages"]), 3)

        roles = [message["role"] for message in metadata["messages"]]
        self.assertEqual(roles, ["system", "user", "assistant"])

        events_files = node_ctx.list_files(conv_dir, suffix=".jsonl")
        self.assertEqual(len(events_files), 1)

        events_path = events_files[0]
        events = node_ctx.read_jsonl(events_path)
        self.assertEqual(len(events), 3)
        self.assertEqual([event["role"] for event in events], ["system", "user", "assistant"])

    def test_append_message(self) -> None:
        node_ctx = self.ctx.node_ctx

        self._mock_chat("first reply")
        conv_id, _reply = create_conversation(self.ctx, "hello", kind="conversation")

        self._mock_chat("second reply")
        reply2 = append_message(self.ctx, conv_id, "how are you")
        self.assertEqual(reply2, "second reply")

        conv_dir = self._conversation_dir()

        meta_files = node_ctx.list_files(conv_dir, suffix=".json")
        self.assertEqual(len(meta_files), 1)

        meta = node_ctx.read_json(meta_files[0])
        self.assertEqual(len(meta["messages"]), 5)

        roles = [message["role"] for message in meta["messages"]]
        self.assertEqual(roles, ["system", "user", "assistant", "user", "assistant"])

        events_files = node_ctx.list_files(conv_dir, suffix=".jsonl")
        self.assertEqual(len(events_files), 1)

        events = node_ctx.read_jsonl(events_files[0])
        self.assertEqual(len(events), 5)
        self.assertEqual([event["role"] for event in events], ["system", "user", "assistant", "user", "assistant"])

    def test_list_conversations(self) -> None:
        self._mock_chat("reply1")
        conv1, _ = create_conversation(self.ctx, "hi", kind="conversation")

        self._mock_chat("reply2")
        conv2, _ = create_conversation(self.ctx, "hi again", kind="oneshot")

        convs = list_conversations(self.ctx, include_oneshots=False)
        ids = [conversation["id"] for conversation in convs]
        self.assertIn(conv1, ids)
        self.assertNotIn(conv2, ids)

        convs_all = list_conversations(self.ctx, include_oneshots=True)
        ids_all = [conversation["id"] for conversation in convs_all]
        self.assertIn(conv1, ids_all)
        self.assertIn(conv2, ids_all)

    def test_oneshot_pipeline(self) -> None:
        node_ctx = self.ctx.node_ctx

        self._mock_chat("oneshot reply")
        conv_id, reply = create_conversation(self.ctx, "prompt", kind="oneshot")
        self.assertEqual(reply, "oneshot reply")

        conv_dir = self._conversation_dir()
        meta_files = node_ctx.list_files(conv_dir, suffix=".json")
        self.assertEqual(len(meta_files), 1)

        meta = node_ctx.read_json(meta_files[0])
        self.assertEqual(meta["kind"], "oneshot")

        convs = list_conversations(self.ctx)
        ids = [conversation["id"] for conversation in convs]
        self.assertNotIn(conv_id, ids)

    def test_append_requires_existing_conversation(self) -> None:
        self._mock_chat("ignored")

        with self.assertRaises(FileNotFoundError):
            append_message(self.ctx, "doesnotexist", "hello")

    def test_execute_tool_call_success(self) -> None:
        def get_weather(city: str) -> dict:
            return {"city": city, "forecast": "sunny"}

        tool_call = ToolCall(
            id="call_1",
            name="get_weather",
            arguments={"city": "Orlando"},
            arguments_json='{"city":"Orlando"}',
        )

        result = execute_tool_call(tool_call, {"get_weather": get_weather})

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool_name"], "get_weather")
        self.assertEqual(result["tool_call_id"], "call_1")
        self.assertEqual(result["result"], {"city": "Orlando", "forecast": "sunny"})

    def test_execute_tool_call_unknown_tool(self) -> None:
        tool_call = ToolCall(
            id="call_2",
            name="missing_tool",
            arguments={},
            arguments_json="{}",
        )

        result = execute_tool_call(tool_call, {})

        self.assertFalse(result["ok"])
        self.assertEqual(result["tool_name"], "missing_tool")
        self.assertEqual(result["tool_call_id"], "call_2")
        self.assertIn("Unknown tool", result["error"])

    def test_run_tool_loop_tool_then_final_reply(self) -> None:
        tools = [
            ToolDef(
                name="get_weather",
                description="Get weather for a city",
                parameters={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            )
        ]

        def get_weather(city: str) -> dict:
            return {"city": city, "forecast": "Partly cloudy", "temp_f": 82}

        first_result = ChatResult(
            text="",
            tool_calls=[
                ToolCall(
                    id="call_1",
                    name="get_weather",
                    arguments={"city": "Orlando"},
                    arguments_json='{"city":"Orlando"}',
                )
            ],
            assistant_message={
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "name": "get_weather",
                        "arguments": {"city": "Orlando"},
                    }
                ],
            },
            raw={},
        )

        second_result = ChatResult(
            text="It looks partly cloudy in Orlando. You probably do not need an umbrella.",
            tool_calls=[],
            assistant_message={
                "role": "assistant",
                "content": "It looks partly cloudy in Orlando. You probably do not need an umbrella.",
            },
            raw={},
        )

        with patch("Core.RohTalk.tool_loop.LLMClient") as mock_client_cls:
            instance = mock_client_cls.return_value
            instance.chat_stream_collect.side_effect = [first_result, second_result]

            messages = [
                {"role": "system", "content": "You are Roh."},
                {"role": "user", "content": "What is the weather in Orlando?"},
            ]

            final_text, final_messages = run_tool_loop(
                messages,
                model="qwen3:0.6b",
                tools=tools,
                tool_impl={"get_weather": get_weather},
                max_steps=5,
            )

        self.assertEqual(
            final_text,
            "It looks partly cloudy in Orlando. You probably do not need an umbrella.",
        )

        self.assertEqual(final_messages[0]["role"], "system")
        self.assertEqual(final_messages[1]["role"], "user")
        self.assertEqual(final_messages[2]["role"], "assistant")
        self.assertIn("tool_calls", final_messages[2])

        self.assertEqual(final_messages[3]["role"], "tool")
        self.assertEqual(final_messages[3]["tool_call_id"], "call_1")
        self.assertEqual(final_messages[3]["tool_name"], "get_weather")

        self.assertEqual(final_messages[4]["role"], "assistant")
        self.assertEqual(
            final_messages[4]["content"],
            "It looks partly cloudy in Orlando. You probably do not need an umbrella.",
        )

    def test_run_tool_loop_unknown_tool_appends_failure_message(self) -> None:
        tools = [
            ToolDef(
                name="missing_tool",
                description="Missing tool",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            )
        ]

        first_result = ChatResult(
            text="",
            tool_calls=[
                ToolCall(
                    id="call_9",
                    name="missing_tool",
                    arguments={},
                    arguments_json="{}",
                )
            ],
            assistant_message={
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_9",
                        "name": "missing_tool",
                        "arguments": {},
                    }
                ],
            },
            raw={},
        )

        second_result = ChatResult(
            text="That tool is unavailable.",
            tool_calls=[],
            assistant_message={
                "role": "assistant",
                "content": "That tool is unavailable.",
            },
            raw={},
        )

        with patch("Core.RohTalk.tool_loop.LLMClient") as mock_client_cls:
            instance = mock_client_cls.return_value
            instance.chat_stream_collect.side_effect = [first_result, second_result]

            messages = [
                {"role": "system", "content": "You are Roh."},
                {"role": "user", "content": "Run the missing tool."},
            ]

            final_text, final_messages = run_tool_loop(
                messages,
                model="qwen3:0.6b",
                tools=tools,
                tool_impl={},
                max_steps=5,
            )

        self.assertEqual(final_text, "That tool is unavailable.")
        self.assertEqual(final_messages[3]["role"], "tool")
        self.assertEqual(final_messages[3]["tool_call_id"], "call_9")
        self.assertEqual(final_messages[3]["tool_name"], "missing_tool")
        self.assertIn('"ok":false', final_messages[3]["content"])

    def test_run_tool_loop_max_steps_raises(self) -> None:
        tools = [
            ToolDef(
                name="loop_tool",
                description="Loop forever",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            )
        ]

        repeated_result = ChatResult(
            text="",
            tool_calls=[
                ToolCall(
                    id="call_loop",
                    name="loop_tool",
                    arguments={},
                    arguments_json="{}",
                )
            ],
            assistant_message={
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_loop",
                        "name": "loop_tool",
                        "arguments": {},
                    }
                ],
            },
            raw={},
        )

        def loop_tool() -> dict:
            return {"still": "looping"}

        with patch("Core.RohTalk.tool_loop.LLMClient") as mock_client_cls:
            instance = mock_client_cls.return_value
            instance.chat_stream_collect.side_effect = [repeated_result, repeated_result]

            messages = [
                {"role": "system", "content": "You are Roh."},
                {"role": "user", "content": "Loop forever."},
            ]

            with self.assertRaises(RuntimeError):
                run_tool_loop(
                    messages,
                    model="qwen3:0.6b",
                    tools=tools,
                    tool_impl={"loop_tool": loop_tool},
                    max_steps=2,
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
