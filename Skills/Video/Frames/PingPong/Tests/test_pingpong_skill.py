import os
import tempfile
import unittest

from Core.Video.frames_to_video import FramesToVideoOptions, prepare_frames_to_video


class TestPingPongSkill(unittest.TestCase):
    def test_prepare_pingpong_sequence_shape(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            for name in ["A.png", "B.png", "C.png"]:
                with open(os.path.join(d, name), "wb") as f:
                    f.write(b"\x89PNG\r\n\x1a\n")

            opts = FramesToVideoOptions(
                frames_dir=d,
                output_path=os.path.join(d, "out.mp4"),
                fps=12,
                pattern="*.png",
                mode="pingpong",
                include_progress=False,
            )

            prep = prepare_frames_to_video(opts)
            try:
                self.assertEqual(prep.frame_count, 3)
                self.assertEqual(prep.sequence_count, 4)  # A B C B
            finally:
                prep.cleanup()


if __name__ == "__main__":
    unittest.main()
