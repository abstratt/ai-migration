# Gradle 9 → 10 Migration Plan

## Input

The repository to migrate is provided via the `REPO_URL` environment variable (e.g. `https://github.com/owner/repo` or `https://github.com/owner/repo/tree/branch`).
- If a branch is embedded in the URL, that branch is the base for the migration work.
- Otherwise, the repo's default branch is used.

## Environment

- **REPO_URL**: The repository URL (and optionally branch) to migrate.
- **JAVA_HOME**: Set by Claude after installing the required JDK via SDKMAN (see Setup).
- **Clone directory**: `<repo-name>` (e.g. `my-project`), derived from the repository name in `REPO_URL`. Create the parent dir if it does not exist yet.
- **Migration branch name**: `gradle-10-migration/<YYYYMMDD-HHMM>` (e.g. `gradle-10-migration/20260331-1400`). The timestamp is set at the start of the workflow and reused throughout.
- **SDKMAN**: Pre-installed in the Docker image at `$HOME/.sdkman`

## Workflow

### Setup

0. **Parse `REPO_URL`** to extract the `owner/repo`, repo name, and optional branch.
1. **Determine clone directory**: `<repo-name>`. If it already exists, delete it first.
2. **Fork or reuse**: If a fork already exists on your GitHub account, use it; otherwise fork with `gh repo fork`
3. **Clone** the fork into the clone directory, fetching only the target branch: `git clone --depth 1 --single-branch --branch <branch> <fork-url> <repo-name>` (use the branch from the URL, or omit `--branch` for the default branch)
6. **Determine required Java version** from the build configuration (e.g. `toolchain { languageVersion }`, `sourceCompatibility`, `targetCompatibility`, `JAVA_HOME` hints in CI files). Default to 21 if unclear.
7. **Install and activate the JDK** via SDKMAN:
   ```bash
   source "$HOME/.sdkman/bin/sdkman-init.sh"
   sdk install java <version>-tem   # e.g. 17.0.14-tem, 21.0.7-tem
   sdk use java <version>-tem
   export JAVA_HOME="$HOME/.sdkman/candidates/java/current"
   ```
8. **Create the migration branch**: Generate the branch name using the current timestamp (e.g. `gradle-10-migration/20260331-1400`). If a branch with this exact name already exists locally or on the remote, **abort with an error** — do not reset or reuse it. Create the branch off the base branch.

### Migration

#### Commit 0 (if needed): Upgrade to Gradle 9.4

If the repository is not already on Gradle 9.x, first upgrade to Gradle 9.4.0:
7a. Run `./gradlew wrapper --gradle-version 9.4` to update the wrapper and distribution
7b. Run `./gradlew help` and fix any issues caused by the major version upgrade
7c. **Commit**: "Upgrade Gradle wrapper to 9.4.0"

Note: Always use the `wrapper` task for standard Gradle version upgrades. Only manually edit `gradle-wrapper.properties` for the custom Provider API distribution URL.

#### Commit 1: Update Gradle distribution

8. Edit `gradle/wrapper/gradle-wrapper.properties` to set:
   ```
   distributionUrl=https://github.com/asodja/gradle-dev-distributions/releases/download/v1.1.0/gradle-provider-api-20260204140400.zip
   ```
   Also remove `distributionSha256Sum` if present, and set `validateDistributionUrl=false`.
9. Validate with `./gradlew help` only to ensure Gradle actualy runs. The build will probably fail - do not do anything about it yet.
10. **Commit**: present tense message (e.g. "Update Gradle distribution to custom Provider API build")

#### Commit 2: Migrate build scripts using migration data

11. **Load the migration reference files** from `report-generator/`:
    - `report-generator/migration-data.json` — lookup table of every changed property (class, old type, new type, kind, removed accessors)
    - `report-generator/MIGRATION_RULES.md` — transformation rules for each property kind

12. **Scan all build files** (`build.gradle`, `build.gradle.kts`, `settings.gradle`, `settings.gradle.kts`, `buildSrc/` sources, convention plugins, and any `*.gradle` or `*.gradle.kts` files) for usages of the removed accessors listed in the JSON.

13. **Apply transformations** by looking up each usage in `migration-data.json` to get its `kind`, then applying the corresponding rule from `MIGRATION_RULES.md`:
    - Prefer lazy wiring (`taskB.foo.set(taskA.foo)`) over eagerly resolving values
    - Use `.get()` only when the resolved value is needed (e.g., passing to an API that does not accept `Provider`)
    - Add a code comment explaining the reason for each non-trivial change
    - Ignore deprecations for now

