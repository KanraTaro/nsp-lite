import unittest
from Core.Video.frames import build_pingpong_sequence


class TestPingPongSkill(unittest.TestCase):
    def test_sequence_shape(self) -> None:
        frames = ["A", "B", "C"]
        seq = build_pingpong_sequence(frames)
        # A B C then B
        self.assertEqual(seq, ["A", "B", "C", "B"])


if __name__ == "__main__":
    unittest.main()

