"""Unit tests for AutoRoh observation helpers."""

from __future__ import annotations

import hashlib
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from Core.AutoRoh.observations import call_observation_tool


class AutoRohObservationTests(unittest.TestCase):
    def test_call_observation_tool_uses_signature_basis_for_signature(self) -> None:
        ctx = object()
        result = {
            "ok": True,
            "source": "test",
            "world": {
                "day": 3,
                "phase": "dusk",
            },
            "signature_basis": {
                "world": {
                    "day": 3,
                    "phase": "dusk",
                },
                "signals": ["dusk_active"],
            },
        }
        toolkit = SimpleNamespace(
            skill_name_map={"snapshot_read": "Game.DST.Snapshot.read"},
        )

        with (
            patch("Core.RohTalk.toolkits.resolve_toolkit", return_value=toolkit) as resolve_toolkit,
            patch("Core.RohTalk.skillcli_tools.execute_skill", return_value=result) as execute_skill,
        ):
            signature, summary = call_observation_tool(
                ctx,
                toolkit_name="dst_director",
                tool_name="snapshot_read",
            )

        resolve_toolkit.assert_called_once_with("dst_director")
        execute_skill.assert_called_once_with(ctx, "Game.DST.Snapshot.read", {})

        expected_summary = json.dumps(result, separators=(",", ":"), sort_keys=True)
        expected_signature_source = json.dumps(
            result["signature_basis"],
            separators=(",", ":"),
            sort_keys=True,
        )
        expected_signature = hashlib.sha256(
            expected_signature_source.encode("utf-8"),
        ).hexdigest()

        self.assertEqual(summary, expected_summary)
        self.assertEqual(signature, expected_signature)

    def test_call_observation_tool_empty_tool_name_returns_none_without_calls(self) -> None:
        with (
            patch("Core.RohTalk.toolkits.resolve_toolkit") as resolve_toolkit,
            patch("Core.RohTalk.skillcli_tools.execute_skill") as execute_skill,
        ):
            signature, summary = call_observation_tool(
                object(),
                toolkit_name="dst_director",
                tool_name="   ",
            )

        self.assertIsNone(signature)
        self.assertIsNone(summary)
        resolve_toolkit.assert_not_called()
        execute_skill.assert_not_called()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
