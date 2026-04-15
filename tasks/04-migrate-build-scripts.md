# Task: Migrate Build Scripts and Gradle API Usages

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- `gradle-wrapper.properties` points to the custom Provider API distribution
- JAVA_HOME is set to a working JDK

## Hard rule: no Gradle execution in this task

This task is a **static, data-driven transformation**. Do **not** run `./gradlew`, `gradle`, `gradle help`, `gradle assemble`, `gradle build`, `gradle tasks`, or any other Gradle invocation at any point during this task — not for validation, not for sanity checks, not to "see what breaks", not to iterate on fixes. Build validation is the job of tasks 05 and 06; running Gradle here will produce failures that you must not react to.

If you feel the urge to run Gradle to check your work, stop and commit what you have instead. Any iteration loop driven by Gradle output belongs in task 05 or later, never here.

## Resume check

1. Check `git log` for a commit message matching "Migrate build scripts" or similar migration-data-driven commit
2. If such a commit exists on the current branch, this task is already complete

## Instructions

1. **Load the migration reference files** from `report-generator/`:
   - `report-generator/migration-data.json` — lookup table of every changed property (class, old type, new type, kind, removed accessors)
   - `report-generator/MIGRATION_RULES.md` — transformation rules for each property kind

   **Leave-alone list.** The following constructs are outside the scope of this migration and must be kept as-is even if they superficially resemble a scan hit:

   > **Intent:** bound the set of code affected by this task to exactly the accessors driven by `migration-data.json`, so unrelated APIs are not modified.

   - `org.gradle.api.Task` accessors: `setDescription`, `setGroup`, `setEnabled`, `setDependsOn`, `setOnlyIf`, `setActions`, `setFinalizedBy`, `setMustRunAfter`, `setShouldRunAfter`, `setTimeout`, `setDidWork` (not lazy-migrated in Gradle 10).
   - Task lifecycle/wiring APIs: `doFirst`, `doLast`, `dependsOn(…)`, `finalizedBy(…)`, `mustRunAfter(…)`, `shouldRunAfter(…)`.
   - `Project` methods called on `project` itself (e.g. `project.file(...)`, `project.files(...)`, `project.layout.*`).
   - Third-party plugin types — any receiver in a non-`org.gradle` package. These are handled in task 05/06 if they produce build errors.
   - `@Input` / `@InputFile` / `@OutputDirectory` annotated fields on custom task classes declared in `buildSrc` — these require a different migration path (declaring the field as `Property<T>` rather than rewriting call sites) and are out of scope for this task.
   - Deprecation warnings reported by the scanner or the compiler — ignore them; this task covers removals only.
   - Comments, KDoc, Javadoc, and string literals that mention removed accessor names — leave them as-is.

2. **Run the automated usage scanner** to get a comprehensive, pre-filtered list of every candidate change site:

   ```bash
   python3 ../report-generator/scan_usages.py . 2>&1 | tee /tmp/scan-results.txt
   ```

   The scanner produces three sections:
   - **Cat-A** — removed accessors (`set*` / `is*` methods listed in `removed_accessors`)
   - **Cat-B** — changed-return-type getters (`get<Prop>()` used without `.get()` / `.set(` / etc.)
   - **Cat-C** — Groovy DSL operator mutations (`-=`, `+=`, `<<` on lazy `list`/`set`/`map` properties)

   The scanner already:
   - Restricts Java/Kotlin/Groovy files to those that import `org.gradle` (avoids application code and Maven plugin false positives)
   - Skips comment lines and method declarations
   - Skips Category B for test source directories (too many generic-name false positives)
   - Skips common Task-only accessors like `setDescription`, `setGroup` (not lazy-migrated in Gradle 10)
   - Annotates each hit with `[CONFIRMED: ClassName]` when a relevant Gradle type is found in the file's imports, or `[unconfirmed - check type]` when no import match was found

   **Review each hit** and decide if it is a real migration site:
   - **`[CONFIRMED]` hits**: the file imports a Gradle API type that owns the property. Almost always real — fix them. The only exception is if the method name is called on a *different* local variable of a non-Gradle type (check the receiver at the call site).
   - **`[unconfirmed]` hits in production source** (`buildSrc/src/main/java/`, `build-plugin/...src/main/java/`): the type may be accessed through a method chain rather than imported directly (e.g. `compile.getOptions().setEncoding(...)` where `CompileOptions` is returned by `getOptions()` but not imported; `publication.pom((pom) -> pom.setPackaging(...))` where `MavenPom` is a lambda parameter). **Treat these as real** and apply the fix — unless you can positively identify the receiver as a non-Gradle type (check the variable declaration or method chain).
   - **`[unconfirmed]` hits in test source or DSL files**: more likely to be false positives. Still check the receiver type before skipping.

   **Receiver-type decision procedure.** For each hit where the owning type is not obvious, walk this ladder in order and stop at the first matching step:

   > **Intent:** convert the ambiguous "is this call on a Gradle type?" judgment into a mechanical check that produces the same answer every time.

   1. Is the method name in the Task-only list (`setDescription`, `setGroup`, `setEnabled`, `setDependsOn`, `setOnlyIf`, `setActions`, `setFinalizedBy`, `setMustRunAfter`, `setShouldRunAfter`, `setTimeout`, `setDidWork`)? → **skip** (not migrated in Gradle 10).
   2. Does the file `import` a class that appears in `migration-data.json` and owns this property? → **apply** the transformation.
   3. Is the receiver a local variable? Find its declaration.
      - Declared type is in `migration-data.json`? → **apply**.
      - Declared type is in a non-`org.gradle` package? → **skip**.
   4. Is the receiver a method chain (`a.b().c()`)? Find `b()`'s declared return type. If that return type is in `migration-data.json` (directly or via `also_known_as`), → **apply**.
   5. Is the receiver a lambda parameter (e.g. `publication.pom(pom -> pom.setX(...))`)? Check the enclosing method's signature — the parameter's type is usually a Gradle configuration type. → **apply** if found in the JSON.
   6. None of the above → **leave unchanged and note in a comment for review**.

