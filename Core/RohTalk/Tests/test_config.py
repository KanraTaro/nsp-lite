"""Tests for RohTalk model runtime configuration."""

from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

import Core.NSPL.NodeCTX as NodeCTX
from Core.NSPL.SkillCLI.ctx import SkillContext
from Core.RohTalk.config import (
    load_config,
    parse_model_option_args,
    resolve_model_profile,
)


class RohTalkConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ctx = SkillContext(
            root=self.root,
            node_tag="testnode",
            instance_id="testinstance",
            global_scope=False,
            node_ctx=NodeCTX,
            debug=False,
            json=False,
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_repo_config(self, payload: dict) -> None:
        path = self.root / "Config" / "RohTalk" / "config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_load_config_keeps_backward_compatibility_with_default_model_only(self) -> None:
        self._write_repo_config({"default_model": "gpt-oss:20b"})

        config = load_config(self.ctx)

        self.assertEqual(config.default_model, "gpt-oss:20b")
        self.assertEqual(config.default_options, {})
        self.assertEqual(config.profiles, {})

    def test_load_config_reads_default_options_and_profiles(self) -> None:
        self._write_repo_config(
            {
                "default_model": "gpt-oss:20b",
                "default_options": {"think": "low"},
                "profiles": {
                    "dst_director_fast": {
                        "model": "qwen3:8b",
                        "options": {"think": False},
                    }
                },
            }
        )

        config = load_config(self.ctx)

        self.assertEqual(config.default_options, {"think": "low"})
        self.assertEqual(config.profiles["dst_director_fast"]["model"], "qwen3:8b")
        self.assertEqual(config.profiles["dst_director_fast"]["options"], {"think": False})

    def test_resolve_model_profile_merges_profile_and_overrides(self) -> None:
        self._write_repo_config(
            {
                "default_model": "gpt-oss:20b",
                "default_options": {"think": "low", "temperature": 0.2},
                "profiles": {
                    "fast": {
                        "model": "qwen3:8b",
                        "host": "http://profile-host",
                        "options": {"think": False},
                    }
                },
            }
        )

        resolved = resolve_model_profile(
            self.ctx,
            "fast",
            model_override="manual:model",
            host_override="http://manual-host",
            option_overrides={"temperature": 0.0},
        )

        self.assertEqual(resolved.profile_name, "fast")
        self.assertEqual(resolved.model, "manual:model")
        self.assertEqual(resolved.host, "http://manual-host")
        self.assertEqual(resolved.options, {"think": False, "temperature": 0.0})

    def test_parse_model_option_args_parses_json_literals(self) -> None:
        self.assertEqual(
            parse_model_option_args(["think=false", "temperature=0.1", "label=fast"]),
            {"think": False, "temperature": 0.1, "label": "fast"},
        )


if __name__ == "__main__":
    unittest.main()
