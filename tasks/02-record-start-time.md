# Task: Record Start Time

@tasks/CONTEXT.md

## Preconditions

- Task 01 has completed: the clone directory exists and the migration branch is checked out

## Resume check

This task has no resume check — it **always runs** and **always overwrites** the start-time file. The whole point is to capture *this run's* start time (after task 01 has made the repo contents available); reusing a timestamp from an earlier run would make task 09's elapsed-time report meaningless.

## Instructions

1. **Record start time**: Capture the current timestamp in ISO 8601 with timezone (e.g. `2026-04-15T15:24:00-03:00`). Write it to `migrated/<repo-name>/.git/migration-start-time` (inside the clone's `.git/` directory), **unconditionally overwriting any existing file**. The report task (task 09) will read this file to compute the migration duration.

   > **Intent:** storing the timestamp inside `.git/` keeps it with the clone it belongs to (per-repo, not shared across migrations), while staying out of the working tree so `git status` assertions in later tasks remain clean and so `git reset --hard` / `git clean -fd` from a subsequent run's task 01 won't wipe it before it's been overwritten with a fresh value.

## Done when

- `migrated/<repo-name>/.git/migration-start-time` exists and contains a single ISO 8601 timestamp with timezone
