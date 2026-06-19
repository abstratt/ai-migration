# Gradle 10 Lazy Property Migration Rules

Use with `migration-data.json` to migrate Gradle build scripts. Look up the class + property in the JSON to get `kind`, `old_type`, `new_type`, `removed_accessors`, `changed_return_accessors`, `new_read_accessor`, `new_write_accessor`, `new_is_provider`, and `inheriting_subtypes`, then apply the matching rule below. Types in the JSON are fully-qualified (e.g. `org.gradle.api.provider.Property<java.lang.String>`); the rules and examples in this document use simplified names for readability.

## Change-minimization principle

> **Rewrite a site only if the old form would fail to compile or change behavior under Gradle 10. If it still compiles and behaves identically, leave it unchanged.**

> **Operator/assignment-overload rule (absolute):** when a call site uses an operator or assignment form (`=`, `+=`, `mapProp[k]`, `mapProp[k] = v`, `files += fc`, `by`-delegation) and adding an `org.gradle.kotlin.dsl` import makes it compile again, you **MUST** add the import and keep the operator form. **Never** convert an operator/assignment form to its method-based equivalent (`.set(...)`, `.add(...)`, `.addAll(...)`, `.put(...)`, `.setFrom(...)`, `.get()[k]`) when an import would have preserved it. Adding the import is *always* the correct fix — not merely the preferred one. Switching to the method form in that situation is a migration defect, even though it compiles.

The rules below describe the *canonical* new form for each kind, but canonical does not mean mandatory. A correct-but-unnecessary rewrite is still a cost: it enlarges the diff, makes the migration harder to review and attribute, and inflates the change-comparison metrics. When in doubt, prefer the smallest diff and preserve the existing idiom.

**Adding an import is the default fix, not a fallback.** Kotlin source frequently keeps working against the migrated (lazy) types through Gradle's `org.gradle.kotlin.dsl` extensions: the assignment overload (`prop = value`, including `ListProperty`/`SetProperty`/`MapProperty`/`ConfigurableFileCollection` targets), the collection operators (`prop += x`), `MapProperty` indexing (`mapProp[k]` read and `mapProp[k] = v` write), and `by`-delegation. See **Kotlin DSL operators that survive migration** below for the full set. When one of these forms stops compiling only because the extension is not in scope, the fix is to bring it into scope:

- In `.gradle.kts` the `org.gradle.kotlin.dsl` package is an implicit default import, so these forms need **no change at all**.
- In a plain `.kt` file under a `kotlin-dsl` module, add `import org.gradle.kotlin.dsl.*` (or the specific symbol — `assign`, `plusAssign`, `get`, `set`, `getValue`, `setValue`) and leave the call site as-is.

Concretely, **do NOT** make any of these rewrites when an import would have kept the original compiling:

| Forbidden rewrite (when an import would work) | Correct fix |
|---|---|
| `prop = v` → `prop.set(v)` | add `import org.gradle.kotlin.dsl.assign`; keep `prop = v` |
| `args = listOf(...)` → `args.set(listOf(...))` | add the import; keep `args = listOf(...)` |
| `classpath = fc` → `classpath.setFrom(fc)` | add the import; keep `classpath = fc` |
| `prop += x` → `prop.add(x)` / `prop.addAll(x)` | add `import org.gradle.kotlin.dsl.plusAssign`; keep `prop += x` |
| `mapProp[k] = v` → `mapProp.put(k, v)` | add the import; keep `mapProp[k] = v` |
| `mapProp[k]` (read) → `mapProp.get()[k]` | add the import; keep `mapProp[k]` |

Rewrite to the method form **only** when no surviving operator exists (e.g. `-=`, which has no `minusAssign` extension; `.remove`/`.filterKeys`, which have no operator) or the language has no such support (Groovy DSL). The lone value-adaptation exception: `DirectoryProperty`/`RegularFileProperty` assigned a `String` has no matching `assign` overload — keep the `=` form but wrap the argument (`prop = File(v)`), do not switch to `.set(...)`.

Apply this principle whenever a removed accessor has an equivalent surviving form at the call site.

