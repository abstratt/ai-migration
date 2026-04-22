# Task: Upgrade to Gradle 9.4

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- JAVA_HOME is set to a working JDK

## Pre-start check: clean working tree

Before doing anything else, run `git -C migrated/<repo-name> status --porcelain`. If the output is **non-empty**, **STOP THE ENTIRE WORKFLOW** — do not commit the changes yourself, do not run the Resume check, do not continue to the next task. Report the dirty paths and exit. Uncommitted changes at this point mean an earlier task skipped its commit checkpoint; proceeding would break resume detection on a subsequent run and compound the bookkeeping error.

## Gradle execution authorized

This task requires running Gradle commands (`./gradlew`). Gradle execution and distribution downloads are pre-authorized for this task.

## Resume check

1. Check the current Gradle version by reading `gradle/wrapper/gradle-wrapper.properties` for the distribution URL
2. If the version is already 9.x or higher (but not the custom Provider API distribution), this task is already complete
3. Also check `git log` for a commit message matching "Upgrade to Gradle 9.4" (the task title)

If the Gradle version is already 9.x+, skip this task entirely.

## Instructions

This task is **conditional** — only needed if the repository is not already on Gradle 9.x.

1. Run `./gradlew wrapper --gradle-version 9.4` to update the wrapper and distribution

2. Run `./gradlew help` and fix any issues caused by the major version upgrade

Note: Always use the `wrapper` task for standard Gradle version upgrades. Only manually edit `gradle-wrapper.properties` for the custom Provider API distribution URL (that happens in the next task).

## Commit checkpoint (mandatory before moving on)

Before starting task 04, commit the changes from this task:

- Subject: `Upgrade to Gradle 9.4` (the task title)
- Include the `Assistant:` trailer (see CONTEXT.md)
- After committing, run `git status` and confirm the working tree is clean

Do not combine these changes with a later task's commit. See the "Commit Discipline" section in CONTEXT.md.

## Done when

- `gradle/wrapper/gradle-wrapper.properties` references Gradle 9.4.x (or was already 9.x+)
- `./gradlew help` succeeds
- A commit with subject `Upgrade to Gradle 9.4` exists on the migration branch (or the repo was already on 9.x, no changes were made, and `git status` is clean)
