# Task: Setup

@tasks/CONTEXT.md

## Preconditions

- `REPO_URL` environment variable is set
- Network access to GitHub is available
- SDKMAN is installed at `$HOME/.sdkman`

## Resume check

1. Check if the clone directory (derived from `REPO_URL`) exists and contains a git repository
2. Check if the migration branch (`gradle-10-migration/<YYYYMMDD-HHMM>`) already exists locally
3. If both are true and JAVA_HOME is set to a working JDK, this task is already complete

If the clone directory exists but the migration branch does not, resume from branch creation.
If JAVA_HOME is not set, resume from JDK detection and installation.

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

6. **Install and activate the JDK** via SDKMAN:
   ```bash
   source "$HOME/.sdkman/bin/sdkman-init.sh"
   sdk install java <version>-tem   # e.g. 17.0.14-tem, 21.0.7-tem
   sdk use java <version>-tem
   export JAVA_HOME="$HOME/.sdkman/candidates/java/current"
   ```

7. **Create the migration branch**: Generate the branch name using the current timestamp (e.g. `gradle-10-migration/20260331-1400`). If a branch with this exact name already exists locally or on the remote, **abort with an error** — do not reset or reuse it. Create the branch off the base branch.

## Done when

- The clone directory exists with the fork checked out
- The migration branch is created and checked out
- JAVA_HOME is set to a working JDK
- `java -version` succeeds with the expected version
