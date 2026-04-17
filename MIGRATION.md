# Gradle 9 → 10 Migration Plan

## Input

The repository to migrate is provided via the `REPO_URL` environment variable (e.g. `https://github.com/owner/repo` or `https://github.com/owner/repo/tree/branch`).

## Workflow

Run all tasks in order, end-to-end, as a **single autonomous workflow**. Each task has a resume check — if work is already done, it will be skipped automatically.

1. @tasks/01-setup.md
2. @tasks/02-upgrade-gradle-9.md
3. @tasks/03-swap-distribution.md
4. @tasks/04-migrate-build-scripts.md
5. @tasks/05-verify-help.md
6. @tasks/06-verify-assemble.md
7. @tasks/07-report.md

**Do not pause between tasks.** After finishing one task, immediately start the next one without asking the user whether to continue, without waiting for confirmation, and without summarizing progress mid-workflow. The workflow is complete only after task 07 finishes (or a task hits an explicit abort condition — e.g. SDKMAN unavailable in task 01). "Task already complete — skipping" is not a stopping point; it means move on to the next task.

Each task can also be run individually by referencing its file directly — but when invoked from this workflow, run all seven without stopping.

## Shared Context

@tasks/CONTEXT.md