3. **Apply transformations** by looking up each real hit in `migration-data.json` to get its `kind`, then applying the corresponding rule from `MIGRATION_RULES.md`:
   - Prefer lazy wiring (`taskB.foo.set(taskA.foo)`) over eagerly resolving values
   - Use `.get()` only when the resolved value is needed (e.g., passing to an API that does not accept `Provider`)
   - Add a code comment explaining the reason for each non-trivial change
   - Ignore deprecations for now

   **Inheritance lookup via `also_known_as`.** A property may be defined on a base class and inherited by many public-API subtypes (e.g. `maxHeapSize` is on `JavaForkOptions` and inherited by `Test`, `JavaExec`, and others). If a direct class + property lookup returns no entry, search `migration-data.json` for the property name alone and check each match's `also_known_as` field.

   > **Intent:** ensure that inherited properties still resolve to their owning entry so the correct rule is applied instead of treating the hit as unmapped.

   Example: a scan hit against `Test.setMaxHeapSize("2g")` will not find an entry keyed by `class=Test, property=maxHeapSize`. The entry is keyed by `class=JavaForkOptions, property=maxHeapSize`, with `Test` listed under `also_known_as`. Apply the `JavaForkOptions.maxHeapSize` rule to the `Test` call site.

   **Additional rules for the new search categories:**

   - **`is*` boolean getter sites**: replace `task.isFoo()` with `task.getFoo().get()` (inside task actions or when a resolved value is needed), or wire lazily with `task.getFoo()` (returns `Property<Boolean>`) elsewhere.
   - **Changed-return-type getter sites**: when `getX()` is used as the old plain type, add `.get()` to resolve it: `task.getArgs()` → `task.getArgs().get()`. When it is passed to an API that accepts `Provider<T>`, no `.get()` is needed.
   - **Groovy DSL operator mutations**: replace `prop -= [value]` / `prop += [value]` with `prop.set(prop.get() - [value])` / `prop.add(value)` respectively.
   - **`file_collection` kind**: replace `task.setX(fc)` with `task.getX().setFrom(fc)`. Use `.setFrom()` (not `.from()`) when replacing the entire collection. Watch for circular references: if the new value references the same property, snapshot first with `.getFiles()`: `task.getX().setFrom(project.files(extra, task.getX().getFiles()).filter(...))`.

   **Defer-and-record escape hatch.** If a hit cannot be confidently transformed — the owning type is ambiguous after walking the receiver-type ladder, the `kind` does not match any rule, or the surrounding code would require a non-trivial restructure — record it in a `MIGRATION_NOTES.md` file at the root of the migrated repo and move on.

   > **Intent:** give each hit a legitimate "punt" outcome so that uncertain sites are flagged for follow-up in task 05/06 (where build errors and compile-error mappings are available) rather than being silently skipped or guessed at.

   Each entry in `MIGRATION_NOTES.md` should include:
   - File path and line number
   - The scanner-reported class + property (so the entry can be looked up in `migration-data.json` later)
   - A one-line description of the reason for deferral (e.g. "receiver type unclear: chained through third-party plugin API")

   Commit `MIGRATION_NOTES.md` together with the transformed files. Task 05/06 will consult it when resolving build failures.

4. **Self-check before commit.** Re-run the scanner on the transformed tree:

   ```bash
   python3 ../report-generator/scan_usages.py . 2>&1 | tee /tmp/scan-results-after.txt
   ```

   > **Intent:** provide a deterministic pass/fail signal that the migration covered every site the scanner can detect, without relying on Gradle execution (which is forbidden in this task).

   Expectations:
   - **Zero `[CONFIRMED]` Cat-A hits** (removed accessors) should remain — every confirmed hit means a real call site was missed.
   - **Zero `[CONFIRMED]` Cat-B hits** (changed-return-type getters without `.get()`/`.set(`) should remain.
   - **Zero `[CONFIRMED]` Cat-C hits** (DSL operator mutations) should remain.
   - `[unconfirmed]` hits may remain; these were already judged non-applicable during step 3.

   If any confirmed hits remain, return to step 3 and address them before committing.

5. **Commit current changes** with a present tense message (e.g. "Migrate build scripts to Gradle 10 lazy property API")

   Do **not** run `./gradlew` (or any other Gradle invocation) to validate the changes. See the "Hard rule" at the top of this task. We want only changes derivable from `migration-data.json` in this changeset; build validation and iteration happen in tasks 05 and 06.

## Done when

- All build scripts **and** all Java/Kotlin/Groovy source files that use Gradle API types have been scanned and transformed according to `migration-data.json`
- Re-running `scan_usages.py` shows zero confirmed hits in any category
- Changes are committed
- No Gradle command was executed during this task (validation belongs to tasks 05 and 06)
