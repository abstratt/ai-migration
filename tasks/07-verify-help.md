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
   - Apply @migration-reference/MIGRATION_RULES.md — the per-kind rules, the **operator/assignment-overload rule (absolute)**, and the **Code Change Guidelines** (refactor-only, comments for non-trivial changes, no cosmetic changes, ignore deprecations) that govern every edit here
   - If `MIGRATION_NOTES.md` exists at the repo root, inspect it: each entry flags a hit that task 06 could not confidently transform. Use the build errors from this task to resolve them, then remove the corresponding entry from `MIGRATION_NOTES.md`.

   **Common compile-error → fix mapping.**

   > **Intent:** translate a given Gradle/compiler error message into the specific rewrite that resolves it, so error output can be acted on without inferring the underlying cause each time.

   | Error message fragment | Likely cause | Fix |
   |---|---|---|
   | `Cannot cast object ... Property<X>` to `X` | Consumer expects the resolved value | Resolve only if a plain `X` is needed (see lazy-first note); else wire the Provider through |
   | `No signature of method: setX(Y)` / `method setX(Y) is undefined` | The `setX` accessor was removed | Replace `obj.setX(y)` with `obj.getX().set(y)` |
   | `No signature of method: leftShift` (`<<`) on `ListProperty`/`SetProperty`/`MapProperty` | Groovy DSL `<<` operator does not apply to lazy properties | Replace `prop << value` with `prop.add(value)` |
   | `Cannot set the value of a property of type X using a provider of type Y` | Source `Provider<T>` doesn't match target `Property<U>` | Wrap the source via `.map { ... }` to convert |
   | `Cannot query the value of task ... because it has no value` | Consumer read the property eagerly before it was wired | Move the `.get()` inside a task action, or switch to lazy wiring |
   | `Could not set unknown property 'X' of task ':Y' of type Z` (**Groovy** DSL) | Groovy DSL property-assignment no longer matches the lazy accessor (Groovy has no `org.gradle.kotlin.dsl` overloads) | Replace `task.X = v` with `task.X.set(v)` |
   | `A value of type X cannot be assigned to a property of type Provider<X>` | Accessor now returns a `Property`/`Provider` | Use `.set(v)` on the returned property |
   | `Cannot invoke method minus()/plus() on null object` on a list/set/map prop (**Groovy**) | `prop -= […]` / `prop += […]` no longer works | Replace with `prop.set(prop.get() - [...])` / `prop.add(...)` |
   | `No applicable 'assign' function found for '=' overload` / `Unresolved reference 'assign'` (**Kotlin**) | `prop = v` on a now-lazy property, with the `org.gradle.kotlin.dsl` assign overload not in scope | **Add `import org.gradle.kotlin.dsl.assign` (or `*`) and keep `prop = v`. Do NOT rewrite to `prop.set(v)` / `prop.setFrom(v)` — the import works for `Property`, `ListProperty`, `SetProperty`, `MapProperty`, and `ConfigurableFileCollection` targets alike.** Only exception: a `DirectoryProperty`/`RegularFileProperty` assigned a `String` has no matching overload — keep `=` and wrap the value: `prop = java.io.File(v)` |
   | `No applicable 'assign' function` / `Unresolved reference 'assign'` on an **`is`-prefixed boolean** `isFoo = v` (**Kotlin**) | `isFoo` is now `Property<Boolean>`, assign overload not in scope | **Add `import org.gradle.kotlin.dsl.assign` and keep the name `isFoo = v`. Do NOT rename to `foo = v`** — even though `removed_accessors` lists `isFoo()`, Gradle keeps a Kotlin back-compat `getIsFoo()`, so `isFoo` still resolves and the rename is pure churn (see the **Accessor-name preservation** rule in `MIGRATION_RULES.md`) |
   | `Unresolved reference 'not' for operator '!'` on a boolean prop | `!boolProp` where `boolProp` is now `Property<Boolean>` | `!boolProp.get()` (no surviving operator) |
   | `Unresolved reference 'plusAssign'` on a `ListProperty`/`SetProperty`/`MapProperty`/`ConfigurableFileCollection` (**Kotlin**) | `prop += x` with the overload not in scope | **Add `import org.gradle.kotlin.dsl.plusAssign` (or `*`) and keep `prop += x`. Do NOT rewrite to `.add`/`.addAll`/`.from`.** |
   | `Unresolved reference 'filterKeys'`/`'remove'`/`'removeAll'` on a `MapProperty`/`ListProperty`/`SetProperty` | collection op with **no** `org.gradle.kotlin.dsl` operator (truly removed) | resolve+reset: `prop.set(prop.get().filterKeys { … })` / `prop.set(prop.get() - keys)` |
   | `operator modifier is required on 'fun get()'` / `Too many arguments for 'fun get()'` | `mapProp[k]` index read/write in `.kt` without `org.gradle.kotlin.dsl` in scope | **Add `import org.gradle.kotlin.dsl.*` to restore the `mapProp[k]` / `mapProp[k] = v` operators and keep the index form. Do NOT rewrite to `mapProp.get()[k]` / `mapProp.put(k, v)`.** |
   | `'val' cannot be reassigned` on `commandLine` | `BaseExecSpec.commandLine` is now a read-only `Provider` | use the method form: `commandLine(listOf(...))` |
   | `Unresolved reference 'maybeRedirect'` / receiver-type mismatch on `url` | `*ArtifactRepository.url` is now `Property<URI>` | read with `url.get()`, write with `url.set(...)` |
   | `StackOverflowError` while configuring (during `help`), inside provider/file-collection resolution | A migrated update wired a property to a derivation of *itself* (`classpath.setFrom(classpath.minus(x))`, `prop.set(prop.map { ... })`) — resolving it re-queries itself | Use the concrete impl's internal `replace(transform)`, which hands the transform the **current value** instead of re-querying: `((DefaultConfigurableFileCollection) task.getClasspath()).replace(it -> it.minus(x))`. See the **Self-reference note** below |

   > **Operator-overload-first note.** When the error is "the overload is not imported" — `No applicable
   > 'assign' function found for '=' overload`, `Unresolved reference 'assign'`/`'plusAssign'`, or
   > `operator modifier is required on 'fun get()'` — add the `org.gradle.kotlin.dsl` import and keep the
   > original `=` / `+=` / `mapProp[k]` form; **never** rewrite it to a method call. This is governed by
   > the **operator/assignment-overload rule (absolute)** under **Change-minimization principle** in
   > `migration-reference/MIGRATION_RULES.md` — see there for the full forbidden-rewrite table and the
   > narrow exceptions (`-=`, `<<`, `.remove`, `.filterKeys`, Groovy DSL).

   > **Lazy-first note (applies to every `.get()`/`.map` row above).** Prefer wiring the Provider
   > through (`dest.set(src)`) or transforming lazily (`.map`/`.flatMap`) over resolving. Reserve
   > `.get()` for when a plain value is genuinely required (string concat, comparison, a JDK/3rd-party
   > API), and resolve it **inside a task action** — never reflexively at configuration time. Reflexive
   > `.get()` risks `Cannot query the value … because it has no value`, silently drops the input/output
   > task-dependency the Provider would carry, and defeats configuration-cache laziness.

   > **Self-reference note (`StackOverflowError` while fixing the build).** When the fix for a removed
   > setter/`-=`/`minus` reads the property and writes a derivation of itself back lazily
   > (`classpath.setFrom(classpath.minus(x))`, `prop.set(prop.map { ... })`), the derived provider
   > references the same property, so resolving it recurses until the stack overflows — it surfaces as a
   > `StackOverflowError` while configuring, not a compile error. Use the concrete impl's **internal**
   > `replace(transform)` method (last resort, only when the overflow actually occurs); it passes the
   > current value to the transform instead of re-querying the property:
   >
   > ```java
   > // WRONG — self-reference; resolving re-queries getClasspath(), StackOverflowError
   > classpath.setFrom(classpath.minus(moduleCompileClasspath));
   > // RIGHT — replace() hands the transform a snapshot, breaking the cycle
   > ((DefaultConfigurableFileCollection) task.getClasspath()).replace(it -> it.minus(moduleCompileClasspath));
   > ```
   >
   > `replace(...)` lives on the internal impls: `ConfigurableFileCollection` →
   > `DefaultConfigurableFileCollection`; `Property`/`other`/`scalar` → `DefaultProperty`;
   > `ListProperty`/`SetProperty`/`MapProperty` → `AbstractCollectionProperty`. See
   > **Self-referential lazy update that recurses** in `migration-reference/MIGRATION_RULES.md`.

