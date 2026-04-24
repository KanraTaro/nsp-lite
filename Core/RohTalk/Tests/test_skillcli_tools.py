"""Unit tests for RohTalk SkillCLI execution helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import Core.NSPL.NodeCTX as NodeCTX
from Core.NSPL.SkillCLI.ctx import SkillContext
from Core.RohTalk.skillcli_tools import (
    _arg_name_to_flag,
    _dict_to_argv,
    build_tool_name_map,
    canonical_skill_name_to_tool_name,
    execute_skill,
)


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

    def test_execute_skill_returns_stdout_fallback_for_non_json_skill(self) -> None:
        result = execute_skill(
            self.ctx,
            "NSPL.Tools.Time.now",
            {},
        )

        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stderr"], "")
        self.assertTrue(str(result["stdout"]).strip() != "")

    def test_execute_skill_raises_for_missing_skill(self) -> None:
        with self.assertRaises(Exception):
            execute_skill(
                self.ctx,
                "NSPL.Tools.DoesNotExist.missing",
                {},
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
