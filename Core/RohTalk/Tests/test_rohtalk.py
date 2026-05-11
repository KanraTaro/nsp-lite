"""Offline unit tests for the RohTalk core spine.

These tests exercise the conversation pipeline and early tool-loop
helpers without requiring any live LLM backend. The tests create a
temporary root directory for each run, so they do not interfere with
any real State/ or Config/ directories on disk.
"""

from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from Core.LLMClient.types import ChatResult, ToolCall, ToolDef
import Core.NSPL.NodeCTX as NodeCTX
from Core.NSPL.SkillCLI.ctx import SkillContext
from Core.RohTalk.conversations import append_message, create_conversation, list_conversations
from Core.RohTalk.tracing import print_step, print_tool_call, print_tool_result
from Core.RohTalk.tool_loop import run_tool_loop
from Core.RohTalk.tool_runner import execute_tool_call
import Skills.RohTalk.chat.skill as rohtalk_chat_skill
import Skills.RohTalk.shell.skill as rohtalk_shell_skill
import Skills.RohTalk.tool_test.skill as rohtalk_tool_test_skill


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

    def test_create_conversation_stores_model_profile_and_options(self) -> None:
        config_path = Path(self.ctx.root) / "Config" / "RohTalk" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            '{"default_model":"gpt-oss:20b","default_options":{"think":"low"},'
            '"profiles":{"fast":{"model":"qwen3:8b","options":{"think":false}}}}',
            encoding="utf-8",
        )

        conv_id, _reply = create_conversation(
            self.ctx,
            "hello",
            kind="conversation",
            model_profile="fast",
            skip_model=True,
        )

        meta_files = self.ctx.node_ctx.list_files(self._conversation_dir(), suffix=".json")
        self.assertEqual(len(meta_files), 1)
        metadata = self.ctx.node_ctx.read_json(meta_files[0])
        self.assertEqual(metadata["model"], "qwen3:8b")
        self.assertEqual(metadata["model_profile"], "fast")
        self.assertEqual(metadata["model_options"], {"think": False})

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

    def test_run_tool_loop_passes_model_options_to_client(self) -> None:
        tools: list[ToolDef] = []
        result = ChatResult(
            text="fast reply",
            tool_calls=[],
            assistant_message={"role": "assistant", "content": "fast reply"},
            raw={},
        )

        with patch("Core.RohTalk.tool_loop.LLMClient") as mock_client_cls:
            instance = mock_client_cls.return_value
            instance.chat_stream_collect.return_value = result

            final_text, _final_messages = run_tool_loop(
                [{"role": "user", "content": "hello"}],
                model="qwen3:8b",
                tools=tools,
                model_options={"think": False},
            )

        self.assertEqual(final_text, "fast reply")
        self.assertEqual(instance.chat_stream_collect.call_args.kwargs["model_options"], {"think": False})

    def test_run_tool_loop_stop_hook_appends_result_and_stops_before_next_model_call(self) -> None:
        tools = [
            ToolDef(
                name="announce_text",
                description="Announce text",
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            )
        ]

        first_result = ChatResult(
            text="",
            tool_calls=[
                ToolCall(
                    id="call_action",
                    name="announce_text",
                    arguments={"text": "hello"},
                    arguments_json='{"text":"hello"}',
                )
            ],
            assistant_message={
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_action",
                        "name": "announce_text",
                        "arguments": {"text": "hello"},
                    }
                ],
            },
            raw={},
        )

        def announce_text(text: str) -> dict:
            return {"announced": text}

        with patch("Core.RohTalk.tool_loop.LLMClient") as mock_client_cls:
            instance = mock_client_cls.return_value
            instance.chat_stream_collect.return_value = first_result

            final_text, final_messages = run_tool_loop(
                [{"role": "user", "content": "announce hello"}],
                model="qwen3:0.6b",
                tools=tools,
                tool_impl={"announce_text": announce_text},
                should_stop_after_tool_result=lambda result: bool(result.get("ok"))
                and result.get("tool_name") == "announce_text",
            )

        self.assertEqual(final_text, "")
        self.assertEqual(instance.chat_stream_collect.call_count, 1)
        self.assertEqual(final_messages[-1]["role"], "tool")
        self.assertEqual(final_messages[-1]["tool_call_id"], "call_action")
        self.assertEqual(final_messages[-1]["tool_name"], "announce_text")
        self.assertIn('"ok":true', final_messages[-1]["content"])

    def test_run_tool_loop_failed_action_result_does_not_stop(self) -> None:
        tools = [
            ToolDef(
                name="announce_text",
                description="Announce text",
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            )
        ]

        first_result = ChatResult(
            text="",
            tool_calls=[
                ToolCall(
                    id="call_action",
                    name="announce_text",
                    arguments={"text": "hello"},
                    arguments_json='{"text":"hello"}',
                )
            ],
            assistant_message={
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_action",
                        "name": "announce_text",
                        "arguments": {"text": "hello"},
                    }
                ],
            },
            raw={},
        )
        second_result = ChatResult(
            text="Action failed.",
            tool_calls=[],
            assistant_message={"role": "assistant", "content": "Action failed."},
            raw={},
        )

        with patch("Core.RohTalk.tool_loop.LLMClient") as mock_client_cls:
            instance = mock_client_cls.return_value
            instance.chat_stream_collect.side_effect = [first_result, second_result]

            final_text, final_messages = run_tool_loop(
                [{"role": "user", "content": "announce hello"}],
                model="qwen3:0.6b",
                tools=tools,
                tool_impl={},
                should_stop_after_tool_result=lambda result: bool(result.get("ok"))
                and result.get("tool_name") == "announce_text",
            )

        self.assertEqual(final_text, "Action failed.")
        self.assertEqual(instance.chat_stream_collect.call_count, 2)
        self.assertEqual(final_messages[-2]["role"], "tool")
        self.assertIn('"ok":false', final_messages[-2]["content"])
        self.assertEqual(final_messages[-1]["content"], "Action failed.")

    def test_run_tool_loop_successful_read_only_result_does_not_stop_when_hook_false(self) -> None:
        tools = [
            ToolDef(
                name="snapshot_read",
                description="Read snapshot",
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
                    id="call_read",
                    name="snapshot_read",
                    arguments={},
                    arguments_json="{}",
                )
            ],
            assistant_message={
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_read",
                        "name": "snapshot_read",
                        "arguments": {},
                    }
                ],
            },
            raw={},
        )
        second_result = ChatResult(
            text="Snapshot ready.",
            tool_calls=[],
            assistant_message={"role": "assistant", "content": "Snapshot ready."},
            raw={},
        )

        def snapshot_read() -> dict:
            return {"summary": "ready"}

        with patch("Core.RohTalk.tool_loop.LLMClient") as mock_client_cls:
            instance = mock_client_cls.return_value
            instance.chat_stream_collect.side_effect = [first_result, second_result]

            final_text, final_messages = run_tool_loop(
                [{"role": "user", "content": "read snapshot"}],
                model="qwen3:0.6b",
                tools=tools,
                tool_impl={"snapshot_read": snapshot_read},
                should_stop_after_tool_result=lambda _result: False,
            )

        self.assertEqual(final_text, "Snapshot ready.")
        self.assertEqual(instance.chat_stream_collect.call_count, 2)
        self.assertEqual(final_messages[-2]["role"], "tool")
        self.assertIn('"ok":true', final_messages[-2]["content"])
        self.assertEqual(final_messages[-1]["content"], "Snapshot ready.")

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

    def test_trace_helpers_format_events(self) -> None:
        stream = io.StringIO()
        tool_call = ToolCall(
            id="call_1",
            name="objective_collect",
            arguments={"target_prefab": "log", "target_count": 1},
            arguments_json='{"target_count":1,"target_prefab":"log"}',
        )

        print_step(0, stream=stream)
        print_tool_call(tool_call, stream=stream)
        print_tool_result({"ok": True, "count": 1}, stream=stream)

        self.assertEqual(
            stream.getvalue(),
            "\n".join(
                [
                    "[step 1]",
                    '[tool_call] objective_collect {"target_count":1,"target_prefab":"log"}',
                    '[tool_result] {"count":1,"ok":true}',
                    "",
                ]
            ),
        )

    def test_rohtalk_cli_parsers_accept_tool_trace(self) -> None:
        chat_parser = argparse.ArgumentParser()
        rohtalk_chat_skill.build_parser(chat_parser)
        chat_args = chat_parser.parse_args(["--tools", "--tool-trace", "0", "--", "hello"])
        self.assertTrue(chat_args.tools)
        self.assertTrue(chat_args.tool_trace)
        profile_args = chat_parser.parse_args(["--model-profile", "fast", "--model-option", "think=false", "0", "--", "hello"])
        self.assertEqual(profile_args.model_profile, "fast")
        self.assertEqual(profile_args.model_options, ["think=false"])

        shell_parser = argparse.ArgumentParser()
        rohtalk_shell_skill.build_parser(shell_parser)
        shell_args = shell_parser.parse_args(["--tools", "--tool-trace"])
        self.assertTrue(shell_args.tools)
        self.assertTrue(shell_args.tool_trace)

        tool_test_parser = argparse.ArgumentParser()
        rohtalk_tool_test_skill.build_parser(tool_test_parser)
        tool_test_args = tool_test_parser.parse_args(["--tool-trace", "--", "hello"])
        self.assertTrue(tool_test_args.tool_trace)

    def test_chat_passes_trace_callbacks_when_tools_and_tool_trace_enabled(self) -> None:
        args = SimpleNamespace(
            conversation_ref="0",
            model=None,
            host=None,
            tools=True,
            tool_backend="skillcli",
            toolkit="basic",
            tool_trace=True,
            message=["hello"],
        )

        with patch.object(rohtalk_chat_skill, "resolve_conversation_ref", return_value="conv_1"):
            with patch.object(rohtalk_chat_skill, "run_turn", return_value=("conv_1", "reply")) as mock_run_turn:
                with patch("sys.stdout", new_callable=io.StringIO):
                    result = rohtalk_chat_skill.run(args, self.ctx)

        self.assertEqual(result, 0)
        kwargs = mock_run_turn.call_args.kwargs
        self.assertIs(kwargs["on_step"], print_step)
        self.assertIs(kwargs["on_tool_call"], print_tool_call)
        self.assertIs(kwargs["on_tool_result"], print_tool_result)

    def test_chat_does_not_pass_trace_callbacks_when_tool_trace_disabled(self) -> None:
        args = SimpleNamespace(
            conversation_ref="0",
            model=None,
            host=None,
            tools=True,
            tool_backend="skillcli",
            toolkit="basic",
            tool_trace=False,
            message=["hello"],
        )

        with patch.object(rohtalk_chat_skill, "resolve_conversation_ref", return_value="conv_1"):
            with patch.object(rohtalk_chat_skill, "run_turn", return_value=("conv_1", "reply")) as mock_run_turn:
                with patch("sys.stdout", new_callable=io.StringIO):
                    result = rohtalk_chat_skill.run(args, self.ctx)

        self.assertEqual(result, 0)
        kwargs = mock_run_turn.call_args.kwargs
        self.assertNotIn("on_step", kwargs)
        self.assertNotIn("on_tool_call", kwargs)
        self.assertNotIn("on_tool_result", kwargs)

    def test_tool_test_quiet_suppresses_trace_callbacks(self) -> None:
        args = SimpleNamespace(
            model=None,
            host=None,
            tool_backend="local",
            toolkit="basic",
            show_history=False,
            quiet=True,
            tool_trace=True,
            prompt=["hello"],
        )

        config = SimpleNamespace(default_model="qwen3:0.6b", default_host="http://localhost:11434")
        with patch.object(rohtalk_tool_test_skill, "load_config", return_value=config):
            with patch.object(
                rohtalk_tool_test_skill,
                "run_tool_loop",
                return_value=("final response", [{"role": "assistant", "content": "final response"}]),
            ) as mock_run_tool_loop:
                with patch("sys.stdout", new_callable=io.StringIO):
                    result = rohtalk_tool_test_skill.run(args, self.ctx)

        self.assertEqual(result, 0)
        kwargs = mock_run_tool_loop.call_args.kwargs
        self.assertNotIn("on_step", kwargs)
        self.assertNotIn("on_tool_call", kwargs)
        self.assertNotIn("on_tool_result", kwargs)
        self.assertNotIn("on_text_delta", kwargs)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
