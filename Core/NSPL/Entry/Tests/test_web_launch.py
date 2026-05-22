from __future__ import annotations

import builtins
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from Core.NSPL.Entry.Commands import web as web_command
from Core.NSPL.Entry.context import EntryContext
from Core.NSPL.Entry.errors import InvalidWebApp, MissingWebDependencyError
from Core.NSPL.Entry.web_context import WebContext


REPO_ROOT = Path(__file__).resolve().parents[4]
WEB_LAUNCH_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "WebLaunch"


class FakeUvicornRunner:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(self, app, **kwargs) -> None:
        self.calls.append({"app": app, **kwargs})


class EntryWebLaunchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = EntryContext.from_paths(repo_root=REPO_ROOT, caller_cwd=REPO_ROOT)

    def test_web_launch_command_parses_host_port_reload_and_log_level(self) -> None:
        captured: dict[str, object] = {}

        def fake_launch(**kwargs):
            captured.update(kwargs)
            return 0

        with patch.object(web_command, "_launch_web_app", side_effect=fake_launch):
            exit_code = web_command.main(
                [
                    "launch",
                    "Good.App",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "7777",
                    "--reload",
                    "--log-level",
                    "debug",
                ],
                context=self.context,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["app_name"], "Good.App")
        self.assertEqual(captured["host"], "0.0.0.0")
        self.assertEqual(captured["port"], 7777)
        self.assertEqual(captured["reload"], True)
        self.assertEqual(captured["log_level"], "debug")

    def test_descriptor_default_port_is_used_without_port_flag(self) -> None:
        runner = FakeUvicornRunner()

        with redirect_stdout(StringIO()):
            exit_code = web_command._launch_web_app(
                app_name="Good.App",
                host=None,
                port=None,
                reload=False,
                log_level="info",
                context=self.context,
                web_root=WEB_LAUNCH_FIXTURE,
                uvicorn_runner=runner,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(runner.calls[0]["host"], "127.0.0.1")
        self.assertEqual(runner.calls[0]["port"], 9012)

    def test_cli_port_overrides_descriptor_default_port(self) -> None:
        runner = FakeUvicornRunner()

        with redirect_stdout(StringIO()):
            web_command._launch_web_app(
                app_name="Good.App",
                host="127.0.0.1",
                port=8765,
                reload=False,
                log_level="warning",
                context=self.context,
                web_root=WEB_LAUNCH_FIXTURE,
                uvicorn_runner=runner,
            )

        self.assertEqual(runner.calls[0]["port"], 8765)
        self.assertEqual(runner.calls[0]["log_level"], "warning")

    def test_missing_web_dependency_error_is_actionable(self) -> None:
        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "uvicorn":
                raise ImportError("No module named uvicorn", name="uvicorn")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            with self.assertRaises(MissingWebDependencyError) as raised:
                web_command._load_uvicorn_runner()

        self.assertIn('python -m pip install -e ".[web]"', str(raised.exception))

    def test_app_factory_loading_passes_web_context_to_fixture_app(self) -> None:
        runner = FakeUvicornRunner()

        with redirect_stdout(StringIO()):
            web_command._launch_web_app(
                app_name="Good.App",
                host=None,
                port=None,
                reload=False,
                log_level="info",
                context=self.context,
                web_root=WEB_LAUNCH_FIXTURE,
                uvicorn_runner=runner,
            )

        app = runner.calls[0]["app"]
        self.assertIsInstance(app.web_context, WebContext)
        self.assertEqual(app.web_context.metadata["name"], "Good.App")

    def test_missing_factory_fails_clearly(self) -> None:
        with self.assertRaises(InvalidWebApp) as raised:
            web_command._launch_web_app(
                app_name="Missing.Factory",
                host=None,
                port=None,
                reload=False,
                log_level="info",
                context=self.context,
                web_root=WEB_LAUNCH_FIXTURE,
                uvicorn_runner=FakeUvicornRunner(),
            )

        self.assertIn("missing or non-callable factory", str(raised.exception))

    def test_app_import_failure_fails_clearly(self) -> None:
        with self.assertRaises(InvalidWebApp) as raised:
            web_command._launch_web_app(
                app_name="Import.Failure",
                host=None,
                port=None,
                reload=False,
                log_level="info",
                context=self.context,
                web_root=WEB_LAUNCH_FIXTURE,
                uvicorn_runner=FakeUvicornRunner(),
            )

        self.assertIn("failed to import module", str(raised.exception))

    def test_invalid_factory_return_fails_clearly(self) -> None:
        with self.assertRaises(InvalidWebApp) as raised:
            web_command._launch_web_app(
                app_name="Invalid.Return",
                host=None,
                port=None,
                reload=False,
                log_level="info",
                context=self.context,
                web_root=WEB_LAUNCH_FIXTURE,
                uvicorn_runner=FakeUvicornRunner(),
            )

        self.assertIn("did not return an ASGI app", str(raised.exception))

    def test_web_command_reports_missing_factory_without_traceback(self) -> None:
        old_env = os.environ.copy()
        os.environ["WEB_ROOT"] = str(WEB_LAUNCH_FIXTURE)
        stdout = StringIO()
        stderr = StringIO()
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = web_command.main(["launch", "Missing.Factory"], context=self.context)
        finally:
            os.environ.clear()
            os.environ.update(old_env)

        self.assertEqual(exit_code, 1)
        self.assertIn("missing or non-callable factory", stderr.getvalue())

    def test_web_context_skill_helper_calls_time_skill_json(self) -> None:
        context = WebContext(
            repo_root=REPO_ROOT,
            caller_cwd=REPO_ROOT,
            web_root=REPO_ROOT / "Web",
            app_dir=REPO_ROOT / "Web" / "NSPL" / "Status",
            metadata={"name": "NSPL.Status", "version": "0.1.0"},
            entry_path=REPO_ROOT / "Web" / "NSPL" / "Status" / "app.py",
            factory_name="create_app",
        )

        result = context.run_skill(
            [
                "skill",
                "NSPL.Tools.Time.now",
                "--timezone",
                "America/New_York",
                "--json",
            ]
        )

        self.assertEqual(result.exit_code, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["timezone"], "America/New_York")
        self.assertIn("utc_iso", payload)


if __name__ == "__main__":
    unittest.main()
