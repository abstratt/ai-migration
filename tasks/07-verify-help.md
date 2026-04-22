# Task: Verify with `./gradlew help`

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- Build scripts have been migrated (previous task committed)
- JAVA_HOME is set to a working JDK

## Pre-start check: clean working tree

Before doing anything else, run `git -C migrated/<repo-name> status --porcelain`. If the output is **non-empty**, **STOP THE ENTIRE WORKFLOW** — do not commit the changes yourself, do not run the Resume check, do not continue to the next task. Report the dirty paths and exit. Uncommitted changes at this point mean an earlier task skipped its commit checkpoint; proceeding would break resume detection on a subsequent run and compound the bookkeeping error.

## Gradle execution authorized

This task requires running Gradle commands (`./gradlew`). Gradle execution and distribution downloads are pre-authorized for this task.

## Resume check

1. Run `./gradlew help`
2. If it succeeds on the first attempt with no changes needed, this task is already complete
3. Also check `git log` for a commit message matching "Verify with `./gradlew help`" (the task title)

## Instructions

1. **Run `./gradlew help`** and inspect any errors

2. **Fix remaining issues** not covered by the migration data:
   - Third-party plugin incompatibilities
   - Custom build logic that uses removed APIs
   - Look up fixes in `migration-data.json` first, then fix manually based on error output
   - If `MIGRATION_NOTES.md` exists at the repo root, inspect it: each entry flags a hit that task 06 could not confidently transform. Use the build errors from this task to resolve them, then remove the corresponding entry from `MIGRATION_NOTES.md`.

   **Common compile-error → fix mapping.**

   > **Intent:** translate a given Gradle/compiler error message into the specific rewrite that resolves it, so error output can be acted on without inferring the underlying cause each time.

   | Error message fragment | Likely cause | Fix |
   |---|---|---|
   | `Cannot cast object ... Property<X>` to `X` | Consumer expects the resolved value | Add `.get()` at the call site |
   | `No signature of method: setX(Y)` / `method setX(Y) is undefined` | The `setX` accessor was removed | Replace `obj.setX(y)` with `obj.getX().set(y)` |
   | `No signature of method: leftShift` (`<<`) on `ListProperty`/`SetProperty`/`MapProperty` | Groovy DSL `<<` operator does not apply to lazy properties | Replace `prop << value` with `prop.add(value)` |
   | `Cannot set the value of a property of type X using a provider of type Y` | Source `Provider<T>` doesn't match target `Property<U>` | Wrap the source via `.map { ... }` to convert |
   | `Cannot query the value of task ... because it has no value` | Consumer read the property eagerly before it was wired | Move the `.get()` inside a task action, or switch to lazy wiring |
   | `Could not set unknown property 'X' of task ':Y' of type Z` | Kotlin/Groovy DSL property-assignment syntax no longer matches the lazy accessor | Replace `task.X = v` with `task.X.set(v)` |
   | `A value of type X cannot be assigned to a property of type Provider<X>` | Accessor now returns a `Property`/`Provider` | Use `.set(v)` on the returned property |
   | `Cannot invoke method minus()/plus() on null object` on a list/set/map prop | `prop -= […]` / `prop += […]` no longer works | Replace with `prop.set(prop.get() - [...])` / `prop.add(...)` |

3. **Iterate** until `./gradlew help` succeeds

## Commit checkpoint (mandatory before moving on)

Before starting task 08, resolve this task's changes:

- If the task made changes, commit them with subject `` Verify with `./gradlew help` `` (the task title — the backticks around `./gradlew help` make it clear these fixes were driven by `help` failures). Include the `Assistant:` trailer (see CONTEXT.md).
- If `./gradlew help` passed on the first try with no edits, skip the commit — but only if `git status` is already clean.
- Either way, run `git status` before starting task 08 and confirm the working tree is clean. Do not carry uncommitted fixes forward into task 08's commit.

See the "Commit Discipline" section in CONTEXT.md.

## Done when

- `./gradlew help` exits 0
- Either a commit with subject `` Verify with `./gradlew help` `` exists on the migration branch, or no changes were needed; in both cases `git status` is clean
