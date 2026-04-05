import unittest

from Core.Video.frames_to_video import FramesToVideoOptions, prepare_frames_to_video


class TestBuildVideoSkill(unittest.TestCase):
    def test_prepare_build_video_forward(self) -> None:
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            for name in ["A1.png", "A2.png", "A3.png"]:
                with open(os.path.join(d, name), "wb") as f:
                    f.write(b"\x89PNG\r\n\x1a\n")

            opts = FramesToVideoOptions(
                frames_dir=d,
                output_path=os.path.join(d, "out.mp4"),
                fps=12,
                pattern="*.png",
                mode="forward",
                include_progress=True,
            )

            prep = prepare_frames_to_video(opts)
            try:
                self.assertEqual(prep.frame_count, 3)
                self.assertEqual(prep.sequence_count, 3)
                self.assertGreater(prep.duration_ms, 0)
                self.assertIn("-progress", prep.args)
                self.assertIn("pipe:1", prep.args)
            finally:
                prep.cleanup()

    def test_prepare_build_video_pingpong(self) -> None:
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            for name in ["A1.png", "A2.png", "A3.png", "A4.png"]:
                with open(os.path.join(d, name), "wb") as f:
                    f.write(b"\x89PNG\r\n\x1a\n")

            opts = FramesToVideoOptions(
                frames_dir=d,
                output_path=os.path.join(d, "out.mp4"),
                fps=12,
                pattern="*.png",
                mode="pingpong",
                include_progress=True,
            )

            prep = prepare_frames_to_video(opts)
            try:
                self.assertEqual(prep.frame_count, 4)
                self.assertEqual(prep.sequence_count, 6)
                self.assertGreater(prep.duration_ms, 0)
            finally:
                prep.cleanup()


if __name__ == "__main__":
    unittest.main()
