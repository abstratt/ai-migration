# Task: Record Start Time

@tasks/CONTEXT.md

## Preconditions

- Tasks 01–04 have completed: clone exists, JDK is installed, Gradle 9.x wrapper is in place, and the custom Provider API distribution URL is configured

## Resume check

This task has no resume check — it **always runs** and **always overwrites** the start-time file. It sits here, *after* the plumbing tasks (clone, JDK, wrapper upgrade, distribution swap), so the duration reported in task 09 measures only the migration work proper (tasks 06–09) and excludes setup time that varies with network/cache. Reusing a timestamp from an earlier run would make the elapsed-time report meaningless.

## Instructions

1. **Record start time**: Capture the current timestamp in ISO 8601 with timezone (e.g. `2026-04-15T15:24:00-03:00`). Write it to `migrated/<repo-name>.migration-start-time` — a **sibling file** alongside the clone directory, not inside it — **unconditionally overwriting any existing file**. The report task (task 09) will read this file to compute the migration duration and then delete it.

   > **Intent:** the timestamp is kept outside the clone so it stays out of the working tree (no `git status` pollution, no risk of accidental staging) and outside `.git/` (agents may have write guards around `.git/` that fire even under permissive permission modes). The per-repo association is preserved via the filename.

## Done when

- `migrated/<repo-name>.migration-start-time` exists and contains a single ISO 8601 timestamp with timezone
