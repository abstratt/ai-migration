# Task: Migrate Build Scripts and Gradle API Usages

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- `gradle-wrapper.properties` points to the custom Provider API distribution
- JAVA_HOME is set to a working JDK

## Resume check

1. Check `git log` for a commit message matching "Migrate build scripts" or similar migration-data-driven commit
2. If such a commit exists on the current branch, this task is already complete

## Instructions

1. **Load the migration reference files** from `report-generator/`:
   - `report-generator/migration-data.json` — lookup table of every changed property (class, old type, new type, kind, removed accessors)
   - `report-generator/MIGRATION_RULES.md` — transformation rules for each property kind

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
   - **`[unconfirmed]` hits**: no import match found. Likely false positives, but still check: the type might be used via a static import, an inner class, or accessed through a method call chain (e.g. `task.getOptions().setEncoding(...)`). If the receiver is clearly a non-Gradle type (e.g. `ZipOutputStream`, `Project.setVersion()`, a custom POJO), skip it.
   - When in doubt, check the import statements and the declared type of the receiver variable.

3. **Apply transformations** by looking up each real hit in `migration-data.json` to get its `kind`, then applying the corresponding rule from `MIGRATION_RULES.md`:
   - Prefer lazy wiring (`taskB.foo.set(taskA.foo)`) over eagerly resolving values
   - Use `.get()` only when the resolved value is needed (e.g., passing to an API that does not accept `Provider`)
   - Add a code comment explaining the reason for each non-trivial change
   - Ignore deprecations for now

   **Additional rules for the new search categories:**

   - **`is*` boolean getter sites**: replace `task.isFoo()` with `task.getFoo().get()` (inside task actions or when a resolved value is needed), or wire lazily with `task.getFoo()` (returns `Property<Boolean>`) elsewhere.
   - **Changed-return-type getter sites**: when `getX()` is used as the old plain type, add `.get()` to resolve it: `task.getArgs()` → `task.getArgs().get()`. When it is passed to an API that accepts `Provider<T>`, no `.get()` is needed.
   - **Groovy DSL operator mutations**: replace `prop -= [value]` / `prop += [value]` with `prop.set(prop.get() - [value])` / `prop.add(value)` respectively.
   - **`file_collection` kind**: replace `task.setX(fc)` with `task.getX().setFrom(fc)`. Use `.setFrom()` (not `.from()`) when replacing the entire collection. Watch for circular references: if the new value references the same property, snapshot first with `.getFiles()`: `task.getX().setFrom(project.files(extra, task.getX().getFiles()).filter(...))`.

4. **Commit current changes** with a present tense message (e.g. "Migrate build scripts to Gradle 10 lazy property API")

   Do **not** try to validate changes using `./gradlew` yet. The build would potentially still fail. We want only changes derivable from `migration-data.json` in this changeset.

## Done when

- All build scripts **and** all Java/Kotlin/Groovy source files that use Gradle API types have been scanned and transformed according to `migration-data.json`
- Changes are committed
- No `./gradlew` validation has been run (that's the next task)
