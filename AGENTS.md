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

- Bugs: when you fix an error the user reported, first file an agent bug report issue from the user's account (`gh issue create -R BrainCOGS/scanreader`, template `.github/ISSUE_TEMPLATE/agent_bug_report.md`). Put the error exactly as the user pasted it under **Reported error**; don't ask for or invent a Slack link. Then fix it with the `bugfix-from-slack` skill (`.claude/skills/bugfix-from-slack/`, vendored from [agent-tooling](https://github.com/BrainCOGS/agent-tooling)); the PR says `Fixes #<issue>`. Commits, pushes, issues and PRs all go through the user's account.
- Commits end with one `Assisted-by: <Harness>:<model>` trailer per agent, e.g. `Assisted-by: ClaudeCode:claude-opus-5-5`. No AI co-authors, and no `Generated with` lines. `prek install` sets up the `ai-attribution` commit-msg hook (`.github/scripts/check_ai_attribution.py`, vendored from agent-tooling), and CI checks every commit of a PR.
- PRs target `master` on `BrainCOGS/scanreader`, opened from the user's own account.
- This is a fork. Always pass `-R BrainCOGS/scanreader` to `gh`, since plain `gh pr create` targets the upstream.
