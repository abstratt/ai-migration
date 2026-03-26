# Gradle 9 → 10 Migration Plan

## Input

The repository to migrate is provided via the `REPO_URL` environment variable (e.g. `https://github.com/owner/repo` or `https://github.com/owner/repo/tree/branch`).
- If a branch is embedded in the URL, that branch is the base for the migration work.
- Otherwise, the repo's default branch is used.

## Environment

- **REPO_URL**: The repository URL (and optionally branch) to migrate.
- **JAVA_HOME**: Set by Claude after installing the required JDK via SDKMAN (see Setup).
- **Clone directory**: `/workspace`
- **Migration branch name**: `gradle-10-migration`
- **SDKMAN**: Pre-installed in the Docker image at `$HOME/.sdkman`

## Workflow

### Setup

0. If `/workspace` dir is not empty, delete its contents first
1. **Parse `REPO_URL`** to extract the `owner/repo` and optional branch.
2. **Fork or reuse**: If a fork already exists on your GitHub account, use it; otherwise fork with `gh repo fork`
3. **Clone** the fork locally into the clone directory (shallow, single-branch: `git clone --depth 1 --single-branch`)
4. If a non-default branch was specified, **check out** that branch
5. ...
6. **Determine required Java version** from the build configuration (e.g. `toolchain { languageVersion }`, `sourceCompatibility`, `targetCompatibility`, `JAVA_HOME` hints in CI files). Default to 21 if unclear.
7. **Install and activate the JDK** via SDKMAN:
   ```bash
   source "$HOME/.sdkman/bin/sdkman-init.sh"
   sdk install java <version>-tem   # e.g. 17.0.14-tem, 21.0.7-tem
   sdk use java <version>-tem
   export JAVA_HOME="$HOME/.sdkman/candidates/java/current"
   ```
8. **Create or reset the migration branch**: If `gradle-10-migration` does not exist locally or on the fork, create it off the base branch. If it already exists, reset it to the tip of the base branch (`git checkout gradle-10-migration && git reset --hard <base>`). 

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
9. Validate with `./gradlew help`
10. **Commit**: present tense message (e.g. "Update Gradle distribution to custom Provider API build")

#### Commit 2: Fix build for `help` task

11. Run `./gradlew help` and inspect errors
12. Fix build script issues caused by the new Gradle version's lazy property (Provider API) changes:
    - Use code inspection to identify incompatible usages
    - Avoid eagerly realizing providers
    - Add a code comment explaining the reason for each non-trivial change
    - Ignore deprecations for now
13. Iterate until `./gradlew help` succeeds
14. **Commit only if changes were made**: present tense message (e.g. "Migrate build scripts to work with `./gradlew help`")

#### Commit 3: Fix build for `assemble` task

15. Run `./gradlew assemble` and inspect errors
16. Fix any additional issues following the same rules as above
17. Iterate until `./gradlew assemble` succeeds
18. **Commit only if changes were made**: present tense message (e.g. "Migrate build scripts to work with `./gradlew assemble`")

#### Commit 4: a copy of the report file 

A copy of the report that is created at the end should be added and committed as part of the repository being migrated.

#### What to do if a previous migration has already been attempted?

- It is possible a migration has been run before. 
- In that case, drop and replace the previous commits so you can repeat the process from scratch with the latest instructions. 
- Do not skip any steps because you found a migration was performed before. You must redo all the work from scratch.


### Publish

19. **Push** the migration branch to the fork
20. **Create a PR** targeting the **fork's base branch** (not the upstream repo)

## Commit Message Style

- Use present tense verbs (e.g. "Update", "Migrate", "Fix")
- Describe what was done, not why

## Code Change Guidelines

- Avoid eagerly realizing providers
- Add explanatory code comments for non-trivial changes
- Trivial changes (simple property get/set) do not need comments
- Ignore deprecations for now
- Do not change observable functionality - this is basically a refactor

## Common Migration Patterns

When the custom Gradle distro removes eager setters, apply replacements as required, like (but not limited to) these:

