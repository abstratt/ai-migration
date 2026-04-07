# Gradle 9 → 10 Migration Plan

## Input

The repository to migrate is provided via the `REPO_URL` environment variable (e.g. `https://github.com/owner/repo` or `https://github.com/owner/repo/tree/branch`).

## Workflow

Run all tasks in order. Each task has a resume check — if work is already done, it will be skipped automatically.

1. @tasks/01-setup.md
2. @tasks/02-upgrade-gradle-9.md
3. @tasks/03-swap-distribution.md
4. @tasks/04-migrate-build-scripts.md
5. @tasks/05-verify-help.md
6. @tasks/06-verify-assemble.md
7. @tasks/07-report.md

Each task can also be run individually by referencing its file directly.

## Shared Context

@tasks/CONTEXT.md
