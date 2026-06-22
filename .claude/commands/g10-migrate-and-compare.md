The repository to migrate against both distro pairs is: $ARGUMENTS (this is `REPO_URL`).

Run a full Gradle 9 → 10 migration of `REPO_URL` **once per distro pair**, push each migrated
branch, then compare the two runs. The point is an apples-to-apples comparison of the same repo
migrated against each distro pair, so each run must be independent.

## Constraints (read first)

- **One separate sub-agent per run, so they never share context.** Spawn each migration as its own
  `Agent` (subagent_type `general-purpose`). Each agent gets a clean context and runs the whole
  workflow itself; do not run the migration tasks inline in this conversation.
- **Never run the two migrations in parallel.** Both runs use the same on-disk clone
  (`migrated/<repo-name>`) and would clobber each other. Run the first agent to completion **in the
  foreground**, wait for it to return, then start the second. Do not set `run_in_background`, and do
  not use Monitor — a migration sub-agent that yields mid-workflow cannot be resumed.
- The default safe-reset (task 00) between runs returns the clone to a pristine base-branch state but
  **never deletes branches**, so the first run's branch survives the second run untouched. Do not pass
  `RESET_STATE=purge`.

## Steps

### 1. Resolve the two distro pairs

Read `distro-pairs.json` at the repo root and list its `pairs`.

- If there are **exactly two** pairs, use both (ordered by `id`).
- If there are more than two, ask the user which two `id`s to compare; do not guess.
- For **each** chosen pair, confirm its bundle exists at
  `migration-reference/distro-pairs/<pair-id>/migration-data.json`. If any is missing, stop and tell
  the user to build it first with `/g10-build-bundle <pair-id>`.

### 2. Migrate against each pair, sequentially

For each pair id `PAIR`, **one at a time**, spawn a foreground `general-purpose` agent with a prompt
that says, in substance:

> You are running a Gradle 9 → 10 migration. The inputs are:
> - `REPO_URL` = `<the REPO_URL from $ARGUMENTS>`
> - `DISTRO_PAIR` = `<PAIR>`
>
> Run the full migration workflow defined in `MIGRATION.md` (tasks 01–09) end to end as a single
> autonomous workflow, from the repo root `<absolute path to this repo>`. Do not skip step 0
> (default safe reset). Wherever a task resolves the active distro pair, set `DISTRO_PAIR=<PAIR>`
> on that command (Bash env does not persist between calls). Run all Gradle commands in the
> foreground — never background them.
>
> When task 09 has finished and the working tree is clean, **push the migration branch** to the
> clone's origin remote:
> `git -C migrated/<repo-name> push -u origin <migration-branch>`
>
> Then report back exactly these values: the resolved pair id, the migration branch name, the base
> branch, the origin remote URL (`git -C migrated/<repo-name> remote get-url origin`), and whether
> the migration succeeded (from the `REPORT-*.md`).

Wait for the agent to return before starting the next pair. Record each run's reported branch name,
base branch, and origin URL.

### 3. Compare the two runs

Both branches are now pushed to the fork (the origin URL the agents reported — both runs share the
same fork). Run the comparison described in `comparisons/README.md`, passing that **fork GIT URL** plus
the two migration branches (one per pair). The comparison must fetch the branches **fresh from the
fork URL** — never inspect the local `migrated/` clone. Produce
`comparisons/COMPARISON-<repo-name>-<pair-1-id>-vs-<pair-2-id>.md` as specified there.

@comparisons/README.md

## Done when

- Each distro pair has a completed migration run (its branch pushed to the fork) produced by its own
  isolated sub-agent, run sequentially.
- A `COMPARISON-<repo-name>-<pair-1>-vs-<pair-2>.md` file exists in `comparisons/` per the
  `comparisons/README.md` spec.
