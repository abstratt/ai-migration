# Task: Setup

@tasks/CONTEXT.md

## Preconditions

- `REPO_URL` environment variable is set
- Network access to GitHub is available
- SDKMAN is installed at `$HOME/.sdkman` (this is a hard requirement — see step 6)

## Resume check

1. Check if the clone directory (derived from `REPO_URL`) exists and contains a git repository
2. Check if the migration branch (`gradle-10-migration/<YYYYMMDD-HHMM>`) already exists locally
3. Check that `JAVA_HOME` is set, starts with `$HOME/.sdkman/candidates/java/`, and `java -version` reports the expected major version from a Temurin build
4. If all of the above are true, this task is already complete

If the clone directory exists but the migration branch does not, resume from branch creation.
If `JAVA_HOME` is unset, points outside SDKMAN, or reports the wrong version/vendor, resume from JDK detection and installation — do not accept it as-is.

## Instructions

1. **Parse `REPO_URL`** to extract the `owner/repo`, repo name, and optional branch.

2. **Determine clone directory**: `<repo-name>`. If it already exists, delete it first.

3. **Fork or reuse**: If a fork already exists on your GitHub account, use it; otherwise fork with `gh repo fork`.

4. **Clone** the fork into the clone directory, fetching only the target branch:
   ```bash
   git clone --depth 1 --single-branch --branch <branch> <fork-url> <repo-name>
   ```
   Use the branch from the URL, or omit `--branch` for the default branch.

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

7. **Create the migration branch**: Generate the branch name using the current timestamp (e.g. `gradle-10-migration/20260331-1400`). If a branch with this exact name already exists locally or on the remote, **abort with an error** — do not reset or reuse it. Create the branch off the base branch.

## Done when

- The clone directory exists with the fork checked out
- The migration branch is created and checked out
- `JAVA_HOME` is set and its path starts with `$HOME/.sdkman/candidates/java/`
- `java -version` succeeds, reports the exact major version determined in step 5, and identifies the build as Temurin
