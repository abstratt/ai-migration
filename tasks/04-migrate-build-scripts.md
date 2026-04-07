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

2. **Identify all files that need migration.** The scan must cover two categories:

   **Build scripts** (Groovy/Kotlin DSL):
   - `build.gradle`, `build.gradle.kts`
   - `settings.gradle`, `settings.gradle.kts`
   - Any `*.gradle` or `*.gradle.kts` files anywhere in the project

   **Java/Kotlin/Groovy sources that use the Gradle API:**
   - `buildSrc/` sources
   - Convention plugins
   - Any subproject whose source files import Gradle API types (e.g. `org.gradle.api.*`). These are typically Gradle plugins, custom tasks, or extensions shipped as part of the project (e.g. a `build-plugin/` or `gradle-plugin/` subproject)

   To find these, extract the class names from `migration-data.json` (the `class` field — e.g. `org.gradle.api.tasks.testing.Test`, `org.gradle.api.tasks.JavaExec`) and search all `*.java`, `*.kt`, `*.groovy`, `*.gradle`, and `*.gradle.kts` files for:
   - Imports of those classes
   - Usages of the removed accessor names listed in `removed_accessors` (e.g. `setClasspath`, `setArgs`, `getMetadataCharset`, `isPreserveFileTimestamps`)

3. **Apply transformations** by looking up each usage in `migration-data.json` to get its `kind`, then applying the corresponding rule from `MIGRATION_RULES.md`:
   - Prefer lazy wiring (`taskB.foo.set(taskA.foo)`) over eagerly resolving values
   - Use `.get()` only when the resolved value is needed (e.g., passing to an API that does not accept `Provider`)
   - Add a code comment explaining the reason for each non-trivial change
   - Ignore deprecations for now

4. **Commit current changes** with a present tense message (e.g. "Migrate build scripts to Gradle 10 lazy property API")

   Do **not** try to validate changes using `./gradlew` yet. The build would potentially still fail. We want only changes derivable from `migration-data.json` in this changeset.

## Done when

- All build scripts **and** all Java/Kotlin/Groovy source files that use Gradle API types have been scanned and transformed according to `migration-data.json`
- Changes are committed
- No `./gradlew` validation has been run (that's the next task)
