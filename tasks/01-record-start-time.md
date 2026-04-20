# Task: Record Start Time

@tasks/CONTEXT.md

## Preconditions

- Write access to the working directory

## Resume check

This task has no resume check — it **always runs** and **always overwrites** `migrated/.migration-start-time`. The whole point is to capture *this run's* start time; reusing a timestamp from an earlier run would make task 08's elapsed-time report meaningless.

## Instructions

1. **Record start time**: Capture the current timestamp in ISO 8601 with timezone (e.g. `2026-04-15T15:24:00-03:00`). Create the `migrated/` parent directory if it does not exist, then write the timestamp to `migrated/.migration-start-time`, **unconditionally overwriting any existing file**. The report task (task 08) will read this file to compute the migration duration.

## Done when

- `migrated/.migration-start-time` exists and contains a single ISO 8601 timestamp with timezone
