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

1. **Summary**: The repository, its migration status (migrated, skipped, failed), the local branch name, the **start time**, **end time**, and **elapsed time** of the migration — start is read from `migrated/.migration-start-time` (recorded by the setup task), end is the current time when writing this report, and elapsed is the wall-clock difference between the two (use ISO 8601 with timezone for start/end, e.g. `2026-04-15T15:24:00-03:00`, and a human-readable duration for elapsed, e.g. `12m 34s`), and the **Assistant identification** — the same three-part trailer used on commit messages, i.e. `<<Tool Name>> / <<Friendly Model Name>> / <<model-id>>` (e.g. `Acme AI / FooModel 3 / foomodel-3` or `Unknown Tool / Unknown Model / unknown-id` if identity cannot be determined). Use `Unknown Tool`, `Unknown Model`, or `unknown-id` for any part that cannot be determined. This line must be present in every report.

2. **Nature of changes**: A summary of the types of changes made, including:
   - Which build files were modified
   - What kinds of transformations were applied (from migration-data.json kinds)
   - Any manual fixes beyond the migration data
   - Any known limitations or issues

3. **Commit the report** to the migration branch using the task title "Generate Report" as the commit message subject — include the `Assistant:` trailer (see CONTEXT.md). The report is an artifact of the migration and is kept on the branch.

## Done when

- `REPORT-<YYYYMMDD-HHMM>.md` exists at the root of the cloned repo with accurate content reflecting the migration outcome
- The report is committed to the migration branch
