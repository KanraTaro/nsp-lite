from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from Core.LifeRPG.store import LifeRPGStore


class LifeRPGTempCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = LifeRPGStore(self.root, node_tag="test-node", global_scope=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()