**Accessor-name preservation (the rule extends to *names*, not just operators).** `removed_accessors` lists removed *JVM signatures*, **not** removed *names*. A name listed there may still resolve at a **Kotlin** call site through a back-compat accessor — most importantly `getIsFoo()`, which Gradle generates alongside the canonical `getFoo()` for every `is`-prefixed boolean property (see the `boolean` kind below). Such a name is typically used in **assignment position** (`isFoo = value`), which keeps working via the assignment overload. The operator/assignment-overload rule therefore extends to the accessor name: when `isFoo = v` (or any existing accessor reference) still resolves after adding the relevant `org.gradle.kotlin.dsl` import, you **MUST keep the existing name** — do **not** rename it to the canonical `getFoo()`/`foo` form. Renaming a still-resolving Kotlin accessor is the same class of defect as switching `=` to `.set(...)`: it compiles, but it is unnecessary churn.

The **compiler**, not `removed_accessors`, is the source of truth for whether a Kotlin name must change. Try keep-the-name + add-the-import first; rename to the canonical accessor only if the original name genuinely fails to resolve. (This is Kotlin-specific — in Java and Groovy the `isFoo()` *method* really is gone and must be rewritten to the `getFoo()` lazy form.)

## Code Change Guidelines

These govern every code change made while applying this migration — i.e. the tasks that actually edit
source: build-script migration (task 06) and the `help`/`assemble` fix passes (tasks 07, 08). They are
the behavioral discipline layered on top of the per-kind mechanics below.

- **Prefer lazy wiring; resolve only when needed.** Avoid eagerly realizing providers — see
  **Cross-cutting concerns** below for the lazy-wiring / `.get()` specifics.
- **Add explanatory code comments for non-trivial changes.** Trivial changes (simple property
  get/set) do not need comments.
- **Ignore deprecations for now.**
- **Do not change observable functionality — this is basically a refactor.**
- **Do not make cosmetic changes** — no rewording comments, no reformatting code, no renaming
  variables. Change only what is necessary to complete the migration.

## End-to-end walkthrough

> **Intent:** demonstrate the complete lookup → decide → rewrite flow on one real example before reading the per-kind rules.

Suppose the scanner emits this hit:

```
buildSrc/src/main/java/MyBuildPlugin.java
  line  42: task.setEncoding("UTF-8");
           [CONFIRMED: JavaCompile]
           → JavaCompile.options.encoding (kind=scalar)
```

**Step 1 — Look up the entry in `migration-data.json`:**

```json
{
  "class": "org.gradle.api.tasks.compile.CompileOptions",
  "property": "encoding",
  "kind": "scalar",
  "old_type": "java.lang.String",
  "new_type": "org.gradle.api.provider.Property<java.lang.String>",
  "new_is_provider": false,
  "new_read_accessor": "getEncoding().get()",
  "new_write_accessor": "getEncoding().set(VALUE)",
  "removed_accessors": ["setEncoding(java.lang.String)"],
  "changed_return_accessors": ["getEncoding()"],
  "inheriting_subtypes": [...]
}
```

**Step 2 — Match the `kind` to a rule.** `kind=scalar` maps to the `scalar` rule below. Old `setX(T)` → new `x.set(T)`.

**Step 3 — Rewrite the call site:**

```java
// before
task.getOptions().setEncoding("UTF-8");
// after
task.getOptions().getEncoding().set("UTF-8");
```

**Step 4 — Check for a lazy-wiring opportunity.** If the argument were itself another task's property (e.g. `task.getOptions().setEncoding(otherTask.getOptions().getEncoding())`), prefer passing the `Provider` directly: `task.getOptions().getEncoding().set(otherTask.getOptions().getEncoding())` — no `.get()` on the source.

## Transformation rules by `kind`

### `boolean`
Old: `isX()` / `setX(boolean)` | New: `Property<Boolean> getX()`
```groovy
// old
task.setFork(true)
if (task.isFork()) { ... }
// new — configuration
task.fork.set(true)
task.fork.set(otherTask.fork)          // lazy wiring
// new — when a resolved value is needed
if (task.fork.get()) { ... }
```

**Kotlin back-compat for `is`-prefixed booleans.** When a boolean property migrates to `Property<Boolean>`, Gradle 10 generates the canonical `getFoo()` **and** a Kotlin-only back-compat accessor `getIsFoo()`. So the original Kotlin property name `isFoo` still resolves, and `isFoo = value` keeps working through the assignment overload. Per the **Accessor-name preservation** rule above:
- **Kotlin:** leave `isFoo = value` unchanged in `.gradle.kts`; in a plain `.kt` file under a `kotlin-dsl` module add `import org.gradle.kotlin.dsl.assign` and keep the name. **Do NOT rename `isFoo` to `foo`** — both names resolve, so the rename is pure churn even though it compiles.
- **Java / Groovy:** there is no such alias for these languages — the `isFoo()` method is genuinely removed, so rewrite to `getFoo().get()` / `.set(...)` as usual.

