# Git Hooks

Repo-wide hooks enforcing the standards in the per-implementation `CLAUDE.md` files. These cover both `typescript/` and `python/`.

## Installation

```bash
git config core.hooksPath .githooks
```

(or run `pnpm setup:hooks` from `typescript/`, which does the same).

## Hooks

### commit-msg (repo-wide)
Rejects any commit whose message contains AI attribution markers (`Co-Authored-By: Claude`, `🤖 Generated with`, `noreply@anthropic.com`, etc.). Applies to every commit in the repo regardless of which implementation it touches.

### pre-commit
Lints staged TypeScript under `typescript/src` and `typescript/scripts` (eslint), and staged Python under `python/` (ruff, using `python/.venv` or a `ruff` on PATH). Skips a stack when nothing relevant is staged.

### pre-push
Runs the TypeScript check sequence (`typecheck`, `lint`, `test`), and the Python checks (`ruff`, `pytest`) when `python/.venv` is present. Blocks the push if any step fails.

## Bypassing (not recommended)

`git commit --no-verify` / `git push --no-verify` bypasses the hooks but violates project standards.
