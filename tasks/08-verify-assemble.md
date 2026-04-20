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

## Commit checkpoint (mandatory before moving on)

Before starting task 09, resolve this task's changes:

- If the task made changes, commit them with subject `` Verify with `./gradlew assemble` `` (the task title — the backticks around `./gradlew assemble` make it clear these fixes were driven by `assemble` failures). Include the `Assistant:` trailer (see CONTEXT.md).
- If `./gradlew assemble` passed on the first try with no edits, skip the commit — but only if `git status` is already clean.
- Either way, run `git status` before starting task 09 and confirm the working tree is clean.

See the "Commit Discipline" section in CONTEXT.md.

## Done when

- `./gradlew assemble` exits 0
- Either a commit with subject `` Verify with `./gradlew assemble` `` exists on the migration branch, or no changes were needed; in both cases `git status` is clean
