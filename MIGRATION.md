# Gradle 9 → 10 Migration Plan

## Input

The repository to migrate is provided via the `REPO_URL` environment variable (e.g. `https://github.com/owner/repo` or `https://github.com/owner/repo/tree/branch`).

## Workflow

Run all tasks in order, end-to-end, as a **single autonomous workflow**. Each task has a resume check — if work is already done, it will be skipped automatically.

1. @tasks/01-prepare-repository.md
2. @tasks/02-install-jdk.md
3. @tasks/03-upgrade-gradle-9.md
4. @tasks/04-swap-distribution.md
5. @tasks/05-record-start-time.md
6. @tasks/06-migrate-build-scripts.md
7. @tasks/07-verify-help.md
8. @tasks/08-verify-assemble.md
9. @tasks/09-report.md

**Do not pause between tasks — but commits are part of each task, not a pause.** After finishing a task's commit (or confirming the task legitimately made no changes and left a clean tree), immediately start the next one without asking the user whether to continue, without waiting for confirmation, and without summarizing progress mid-workflow. Skipping a task's commit is not "proceeding faster" — it breaks resume detection on the next run and compounds across the rest of the workflow. Every task from 02 onwards begins with a **Pre-start check** that aborts the entire workflow if the migrated clone has uncommitted changes. The workflow is complete only after task 09 finishes (or a task hits an explicit abort condition — e.g. SDKMAN unavailable in task 02, or a Pre-start check failing). "Task already complete — skipping" is not a stopping point; it means move on to the next task.

Each task can also be run individually by referencing its file directly — but when invoked from this workflow, run all nine without stopping.

## Shared Context

@tasks/CONTEXT.md
