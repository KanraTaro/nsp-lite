import unittest

from Core.Video.frames import build_pingpong_sequence
from Core.Video.fit import FitMode, TargetSize, build_fit_filter
from Core.Video.export import ExportOptions, build_export_args


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


if __name__ == "__main__":
    unittest.main()

