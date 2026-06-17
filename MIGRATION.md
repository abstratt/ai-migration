# Gradle 9 → 10 Migration Plan

## Input

The repository to migrate is provided via the `REPO_URL` environment variable (e.g. `https://github.com/owner/repo` or `https://github.com/owner/repo/tree/branch`).

**Brute-force mode (`SKIP_BUILD_SCRIPTS`).** When the `SKIP_BUILD_SCRIPTS` environment variable is set, the data-driven build-script migration (task 06) is skipped entirely and replaced by `@tasks/06-skip-build-scripts.md`, which only ensures no `MIGRATION_NOTES.md` exists. Tasks 07/08 then fix every build error from scratch. Default (unset) = normal data-driven migration. See **Environment** in @tasks/CONTEXT.md.

**Clean start (default).** Migration state lives on disk, not in the conversation — clearing the chat context does not reset it, so a re-run would otherwise reuse the existing `migrated/<repo>` clone and its leftover artifacts (this is what makes a previous run appear to "leak" into a new one). To avoid that, the workflow **always runs @tasks/00-clear-repository-state.md first (step 0 below)** to scrub that state. The `RESET_STATE` environment variable tunes this: unset = safe reset (default); `purge` = delete and re-clone; `keep` (or `off`) = skip step 0 to resume an interrupted run. See **Environment** in @tasks/CONTEXT.md.

## Workflow

Run all tasks in order, end-to-end, as a **single autonomous workflow**. Each task has a resume check — if work is already done, it will be skipped automatically.

0. **Clear repository state (runs by default):** @tasks/00-clear-repository-state.md (scrubs prior-run state for a clean start). Skip this step **only** when `RESET_STATE` is `keep` or `off`, or when this workflow was invoked via the `/g10-resume` entry point (both mean: resume an interrupted run, preserving on-disk state). `RESET_STATE=purge` makes it delete and re-clone.
1. @tasks/01-prepare-repository.md
2. @tasks/02-install-jdk.md
3. @tasks/03-upgrade-gradle-9.md
4. @tasks/04-swap-distribution.md
5. @tasks/05-record-start-time.md
6. Build scripts — select by mode: if `SKIP_BUILD_SCRIPTS` is set → @tasks/06-skip-build-scripts.md (brute-force mode); otherwise → @tasks/06-migrate-build-scripts.md
7. @tasks/07-verify-help.md
8. @tasks/08-verify-assemble.md
9. @tasks/09-report.md

**Progress reporting: At a minimum, show information on what task is being executed, including the time it started.**

**Do not pause between tasks — but commits are part of each task, not a pause.** After finishing a task's commit (or confirming the task legitimately made no changes and left a clean tree), immediately start the next one without asking the user whether to continue, without waiting for confirmation, and without summarizing progress mid-workflow. Skipping a task's commit is not "proceeding faster" — it breaks resume detection on the next run and compounds across the rest of the workflow. Every task from 02 onwards begins with a **Pre-start check** that aborts the entire workflow if the migrated clone has uncommitted changes. The workflow is complete only after task 09 finishes (or a task hits an explicit abort condition — e.g. SDKMAN unavailable in task 02, or a Pre-start check failing). "Task already complete — skipping" is not a stopping point; it means move on to the next task.

Each task can also be run individually by referencing its file directly — but when invoked from this workflow, run all nine without stopping (but report progress).

## Shared Context

@tasks/CONTEXT.md