### `scalar`
Old: `T getX()` / `setX(T)` where T is String, int, long | New: `Property<T> getX()`
```groovy
// old
task.setEncoding("UTF-8")
String enc = task.getEncoding()
// new — configuration
task.encoding.set("UTF-8")
task.encoding.set(otherTask.encoding)  // lazy wiring
task.encoding.set(provider { compute() })
// new — when a resolved value is needed
String enc = task.encoding.get()
```

### `dir`
Old: `File getX()` / `setX(File)` | New: `DirectoryProperty getX()`
```groovy
// old
task.setBaseDir(file("src"))
File dir = task.getBaseDir()
// new — configuration
task.baseDir.set(layout.projectDirectory.dir("src"))
task.baseDir.set(otherTask.baseDir)    // lazy wiring
// new — when a resolved value is needed
File dir = task.baseDir.get().asFile
```

### `file`
Old: `File getX()` / `setX(File)` | New: `RegularFileProperty getX()`
```groovy
// old
task.setOutputFile(file("out.txt"))
File f = task.getOutputFile()
// new — configuration
task.outputFile.set(layout.buildDirectory.file("out.txt"))
task.outputFile.set(otherTask.outputFile) // lazy wiring
// new — when a resolved value is needed
File f = task.outputFile.get().asFile
```

### `file_collection`
Old: `FileCollection getX()` / `setX(FileCollection)` | New: `ConfigurableFileCollection getX()`

The replacement for `setX(FileCollection)` is `.setFrom(...)`, which **replaces** all entries and matches the old setter's behavior. `ConfigurableFileCollection` also exposes `.from(...)`, which **appends** — that is a distinct operation and is **not** a migration for the old setter. If a call site used `setX(...)`, always rewrite it as `.setFrom(...)`.

```groovy
// old
task.setClasspath(files("a.jar", "b.jar"))
FileCollection cp = task.getClasspath()
// new — configuration (replaces, matching the old setter)
task.classpath.setFrom("a.jar", "b.jar")
task.classpath.setFrom(otherTask.classpath) // lazy wiring
// new — when a resolved value is needed (iteration)
task.classpath.files.each { ... }
```

### `list`
Old: `List<T> getX()` / `setX(List<T>)` | New: `ListProperty<T> getX()`
```groovy
// old
task.setCompilerArgs(["-Xlint"])
List<String> args = task.getCompilerArgs()
// new — configuration
task.compilerArgs.set(["-Xlint"])
task.compilerArgs.add("-Xlint")
task.compilerArgs.addAll(otherTask.compilerArgs) // lazy wiring
// new — when a resolved value is needed
List<String> args = task.compilerArgs.get()
```
> **Preserve existing Groovy `<<` / `+=`.** In Groovy DSL, `task.compilerArgs << "-Xlint"` and `task.compilerArgs += "-Xlint"` (and `+= [..]`) keep compiling and behaving identically against the now-`ListProperty` type — leave them unchanged. Use `.add(..)`/`.addAll(..)` only for *new* code or when rewriting a `-=` (which has no surviving operator). See **What has no operator** under "Kotlin DSL operators that survive migration".

### `set`
Old: `Set<T> getX()` / `setX(Set<T>)` | New: `SetProperty<T> getX()`
```groovy
// old
task.setArtifactUrls([uri1, uri2])
Set<URI> urls = task.getArtifactUrls()
// new — configuration
task.artifactUrls.set([uri1, uri2])
task.artifactUrls.add(uri1)
task.artifactUrls.addAll(otherTask.artifactUrls) // lazy wiring
// new — when a resolved value is needed
Set<URI> urls = task.artifactUrls.get()
```

### `map`
Old: `Map<K,V> getX()` / `setX(Map<K,V>)` | New: `MapProperty<K,V> getX()`
```groovy
// old
task.setProperties(["key": "value"])
Map<String, String> props = task.getProperties()
// new — configuration
task.properties.set(["key": "value"])
task.properties.put("key", "value")
task.properties.putAll(otherTask.properties) // lazy wiring
// new — when a resolved value is needed
Map<String, String> props = task.properties.get()
```

