import unittest
from Core.Video.export import ExportOptions, build_export_args


class TestExportSkill(unittest.TestCase):
    def test_build_export_args_vf_only(self) -> None:
        opts = ExportOptions(
            input_path="in.mp4",
            output_path="out.mp4",
            vf="eq=contrast=1.2",
            preset="hq",
        )
        args = build_export_args(opts)
        self.assertIn("-vf", args)
        self.assertEqual(args[-1], "out.mp4")


if __name__ == "__main__":
    unittest.main()

