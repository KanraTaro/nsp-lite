from __future__ import annotations

import argparse
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from Skills.Voice.Listen import skill


class VoiceListenSkillTests(unittest.TestCase):
    def _run(self, argv: list[str], *, json_flag: bool = True):
        parser = argparse.ArgumentParser()
        skill.build_parser(parser)
        args = parser.parse_args(argv)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = skill.run(args, SimpleNamespace(json=json_flag))
        return code, stdout.getvalue().strip(), stderr.getvalue().strip()

    @patch("Core.Voice.speechnote.shutil.which")
    @patch("Core.Voice.speechnote.subprocess.run")
    def test_listen_returns_clipboard_transcript(self, run_mock, which_mock) -> None:
        which_mock.side_effect = lambda name: f"/usr/bin/{name}" if name == "wl-paste" else None
        clipboard_reads = iter(["old clipboard text", "Roh, status report."])

        def fake_run(command, **_kwargs):
            if command[:2] == ["flatpak", "info"]:
                return SimpleNamespace(returncode=0, stdout="SpeechNote", stderr="")
            if command[:2] == ["flatpak", "run"]:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            if command == ["wl-paste"]:
                return SimpleNamespace(returncode=0, stdout=next(clipboard_reads), stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

        run_mock.side_effect = fake_run

        code, stdout, stderr = self._run(["--provider", "speechnote", "--timeout", "5"])
        payload = json.loads(stdout)

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["transcript"], "Roh, status report.")
        self.assertEqual(payload["method"], "clipboard")
        self.assertEqual(payload["clipboard_tool"], "wl-paste")
        self.assertTrue(payload["changed"])
        self.assertGreater(payload["initial_clipboard_length"], 0)
        self.assertGreater(payload["final_clipboard_length"], 0)

    @patch("Core.Voice.speechnote.shutil.which")
    @patch("Core.Voice.speechnote.subprocess.run")
    def test_unchanged_clipboard_times_out_without_returning_old_text(self, run_mock, which_mock) -> None:
        which_mock.side_effect = lambda name: f"/usr/bin/{name}" if name == "wl-paste" else None

        def fake_run(command, **_kwargs):
            if command[:2] == ["flatpak", "info"]:
                return SimpleNamespace(returncode=0, stdout="SpeechNote", stderr="")
            if command[:2] == ["flatpak", "run"]:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            if command == ["wl-paste"]:
                return SimpleNamespace(returncode=0, stdout="old clipboard text", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

        run_mock.side_effect = fake_run

        code, stdout, _stderr = self._run(["--timeout", "1", "--poll-interval", "0.01"])
        payload = json.loads(stdout)

        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["transcript"], "")
        self.assertFalse(payload["changed"])
        self.assertIn("No new SpeechNote transcript detected.", payload["error"])

    @patch("Core.Voice.speechnote.shutil.which", return_value=None)
    @patch("Core.Voice.speechnote.subprocess.run")
    def test_missing_clipboard_tool_returns_clear_error(self, run_mock, _which_mock) -> None:
        def fake_run(command, **_kwargs):
            if command[:2] == ["flatpak", "info"]:
                return SimpleNamespace(returncode=0, stdout="SpeechNote", stderr="")
            if command[:2] == ["flatpak", "run"]:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

        run_mock.side_effect = fake_run

        code, stdout, _stderr = self._run(["--timeout", "5"])
        payload = json.loads(stdout)

        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assertIn("clipboard reader", payload["error"])

    @patch("Core.Voice.speechnote.subprocess.run")
    def test_missing_speechnote_returns_clear_error(self, run_mock) -> None:
        run_mock.return_value = SimpleNamespace(returncode=1, stdout="", stderr="SpeechNote missing")

        code, stdout, _stderr = self._run(["--timeout", "5"])
        payload = json.loads(stdout)

        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["provider"], "speechnote")
        self.assertEqual(payload["method"], "clipboard")
        self.assertEqual(payload["transcript"], "")


if __name__ == "__main__":
    unittest.main()
