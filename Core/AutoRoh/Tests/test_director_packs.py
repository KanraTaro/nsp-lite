"""Tests for AutoRoh director pack helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from Core.AutoRoh.director_packs import load_director_pack, render_director_pack_prompt


DST_PACK_PATH = (
    Path(__file__).resolve().parents[2]
    / "Game"
    / "DST"
    / "DirectorPacks"
    / "dst_director_v0.json"
)
SAFE_PREFABS = {"log", "cutgrass", "twigs", "flint", "silk", "goldnugget"}


class DirectorPackTests(unittest.TestCase):
    def test_loads_dst_pack_json(self) -> None:
        pack = load_director_pack(DST_PACK_PATH)

        self.assertEqual(pack.name, "dst_director_v0")
        self.assertEqual(pack.domain, "dst")

    def test_required_fields_exist(self) -> None:
        pack = load_director_pack(DST_PACK_PATH)

        self.assertTrue(pack.style_lines)
        self.assertTrue(pack.anti_spam_lines)
        self.assertTrue(pack.situation_themes)
        self.assertTrue(pack.announce_examples)
        self.assertTrue(pack.objective_templates)
        self.assertTrue(pack.safe_collect_prefabs)
        self.assertTrue(pack.safe_reward_prefabs)
        self.assertTrue(pack.reward_count_ranges)
        self.assertTrue(pack.constraints)

    def test_safe_prefab_lists_include_expected_prefabs(self) -> None:
        pack = load_director_pack(DST_PACK_PATH)

        self.assertTrue(SAFE_PREFABS.issubset(set(pack.safe_collect_prefabs)))
        self.assertTrue(SAFE_PREFABS.issubset(set(pack.safe_reward_prefabs)))

    def test_render_director_pack_prompt_includes_core_content(self) -> None:
        pack = load_director_pack(DST_PACK_PATH)

        prompt = render_director_pack_prompt(pack)

        self.assertIn("Style:", prompt)
        self.assertIn("Constraints:", prompt)
        self.assertIn("Safe collect prefabs:", prompt)
        self.assertIn("log, cutgrass, twigs, flint, silk, goldnugget", prompt)
        self.assertIn("Announce examples:", prompt)
        self.assertIn("Dusk is settling in", prompt)

    def test_render_director_pack_prompt_includes_canonical_command_guidance(self) -> None:
        pack = load_director_pack(DST_PACK_PATH)

        prompt = render_director_pack_prompt(pack)

        self.assertIn("Use only canonical command_write type values", prompt)
        self.assertIn("announce_text", prompt)
        self.assertNotIn("use type announce", prompt.lower())


if __name__ == "__main__":
    unittest.main()
