# Task: Upgrade Baseline Gradle

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- JAVA_HOME is set to a working JDK

## Pre-start check: clean working tree

Before doing anything else, run `git -C migrated/<repo-name> status --porcelain`. If the output is **non-empty**, **STOP THE ENTIRE WORKFLOW** — do not commit the changes yourself, do not run the Resume check, do not continue to the next task. Report the dirty paths and exit. Uncommitted changes at this point mean an earlier task skipped its commit checkpoint; proceeding would break resume detection on a subsequent run and compound the bookkeeping error.

## Gradle execution authorized

This task requires running Gradle commands (`./gradlew`). Gradle execution and distribution downloads are pre-authorized for this task.

## Resume check

First resolve the active distro pair to get **BASELINE_VERSION** (see **Distro pair selection** in CONTEXT.md).

1. Check the current Gradle version by reading `gradle/wrapper/gradle-wrapper.properties` for the distribution URL
2. If the version is already at **BASELINE_VERSION** or higher (but not the custom Provider API distribution), this task is already complete
3. Also check `git log` for a commit message matching "Upgrade Baseline Gradle" (the task title)

If the Gradle version is already at BASELINE_VERSION or higher, skip this task entirely.

## Instructions

This task is **conditional** — only needed if the repository is not already on the baseline Gradle version (or higher).

First resolve the active distro pair to get **BASELINE_VERSION** (see **Distro pair selection** in CONTEXT.md). This is the baseline release the pair's migration data was computed against, so the project must be on it before later tasks apply that data.

1. Run `./gradlew wrapper --gradle-version <BASELINE_VERSION>` to update the wrapper and distribution

2. Run `./gradlew help` and fix any issues caused by the major version upgrade

Note: Always use the `wrapper` task for standard Gradle version upgrades. Only manually edit `gradle-wrapper.properties` for the custom Provider API distribution URL (that happens in the next task).

## Commit checkpoint (mandatory before moving on)

Before starting task 04, commit the changes from this task:

- Subject: `Upgrade Baseline Gradle` (the task title)
- Include the `Assistant:` trailer (see CONTEXT.md)
- After committing, run `git status` and confirm the working tree is clean

Do not combine these changes with a later task's commit. See the "Commit Discipline" section in CONTEXT.md.

## Done when

- `gradle/wrapper/gradle-wrapper.properties` references the pair's baseline Gradle version (or was already at that version or higher)
- `./gradlew help` succeeds
- A commit with subject `Upgrade Baseline Gradle` exists on the migration branch (or the repo was already at the baseline version or higher, no changes were made, and `git status` is clean)
