# RohTalk Model Profile Results - 2026-06-19

## Decision

The RohTalk profiles below are config-backed runtime presets in
`Config/RohTalk/config.json`. They do not change the global default model or
replace the existing `dst_director_fast` or `dst_director_quality` profiles.

| Profile | Model | Options | Recommended role |
| --- | --- | --- | --- |
| `roh_demo_cloud` | `gemma4:31b-cloud` | `think:false` | Roh Demo Cloud brain |
| `roh_local_daily` | `gemma4:e2b` | `think:false` | Roh Local Daily brain |
| `roh_local_heavy` | `gpt-oss:20b` | `think:"low"` | Warmed local heavy/fallback |

`gemma4:12b` is parked for current demos because no-tools latency was too slow
on KanraDesktop.

## Benchmark Findings

All director checks used the `dst_director_fast` runtime-options baseline:
`think:false`. The new named profiles preserve the winning model and matching
benchmark options as standalone runtime presets.

| Model | Dry announce | Dry chaos tier | Dry Deerclops | Live announce | Live Deerclops | Result |
| --- | --- | --- | --- | --- | --- | --- |
| `gemma4:31b-cloud` | pass, ~1.98s | pass, ~0.89s | pass, ~0.93s | pass, ~6.24s | pass, ~6.27s | Demo default |
| `gemma4:e2b` | pass, ~8.61s | pass, ~2.10s | pass, ~3.32s | pass, ~15.28s | pass, ~16.46s | Local daily |
| `gpt-oss:20b` | pass, ~34.22s | pass, ~14.19s | ~98.35s; failed, only `enemy_spawn` observed | not selected | not selected | Heavy fallback only |

## Precedence

RohTalk resolves request settings in this order:

1. Base `default_options`.
2. The selected `--model-profile` model, host, and options.
3. Explicit `--model`, `--host`, and repeatable `--model-option key=value`
   overrides.

Thus, `--model-profile` supplies a runtime model/host/options preset. It does
not select a toolkit or modify Roh's identity prompt. `--model` overrides only
the selected profile's model while retaining the profile options unless an
explicit `--model-option` overrides them. `--toolkit` selects the tool belt
for tool-enabled RohTalk commands; DST benchmark modes infer
`dst_director` unless tools are explicitly disabled.

## Exact Benchmark Commands

Demo cloud DST dry:

```bash
python nspl.py skill RohTalk.benchmark --model-profile roh_demo_cloud --mode dst-director-dry --toolkit dst_director --suite smoke --iterations 1 --json
```

Demo cloud live announce:

```bash
python nspl.py skill RohTalk.benchmark --model-profile roh_demo_cloud --mode dst-director-live --toolkit dst_director --case dst_announce_live --allow-live-dst-actions --json
```

Demo cloud live Deerclops:

```bash
python nspl.py skill RohTalk.benchmark --model-profile roh_demo_cloud --mode dst-director-live --toolkit dst_director --case deerclops_live --allow-live-dst-actions --json
```

Local daily DST dry:

```bash
python nspl.py skill RohTalk.benchmark --model-profile roh_local_daily --mode dst-director-dry --toolkit dst_director --suite smoke --iterations 1 --json
```

Local daily live announce:

```bash
python nspl.py skill RohTalk.benchmark --model-profile roh_local_daily --mode dst-director-live --toolkit dst_director --case dst_announce_live --allow-live-dst-actions --json
```

Local daily live Deerclops:

```bash
python nspl.py skill RohTalk.benchmark --model-profile roh_local_daily --mode dst-director-live --toolkit dst_director --case deerclops_live --allow-live-dst-actions --json
```

The live commands are recorded for deliberate operator use only. They were not
run during this pass.