### Process execution (ExecSpec / BaseExecSpec / JavaExecSpec)
- `spec.setIgnoreExitValue(b)` → `spec.getIgnoreExitValue().set(b)`
- `spec.setStandardOutput(os)` → `spec.getStandardOutput().set(os)`
- `spec.setErrorOutput(os)` → `spec.getErrorOutput().set(os)`
- `spec.setStandardInput(is)` → `spec.getStandardInput().set(is)`
- `spec.setExecutable(s)` → `spec.executable(s)`
- `spec.setArgs(list)` → `spec.args(list)`
- `spec.setWorkingDir(f)` → `spec.workingDir(f)`
- `spec.setEnvironment(map)` → `spec.getEnvironment().set(map)`

### Test tasks
- `test.setTestClassesDirs(fc)` → `test.getTestClassesDirs().setFrom(fc)`
- `test.setClasspath(fc)` → `test.getClasspath().setFrom(fc)`
- `test.setMaxParallelForks(n)` → `test.getMaxParallelForks().set(n)`
- `test.getJavaVersion()` now returns `Provider<JavaVersion>` → use `.get()` when needed
- `test.getSystemProperties()` now returns `MapProperty` → `putIfAbsent` unavailable, use `systemProperty(k,v)` or `.put(k,v)`

### Publishing
- `pomTask.setDestination(x)` → `pomTask.getDestination().set(x)` (now `RegularFileProperty`)
- `publication.setArtifactId(s)` → `publication.getArtifactId().set(s)` (can wire to Provider, removing need for `afterEvaluate`)
- `generateMavenPom.map(GenerateMavenPom::getDestination)` → `generateMavenPom.flatMap(GenerateMavenPom::getDestination)` (returns property now)

### Task properties
- `task.setGroup(s)` → `task.getGroup().set(s)`
- `task.setDescription(s)` → `task.getDescription().set(s)`

### Compilation
- `javaCompile.setClasspath(fc)` → `javaCompile.getClasspath().setFrom(fc)`

### Archives
- `archiveTask.setDestinationDir(f)` → `archiveTask.getDestinationDirectory().set(f)`

### Wrapper properties cleanup
- Remove `distributionSha256Sum` (won't match custom distro)
- Set `validateDistributionUrl=false`

### General
- When a getter now returns a `Provider<T>` instead of `T`, add `.get()` to realize it
- When a getter returns `DirectoryProperty` instead of `File`, use `.get().getAsFile()`
- When a getter returns `RegularFileProperty` instead of `File`, use `.get().getAsFile()`
- Use `flatMap` instead of `map` when chaining providers that return property types
- If you believe a provider needs to be evaluated, make sure there is a strong reason to do so, and there is lazy alternative  

## Allowed Operations

You will be running under a Docker container. 

You are authorized to:
- Edit, create, and delete files in this repository
- Run git commands (add, commit, push)
- Run tests and linters
- Install dependencies

The following operations are pre-authorized and should be performed without asking for confirmation:

- Fork the repository and clone it into the clone directory
- Create branches, commit, and push to forked repositories
- Create PRs on forked repositories
- Edit build files (e.g. `build.gradle`, `build.gradle.kts`, `settings.gradle`, `settings.gradle.kts`, `gradle.properties`, `gradle-wrapper.properties`, and `buildSrc`/convention plugin sources)
- Edit Java/Kotlin/Groovy source files that are part of the build tooling (e.g. custom Gradle plugins, tasks, and extensions)
- Run Gradle commands (`./gradlew help`, `./gradlew assemble`, etc.)
- Run `gh` CLI commands for forking and PR creation
- Run `git` commands (clone, checkout, branch, add, commit, push, reset, diff, status, log)
- Run shell commands for inspecting build output, searching for patterns, and reading files
- Download Gradle distributions (triggered automatically by `./gradlew`)
- Install JDK versions via SDKMAN (`sdk install java`, `sdk use java`)

## Report

After the migration is complete, produce a `REPORT-<YYYYMMDD-HHMM>.md` (e.g. `REPORT-20260320-1430.md`) under this directory and under `${REPO_DIR}/migrations/` containing:

1. **Summary**: The repository, its migration status (migrated, skipped, failed), and PR link
2. **Nature of changes**: A summary of the types of changes made, with links to the actual changed locations in the PR

Add a copy of the report to the repository under `REPO_DIR`, and commit and push that to the remote branch under the fork.

## Important Notes

- Do NOT sync the fork with upstream; use whatever state the fork is in.
- The PR is created against the fork, not the original upstream repository.
- The PR targets the fork's base branch (default or the branch from `REPO_URL`).
- Skip commits if no code changes are needed (no empty commits).