14. **Commit current changes**

    - Do not try to validate your changes using `./gradlew ...`yet. The build would potentially still fail - do not do anything about it yet. We want only changes you can make based on `migration-data.json` in this changeset


#### Commit 3: verify and fix remaining issues

14. **Verify** with `./gradlew help`. Fix any remaining issues not covered by the migration data (e.g., third-party plugin incompatibilities, custom build logic).

15. Iterate until `./gradlew help` succeeds.

16. **Commit only if changes were made**: present tense message (e.g. "Migrate build scripts to Gradle 10 lazy property API")

#### Commit 4: Verify full build and fix remaining issues

17. Run `./gradlew assemble` and inspect errors
18. Fix any additional issues following the same approach (look up in migration data first, then fix manually)
19. Iterate until `./gradlew assemble` succeeds
20. **Commit only if changes were made**: present tense message (e.g. "Fix remaining build issues for `./gradlew assemble`")

#### What to do if a previous migration has already been attempted?

- Previous migration branches (e.g. `gradle-10-migration/20260320-1430`) may exist. Ignore them — the timestamped branch name ensures no collision, in case of collision, do not proceed.
- Do not skip any steps because a previous migration exists. Always start fresh.

## Commit Message Style

- Use present tense verbs (e.g. "Update", "Migrate", "Fix")
- Describe what was done, not why

## Code Change Guidelines

- Avoid eagerly realizing providers
- Add explanatory code comments for non-trivial changes
- Trivial changes (simple property get/set) do not need comments
- Ignore deprecations for now
- Do not change observable functionality - this is basically a refactor

## Migration Reference

The complete set of API changes and transformation rules lives in `report-generator/`:

- **`report-generator/migration-data.json`** — structured lookup table with every changed property: class, property name, old type, new type, `kind` (boolean, scalar, dir, file, file_collection, list, set, map, other, read_only), and removed accessors.
- **`report-generator/MIGRATION_RULES.md`** — one transformation rule per `kind`, covering `.set()`, `.get()`, `.from()`, `.add()`, lazy wiring, conventions, and read-only providers.

**How to use**: look up the class + property in the JSON to get its `kind`, then apply the matching rule.

### Additional patterns not in the migration data

These are patterns not captured by `@ReplacesEagerProperty` but commonly needed:

- **Wrapper properties cleanup**: remove `distributionSha256Sum` (won't match custom distro), set `validateDistributionUrl=false`
- **`flatMap` instead of `map`**: when chaining providers that return property types (e.g., `generateMavenPom.flatMap(GenerateMavenPom::getDestination)` instead of `.map(...)`)
- **Third-party plugin issues**: not covered by migration data; fix based on build error output

## Allowed Operations

You will be running under a Docker container. 

You are authorized to:
- Edit, create, and delete files in this repository - but not elsewhere
- Run git commands (add, commit — but **not push**)
- Run tests and linters
- Install dependencies

The following operations are pre-authorized and should be performed without asking for confirmation:

- Fork the repository and clone it into the clone directory
- Create branches and commit locally (do **not** push or create PRs)
- Edit build files (e.g. `build.gradle`, `build.gradle.kts`, `settings.gradle`, `settings.gradle.kts`, `gradle.properties`, `gradle-wrapper.properties`, and `buildSrc`/convention plugin sources)
- Edit Java/Kotlin/Groovy source files that are part of the build tooling (e.g. custom Gradle plugins, tasks, and extensions)
- Run Gradle commands (`./gradlew help`, `./gradlew assemble`, etc.)
- Run `gh` CLI commands for forking
- Run `git` commands (clone, checkout, branch, add, commit, diff, status, log — but **not push**)
- Run shell commands for inspecting build output, searching for patterns, and reading files
- Download Gradle distributions (triggered automatically by `./gradlew`), including the custom Provider API build from `https://github.com/asodja/gradle-dev-distributions/releases/download/v1.1.0/gradle-provider-api-20260204140400.zip`
- Install JDK versions via SDKMAN (`sdk install java`, `sdk use java`)

## Report

After the migration is complete, produce a `REPORT-<YYYYMMDD-HHMM>.md` (e.g. `REPORT-20260320-1430.md`) under this directory containing:

1. **Summary**: The repository, its migration status (migrated, skipped, failed), and the local branch name
2. **Nature of changes**: A summary of the types of changes made

## Important Notes

- Do NOT sync the fork with upstream; use whatever state the fork is in.
- Do NOT push to any remote. All commits stay local.
- Skip commits if no code changes are needed (no empty commits).
