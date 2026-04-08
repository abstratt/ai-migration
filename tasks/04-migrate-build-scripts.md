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

   To find these, extract the class names from `migration-data.json` — both the `class` field **and** every entry in the `also_known_as` array (which lists public API subtypes that inherit the property, e.g. `Test` for `JavaForkOptions.maxHeapSize`, `MavenArtifactRepository` for `UrlArtifactRepository.url`) — and search all `*.java`, `*.kt`, `*.groovy`, `*.gradle`, and `*.gradle.kts` files for the three categories of usage described below.

   **Three categories of usage to search for:**

   **A. Removed accessors** — search for every name listed in `removed_accessors` across all entries in `migration-data.json`. This includes:
   - `set*` setters (e.g. `setClasspath`, `setArgs`, `setEncoding`)
   - `is*` boolean getters (e.g. `isPreserveFileTimestamps`, `isFork`, `isEnabled`) — these are removed for `boolean` kind properties and replaced by `getX()` returning `Property<Boolean>`

   **B. Getters whose return type changed** — for every entry in `migration-data.json`, derive the getter name as `get` + capitalised property name (e.g. `property: "args"` → `getArgs()`, `property: "metadataCharset"` → `getMetadataCharset()`). These getters are **not** listed in `removed_accessors` because the method name is unchanged, but their return type changes from `T` / `List<T>` / `Set<T>` etc. to `Property<T>` / `ListProperty<T>` / `SetProperty<T>` etc. Search for these getter names and flag every site where the result is used as the old type — i.e. where the call is **not** immediately chained with a `Property` API method such as `.get()`, `.set(`, `.from(`, `.add(`, `.addAll(`, `.isPresent()`, `.map(`, `.flatMap(`, or `.orElse(`.

   **C. Groovy DSL bare property access** — in `*.gradle` and `*.gradle.kts` files, Groovy/Kotlin DSL can access properties without `get`/`set` prefixes, and list/set properties can be mutated with operators. For every `list`, `set`, or `map` kind entry in `migration-data.json`, search `*.gradle` / `*.gradle.kts` files for the bare property name (e.g. `compilerArgs`, `jvmArgs`, `links`) and check for operator-style mutations (`-=`, `+=`, `<<`) which no longer work on lazy `ListProperty` / `SetProperty` / `MapProperty`.

3. **Apply transformations** by looking up each usage in `migration-data.json` to get its `kind`, then applying the corresponding rule from `MIGRATION_RULES.md`:
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
