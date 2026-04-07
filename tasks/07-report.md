# Task: Generate Report

@tasks/CONTEXT.md

## Preconditions

- Migration is complete (all previous tasks finished)
- On the migration branch with all commits in place

## Resume check

1. Check if a `REPORT-<YYYYMMDD-HHMM>.md` file already exists matching the current migration branch timestamp
2. If it exists and reflects the current state of the branch, this task is already complete

## Instructions

Produce a `REPORT-<YYYYMMDD-HHMM>.md` (e.g. `REPORT-20260320-1430.md`) under the root of this repository (the ai-migration directory, not the clone directory) containing:

1. **Summary**: The repository, its migration status (migrated, skipped, failed), and the local branch name

2. **Nature of changes**: A summary of the types of changes made, including:
   - Which build files were modified
   - What kinds of transformations were applied (from migration-data.json kinds)
   - Any manual fixes beyond the migration data
   - Any known limitations or issues

## Done when

- `REPORT-<YYYYMMDD-HHMM>.md` exists with accurate content reflecting the migration outcome
