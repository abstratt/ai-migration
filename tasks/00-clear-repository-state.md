# Task: Clear Repository State

@tasks/CONTEXT.md

## Purpose

Remove the on-disk state of a **previous** migration run of this repository so the next
run starts from a clean slate. Migration state lives on the filesystem, not in the
conversation — clearing the chat context does **not** reset it. The artifacts that make a
prior run "leak" into a new one are:

- the reused clone at `migrated/<repo-name>` with **uncommitted changes** and **untracked
  files** (notably a leftover `MIGRATION_NOTES.md`) — these are discarded; old
  `gradle-10-migration/*` branches are **left untouched** (never deleted);
- the **start-time sidecar** `migrated/<repo-name>.migration-start-time` (normally deleted
  by task 09, but left behind when an earlier run crashed before reporting).

This task scrubs those. It does **not** touch the GitHub fork, other repositories under
`migrated/`, or the shared `migration-reference/` data.

## When this runs

This task runs **by default**. From the full workflow (`@MIGRATION.md`) it runs as step 0 on
every run, so each migration starts from a clean slate. It can also be run on its own via the
`g10-clear-repository-state` command to wipe a single repo's state by hand.

The `RESET_STATE` environment variable tunes the behavior:

- **unset** (the default) → **safe reset** (see Modes below).
- **`purge`** → full reset (delete and re-clone).
- **`keep`** / **`off`** → **skip this task entirely**, preserving on-disk state so an
  interrupted run can resume. The full workflow honors this opt-out at step 0; the standalone
  command ignores it (running the command always means you want to clear). The `/g10-resume`
  entry point is the prompt-accessible equivalent of `RESET_STATE=keep` — it runs the full
  workflow but skips this task.

> **Intent:** the rest of the workflow can resume an interrupted run from the clone's state,
> but a re-run after clearing the conversation context otherwise silently inherits the
> previous run's artifacts. Clearing by default makes "fresh chat ⇒ fresh migration" the
> behavior people expect; `RESET_STATE=keep` is the explicit escape hatch for resuming.

## Resume check

None — this task is itself the reset. It always runs (when invoked) and is idempotent: if
there is nothing to clear (no clone, no sidecar), it is a no-op and succeeds.

## Modes

Selected by the value of `RESET_STATE` (or the command argument when run standalone):

- **`purge`** — full reset: delete the clone directory `migrated/<repo-name>` entirely, so
  task 01 does a fresh fork + clone. Use when the clone itself may be corrupt or you want a
  guaranteed-pristine checkout.
- **unset / any other value** — **safe reset** (the default): keep the clone (avoids
  re-cloning and preserves any unrelated local work) but return it to a pristine base-branch
  state, as below.

## Instructions

1. **Parse `REPO_URL`** to derive the `<repo-name>` exactly as task 01 does — strip any
   trailing `.git` so `https://github.com/owner/repo` and `.../repo.git` both yield
   `repo`. The clone directory is `migrated/<repo-name>` and the sidecar is
   `migrated/<repo-name>.migration-start-time`.

2. **Remove the start-time sidecar** (both modes), if it exists:

   ```
   rm -f migrated/<repo-name>.migration-start-time
   ```

3. **Reset the clone** according to the mode:

   - **`purge` mode:** if `migrated/<repo-name>` exists, delete it:

     ```
     rm -rf migrated/<repo-name>
     ```

     Done — task 01 will re-create it.

   - **safe-reset mode:** if `migrated/<repo-name>` does **not** exist or is not a git repo,
     there is nothing to reset — skip to **Done when**. Otherwise, operating inside the
     clone with `git -C migrated/<repo-name>`:

     1. **Determine the base branch** — the branch from `REPO_URL` if one was specified,
        otherwise the remote's default branch (`git remote show origin`, typically `main` or
        `master`). **Never** pick a maintenance or release branch yourself.
     2. **Abort any in-progress git operation** that a crashed run may have left:
        `git rebase --abort`, `git merge --abort`, `git cherry-pick --abort` (ignore "no
        operation in progress" errors).
     3. **Check out the base branch** and discard all changes:

        ```
        git checkout <base-branch>
        git reset --hard
        git clean -fdx
        ```

        `git clean -fdx` removes every untracked/ignored file — including any leftover
        `MIGRATION_NOTES.md` and stray build output.

        **Do not delete any branches.** Checking out the base branch is sufficient — task 01
        creates a fresh timestamped branch off it regardless. Old `gradle-10-migration/*`
        branches are left in place; they never collide (each run's branch name is unique) and
        deleting them would risk discarding a previous run's commits, which are local-only
        because the workflow never pushes. (`RESET_STATE=purge` is the explicit opt-in for a
        clean slate — it deletes the whole clone directory.)
     4. **Confirm a clean tree:** `git -C migrated/<repo-name> status --porcelain` must be
        empty.

## Done when

- `migrated/<repo-name>.migration-start-time` does not exist.
- In **purge** mode: `migrated/<repo-name>` does not exist.
- In **safe-reset** mode: the clone is on the base branch with a clean working tree
  (`git status --porcelain` empty) and no `MIGRATION_NOTES.md` is present. **No branches are
  deleted** — old `gradle-10-migration/*` branches remaining is expected, not a failure.
