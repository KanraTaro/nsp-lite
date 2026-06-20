from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import Core.NSPL.NodeCTX as NodeCTX
from Core.NSPL.SkillCLI.ctx import SkillContext
from Core.RohTalk.Benchmarks.results import BenchmarkResult
import Skills.RohTalk.benchmark.skill as benchmark_skill


class RohTalkBenchmarkSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.ctx = SkillContext(
            root=Path(self._tmp.name),
            node_tag="testnode",
            instance_id="testinstance",
            global_scope=False,
            node_ctx=NodeCTX,
            debug=False,
            json=False,
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _parse(self, argv: list[str]) -> argparse.Namespace:
        parser = argparse.ArgumentParser()
        benchmark_skill.build_parser(parser)
        return parser.parse_args(argv)

    def _result(self) -> BenchmarkResult:
        return BenchmarkResult(
            timestamp="2026-06-18T00:00:00Z",
            case_id="simple_hello",
            mode="no-tools",
            suite="smoke",
            model="test:model",
            model_profile=None,
            toolkit=None,
            tools_enabled=False,
            host=None,
            model_options={},
            elapsed_seconds=0.01,
            exit_code=0,
            success=True,
            expected_tool_names=[],
            observed_tool_names=[],
            expected_json_shape_met=None,
            stdout_snippet="hello",
            stderr_snippet="",
            notes="",
            errors=[],
        )

    def test_json_output(self) -> None:
        args = self._parse(["--mode", "no-tools"])
        self.ctx = SkillContext(
            root=self.ctx.root,
            node_tag=self.ctx.node_tag,
            instance_id=self.ctx.instance_id,
            global_scope=self.ctx.global_scope,
            node_ctx=self.ctx.node_ctx,
            debug=False,
            json=True,
        )
        output = io.StringIO()

        with patch.object(benchmark_skill, "run_benchmark", return_value=[self._result()]):
            with redirect_stdout(output):
                code = benchmark_skill.run(args, self.ctx)

        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["results"][0]["case_id"], "simple_hello")

    def test_save_writes_jsonl(self) -> None:
        args = self._parse(["--mode", "no-tools", "--save"])
        output = io.StringIO()

        with patch.object(benchmark_skill, "run_benchmark", return_value=[self._result()]):
            with redirect_stdout(output):
                code = benchmark_skill.run(args, self.ctx)

        self.assertEqual(code, 0)
        out_dir = self.ctx.node_ctx.build_state_dir(
            root=self.ctx.root,
            instance_id=self.ctx.instance_id,
            node_tag=self.ctx.node_tag,
            bucket="Logs",
            domain="RohTalk",
            global_scope=self.ctx.global_scope,
            subpath="Benchmarks",
        )
        records = self.ctx.node_ctx.read_jsonl(out_dir / "rohtalk_benchmark.jsonl")
        self.assertEqual(records[0]["case_id"], "simple_hello")
        self.assertIn("markdown:", output.getvalue())

    def test_live_mode_requires_explicit_flag(self) -> None:
        args = self._parse(["--mode", "dst-director-live"])
        code = benchmark_skill.run(args, self.ctx)
        self.assertEqual(code, 2)

    def test_toolkit_and_case_args_are_forwarded(self) -> None:
        args = self._parse(
            [
                "--mode",
                "dst-director-dry",
                "--toolkit",
                "dst_director",
                "--case",
                "deerclops_intent",
                "--tools",
            ]
        )

        with patch.object(benchmark_skill, "run_benchmark", return_value=[self._result()]) as patched:
            code = benchmark_skill.run(args, self.ctx)

        self.assertEqual(code, 0)
        request = patched.call_args.args[1]
        self.assertEqual(request.toolkit, "dst_director")
        self.assertEqual(request.case_ids, ["deerclops_intent"])
        self.assertTrue(request.tools_enabled)


if __name__ == "__main__":
    unittest.main()
