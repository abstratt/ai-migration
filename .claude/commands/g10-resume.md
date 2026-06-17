The partial repository name to resume is: $ARGUMENTS

Resume a previously-started migration **without clearing repository state first**, identifying
the repository by a partial name match against the existing clones under `migrated/`.

## Resolve the repository

1. **List candidate clones**: every immediate subdirectory of `migrated/` that contains a
   `.git` directory (i.e. is a git repository). Ignore the `*.migration-start-time` sibling
   files — they are not clones.
2. **Match `$ARGUMENTS` against the candidate directory names** (case-insensitive):
   - If exactly one directory name **equals** `$ARGUMENTS`, that is the match.
   - Otherwise, if exactly one directory name **contains** `$ARGUMENTS` as a substring, that
     is the match.
   - **Zero matches** → abort: print `No migrated clone matches "<arg>".` followed by the
     full list of candidate clones, and stop. Do not migrate anything.
   - **More than one match** (and no exact match) → abort: print
     `"<arg>" is ambiguous — N clones match:` followed by the matching directory names, ask
     the user to be more specific, and stop. Do not guess.
3. **Bind the workflow inputs** from the matched clone `migrated/<repo-name>`:
   - `<repo-name>` is the matched directory name.
   - Set `REPO_URL` to the clone's origin remote: `git -C migrated/<repo-name> remote get-url origin`.
     This keeps every downstream task's `REPO_URL`-derived repo name identical to the existing
     clone, so resume detection lines up. The base branch is whatever the clone's remote
     reports as default (no branch is taken from `REPO_URL` here).

## Run the workflow

Run the full migration workflow (tasks 01–09) on the resolved repository, but **skip step 0**
(`tasks/00-clear-repository-state.md`) entirely — the existing clone and all of its in-progress
state must be preserved so the normal per-task resume checks pick up where the previous run
left off. This is exactly equivalent to running `/g10-migrate` with `RESET_STATE=keep`.

@MIGRATION.md
