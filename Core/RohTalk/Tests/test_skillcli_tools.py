"""Unit tests for RohTalk SkillCLI execution helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import Core.NSPL.NodeCTX as NodeCTX
from Core.NSPL.SkillCLI.ctx import SkillContext
from Core.LLMClient.types import ToolCall
from Core.RohTalk.skillcli_tools import (
    DST_DIRECTOR_RESULT_INTERVAL_SECONDS,
    DST_DIRECTOR_RESULT_TIMEOUT_SECONDS,
    _arg_name_to_flag,
    _dict_to_argv,
    build_tool_name_map,
    canonical_skill_name_to_tool_name,
    execute_skill,
)
from Core.RohTalk.tool_runner import execute_tool_call


class SkillCLIToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]

        self.ctx = SkillContext(
            root=repo_root,
            node_tag="testnode",
            instance_id="testinstance",
            global_scope=False,
            node_ctx=NodeCTX,
            debug=False,
            json=False,
        )

    def test_arg_name_to_flag_converts_underscores_to_dashes(self) -> None:
        self.assertEqual(_arg_name_to_flag("city_name"), "--city-name")
        self.assertEqual(_arg_name_to_flag("format"), "--format")

    def test_arg_name_to_flag_rejects_empty_name(self) -> None:
        with self.assertRaises(ValueError):
            _arg_name_to_flag("")

        with self.assertRaises(ValueError):
            _arg_name_to_flag("   ")

    def test_dict_to_argv_omits_none_and_false(self) -> None:
        argv = _dict_to_argv(
            {
                "city": "Orlando",
                "debug": False,
                "host": None,
            }
        )
        self.assertEqual(argv, ["--city", "Orlando"])

    def test_dict_to_argv_emits_true_boolean_as_flag(self) -> None:
        argv = _dict_to_argv({"verbose": True})
        self.assertEqual(argv, ["--verbose"])

    def test_dict_to_argv_emits_scalar_values_as_flag_value_pairs(self) -> None:
        argv = _dict_to_argv(
            {
                "city": "Orlando",
                "count": 3,
                "ratio": 1.5,
            }
        )
        self.assertEqual(
            argv,
            ["--city", "Orlando", "--count", "3", "--ratio", "1.5"],
        )

    def test_dict_to_argv_repeats_flags_for_list_values(self) -> None:
        argv = _dict_to_argv(
            {
                "tag": ["one", "two", "three"],
            }
        )
        self.assertEqual(
            argv,
            ["--tag", "one", "--tag", "two", "--tag", "three"],
        )

    def test_dict_to_argv_serializes_dict_values_as_json(self) -> None:
        argv = _dict_to_argv(
            {
                "payload": {
                    "city": "Orlando",
                    "temp_f": 82,
                }
            }
        )
        self.assertEqual(
            argv,
            ['--payload', '{"city":"Orlando","temp_f":82}'],
        )

    def test_canonical_skill_name_to_tool_name_uses_public_naming_policy(self) -> None:
        self.assertEqual(
            canonical_skill_name_to_tool_name("NSPL.Tools.Weather.get"),
            "get_weather",
        )
        self.assertEqual(
            canonical_skill_name_to_tool_name("NSPL.Tools.Time.now"),
            "time_now",
        )

    def test_build_tool_name_map_uses_semantic_names(self) -> None:
        result = build_tool_name_map(
            [
                "NSPL.Tools.Weather.get",
                "NSPL.Tools.Time.now",
            ]
        )

        expected = {
            "get_weather": "NSPL.Tools.Weather.get",
            "time_now": "NSPL.Tools.Time.now",
        }

        self.assertEqual(result, expected)

    def test_build_tool_name_map_uses_namespaced_fallback_on_collision(self) -> None:
        result = build_tool_name_map(
            [
                "NSPL.Tools.Weather.get",
                "Game.Tools.Weather.get",
            ]
        )

        expected = {
            "nspl_get_weather": "NSPL.Tools.Weather.get",
            "game_get_weather": "Game.Tools.Weather.get",
        }

        self.assertEqual(result, expected)

    def test_execute_skill_runs_json_printing_skill(self) -> None:
        result = execute_skill(
            self.ctx,
            "NSPL.Tools.Weather.get",
            {"city": "Orlando"},
        )

        expected = {
            "city": "Orlando",
            "forecast": "Partly cloudy",
            "temp_f": 82,
        }

        self.assertEqual(result, expected)

    def test_execute_skill_runs_time_skill_as_json(self) -> None:
        result = execute_skill(
            self.ctx,
            "NSPL.Tools.Time.now",
            {},
        )

        self.assertIsInstance(result, dict)
        self.assertIn("utc_iso", result)
        self.assertIn("local_iso", result)
        self.assertIn("date", result)
        self.assertIn("time", result)
        self.assertIn("weekday", result)
        self.assertIn("timezone", result)
        self.assertIn("timezone_abbreviation", result)
        self.assertIn("utc_offset", result)
        
    def test_execute_skill_runs_time_skill_with_timezone_argument(self) -> None:
        result = execute_skill(
            self.ctx,
            "NSPL.Tools.Time.now",
            {"timezone": "America/New_York"},
        )

        self.assertEqual(result["timezone"], "America/New_York")
        self.assertEqual(result["timezone_abbreviation"], "EDT")
        self.assertEqual(result["utc_offset"], "-04:00")

    def test_execute_skill_queues_dst_director_command_and_waits_for_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            command_path = Path(temp_dir) / "roh_dst_command.json"
            result_path = Path(temp_dir) / "roh_dst_command_result.json"
            bridge_result = {
                "schema_version": "dst.v0.3.command_result",
                "command_id": "cmd-rohtalk",
                "type": "set_chaos_tier",
                "ok": False,
                "status": "rejected",
                "reason": "test_rejection",
            }
            result_path.write_text(json.dumps(bridge_result), encoding="utf-8")

            result = execute_skill(
                self.ctx,
                "Game.DST.Chaos.set_tier",
                {
                    "chaos_tier": 2,
                    "path": str(command_path),
                    "command_id": "cmd-rohtalk",
                    "result_timeout": 0.1,
                    "result_interval": 0.01,
                },
            )

        self.assertFalse(result["ok"])
        self.assertTrue(result["queued"])
        self.assertEqual(result["bridge_result"], bridge_result)

    def test_dst_tool_missing_required_args_returns_clear_tool_error(self) -> None:
        tool_call = ToolCall(
            id="call-missing-chaos-tier",
            name="chaos_set_tier",
            arguments={},
            arguments_json="{}",
        )

        result = execute_tool_call(
            tool_call,
            execution_mode="skillcli",
            ctx=self.ctx,
            skill_name_map={"chaos_set_tier": "Game.DST.Chaos.set_tier"},
            skill_executor=execute_skill,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["tool_name"], "chaos_set_tier")
        self.assertIn("argument parsing failed", result["error"])
        self.assertIn("--chaos-tier", result["error"])

    def test_execute_skill_uses_longer_dst_director_result_wait_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            command_path = Path(temp_dir) / "roh_dst_command.json"
            result_path = Path(temp_dir) / "roh_dst_command_result.json"

            with patch(
                "Skills.Game.DST._command_skill.wait_for_command_result",
                side_effect=TimeoutError("timeout for test"),
            ) as wait_result:
                result = execute_skill(
                    self.ctx,
                    "Game.DST.Chaos.set_tier",
                    {
                        "chaos_tier": 2,
                        "path": str(command_path),
                        "command_id": "cmd-defaults",
                    },
                )

        wait_result.assert_called_once_with(
            "cmd-defaults",
            result_path,
            DST_DIRECTOR_RESULT_TIMEOUT_SECONDS,
            DST_DIRECTOR_RESULT_INTERVAL_SECONDS,
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["queued"])
        self.assertEqual(result["command_id"], "cmd-defaults")
        self.assertEqual(result["path"], str(command_path.with_name("roh_dst_command_queue.json")))
        self.assertEqual(result["result_path"], str(result_path))
        self.assertEqual(result["reason"], "result_timeout")
        self.assertEqual(result["status"], "queued_unknown")
        self.assertEqual(
            result["message"],
            "Command was queued but no matching RohBridge result was observed before timeout.",
        )

    def test_execute_skill_raises_for_missing_skill(self) -> None:
        with self.assertRaises(Exception):
            execute_skill(
                self.ctx,
                "NSPL.Tools.DoesNotExist.missing",
                {},
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
