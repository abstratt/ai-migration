# Task: Setup

@tasks/CONTEXT.md

## Preconditions

- `REPO_URL` environment variable is set
- Network access to GitHub is available
- SDKMAN is installed at `$HOME/.sdkman` (this is a hard requirement — see step 6)

## Resume check

A fresh migration branch is created on every run of this task, so branch existence is never a reason to skip. The only parts of this task that can be resumed are the clone and the JDK install.

1. Check if the clone directory (derived from `REPO_URL`) exists and contains a git repository — if so, the clone step can be skipped.
2. Check that `JAVA_HOME` is set, starts with `$HOME/.sdkman/candidates/java/`, and `java -version` reports the expected major version from a Temurin build — if so, the JDK install step can be skipped.
3. Branch creation (step 7 below) always runs; it creates a new timestamped branch off the base branch. **Never** check out or reuse any pre-existing `gradle-10-migration/*` branch, regardless of its timestamp.

If `JAVA_HOME` is unset, points outside SDKMAN, or reports the wrong version/vendor, resume from JDK detection and installation — do not accept it as-is.

## Instructions

1. **Parse `REPO_URL`** to extract the `owner/repo`, repo name, and optional branch.

2. **Determine clone directory**: `migrated/<repo-name>` (e.g. `migrated/spring-framework`), relative to the working directory. Create the `migrated/` parent directory if it does not exist. If the clone directory already exists, delete it first.

3. **Fork or reuse**: If a fork already exists on your GitHub account, use it; otherwise fork with `gh repo fork`.

4. **Clone** the fork into the clone directory (`migrated/<repo-name>`), fetching only the target branch:
   ```bash
   git clone --depth 1 --single-branch --branch <branch> <fork-url> migrated/<repo-name>
   ```
   Use the branch from the URL, or omit `--branch` for the default branch. **Do not** clone to the working-directory root — the clone must land under `migrated/`.

5. **Determine required Java version** from the build configuration (e.g. `toolchain { languageVersion }`, `sourceCompatibility`, `targetCompatibility`, `JAVA_HOME` hints in CI files). Default to 21 if unclear.

6. **Install and activate the JDK via SDKMAN — this is the only supported path.**

   First, verify SDKMAN is available. If this fails, **abort the task immediately** and report the error to the user. Do not attempt to install SDKMAN yourself, and do not fall back to another JDK source.
   ```bash
   source "$HOME/.sdkman/bin/sdkman-init.sh"
   ```

   Then install the required Temurin build and activate it:
   ```bash
   sdk install java <version>-tem   # e.g. 17.0.14-tem, 21.0.7-tem
   sdk use java <version>-tem
   export JAVA_HOME="$HOME/.sdkman/candidates/java/current"
   ```

   If `sdk install` fails for any reason (network error, version not listed, checksum failure, etc.), **abort the task and surface the error to the user**. Do not retry with a different vendor, a different major version, or a different installation method.

   **Do not, under any circumstances:**
   - Install SDKMAN yourself or bootstrap it through another package manager
   - Install a JDK through Homebrew, apt, yum, `/usr/libexec/java_home`, manual tarball download, or any non-SDKMAN mechanism
   - Use a pre-existing system JDK even if `java -version` already works and happens to match
   - Substitute a different vendor (`-zulu`, `-oracle`, `-graal`, `-amzn`, etc.) for `-tem`
   - Substitute a different major version than the one determined in step 5
   - Proceed to later tasks if `JAVA_HOME` is unset or points outside `$HOME/.sdkman/candidates/java/` — stop and report to the user instead

7. **Create the migration branch**: Generate the branch name using the current timestamp (e.g. `gradle-10-migration/20260331-1400`). Always create a **fresh** branch on every run — never check out, reset, or otherwise reuse any pre-existing `gradle-10-migration/*` branch, even one created earlier today. If a branch with this exact name already exists locally or on the remote, **abort with an error**; wait a minute and retry so the timestamp changes. Create the branch off the **base branch** — that is, the branch from `REPO_URL` if one was specified, or the repo's default branch (typically `main`, `master`, or a maintenance branch). Do **not** branch from another `gradle-10-migration/*` branch or from any other feature/topic branch.

## Done when

- The clone directory exists with the fork checked out
- The migration branch is created and checked out
- `JAVA_HOME` is set and its path starts with `$HOME/.sdkman/candidates/java/`
- `java -version` succeeds, reports the exact major version determined in step 5, and identifies the build as Temurin
