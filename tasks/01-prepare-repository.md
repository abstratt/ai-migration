# Task: Prepare Repository

@tasks/CONTEXT.md

## Preconditions

- `REPO_URL` environment variable is set
- Network access to GitHub is available

## Resume check

A fresh migration branch is created on every run of this task, so branch existence is never a reason to skip. The only part of this task that can be resumed is the clone.

1. Check if the clone directory (derived from `REPO_URL`) exists and contains a git repository — if so, the clone step can be skipped.
2. **If the repo is currently on a `gradle-10-migration/*` branch**, switch back to the base branch (`git checkout <base-branch>`) before proceeding. That old migration branch belongs to a previous run and must not be reused.
3. Branch creation (final step below) always runs; it creates a new timestamped branch off the base branch. **Never** check out or reuse any pre-existing `gradle-10-migration/*` branch, regardless of its timestamp.

## Instructions

1. **Parse `REPO_URL`** to extract the `owner/repo`, repo name, and optional branch.

2. **Determine clone directory**: `migrated/<repo-name>` (e.g. `migrated/spring-framework`), relative to the working directory. Create the `migrated/` parent directory if it does not exist.

3. **Reuse existing clone or create a fresh one**:

   - **If `migrated/<repo-name>` already exists and is a valid git repository**, reuse it. Do **not** delete it — other work may live there. Instead, get it back to a clean state on the base branch:
     ```bash
     cd migrated/<repo-name>
     git reset --hard HEAD            # discard uncommitted/unstaged changes
     git clean -fd                    # remove untracked files and directories
     git checkout <base-branch>       # base branch = branch from REPO_URL, or the repo's default branch
     git pull --ff-only               # optional: bring base branch up to date; skip on network errors
     ```
     The **base branch** is the branch from `REPO_URL` if one was specified, otherwise the repo's default branch (typically `main` or `master`). **Never** pick a maintenance or release branch yourself. If the repo is currently on a `gradle-10-migration/*` branch, checking out the base branch is sufficient — do not delete the old migration branch (step 4 creates a fresh timestamped branch off the base branch regardless).
     There should be no outgoing changes (staged or not) in the directory.

   - **Otherwise** (directory does not exist, or exists but is not a git repo), do a fresh fork + clone:
     1. **Fork or reuse**: If a fork already exists on your GitHub account, use it; otherwise fork with `gh repo fork`.
     2. **Clone** the fork into the clone directory (`migrated/<repo-name>`), fetching only the target branch:
        ```bash
        git clone --depth 1 --single-branch --branch <branch> <fork-url> migrated/<repo-name>
        ```
        Use the branch from the URL if one was specified, or omit `--branch` to get the repo's default branch. **Do not** pick a branch yourself — never use a maintenance branch (e.g. `6.1.x`, `6.8`), release branch, or any non-default branch unless it was explicitly part of `REPO_URL`. **Do not** clone to the working-directory root — the clone must land under `migrated/`.

4. **Create the migration branch**: Generate the branch name using the current timestamp (e.g. `gradle-10-migration/20260331-1400`). Always create a **fresh** branch on every run — never check out, reset, or otherwise reuse any pre-existing `gradle-10-migration/*` branch, even one created earlier today. If a branch with this exact name already exists locally or on the remote, **abort with an error**; wait a minute and retry so the timestamp changes. Create the branch off the **base branch** — that is, the branch from `REPO_URL` if one was specified, or the repo's default branch (typically `main` or `master`). Never branch from a maintenance branch (e.g. `6.1.x`, `6.8`) unless it was explicitly in `REPO_URL`. Do **not** branch from another `gradle-10-migration/*` branch or from any other feature/topic branch.

## Done when

- The clone directory exists with the fork checked out
- The migration branch is created and checked out
