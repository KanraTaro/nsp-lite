import os
import unittest

from Core.NSPL.Deps.deps import (
    DependencyError,
    ffmpeg_install_hints,
    require_executable,
    which,
)


class TestDeps(unittest.TestCase):
    def test_which_handles_missing(self) -> None:
        path = which("definitely_not_a_real_executable_kanra")
        self.assertTrue(path is None)

    def test_require_executable_ffmpeg_or_skip(self) -> None:
        try:
            info = require_executable(
                "ffmpeg",
                env_vars=("NSP_FFMPEG",),
                install_hints=ffmpeg_install_hints(),
            )
        except DependencyError:
            self.skipTest("ffmpeg not installed on this machine (expected on some test environments).")
            return

        self.assertTrue(os.path.isabs(info.path))
        self.assertTrue("ffmpeg" in info.version.lower() or "version" in info.version.lower())

    def test_require_executable_respects_env_override_if_set(self) -> None:
        # This test is intentionally soft: only asserts behavior when NSP_FFMPEG is set.
        override = os.environ.get("NSP_FFMPEG")
        if override is None or override.strip() == "":
            self.skipTest("NSP_FFMPEG not set; skipping env override test.")
            return

        info = require_executable(
            "ffmpeg",
            env_vars=("NSP_FFMPEG",),
            install_hints=ffmpeg_install_hints(),
        )
        self.assertTrue(os.path.isabs(info.path))


if __name__ == "__main__":
    unittest.main()

