from __future__ import annotations

import asyncio
import importlib.util
import json
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from Core.NSPL.Entry.Discovery.web_loader import discover_web_apps
from Core.NSPL.Entry.web_context import SkillInvocationResult


REPO_ROOT = Path(__file__).resolve().parents[4]
APP_PATH = REPO_ROOT / "Web" / "Roh" / "OperatorStation" / "app.py"


def _load_app_module():
    spec = importlib.util.spec_from_file_location("_test_roh_operator_station_app", str(APP_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Roh Operator Station app")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


@dataclass
class FakeContext:
    repo_root: Path = REPO_ROOT
    app_dir: Path = REPO_ROOT / "Web" / "Roh" / "OperatorStation"
    metadata: dict[str, Any] = field(default_factory=lambda: {"name": "Roh.OperatorStation", "version": "0.1.0"})
    calls: list[tuple[list[str], float]] = field(default_factory=list)
    snapshot_path: Path | None = None
    include_rohtalk: bool = True
    snapshot_ok: bool = True
    operator_conversation_id: str = ""
    listen_ok: bool = True
    listen_transcript: str = "Roh, give me a status report."

    def run_skill(self, argv, timeout=30.0):
        self.calls.append((list(argv), float(timeout)))
        name = argv[0]
        if name == "NSPL.Tools.Time.now":
            return SkillInvocationResult(exit_code=0, stdout=json.dumps({"display": "now"}), stderr="")
        if name == "list":
            skills = ["NSPL.Tools.Time.now", "Game.DST.Snapshot.read", "Voice.Speak", "Voice.Listen"]
            if self.include_rohtalk:
                skills.extend(["RohTalk.start", "RohTalk.chat", "RohTalk.list_conversations"])
            return SkillInvocationResult(exit_code=0, stdout="\n".join(skills), stderr="")
        if name == "Voice.Speak":
            if "--check" in argv:
                return SkillInvocationResult(exit_code=0, stdout=json.dumps({"ok": True, "provider": "speechnote"}), stderr="")
            return SkillInvocationResult(exit_code=0, stdout=json.dumps({"ok": True, "message": "SpeechNote speak command sent."}), stderr="")
        if name == "Voice.Listen":
            if not self.listen_ok:
                return SkillInvocationResult(
                    exit_code=1,
                    stdout=json.dumps(
                        {
                            "ok": False,
                            "provider": "speechnote",
                            "transcript": "",
                            "method": "clipboard",
                            "error": "No new SpeechNote transcript detected.",
                            "changed": False,
                        }
                    ),
                    stderr="No new SpeechNote transcript detected.",
                )
            return SkillInvocationResult(
                exit_code=0,
                stdout=json.dumps(
                    {
                        "ok": True,
                        "provider": "speechnote",
                        "transcript": self.listen_transcript,
                        "method": "clipboard",
                        "error": None,
                    }
                ),
                stderr="",
            )
        if name == "RohTalk.list_conversations":
            if self.operator_conversation_id:
                line = (
                    f"[0] Roh Operator Station | {self.operator_conversation_id[:8]} | "
                    f"2026-06-07T12:00:00Z | {self.operator_conversation_id}"
                )
                return SkillInvocationResult(exit_code=0, stdout=line, stderr="")
            return SkillInvocationResult(exit_code=0, stdout="", stderr="")
        if name == "RohTalk.start":
            self.operator_conversation_id = "abc123def456"
            return SkillInvocationResult(
                exit_code=0,
                stdout="conversation_id: abc123def456\ntitle: Roh Operator Station\nRoh is online.",
                stderr="",
            )
        if name == "RohTalk.chat":
            return SkillInvocationResult(exit_code=0, stdout="Still here on the same thread.", stderr="[step 1]\n")
        if name == "Game.DST.Snapshot.read":
            if not self.snapshot_ok:
                return SkillInvocationResult(exit_code=1, stdout=json.dumps({"ok": False}), stderr="No valid RohBridge DST snapshot found")
            payload = {
                "ok": True,
                "path": str(self.snapshot_path or REPO_ROOT / "roh_dst_snapshot.json"),
                "world": {"day": 11, "season": "autumn", "phase": "day"},
                "players": [{"name": "KanraTaro"}],
                "director_hint": "No urgent signal detected.",
            }
            return SkillInvocationResult(exit_code=0, stdout=json.dumps(payload), stderr="")
        return SkillInvocationResult(exit_code=1, stdout="", stderr="unexpected skill")


class RohOperatorStationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_app_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        snapshot_path = Path(self.temp_dir.name) / "roh_dst_snapshot.json"
        snapshot_path.write_text("{}", encoding="utf-8")
        self.context = FakeContext(snapshot_path=snapshot_path)
        self.app = self.module.create_app(self.context)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _endpoint(self, path: str):
        for route in self.app.routes:
            if getattr(route, "path", None) == path:
                return route.endpoint
        raise AssertionError(f"route not found: {path}")

    def _render(self, response) -> str:
        return response.template.render(response.context)

    def test_web_discovery_lists_operator_station(self) -> None:
        registry = discover_web_apps(REPO_ROOT / "Web")
        self.assertIn("Roh.OperatorStation", registry)
        self.assertEqual(registry["Roh.OperatorStation"]["meta"]["default_port"], 8780)

    def test_health_returns_app_name(self) -> None:
        result = asyncio.run(self._endpoint("/health")())
        self.assertEqual(result, {"ok": True, "app": "Roh.OperatorStation"})

    def test_api_status_uses_safe_skill_probes(self) -> None:
        result = asyncio.run(self._endpoint("/api/status")())
        self.assertIn(result["ui"]["overall_status"], {"ONLINE", "DEGRADED"})
        self.assertTrue(result["skillcli"]["available"])
        self.assertTrue(result["rohtalk"]["available"])
        self.assertEqual(result["voice"]["value"], "SpeechNote")
        self.assertEqual(result["dst"]["status"], "LIVE")
        self.assertEqual(
            [call[0] for call in self.context.calls],
            [
                ["NSPL.Tools.Time.now", "--json"],
                ["list"],
                ["Game.DST.Snapshot.read", "--json"],
                ["Voice.Speak", "--check", "--provider", "speechnote", "--json"],
                ["RohTalk.list_conversations"],
            ],
        )
        self.assertLessEqual(self.context.calls[0][1], 4.0)

    def test_index_renders_required_panels_and_enabled_prompts(self) -> None:
        response = asyncio.run(self._endpoint("/")(_FakeRequest({})))
        html = self._render(response)

        self.assertIn("Roh Operator Station", html)
        self.assertIn("LOCAL OPERATOR", html)
        self.assertNotIn("First Clip Mode", html)
        self.assertIn("NSPL Root", html)
        self.assertIn("SkillCLI", html)
        self.assertIn("RohTalk", html)
        self.assertIn("Voice Provider", html)
        self.assertIn("DST Bridge", html)
        self.assertIn('id="roh-command-panel"', html)
        self.assertIn('id="roh-response-panel"', html)
        self.assertIn('id="action-trace-panel"', html)
        self.assertIn('id="dst-bridge-panel"', html)
        self.assertIn("Roh responses will appear here.", html)
        self.assertIn("Tool calls and skill results will appear here.", html)
        self.assertIn("Roh, are you online?", html)
        self.assertIn("Check DST bridge", html)
        self.assertIn("Say hi in DST", html)
        self.assertIn("Warn us before night", html)
        self.assertIn('class="primary-action">Send</button>', html)
        self.assertIn('name="demo_prompt" value="Check DST bridge"', html)
        self.assertIn("Auto-speak Roh responses", html)
        self.assertIn("Send now prompts", html)
        self.assertIn("Roh is thinking...", html)

    def test_missing_dst_snapshot_is_reported(self) -> None:
        context = FakeContext(snapshot_ok=False)
        app = self.module.create_app(context)
        for route in app.routes:
            if getattr(route, "path", None) == "/api/status":
                result = asyncio.run(route.endpoint())
                break
        else:
            raise AssertionError("api route not found")

        self.assertEqual(result["dst"]["status"], "MISSING")
        self.assertFalse(result["dst"]["snapshot_found"])

    def test_send_starts_then_reuses_persistent_rohtalk_conversation(self) -> None:
        send_endpoint = self._endpoint("/send")

        first_html = self._render(asyncio.run(send_endpoint(_FakeRequest({"prompt": "Roh, are you online?"}))))
        self.assertIn("Roh is online.", first_html)
        self.assertIn("abc123de", first_html)
        self.assertIn("RohTalk.start", first_html)
        self.assertIn("response-updated", first_html)
        self.assertIn("trace-updated", first_html)
        self.assertIn("Updated just now", first_html)
        self.assertNotIn(">Roh, are you online?</textarea>", first_html)

        second_html = self._render(asyncio.run(send_endpoint(_FakeRequest({"prompt": "Check DST bridge"}))))
        self.assertIn("Still here on the same thread.", second_html)
        self.assertIn("RohTalk.chat", second_html)

        call_names = [call[0][0] for call in self.context.calls]
        self.assertIn("RohTalk.start", call_names)
        self.assertIn("RohTalk.chat", call_names)
        chat_call = [call for call in self.context.calls if call[0][0] == "RohTalk.chat"][-1][0]
        self.assertEqual(chat_call[:6], ["RohTalk.chat", "--tools", "--toolkit", "dst_director", "--tool-trace", "abc123def456"])

    def test_demo_prompt_sends_immediately(self) -> None:
        html = self._render(
            asyncio.run(
                self._endpoint("/send")(
                    _FakeRequest({"prompt": "ignored typed text", "demo_prompt": "Warn us before night"})
                )
            )
        )

        self.assertIn("Roh is online.", html)
        start_call = [call for call in self.context.calls if call[0][0] == "RohTalk.start"][-1][0]
        self.assertEqual(start_call[-1], "Warn us before night")

    def test_auto_speak_calls_voice_after_successful_send(self) -> None:
        html = self._render(
            asyncio.run(
                self._endpoint("/send")(
                    _FakeRequest({"prompt": "Roh, are you online?", "auto_speak": "on"})
                )
            )
        )

        self.assertIn("Speech sent.", html)
        speak_calls = [call for call in self.context.calls if call[0][0] == "Voice.Speak" and "--text" in call[0]]
        self.assertTrue(speak_calls)

    def test_listen_fills_command_textarea(self) -> None:
        html = self._render(asyncio.run(self._endpoint("/listen")(_FakeRequest({}))))

        self.assertIn("Transcript ready.", html)
        self.assertIn(">Roh, give me a status report.</textarea>", html)
        listen_call = [call for call in self.context.calls if call[0][0] == "Voice.Listen"][-1][0]
        self.assertEqual(listen_call, ["Voice.Listen", "--provider", "speechnote", "--timeout", "20", "--json"])

    def test_listen_failure_preserves_command_textarea(self) -> None:
        context = FakeContext(snapshot_ok=True, listen_ok=False)
        app = self.module.create_app(context)
        listen_endpoint = None
        for route in app.routes:
            if getattr(route, "path", None) == "/listen":
                listen_endpoint = route.endpoint
                break
        if listen_endpoint is None:
            raise AssertionError("listen route not found")

        html = self._render(asyncio.run(listen_endpoint(_FakeRequest({"prompt": "keep this command"}))))

        self.assertIn("No new SpeechNote transcript detected.", html)
        self.assertIn(">keep this command</textarea>", html)

    def test_speak_calls_voice_skill_with_latest_response(self) -> None:
        response = asyncio.run(
            self._endpoint("/speak")(
                _FakeRequest(
                    {
                        "response_text": "Roh is online.",
                        "latest_prompt": "Roh?",
                        "conversation_id": "abc123def456",
                    }
                )
            )
        )
        html = self._render(response)

        self.assertIn("Speech sent.", html)
        speak_call = [call for call in self.context.calls if call[0][0] == "Voice.Speak" and "--text" in call[0]][-1][0]
        self.assertEqual(speak_call, ["Voice.Speak", "--provider", "speechnote", "--text", "Roh is online.", "--json"])


class _FakeRequest:
    def __init__(self, form: dict[str, str]):
        self._form = form
        self.headers = {}
        self.scope = {"type": "http", "method": "GET", "path": "/"}

    async def form(self):
        return self._form

    async def body(self):
        return b""


if __name__ == "__main__":
    unittest.main()