### `other`
Old: `T getX()` / `setX(T)` where T is an enum or domain type | New: `Property<T> getX()`
```groovy
// old
task.setCompression(Compression.GZIP)
Compression c = task.getCompression()
// new — configuration
task.compression.set(Compression.GZIP)
task.compression.set(otherTask.compression) // lazy wiring
// new — when a resolved value is needed
Compression c = task.compression.get()
```

### `read_only`
Old: `T getX()` | New: `Provider<T> getX()` (no setter in either version)
```groovy
// Cannot set — only consume
otherTask.someInput.set(task.javaVersion) // pass the Provider
// when a resolved value is needed
JavaVersion ver = task.javaVersion.get()
```

## Language-specific syntax

> **Intent:** map the Groovy DSL examples above to the two other call-site languages migrations frequently touch — Kotlin DSL and Java — so transformations in each language use its native property-access syntax rather than a transliteration of Groovy.

All examples below assume the `scalar` rule applied to `CompileOptions.encoding`.

### Groovy DSL (`build.gradle`)

```groovy
// old
compileJava.options.encoding = "UTF-8"
compileJava.options.setEncoding("UTF-8")
// new
compileJava.options.encoding.set("UTF-8")
```

### Kotlin DSL (`build.gradle.kts`)

```kotlin
// before migration
tasks.compileJava {
    options.encoding = "UTF-8"
}
// after migration — UNCHANGED. The assignment overload (active in .gradle.kts and
// kotlin-dsl modules) rewrites `= value` to `.set(value)` at compile time, so the
// original line keeps compiling against the now-lazy Property<String>. Leave it.
tasks.compileJava {
    options.encoding = "UTF-8"
}

// `.set(...)` is only needed where the overload is NOT available — plain Kotlin in a
// module that does not apply `kotlin-dsl`:
options.encoding.set("UTF-8")
```

> **Note on `=` in Kotlin DSL.** Gradle's lazy property assignment (the Kotlin assignment-overload compiler plugin) rewrites `prop = value` to `prop.set(value)` at compile time for `Property<T>` and other lazy types. It is active in `.gradle.kts` script files and in any source set of a project that applies the `` `kotlin-dsl` `` plugin. In those contexts `prop = value` keeps compiling after migration and needs no change. Rewriting to `.set(...)` there is therefore optional — correct, but not required. The `.set(...)` form *is* required only in plain Kotlin compiled **without** the assignment overload (Kotlin source in a module that does not apply `kotlin-dsl`). Preserve the existing `=` idiom when the overload is active; rewrite to `.set(...)` only when it is not.

### Kotlin DSL operators that survive migration

> **Intent:** beyond `=`, Gradle ships operator extensions in the `org.gradle.kotlin.dsl` package that let existing Kotlin call sites keep compiling against the migrated lazy types. Per the change-minimization principle's **operator/assignment-overload rule (absolute)**, you **must** preserve these forms by adding `import org.gradle.kotlin.dsl.*` (or the specific symbol) where needed. Rewriting any of them to a method call (`.set`/`.add`/`.put`/`.setFrom`/`.get()[k]`) when an import would have worked is a defect, not a stylistic choice.

| Existing syntax | Backed by (`org.gradle.kotlin.dsl`) | Applies to |
|---|---|---|
| `prop = value` | assignment overload (compiler plugin) | any `Property` / lazy type |
| `prop += element` / `prop += listOf(..)` / `prop += arrayOf(..)` | `plusAssign(HasMultipleValues<T>, …)` | `ListProperty`, `SetProperty` |
| `mapProp += (k to v)` / `mapProp += mapOf(..)` | `plusAssign(MapProperty<K,V>, …)` | `MapProperty` |
| `mapProp[k]` (read) / `mapProp[k] = v` | `get` / `set(MapProperty<K,V>, …)` | `MapProperty` |
| `files += otherFiles` | `plusAssign(ConfigurableFileCollection, FileCollection)` | `ConfigurableFileCollection` |
| `val x by prop` / `var x by prop` | `getValue` / `setValue` | `Property<T>`, `ConfigurableFileCollection` |

