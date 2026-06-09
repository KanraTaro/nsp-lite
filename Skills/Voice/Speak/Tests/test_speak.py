from __future__ import annotations

import argparse
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from Skills.Voice.Speak import skill


class VoiceSpeakSkillTests(unittest.TestCase):
    def _run(self, argv: list[str], *, json_flag: bool = True):
        parser = argparse.ArgumentParser()
        skill.build_parser(parser)
        args = parser.parse_args(argv)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = skill.run(args, SimpleNamespace(json=json_flag))
        return code, stdout.getvalue().strip(), stderr.getvalue().strip()

    @patch("Core.Voice.speechnote.subprocess.run")
    def test_check_returns_json_success(self, run_mock) -> None:
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = "Name: SpeechNote"
        run_mock.return_value.stderr = ""

        code, stdout, stderr = self._run(["--check", "--provider", "speechnote"])
        payload = json.loads(stdout)

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["provider"], "speechnote")
        self.assertEqual(run_mock.call_args.args[0], ["flatpak", "info", "net.mkiol.SpeechNote"])

    @patch("Core.Voice.speechnote.subprocess.run")
    def test_speak_uses_flatpak_action(self, run_mock) -> None:
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = ""
        run_mock.return_value.stderr = ""

        code, stdout, _stderr = self._run(["--text", "Roh is online."])
        payload = json.loads(stdout)

        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(run_mock.call_args_list[0].args[0], ["flatpak", "info", "net.mkiol.SpeechNote"])
        self.assertEqual(
            run_mock.call_args_list[1].args[0],
            [
                "flatpak",
                "run",
                "net.mkiol.SpeechNote",
                "--action",
                "start-reading-text",
                "--text",
                "Roh is online.",
            ],
        )

    def test_empty_text_fails_cleanly(self) -> None:
        code, stdout, stderr = self._run([], json_flag=False)

        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("text is required", stderr)


if __name__ == "__main__":
    unittest.main()
