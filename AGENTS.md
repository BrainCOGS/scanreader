# scanreader (BrainCOGS fork)

BrainCOGS's fork of atlab/scanreader: reads ScanImage TIFF stacks, including
mesoscope multiROI scans. Python >= 3.10, managed with uv.

## Setup and tests

```bash
uv sync --locked
uv run pytest               # CI: Python 3.10 and 3.13
```

Lint: `uvx prek run --all-files` (the same as CI's Lint workflow).

## Pins and gotchas

- ScanImage 2021/2022 files use the "2023" header names.
- Changes stay on the BrainCOGS fork; no PRs to atlab.

## Agent workflow

- Errors reported in Slack: use the `bugfix-from-slack` skill (agent-tooling). The agent files nothing itself: commits, pushes and PRs are the user's.
- Commits end with one `Assisted-by: <Harness>:<model>` trailer per agent, e.g. `Assisted-by: ClaudeCode:claude-opus-5-5`. No AI co-authors, and no `Generated with` lines. `prek install` sets up the `ai-attribution` commit-msg hook (`.github/scripts/check_ai_attribution.py`, vendored from agent-tooling), and CI checks every commit of a PR.
- PRs target `master` on `BrainCOGS/scanreader`, opened from the user's own account.
- This is a fork. Always pass `-R BrainCOGS/scanreader` to `gh`, since plain `gh pr create` targets the upstream.
