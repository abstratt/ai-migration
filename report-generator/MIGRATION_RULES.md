# Gradle 10 Lazy Property Migration Rules

Use with `migration-data.json` to migrate Gradle build scripts. Look up the class + property in the JSON to get `kind`, `old_type`, `new_type`, and `removed_accessors`, then apply the matching rule below.

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
  "class": "CompileOptions",
  "property": "encoding",
  "kind": "scalar",
  "old_type": "String",
  "new_type": "Property<String>",
  "removed_accessors": ["setEncoding(String)"]
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
```groovy
// old
task.setClasspath(files("a.jar", "b.jar"))
FileCollection cp = task.getClasspath()
// new — configuration
task.classpath.from("a.jar", "b.jar")
task.classpath.from(configurations.compileClasspath)
task.classpath.from(otherTask.classpath) // lazy wiring
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
// old
tasks.compileJava {
    options.encoding = "UTF-8"
}
// new — .set() is required; direct assignment via `=` does NOT work on Property<T>
tasks.compileJava {
    options.encoding.set("UTF-8")
}
```

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
| `file_collection` | `task.classpath.from(fc)` | `task.classpath.from(fc)` | `task.getClasspath().from(fc)` |
| `dir` | `task.dir.set(layout.projectDirectory.dir("x"))` | `task.dir.set(layout.projectDirectory.dir("x"))` | `task.getDir().set(layout.getProjectDirectory().dir("x"))` |

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

### `.setFrom(.get())` on file collections

```groovy
// WRONG — eagerly resolves the source file collection
task.classpath.setFrom(otherTask.classpath.get())

// RIGHT — pass the lazy collection directly
task.classpath.from(otherTask.classpath)
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