**Import scope.** All of the above are in scope automatically in `.gradle.kts` (the `org.gradle.kotlin.dsl` package is an implicit default import). In a plain `.kt` file under a `kotlin-dsl` module the extensions are on the classpath but **not** auto-imported — the file's existing `+=` (or `=`, `mapProp[k]`, …) on a now-lazy type compiles only if `import org.gradle.kotlin.dsl.*` (or the specific operator) is present. When migration changes a property's type to a lazy one in such a file, **you must add the import to preserve the operator form.** Rewriting the call site to the method form (`.set`/`.add`/`.put`/`.setFrom`/`.get()[k]`) is **not** an acceptable alternative here, even for "determinism" or to match a sibling line that genuinely needed a method rewrite — add the import instead. The error that signals this case is `No applicable 'assign' function found for '=' overload` / `Unresolved reference 'assign'` / `Unresolved reference 'plusAssign'` / `operator modifier is required on 'fun get()'`: every one of these means "the overload exists but isn't imported", so the fix is the import.

**What has no operator (must be rewritten).** In **Kotlin**, there is no `minusAssign` and no `leftShift` extension for these types, so `prop -= x` and `prop << x` have no surviving Kotlin operator — rewrite them (`prop -= x` → `prop.set(prop.get() - x)`; `<<` → `.add(..)`).

> **Groovy DSL is different — `<<` and `+=` survive on collection properties; do NOT rewrite them.** Gradle defines Groovy operator methods (`leftShift`/`plus`/`addAll`) directly on `ListProperty`/`SetProperty` (via the property type itself, *not* via the `org.gradle.kotlin.dsl` extensions, which are Kotlin-only). So in a `.gradle` script:
> - `prop << x` → **survives** (single-element append). Keep it.
> - `prop += x` and `prop += [a, b]` → **survive** (`add` / `addAll`). Keep them.
> - `prop -= x` → **fails** with `MissingMethodException: …minus()`. This one genuinely has no operator — rewrite it (`prop.set(prop.get() - x)`).
>
> Rewriting Groovy `compilerArgs << '-x'` to `compilerArgs.add('-x')` is therefore unnecessary churn — exactly the kind of correct-but-pointless rewrite the change-minimization principle forbids. See the anti-pattern **Rewriting Groovy `<<`/`+=` on a collection property** below.

### Java (`buildSrc/src/main/java`, custom plugins)

```java
// old
compileTask.getOptions().setEncoding("UTF-8");
String enc = compileTask.getOptions().getEncoding();
// new — no property-access shorthand in Java, everything goes through the getter
compileTask.getOptions().getEncoding().set("UTF-8");
String enc = compileTask.getOptions().getEncoding().get();
```

### Per-kind quick reference across languages

| Kind | Groovy DSL | Kotlin DSL | Java |
|---|---|---|---|
| `scalar` | `task.x.set("v")` | `task.x.set("v")` | `task.getX().set("v")` |
| `boolean` | `task.fork.set(true)` | `task.fork.set(true)` | `task.getFork().set(true)` |
| `list` | `task.args.add("-v")` | `task.args.add("-v")` | `task.getArgs().add("-v")` |
| `file_collection` | `task.classpath.setFrom(fc)` | `task.classpath.setFrom(fc)` | `task.getClasspath().setFrom(fc)` |
| `dir` | `task.dir.set(layout.projectDirectory.dir("x"))` | `task.dir.set(layout.projectDirectory.dir("x"))` | `task.getDir().set(layout.getProjectDirectory().dir("x"))` |

> The **Kotlin DSL** column shows the explicit lazy-API form for reference; it is *not* the preferred rewrite. Per the change-minimization principle, when an existing Kotlin call site already uses an operator form that survives migration (`task.x = "v"`, `task.args += "-v"`, `task.classpath += fc`, `mapProp[k] = v`), **preserve it** — only fall back to the explicit `.set(...)` / `.add(...)` / `.setFrom(...)` form when no operator applies or the overload/import is unavailable.

## Cross-cutting concerns

- **Lazy wiring**: `taskB.foo.set(taskA.foo)` passes the `Provider` itself, not its value. Gradle infers the task dependency. Prefer this over `taskB.foo.set(taskA.foo.get())`.
- **`.get()` resolves the value**. Use it inside task actions, or when passing to any API that does not accept `Provider`.
- **`.convention()` vs `.set()`**: `.convention()` sets a default that `.set()` can override. Both are lazy. Use `.convention()` in plugins, `.set()` in build scripts.
- **`Property` extends `Provider`**: anywhere a `Provider<T>` is accepted, a `Property<T>` works.

## Anti-patterns