3. **Iterate** until `./gradlew help` succeeds

## Iteration strategy (avoid one-error-at-a-time whack-a-mole)

Most real rewrites in this task come from the scanner's blind spot (Kotlin property-assignment/access
syntax — see CONTEXT.md). Discovering them one Gradle run at a time is the dominant time sink. Instead:

- **Surface many errors per run.** Run with `--continue` so a failing module doesn't stop the build;
  collect all compile errors from the run before fixing.
- **Batch repeated patterns across the whole tree.** When an error matches a known lazy-property shape,
  `grep -rn` the repo for that shape and fix *every* occurrence before re-running — don't fix one and
  re-iterate. Patterns that recurred heavily in practice:
  `\bprop = ` (property assign), `prop += `, `environment.remove(`/`systemProperties.remove(`,
  `standardOutput = `/`errorOutput = `/`isIgnoreExitValue = `, `\.url = `, `artifactId = artifactId`,
  `commandLine = `, `allWarningsAsErrors.set(true)`.
- **Defeat config-cache staleness.** While iterating, run with `--no-configuration-cache` so
  `gradle.properties` changes (esp. warnings-as-errors flags) actually take effect; do a final clean run
  with the cache on to confirm `help` truly passes.
- **Distinguish deprecation noise from real errors** when scanning output (`grep " e: "` for Kotlin
  errors; ignore `w:`/`is deprecated` lines — those are handled by disabling warnings-as-errors, not by
  rewriting). See the infra-issues guidance in CONTEXT.md.

## Commit checkpoint (mandatory before moving on)

Before starting task 08, resolve this task's changes:

- If the task made changes, commit them with subject `` Verify with `./gradlew help` `` (the task title — the backticks around `./gradlew help` make it clear these fixes were driven by `help` failures). Include the `Assistant:` trailer (see CONTEXT.md).
- If `./gradlew help` passed on the first try with no edits, skip the commit — but only if `git status` is already clean.
- Either way, run `git status` before starting task 08 and confirm the working tree is clean. Do not carry uncommitted fixes forward into task 08's commit.

See the "Commit Discipline" section in CONTEXT.md.

## Done when

- `./gradlew help` exits 0
- Either a commit with subject `` Verify with `./gradlew help` `` exists on the migration branch, or no changes were needed; in both cases `git status` is clean
