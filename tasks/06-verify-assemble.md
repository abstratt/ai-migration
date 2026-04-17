# Task: Verify with `./gradlew assemble`

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- `./gradlew help` succeeds (previous task completed)
- JAVA_HOME is set to a working JDK

## Gradle execution authorized

This task requires running Gradle commands (`./gradlew`). Gradle execution and distribution downloads are pre-authorized for this task.

## Resume check

1. Run `./gradlew assemble`
2. If it succeeds on the first attempt with no changes needed, this task is already complete
3. Also check `git log` for a commit message matching "Verify with `./gradlew assemble`" (the task title)

## Instructions

1. **Run `./gradlew assemble`** and inspect errors

2. **Fix any additional issues** following the same approach:
   - Look up in `migration-data.json` first
   - Then fix manually based on error output

3. **Iterate** until `./gradlew assemble` succeeds

4. **Commit only if changes were made** — use the task title "Verify with `./gradlew assemble`" as the commit message subject (the task title contains the literal `./gradlew assemble` so it is clear these fixes were driven by `assemble` failures). Include the `Assistant:` trailer (see CONTEXT.md).

## Done when

- `./gradlew assemble` exits 0
- Any fixes are committed (or no commit needed if assemble passed without changes)