> **Intent:** surface rewrites that are syntactically valid after migration but semantically wrong, so they can be distinguished from the correct pattern when both forms are available.

### Eager resolution where lazy wiring is available

```groovy
// WRONG — resolves otherTask.encoding at configuration time, loses task dependency
task.encoding.set(otherTask.getEncoding())
task.encoding.set(otherTask.encoding.get())

// RIGHT — passes the Provider, Gradle infers the dependency
task.encoding.set(otherTask.encoding)
```

### Eager `.get()` when wiring file collections

```groovy
// WRONG — eagerly resolves the source file collection, loses task dependency
task.classpath.setFrom(otherTask.classpath.get())

// RIGHT — pass the lazy collection directly
task.classpath.setFrom(otherTask.classpath)
```

### `.from(...)` where `.setFrom(...)` preserves semantics

```groovy
// WRONG — appends to whatever classpath already contains, diverging from the old setter
task.classpath.from(files("a.jar", "b.jar"))

// RIGHT — replaces, matching the behavior of the removed setClasspath(...)
task.classpath.setFrom(files("a.jar", "b.jar"))
```

### `.map { }` where the lambda returns a Provider

```groovy
// WRONG — yields Provider<Provider<File>>, not Provider<File>
def pom = generateMavenPom.map { it.getDestination() }

// RIGHT — flatMap unwraps the inner Provider
def pom = generateMavenPom.flatMap { it.getDestination() }
```

### Mechanical `setX` → `.x.set()` on Task-only accessors

```groovy
// WRONG — setDescription is on org.gradle.api.Task and is NOT lazy-migrated
task.description.set("my task")

// RIGHT — leave Task-only accessors unchanged
task.setDescription("my task")
```

### Calling `.get()` on a configuration-time `Property` inside a task action

```groovy
// WRONG — captures the value at configuration time, before it may be set
task.doLast {
    def value = myProperty.get()  // where myProperty was captured from outer scope
    // ...
}

// RIGHT — resolve inside the action body so the value is current
task.doLast {
    def value = task.myProperty.get()
}
```

### Renaming a Kotlin `is`-boolean accessor that still resolves

For `TestFilter.failOnNoMatchingTests` (kind `boolean`), `removed_accessors` lists `isFailOnNoMatchingTests()`. But in Kotlin the property name `isFailOnNoMatchingTests` still resolves via the back-compat `getIsFoo()` accessor, so the assignment keeps working once the assign overload is imported.

```kotlin
// WRONG — renames to the canonical accessor; pure churn (isFailOnNoMatchingTests still resolves via getIsFailOnNoMatchingTests())
testTask.filter.failOnNoMatchingTests = false

// RIGHT — keep the existing name; add the import (or nothing in .gradle.kts, where it is implicit)
import org.gradle.kotlin.dsl.assign
testTask.filter.isFailOnNoMatchingTests = false
```

### Self-referential lazy update that recurses (`StackOverflowError`)

An old eager "read, transform, write back" update (`setClasspath(files(getClasspath().minus(x)))`, `prop -= x`) must not migrate to a lazy form that wires a property to a derivation of itself (`classpath.setFrom(classpath.minus(x))`, `prop.set(prop.map { ... })`) — resolving it re-queries itself and overflows the stack at configuration time. Fix with the internal `replace(transform)` method (passes the current value, not a re-query) on `DefaultConfigurableFileCollection` / `DefaultProperty` / `AbstractCollectionProperty`. This is a last-resort internal API — apply it only when the `StackOverflowError` actually occurs while fixing `help`/`assemble` (tasks 07/08).

### Rewriting Groovy `<<` / `+=` on a collection property

```groovy
// WRONG — unnecessary churn; the `<<` form still compiles and behaves identically
options.compilerArgs.add('--add-modules=jdk.incubator.vector')
options.compilerArgs.add('-nowarn')

// RIGHT — leave the Groovy append operators untouched (compilerArgs is now a ListProperty,
// and Gradle defines leftShift/plus/addAll on ListProperty/SetProperty for Groovy)
options.compilerArgs << '--add-modules=jdk.incubator.vector'
options.compilerArgs << '-nowarn'
```

`<<` (single append) and `+=` (`add`/`addAll`) survive on `ListProperty`/`SetProperty` in Groovy DSL. Only `-=` has no operator and must be rewritten. This is the Groovy analogue of the Kotlin operator-preservation rule: do not de-sugar a surviving operator into a method call.
