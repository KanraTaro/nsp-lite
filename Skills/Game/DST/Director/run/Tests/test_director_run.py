"""Tests for Game.DST.Director.run."""

from __future__ import annotations

import argparse
import importlib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch


skill = importlib.import_module("Skills.Game.DST.Director.run.skill")


def parse_args(*argv: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    skill.build_parser(parser)
    return parser.parse_args(list(argv))


class DirectorRunSkillTests(unittest.TestCase):
    def run_skill(self, args: argparse.Namespace):
        stdout = StringIO()
        stderr = StringIO()
        ctx = SimpleNamespace()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = skill.run(args, ctx)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_parser_accepts_v0_flags(self) -> None:
        args = parse_args(
            "--conversation",
            "abc",
            "--title",
            "Live DST",
            "--interval",
            "3",
            "--max-turns",
            "2",
            "--no-tool-trace",
            "--no-idle-skip",
            "--skip-checks",
            "--model",
            "m",
            "--host",
            "h",
        )

        self.assertEqual(args.conversation_ref, "abc")
        self.assertEqual(args.title, "Live DST")
        self.assertEqual(args.interval, 3)
        self.assertEqual(args.max_turns, 2)
        self.assertFalse(args.tool_trace)
        self.assertFalse(args.idle_skip)
        self.assertTrue(args.skip_checks)
        self.assertEqual(args.model, "m")
        self.assertEqual(args.host, "h")

    def test_once_alias_sets_one_max_turn(self) -> None:
        args = parse_args("--once")

        self.assertEqual(args.max_turns, 1)

    def test_default_config_is_product_shaped(self) -> None:
        args = parse_args("--skip-checks")

        with patch.object(skill, "create_conversation", return_value=("new_conv", "")):
            with patch.object(skill, "run_autoroh_loop", return_value=0) as run_loop:
                code, _stdout, _stderr = self.run_skill(args)

        self.assertEqual(code, 0)
        config = run_loop.call_args.args[1]
        self.assertTrue(config.forever)
        self.assertTrue(config.idle_skip)
        self.assertTrue(config.tool_trace)
        self.assertEqual(config.interval, 10.0)

    def test_max_turns_disables_forever_and_passes_count(self) -> None:
        args = parse_args("--skip-checks", "--max-turns", "7")

        with patch.object(skill, "create_conversation", return_value=("new_conv", "")):
            with patch.object(skill, "run_autoroh_loop", return_value=0) as run_loop:
                code, _stdout, _stderr = self.run_skill(args)

        self.assertEqual(code, 0)
        config = run_loop.call_args.args[1]
        self.assertFalse(config.forever)
        self.assertEqual(config.max_turns, 7)

    def test_no_tool_trace_disables_trace(self) -> None:
        args = parse_args("--skip-checks", "--no-tool-trace")

        with patch.object(skill, "create_conversation", return_value=("new_conv", "")):
            with patch.object(skill, "run_autoroh_loop", return_value=0) as run_loop:
                code, _stdout, _stderr = self.run_skill(args)

        self.assertEqual(code, 0)
        self.assertFalse(run_loop.call_args.args[1].tool_trace)

    def test_no_idle_skip_disables_idle_skip(self) -> None:
        args = parse_args("--skip-checks", "--no-idle-skip")

        with patch.object(skill, "create_conversation", return_value=("new_conv", "")):
            with patch.object(skill, "run_autoroh_loop", return_value=0) as run_loop:
                code, _stdout, _stderr = self.run_skill(args)

        self.assertEqual(code, 0)
        self.assertFalse(run_loop.call_args.args[1].idle_skip)

    def test_conversation_resolves_existing_ref_and_does_not_create(self) -> None:
        args = parse_args("--skip-checks", "--conversation", "short")

        with patch.object(skill, "resolve_conversation_ref", return_value="existing_conv") as resolve:
            with patch.object(skill, "create_conversation") as create:
                with patch.object(skill, "run_autoroh_loop", return_value=0) as run_loop:
                    code, _stdout, _stderr = self.run_skill(args)

        self.assertEqual(code, 0)
        resolve.assert_called_once()
        create.assert_not_called()
        self.assertEqual(run_loop.call_args.args[1].conversation_id, "existing_conv")

    def test_omitted_conversation_creates_conversation_without_model_reply(self) -> None:
        args = parse_args("--skip-checks")

        with patch.object(skill, "create_conversation", return_value=("new_conv", "")) as create:
            with patch.object(skill, "run_autoroh_loop", return_value=0):
                code, _stdout, _stderr = self.run_skill(args)

        self.assertEqual(code, 0)
        create.assert_called_once()
        self.assertTrue(create.call_args.kwargs["skip_model"])

    def test_skip_checks_bypasses_snapshot_preflight(self) -> None:
        args = parse_args("--skip-checks")

        with patch.object(skill, "create_conversation", return_value=("new_conv", "")):
            with patch.object(skill, "call_observation_tool") as preflight:
                with patch.object(skill, "run_autoroh_loop", return_value=0):
                    code, _stdout, _stderr = self.run_skill(args)

        self.assertEqual(code, 0)
        preflight.assert_not_called()

    def test_snapshot_preflight_failure_returns_nonzero_and_does_not_start_loop(self) -> None:
        args = parse_args()

        with patch.object(skill, "create_conversation", return_value=("new_conv", "")):
            with patch.object(skill, "call_observation_tool", side_effect=RuntimeError("missing snapshot")):
                with patch.object(skill, "run_autoroh_loop") as run_loop:
                    code, _stdout, stderr = self.run_skill(args)

        self.assertEqual(code, 1)
        self.assertIn("snapshot_read preflight failed: missing snapshot", stderr)
        run_loop.assert_not_called()

    def test_printed_shell_command_includes_conversation_id(self) -> None:
        args = parse_args("--skip-checks")

        with patch.object(skill, "create_conversation", return_value=("new_conv", "")):
            with patch.object(skill, "run_autoroh_loop", return_value=0):
                code, stdout, _stderr = self.run_skill(args)

        self.assertEqual(code, 0)
        self.assertIn("conversation_id: new_conv", stdout)
        self.assertIn(
            "nspl-skill skill RohTalk.shell --conversation new_conv --tools --toolkit dst_director --tool-trace",
            stdout,
        )

    def test_loop_runner_receives_dst_tool_defaults(self) -> None:
        args = parse_args("--skip-checks")

        with patch.object(skill, "create_conversation", return_value=("new_conv", "")):
            with patch.object(skill, "run_autoroh_loop", return_value=0) as run_loop:
                code, _stdout, _stderr = self.run_skill(args)

        self.assertEqual(code, 0)
        config = run_loop.call_args.args[1]
        self.assertEqual(config.toolkit, "dst_director")
        self.assertTrue(config.tools)
        self.assertEqual(config.observation_tool, "snapshot_read")
        self.assertEqual(config.tool_backend, "skillcli")


if __name__ == "__main__":
    unittest.main()
