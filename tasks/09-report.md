# Task: Generate Report

@tasks/CONTEXT.md

## Preconditions

- Migration is complete (all previous tasks finished)
- On the migration branch with all commits in place

## Pre-start check: clean working tree

Before doing anything else, run `git -C migrated/<repo-name> status --porcelain`. If the output is **non-empty**, **STOP THE ENTIRE WORKFLOW** — do not commit the changes yourself, do not run the Resume check, do not continue to the next task. Report the dirty paths and exit. Uncommitted changes at this point mean an earlier task skipped its commit checkpoint; proceeding would break resume detection on a subsequent run and compound the bookkeeping error.

## Resume check

1. Check if a `REPORT-<YYYYMMDD-HHMM>.md` file already exists at the root of the cloned repo matching the current migration branch timestamp
2. Check `git log` on the migration branch for a commit adding that report
3. If both are true and the report reflects the current state of the branch, this task is already complete

## Instructions

Produce a `REPORT-<YYYYMMDD-HHMM>.md` (e.g. `REPORT-20260320-1430.md`) at the **root of the cloned repo** (i.e. inside `migrated/<repo-name>/`, alongside the repo's own files). Do **not** write this file at the root of the tooling repo, and do **not** name it `BENCHMARK-*.md` — that prefix is reserved for the off-pipeline `/g10-benchmark` task and lives under `benchmarks/`. The report file must contain:

1. **Summary**: The repository, its migration status (migrated, skipped, failed), the local branch name, the **start time**, **end time**, and **elapsed time** of the migration — start is read from `migrated/<repo-name>.migration-start-time` (a sibling file recorded by task 05, after setup/plumbing finishes), end is the current time when writing this report, and elapsed is the wall-clock difference between the two (use ISO 8601 with timezone for start/end, e.g. `2026-04-15T15:24:00-03:00`, and a human-readable duration for elapsed, e.g. `12m 34s`), and the **Assistant identification** — the same three-part trailer used on commit messages, i.e. `<<Tool Name>> / <<Friendly Model Name>> / <<model-id>>` (e.g. `Acme AI / FooModel 3 / foomodel-3` or `Unknown Tool / Unknown Model / unknown-id` if identity cannot be determined). Use `Unknown Tool`, `Unknown Model`, or `unknown-id` for any part that cannot be determined. This line must be present in every report.

2. **Nature of changes**: A summary of the types of changes made, including:
   - Which build files were modified
   - What kinds of transformations were applied (from migration-data.json kinds)
   - Any manual fixes beyond the migration data
   - Any known limitations or issues

3. **`MIGRATION_NOTES.md` characterization (only if the file exists on the branch).** Describe the file by what it *actually is*, not by what task 06 aspires to produce. Before writing this section, run the two audits from task 06 step 5(b) against the file on disk and include their exact output (entry count, distinct-reason count, any reasons repeating more than 3 times). Do not use words like "curated", "analyzed", or "per-entry reasoning" unless both audits pass. If the file is mostly machine-generated categorical reasons, say so plainly (e.g. *"596 entries, 7 distinct reason strings; 511 of 596 share the same Cat-B category label — this is a backlog of deferred sites, not per-entry analysis"*). Misdescribing `MIGRATION_NOTES.md` in the REPORT is a self-reporting failure — the file is the only audit trail of what task 06 considered, and its character must be reported truthfully.

## Commit checkpoint (mandatory — final commit of the workflow)

Commit the report to the migration branch:

- Subject: `Generate Report` (the task title)
- Include the `Assistant:` trailer (see CONTEXT.md)
- After committing, run `git status` and confirm the working tree is clean

The report is an artifact of the migration and is kept on the branch. See the "Commit Discipline" section in CONTEXT.md.

## Cleanup

After the report commit succeeds, delete the start-time sibling file: `rm -f migrated/<repo-name>.migration-start-time`. It has served its purpose and leaving it around would make a subsequent run's start time ambiguous if task 05 fails before overwriting it.

## Done when

- `REPORT-<YYYYMMDD-HHMM>.md` exists at the root of the cloned repo with accurate content reflecting the migration outcome
- A commit with subject `Generate Report` exists on the migration branch and `git status` is clean
- `migrated/<repo-name>.migration-start-time` has been deleted
