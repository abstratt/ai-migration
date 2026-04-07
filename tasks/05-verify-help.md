# Task: Verify with `./gradlew help`

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- Build scripts have been migrated (previous task committed)
- JAVA_HOME is set to a working JDK

## Resume check

1. Run `./gradlew help`
2. If it succeeds on the first attempt with no changes needed, this task is already complete
3. Also check `git log` for a commit message matching "Fix remaining" or similar post-migration fix commit after the migration commit

## Instructions

1. **Run `./gradlew help`** and inspect any errors

2. **Fix remaining issues** not covered by the migration data:
   - Third-party plugin incompatibilities
   - Custom build logic that uses removed APIs
   - Look up fixes in `migration-data.json` first, then fix manually based on error output

3. **Iterate** until `./gradlew help` succeeds

4. **Commit only if changes were made**: present tense message (e.g. "Fix remaining build issues for `./gradlew help`")

## Done when

- `./gradlew help` exits 0
- Any fixes are committed (or no commit needed if help passed without changes)
