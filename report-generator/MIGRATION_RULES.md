# Gradle 10 Lazy Property Migration Rules

Use with `migration-data.json` to migrate Gradle build scripts. Look up the class + property in the JSON to get `kind`, `old_type`, `new_type`, and `removed_accessors`, then apply the matching rule below.

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

## Cross-cutting concerns

- **Lazy wiring**: `taskB.foo.set(taskA.foo)` passes the `Provider` itself, not its value. Gradle infers the task dependency. Prefer this over `taskB.foo.set(taskA.foo.get())`.
- **`.get()` resolves the value**. Use it inside task actions, or when passing to any API that does not accept `Provider`.
- **`.convention()` vs `.set()`**: `.convention()` sets a default that `.set()` can override. Both are lazy. Use `.convention()` in plugins, `.set()` in build scripts.
- **`Property` extends `Provider`**: anywhere a `Provider<T>` is accepted, a `Property<T>` works.
