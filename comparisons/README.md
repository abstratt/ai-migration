# Task: Compare Migration Runs

This folder collects comparisons between different migration runs for the same repository. This file doubles as the instructions for the `/g10-compare` skill (`.claude/commands/g10-compare.md`).

## Input

The repository and the migration runs to compare are provided as arguments (e.g. a repository GIT URL plus the two migration branches, or links to their reports). Each run is identified by its distro pair.

## Preconditions

- A repository GIT URL is provided by the user.
- For each run being compared, its migration branch (or its `REPORT-<timestamp>.md` / `MIGRATION_NOTES.md`) is reachable via that GIT URL.
- Network access to the remote is available.

## Instructions

1. Comparing relies **exclusively** on inspecting the `MIGRATION_NOTES.md` and `REPORT-<timestamp>.md` files of each run.
2. Produce a comparison that:
   - shows the repository migrated (with link);
   - shows a table with a column for each migration run, ordered by distro pair name, where each column lists:
     - the branches compared (with links);
     - links to the reports and migration notes for each migration;
     - the distro pairs;
     - the number of files and lines changed;
     - whether the migration succeeded.
3. Store the result in a file named `COMPARISON-<repository-name>-<distro-pair-1>-vs-<distro-pair-2>.md` in this folder.
4. If a comparison file with the required name already exists, **replace** it.

## Constraints

- Never inspect the local state of the migrated repositories — rely **uniquely** on the GIT URL provided by the user.
- Do not make observations about the quality of the migration (other than succeeded/failed status). We only care about the number of changes (files and lines).

## Done when

- A `COMPARISON-<repository-name>-<distro-pair-1>-vs-<distro-pair-2>.md` file exists in this folder, with columns ordered by distro pair name and containing all the fields listed above.
