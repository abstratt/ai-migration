# Task: Verify with `./gradlew help`

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- Build scripts have been migrated (previous task committed)
- JAVA_HOME is set to a working JDK

## Gradle execution authorized

This task requires running Gradle commands (`./gradlew`). Gradle execution and distribution downloads are pre-authorized for this task.

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
   - If `MIGRATION_NOTES.md` exists at the repo root, inspect it: each entry flags a hit that task 04 could not confidently transform. Use the build errors from this task to resolve them, then remove the corresponding entry from `MIGRATION_NOTES.md`.

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

4. **Commit only if changes were made** — include the `Assistant:` trailer (see CONTEXT.md). The commit message **must** contain the literal string `./gradlew help` so it is clear these fixes were driven by `help` failures. Example: `Fix build issues found by ./gradlew help`.

## Done when

- `./gradlew help` exits 0
- Any fixes are committed (or no commit needed if help passed without changes)
