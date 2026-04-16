# Task: Generate Report

@tasks/CONTEXT.md

## Preconditions

- Migration is complete (all previous tasks finished)
- On the migration branch with all commits in place

## Resume check

1. Check if a `REPORT-<YYYYMMDD-HHMM>.md` file already exists at the root of the cloned repo matching the current migration branch timestamp
2. Check `git log` on the migration branch for a commit adding that report
3. If both are true and the report reflects the current state of the branch, this task is already complete

## Instructions

Produce a `REPORT-<YYYYMMDD-HHMM>.md` (e.g. `REPORT-20260320-1430.md`) at the **root of the cloned repo** (i.e. inside `migrated/<repo-name>/`, alongside the repo's own files) containing:

1. **Summary**: The repository, its migration status (migrated, skipped, failed), the local branch name, and the **Assistant identification** — the same three-part trailer used on commit messages, i.e. `<<Tool Name>> / <<Friendly Model Name>> / <<model-id>>` (e.g. `Claude Code / Claude Opus 4.6 / claude-opus-4-6`). Use `Unknown Tool`, `Unknown Model`, or `unknown-id` for any part that cannot be determined. This line must be present in every report.

2. **Nature of changes**: A summary of the types of changes made, including:
   - Which build files were modified
   - What kinds of transformations were applied (from migration-data.json kinds)
   - Any manual fixes beyond the migration data
   - Any known limitations or issues

3. **Commit the report** to the migration branch with a present tense message (e.g. "Add Gradle 10 migration report"). The report is an artifact of the migration and is kept on the branch.

## Done when

- `REPORT-<YYYYMMDD-HHMM>.md` exists at the root of the cloned repo with accurate content reflecting the migration outcome
- The report is committed to the migration branch
