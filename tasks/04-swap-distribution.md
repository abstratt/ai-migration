# Task: Swap Gradle Distribution

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- Gradle version is 9.x (either already was, or upgraded by the previous task)
- JAVA_HOME is set to a working JDK

## Pre-start check: clean working tree

Before doing anything else, run `git -C migrated/<repo-name> status --porcelain`. If the output is **non-empty**, **STOP THE ENTIRE WORKFLOW** — do not commit the changes yourself, do not run the Resume check, do not continue to the next task. Report the dirty paths and exit. Uncommitted changes at this point mean an earlier task skipped its commit checkpoint; proceeding would break resume detection on a subsequent run and compound the bookkeeping error.

## Gradle execution authorized

This task requires running Gradle commands (`./gradlew`). Gradle execution and distribution downloads are pre-authorized for this task.

## Resume check

First resolve the active distro pair to get **TARGET_URL** (see **Distro pair selection** in CONTEXT.md).

1. Read `gradle/wrapper/gradle-wrapper.properties`
2. If `distributionUrl` already points to the pair's **TARGET_URL**, this task is already complete
3. Also check `git log` for a commit message matching "Swap Gradle Distribution" (the task title)

## Instructions

First resolve the active distro pair to get **TARGET_URL** (see **Distro pair selection** in CONTEXT.md) — the Gradle 10 preview distribution this migration targets.

1. Edit `gradle/wrapper/gradle-wrapper.properties` to set `distributionUrl` to the pair's **TARGET_URL**:
   ```
   distributionUrl=<TARGET_URL>
   ```
   Also remove `distributionSha256Sum` if present, and set `validateDistributionUrl=false`.

2. Run `./gradlew help` **once** to confirm that the custom distribution downloads and Gradle starts up. That is the only goal here.

   **Success criterion is invocation, not build success.** The build is expected to fail at this point. As long as the wrapper was able to fetch the distribution and Gradle began executing (you see Gradle output, configuration starts, etc.), this step is done — even if `./gradlew help` exits non-zero.

   Do **not**:
   - Re-run `./gradlew` to see if it passes
   - Try to fix build errors, deprecation warnings, or configuration failures reported by this run
   - Iterate on any output from this command
   - Run any other Gradle task (`assemble`, `build`, `tasks`, etc.)

   Fixing the build is the job of task 06 (static transformations) followed by tasks 07 and 08 (validation and iteration).

## Commit checkpoint (mandatory before moving on)

Before starting task 05, commit the changes from this task:

- Subject: `Swap Gradle Distribution` (the task title)
- Include the `Assistant:` trailer (see CONTEXT.md)
- After committing, run `git status` and confirm the working tree is clean

Do not combine these changes with a later task's commit. See the "Commit Discipline" section in CONTEXT.md.

## Done when

- `gradle-wrapper.properties` points to the custom Provider API distribution
- `distributionSha256Sum` is removed (if it was present)
- `validateDistributionUrl=false` is set
- `./gradlew help` was invoked exactly once, the distribution downloaded, and Gradle started executing (pass/fail of the `help` task itself is irrelevant)
- A commit with subject `Swap Gradle Distribution` exists on the migration branch and `git status` is clean
