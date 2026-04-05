import unittest

from Core.Video.frames import build_pingpong_sequence
from Core.Video.fit import FitMode, TargetSize, build_fit_filter
from Core.Video.export import ExportOptions, build_export_args
from Core.Video.frames_to_video import FramesToVideoOptions, prepare_frames_to_video


class TestVideoCore(unittest.TestCase):
    def test_pingpong_sequence_skips_ends(self) -> None:
        frames = ["A.png", "B.png", "C.png", "D.png"]
        seq = build_pingpong_sequence(frames)
        # forward: A B C D
        # reverse: C B
        self.assertEqual(seq, ["A.png", "B.png", "C.png", "D.png", "C.png", "B.png"])

    def test_fit_filter_pad(self) -> None:
        vf = build_fit_filter(TargetSize(w=1080, h=1920), FitMode.pad)
        self.assertIn("force_original_aspect_ratio=decrease", vf)
        self.assertIn("pad=1080:1920", vf)

    def test_fit_filter_crop(self) -> None:
        vf = build_fit_filter(TargetSize(w=1080, h=1920), FitMode.crop)
        self.assertIn("force_original_aspect_ratio=increase", vf)
        self.assertIn("crop=1080:1920", vf)

    def test_export_args_contains_vf_and_output(self) -> None:
        # use a raw vf (no file IO)
        opts = ExportOptions(
            input_path="in.mp4",
            output_path="out.mp4",
            vf="eq=contrast=1.2,format=yuv420p",
            preset="fast",
            target="1080x1920",
            fit="pad",
        )
        args = build_export_args(opts)
        self.assertIn("-vf", args)
        self.assertEqual(args[-1], "out.mp4")

    def test_prepare_frames_to_video_estimates_duration(self) -> None:
        # This is a unit test for math and arg structure only, it does not run ffmpeg.
        # We just need a real dir with fake names, so we create a temp dir and files.
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            # Create 4 png files so pingpong has 6 sequence frames.
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
                self.assertIn("-progress", prep.args)
                self.assertIn("pipe:1", prep.args)
            finally:
                prep.cleanup()


if __name__ == "__main__":
    unittest.main()

