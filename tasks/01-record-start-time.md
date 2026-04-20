# Task: Record Start Time

@tasks/CONTEXT.md

## Preconditions

- Write access to the working directory

## Resume check

1. If `migrated/.migration-start-time` already exists and contains a parseable ISO 8601 timestamp, this task is already complete — skip it and move on to the next task.
2. Otherwise, run the instructions below.

## Instructions

1. **Record start time**: Capture the current timestamp in ISO 8601 with timezone (e.g. `2026-04-15T15:24:00-03:00`). Create the `migrated/` parent directory if it does not exist, then write the timestamp to `migrated/.migration-start-time` so the report task can read it later.

## Done when

- `migrated/.migration-start-time` exists and contains a single ISO 8601 timestamp with timezone
