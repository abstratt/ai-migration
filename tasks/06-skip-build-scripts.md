# Task: Skip Build Script Migration (brute-force mode)

@tasks/CONTEXT.md

This is the **brute-force-mode** replacement for `tasks/06-migrate-build-scripts.md`. It
runs in place of that task when `SKIP_BUILD_SCRIPTS` is set (see **Environment** in
CONTEXT.md and the conditional step 6 in `MIGRATION.md`). Instead of the data-driven
scan/rewrite of build scripts, it makes **no** source changes — it only guarantees a
clean starting point for the verification tasks, which then fix every build error from
scratch with no scaffolding from this task.

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- `gradle-wrapper.properties` points to the custom Provider API distribution
- JAVA_HOME is set to a working JDK

## Pre-start check: clean working tree

Before doing anything else, run `git -C migrated/<repo-name> status --porcelain`. If the output is **non-empty**, **STOP THE ENTIRE WORKFLOW** — do not commit the changes yourself, do not run the Resume check, do not continue to the next task. Report the dirty paths and exit. Uncommitted changes at this point mean an earlier task skipped its commit checkpoint; proceeding would break resume detection on a subsequent run and compound the bookkeeping error.

## Hard rule: no Gradle execution, no build-script rewrites

This task is deliberately a **no-op on source**. Do **not**:

- run `./gradlew` (or any `gradle` invocation) — build validation belongs to tasks 07/08;
- run `scan_usages.py` or `apply_migrations.py`, or read `migration-data.json` to apply rewrites;
- edit any build script or Java/Kotlin/Groovy source file.

The whole point of brute-force mode is to let tasks 07 and 08 discover and fix every
migration site purely from build-error output, with no proactive transformation here.

## Resume check

This task has **no resume check** — it always runs, every time, and is idempotent. It
produces no commit, so there is nothing to detect on a re-run; re-running it simply
re-confirms that no `MIGRATION_NOTES.md` is present.

## Instructions

1. **Ensure no `MIGRATION_NOTES.md` exists.** Check for `migrated/<repo-name>/MIGRATION_NOTES.md`. If it is present (e.g. a stray untracked file left by a prior task-06 attempt on this clone), delete it so task 07 has nothing to inspect. In a normal brute-force run the file will not exist at all, in which case there is nothing to do.

2. **Make no other changes.** Do not edit build scripts or source files. Do not create any new files.

## Commit checkpoint (no commit in this task)

This task produces **no commit** inside the migrated repo (like task 05). There are no
source changes to record, and deleting a stray untracked `MIGRATION_NOTES.md` leaves
nothing staged.

- Do **not** create an empty commit, and do **not** invent a "Migrate Build Scripts and Gradle API Usages" commit — its absence is exactly how task 09 detects that build-script migration was skipped.
- Run `git -C migrated/<repo-name> status --porcelain` and confirm the working tree is clean before starting task 07. Do not carry anything forward.

See the "Commit Discipline" section in CONTEXT.md.

## Done when

- No `MIGRATION_NOTES.md` exists at the root of the cloned repo
- No `Migrate Build Scripts and Gradle API Usages` commit was created (none should exist on the migration branch)
- `git status` is clean
- No Gradle command was executed and no build script or source file was edited
