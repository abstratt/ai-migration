# Task: Compare Migration Runs

This folder collects comparisons between different migration runs for the same repository. This file doubles as the instructions for the `/g10-compare` skill (`.claude/commands/g10-compare.md`).

## Input

The repository and the migration runs to compare are provided as arguments (e.g. a repository GIT URL plus the two migration branches, or links to their reports). Each run is identified by its distro pair.

## Preconditions

- A repository GIT URL is provided by the user.
- For each run being compared, its migration branch (or its `REPORT-<timestamp>.md` / `MIGRATION_NOTES.md`) is reachable via that GIT URL.
- Network access to the remote is available.

## Instructions

1. **Fetch each run's branch and its base ref from the provided GIT URL** into a throwaway clone (never the local `migrated/` working copies — see Constraints). A shallow fetch of each run's base branch and migration branch is enough. Read each run's base branch from its `REPORT-<timestamp>.md` (the **Base branch** field).
2. For **each** run, categorize the change counts by running the helper against that clone:

   ```
   python3 comparisons/categorize_diff.py <clone-dir> --base <base-ref> --branch <migration-branch>
   ```

   It computes `git diff <base>...<branch>` (three-dot, matching the REPORT files), excludes the generated artifacts (`MIGRATION_NOTES.md`, `REPORT-*.md`), and splits the changed lines into four **disjoint** buckets that sum to the total:
   - **formatting** — whitespace/indent/blank-line-only churn (exact, via `git diff -w`);
   - **warnings** — warnings-as-errors & deprecation-suppression flag changes;
   - **infra** — other throwaway-preview relaxations (`verification-metadata.xml` blanket trust, Develocity/build-scan disabling);
   - **core** — the residual = the genuine Provider-API migration work.

   Use the helper's numbers; do **not** hand-estimate. The qualitative status (succeeded/failed) still comes from each run's `REPORT-<timestamp>.md`.
3. Produce a comparison that:
   - shows the repository migrated (with link);
   - shows a table with a column for each migration run, ordered by distro pair name, where each column lists:
     - the branches compared (with links);
     - links to the reports and migration notes for each migration;
     - the distro pairs;
     - the change counts, broken down as: **total lines changed (excl. artifacts)**, then `− formatting`, `− warnings-as-errors & deprecations`, `− other infra relaxations`, and `= core migration changes` (the **primary** figure to compare), plus **files changed** annotated with how many files each non-core category touched;
     - whether the migration succeeded.
   - includes a short **Methodology** note stating that counts come from `categorize_diff.py` over `git diff <base>...<branch>`, that `formatting` is exact (whitespace-ignoring diff) while `warnings`/`infra` are pattern-based heuristics, and the precedence used (infra-by-path → warnings → infra-by-content → formatting → core). The helper's JSON echoes the exact patterns it matched; cite them if useful.
4. Store the result in a file named `COMPARISON-<repository-name>-<distro-pair-1>-vs-<distro-pair-2>.md` in this folder.
5. If a comparison file with the required name already exists, **replace** it.

## Constraints

- Never inspect the local state of the migrated repositories under `migrated/` — fetch the branches you compare **fresh from the GIT URL** provided by the user.
- Do not make observations about the quality of the migration (other than succeeded/failed status). We only care about the number of changes (files and lines), split into the buckets above.

## Done when

- A `COMPARISON-<repository-name>-<distro-pair-1>-vs-<distro-pair-2>.md` file exists in this folder, with columns ordered by distro pair name, the per-category change breakdown (formatting / warnings / infra / core) from `categorize_diff.py`, the Methodology note, and all the other fields listed above.
