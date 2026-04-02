# Gradle 10 Lazy Property Migration Report

Properties annotated with `@ReplacesEagerProperty` in Gradle 10 preview (`gradle-provider-api-20260204140400`), compared against Gradle 9.4.0.

> **What does `@ReplacesEagerProperty` mean?**
> In Gradle 10, eager getters/setters (e.g. `String getFoo()` / `void setFoo(String)`) are replaced by lazy provider-based properties (e.g. `Property<String> getFoo()`). The annotation marks these new lazy accessors and instructs Gradle's bytecode instrumentation to intercept calls to the old eager API, bridging them to the new lazy one during the transition.

---

## Lazy Wiring Principles

The migration to lazy properties is **not** just a mechanical `getFoo()` → `foo.get()` rename. The goal is to keep values **lazy** — evaluated only when needed, typically at task execution time. Calling `.get()` at configuration time defeats the purpose.

### Rules of thumb

1. **Wire providers to providers** — never unpack a `Provider` just to pass its value to another property:
   ```groovy
   // WRONG — eagerly unpacks, breaks task dependency inference
   taskB.encoding.set(taskA.encoding.get())

   // RIGHT — lazy wiring, Gradle infers the task dependency automatically
   taskB.encoding.set(taskA.encoding)
   ```
2. **`.convention()` vs `.set()`** — both are lazy, but they differ in intent. `.convention()` provides a default that can be overridden by `.set()`; `.set()` provides an explicit value. Use `.convention()` when defining a default in a plugin, `.set()` when configuring a task:
   ```groovy
   // In a plugin — overridable default
   task.encoding.convention("UTF-8")

   // In a build script — explicit configuration
   task.encoding.set("ISO-8859-1")
   ```
3. **`.get()` is needed when you need the resolved value** — inside task actions, or when passing a value to any API that does not accept `Provider`:
   ```groovy
   // Inside a task action
   task.doLast {
       println("Encoding: ${task.encoding.get()}")
   }

   // Feeding a lazy value into an API that expects a plain type
   someApi.configure(compileTask.encoding.get())
   ```
4. **For file properties**, prefer `layout`-based APIs over `project.file()`:
   ```groovy
   task.outputFile.set(layout.buildDirectory.file("report.txt"))
   task.baseDir.set(layout.projectDirectory.dir("src"))
   ```
6. **For collection properties**, use incremental APIs to add items lazily:
   ```groovy
   task.compilerArgs.add("-Xlint")
   task.compilerArgs.addAll(otherTask.compilerArgs)
   task.properties.put("key", provider { computeValue() })
   task.classpath.from(configurations.compileClasspath)
   ```

---

## Summary

| # | Class | Properties Changed |
|---|-------|--------------------|
| 1 | `MavenArtifactRepository` | 1 |
| 2 | `UrlArtifactRepository` | 2 |
| 3 | `DeleteSpec` | 1 |
| 4 | `JavaApplication` | 3 |
| 5 | `AntlrTask` | 8 |
| 6 | `Checkstyle` | 7 |
| 7 | `CheckstyleExtension` | 4 |
| 8 | `CodeNarc` | 5 |
| 9 | `CodeNarcExtension` | 4 |
| 10 | `CodeQualityExtension` | 4 |
| 11 | `Pmd` | 7 |
| 12 | `PmdExtension` | 4 |
| 13 | `PublicationArtifact` | 1 |
| 14 | `IvyArtifact` | 5 |
| 15 | `IvyModuleDescriptorSpec` | 2 |
| 16 | `IvyPublication` | 3 |
| 17 | `GenerateIvyDescriptor` | 1 |
| 18 | `MavenArtifact` | 2 |
| 19 | `MavenPom` | 1 |
| 20 | `MavenPublication` | 3 |
| 21 | `GenerateMavenPom` | 1 |
| 22 | `AbstractExecTask` | 5 |
| 23 | `Delete` | 2 |
| 24 | `Exec` | 5 |
| 25 | `JavaExec` | 7 |
| 26 | `WriteProperties` | 4 |
| 27 | `AntTarget` | 2 |
| 28 | `AbstractArchiveTask` | 2 |
| 29 | `Tar` | 1 |
| 30 | `War` | 2 |
| 31 | `Zip` | 3 |
| 32 | `AbstractCompile` | 2 |
| 33 | `BaseForkOptions` | 3 |
| 34 | `CompileOptions` | 17 |
| 35 | `DebugOptions` | 1 |
| 36 | `ForkOptions` | 2 |
| 37 | `GroovyCompile` | 1 |
| 38 | `GroovyCompileOptions` | 12 |
| 39 | `ProviderAwareCompilerDaemonForkOptions` | 2 |
| 40 | `AbstractDependencyReportTask` | 2 |
| 41 | `ConventionReportTask` | 2 |
| 42 | `DependencyInsightReportTask` | 3 |
| 43 | `PropertyReportTask` | 1 |
| 44 | `TaskReportTask` | 3 |
| 45 | `Groovydoc` | 11 |
| 46 | `Javadoc` | 7 |
| 47 | `ScalaCompile` | 3 |
| 48 | `ScalaDoc` | 4 |
| 49 | `ScalaDocOptions` | 9 |
| 50 | `JUnitXmlReport` | 1 |
| 51 | `Test` | 7 |
| 52 | `TestFilter` | 3 |
| 53 | `TestReport` | 1 |
| 54 | `JUnitOptions` | 2 |
| 55 | `JUnitPlatformOptions` | 4 |
| 56 | `TestLogging` | 10 |
| 57 | `TestNGOptions` | 16 |
| 58 | `Wrapper` | 12 |
| | **Total** | **243** |

---

## Detailed Migration Guide

### `org.gradle.api.artifacts.repositories.MavenArtifactRepository`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `artifactUrls` | `Set<URI>` | `SetProperty<URI>` | `setArtifactUrls(Set<URI>)`, `setArtifactUrls(Iterable<?>)` |

**Migration examples:**

```groovy
task.artifactUrls.add(item)
task.artifactUrls.addAll(otherTask.artifactUrls)  // lazy wiring
```

---

### `org.gradle.api.artifacts.repositories.UrlArtifactRepository`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `allowInsecureProtocol` | `boolean` | `Property<Boolean>` | `setAllowInsecureProtocol(boolean)`, `isAllowInsecureProtocol()` |
| `url` | `URI` | `Property<URI>` | — |

**Migration examples:**

```groovy
task.allowInsecureProtocol.set(true)
task.allowInsecureProtocol.set(otherTask.allowInsecureProtocol)  // lazy wiring
task.url.set(someValue)
task.url.set(otherTask.url)  // lazy wiring
```

---

### `org.gradle.api.file.DeleteSpec`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `followSymlinks` | `boolean` | `Property<Boolean>` | `setFollowSymlinks(boolean)` |

**Migration examples:**

```groovy
task.followSymlinks.set(true)
task.followSymlinks.set(otherTask.followSymlinks)  // lazy wiring
```

---

### `org.gradle.api.plugins.JavaApplication`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `applicationDefaultJvmArgs` | `Iterable<String>` | `ListProperty<String>` | `setApplicationDefaultJvmArgs(Iterable<String>)` |
| `applicationName` | `String` | `Property<String>` | `setApplicationName(String)` |
| `executableDir` | `String` | `Property<String>` | `setExecutableDir(String)` |

**Migration examples:**

```groovy
task.applicationName.set("value")  // also: executableDir
task.applicationName.set(provider { computeValue() })
task.applicationName.set(otherTask.applicationName)  // lazy wiring
task.applicationDefaultJvmArgs.add("item")
task.applicationDefaultJvmArgs.addAll(otherTask.applicationDefaultJvmArgs)  // lazy wiring
```

---

### `org.gradle.api.plugins.antlr.AntlrTask`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `antlrClasspath` | `FileCollection` | `ConfigurableFileCollection` | — |
| `arguments` | `List<String>` | `ListProperty<String>` | `setArguments(List<String>)` |
| `maxHeapSize` | `String` | `Property<String>` | `setMaxHeapSize(String)` |
| `outputDirectory` | `File` | `DirectoryProperty` | `setOutputDirectory(File)` |
| `trace` | `boolean` | `Property<Boolean>` | `setTrace(boolean)`, `isTrace()` |
| `traceLexer` | `boolean` | `Property<Boolean>` | `setTraceLexer(boolean)`, `isTraceLexer()` |
| `traceParser` | `boolean` | `Property<Boolean>` | `setTraceParser(boolean)`, `isTraceParser()` |
| `traceTreeWalker` | `boolean` | `Property<Boolean>` | `setTraceTreeWalker(boolean)`, `isTraceTreeWalker()` |

**Migration examples:**

```groovy
task.trace.set(true)  // also: traceLexer, traceParser, traceTreeWalker
task.trace.set(otherTask.trace)  // lazy wiring
task.maxHeapSize.set("value")
task.maxHeapSize.set(provider { computeValue() })
task.maxHeapSize.set(otherTask.maxHeapSize)  // lazy wiring
task.outputDirectory.set(layout.projectDirectory.dir("src"))
task.outputDirectory.set(otherTask.outputDirectory)  // lazy wiring
task.antlrClasspath.from(configurations.someConfig)
task.antlrClasspath.from(otherTask.antlrClasspath)  // lazy wiring
task.arguments.add("item")
task.arguments.addAll(otherTask.arguments)  // lazy wiring
```

---

### `org.gradle.api.plugins.quality.Checkstyle`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `checkstyleClasspath` | `FileCollection` | `ConfigurableFileCollection` | `setCheckstyleClasspath(FileCollection)` |
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `setClasspath(FileCollection)` |
| `configProperties` | `Map<String, Object>` | `MapProperty<String, Object>` | `setConfigProperties(Map<String, Object>)` |
| `isIgnoreFailures` | `boolean` | `Property<Boolean>` | — |
| `maxErrors` | `int` | `Property<Integer>` | `setMaxErrors(int)` |
| `maxWarnings` | `int` | `Property<Integer>` | `setMaxWarnings(int)` |
| `showViolations` | `boolean` | `Property<Boolean>` | `setShowViolations(boolean)`, `isShowViolations()` |

**Migration examples:**

```groovy
task.isIgnoreFailures.set(true)  // also: showViolations
task.isIgnoreFailures.set(otherTask.isIgnoreFailures)  // lazy wiring
task.maxErrors.set(4)  // also: maxWarnings
task.maxErrors.set(provider { computeValue() })
task.maxErrors.set(otherTask.maxErrors)  // lazy wiring
task.checkstyleClasspath.from(configurations.someConfig)  // also: classpath
task.checkstyleClasspath.from(otherTask.checkstyleClasspath)  // lazy wiring
task.configProperties.put("key", "value")
task.configProperties.putAll(otherTask.configProperties)  // lazy wiring
```

---

### `org.gradle.api.plugins.quality.CheckstyleExtension`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `configProperties` | `Map<String, Object>` | `MapProperty<String, Object>` | `setConfigProperties(Map<String, Object>)` |
| `maxErrors` | `int` | `Property<Integer>` | `setMaxErrors(int)` |
| `maxWarnings` | `int` | `Property<Integer>` | `setMaxWarnings(int)` |
| `showViolations` | `boolean` | `Property<Boolean>` | `setShowViolations(boolean)`, `isShowViolations()` |

**Migration examples:**

```groovy
task.showViolations.set(true)
task.showViolations.set(otherTask.showViolations)  // lazy wiring
task.maxErrors.set(4)  // also: maxWarnings
task.maxErrors.set(provider { computeValue() })
task.maxErrors.set(otherTask.maxErrors)  // lazy wiring
task.configProperties.put("key", "value")
task.configProperties.putAll(otherTask.configProperties)  // lazy wiring
```

---

### `org.gradle.api.plugins.quality.CodeNarc`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `codenarcClasspath` | `FileCollection` | `ConfigurableFileCollection` | `setCodenarcClasspath(FileCollection)` |
| `compilationClasspath` | `FileCollection` | `ConfigurableFileCollection` | `setCompilationClasspath(FileCollection)` |
| `maxPriority1Violations` | `int` | `Property<Integer>` | `setMaxPriority1Violations(int)` |
| `maxPriority2Violations` | `int` | `Property<Integer>` | `setMaxPriority2Violations(int)` |
| `maxPriority3Violations` | `int` | `Property<Integer>` | `setMaxPriority3Violations(int)` |

**Migration examples:**

```groovy
task.maxPriority1Violations.set(4)  // also: maxPriority2Violations, maxPriority3Violations
task.maxPriority1Violations.set(provider { computeValue() })
task.maxPriority1Violations.set(otherTask.maxPriority1Violations)  // lazy wiring
task.codenarcClasspath.from(configurations.someConfig)  // also: compilationClasspath
task.codenarcClasspath.from(otherTask.codenarcClasspath)  // lazy wiring
```

---

### `org.gradle.api.plugins.quality.CodeNarcExtension`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `maxPriority1Violations` | `int` | `Property<Integer>` | `setMaxPriority1Violations(int)` |
| `maxPriority2Violations` | `int` | `Property<Integer>` | `setMaxPriority2Violations(int)` |
| `maxPriority3Violations` | `int` | `Property<Integer>` | `setMaxPriority3Violations(int)` |
| `reportFormat` | `String` | `Property<String>` | `setReportFormat(String)` |

**Migration examples:**

```groovy
task.maxPriority1Violations.set(4)  // also: maxPriority2Violations, maxPriority3Violations, reportFormat
task.maxPriority1Violations.set(provider { computeValue() })
task.maxPriority1Violations.set(otherTask.maxPriority1Violations)  // lazy wiring
```

---

### `org.gradle.api.plugins.quality.CodeQualityExtension`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `ignoreFailures` | `boolean` | `Property<Boolean>` | `setIgnoreFailures(boolean)`, `isIgnoreFailures()` |
| `reportsDir` | `File` | `DirectoryProperty` | `setReportsDir(File)` |
| `sourceSets` | `java.util.Collection<SourceSet>` | `ListProperty<SourceSet>` | `setSourceSets(java.util.Collection<SourceSet>)` |
| `toolVersion` | `String` | `Property<String>` | `setToolVersion(String)` |

**Migration examples:**

```groovy
task.ignoreFailures.set(true)
task.ignoreFailures.set(otherTask.ignoreFailures)  // lazy wiring
task.toolVersion.set("value")
task.toolVersion.set(provider { computeValue() })
task.toolVersion.set(otherTask.toolVersion)  // lazy wiring
task.reportsDir.set(layout.projectDirectory.dir("src"))
task.reportsDir.set(otherTask.reportsDir)  // lazy wiring
task.sourceSets.add("item")
task.sourceSets.addAll(otherTask.sourceSets)  // lazy wiring
```

---

### `org.gradle.api.plugins.quality.Pmd`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `setClasspath(FileCollection)` |
| `consoleOutput` | `boolean` | `Property<Boolean>` | `setConsoleOutput(boolean)`, `isConsoleOutput()` |
| `incrementalCacheFile` | `File` | `Provider<RegularFile>` | — |
| `pmdClasspath` | `FileCollection` | `ConfigurableFileCollection` | `setPmdClasspath(FileCollection)` |
| `ruleSetFiles` | `FileCollection` | `ConfigurableFileCollection` | `setRuleSetFiles(FileCollection)` |
| `ruleSets` | `List<String>` | `ListProperty<String>` | `setRuleSets(List<String>)` |
| `targetJdk` | `TargetJdk` | `Property<TargetJdk>` | `setTargetJdk(TargetJdk)` |

**Migration examples:**

```groovy
task.consoleOutput.set(true)
task.consoleOutput.set(otherTask.consoleOutput)  // lazy wiring
task.classpath.from(configurations.someConfig)  // also: pmdClasspath, ruleSetFiles
task.classpath.from(otherTask.classpath)  // lazy wiring
task.ruleSets.add("item")
task.ruleSets.addAll(otherTask.ruleSets)  // lazy wiring
task.targetJdk.set(someValue)
task.targetJdk.set(otherTask.targetJdk)  // lazy wiring

// Read-only (incrementalCacheFile) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.incrementalCacheFile)
```

---

### `org.gradle.api.plugins.quality.PmdExtension`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `consoleOutput` | `boolean` | `Property<Boolean>` | `setConsoleOutput(boolean)`, `isConsoleOutput()` |
| `ruleSetFiles` | `FileCollection` | `ConfigurableFileCollection` | `setRuleSetFiles(FileCollection)` |
| `ruleSets` | `List<String>` | `ListProperty<String>` | `setRuleSets(List<String>)` |
| `targetJdk` | `TargetJdk` | `Property<TargetJdk>` | `setTargetJdk(TargetJdk)`, `setTargetJdk(Object)` |

**Migration examples:**

```groovy
task.consoleOutput.set(true)
task.consoleOutput.set(otherTask.consoleOutput)  // lazy wiring
task.ruleSetFiles.from(configurations.someConfig)
task.ruleSetFiles.from(otherTask.ruleSetFiles)  // lazy wiring
task.ruleSets.add("item")
task.ruleSets.addAll(otherTask.ruleSets)  // lazy wiring
task.targetJdk.set(someValue)
task.targetJdk.set(otherTask.targetJdk)  // lazy wiring
```

---

### `org.gradle.api.publish.PublicationArtifact`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `file` | `File` | `Provider<RegularFile>` | — |

**Migration examples:**

```groovy
// Read-only (file) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.file)
```

---

### `org.gradle.api.publish.ivy.IvyArtifact`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classifier` | `String` | `Property<String>` | `setClassifier(String)` |
| `conf` | `String` | `Property<String>` | `setConf(String)` |
| `extension` | `String` | `Property<String>` | `setExtension(String)` |
| `name` | `String` | `Property<String>` | `setName(String)` |
| `type` | `String` | `Property<String>` | `setType(String)` |

**Migration examples:**

```groovy
task.classifier.set("value")  // also: conf, extension, name, type
task.classifier.set(provider { computeValue() })
task.classifier.set(otherTask.classifier)  // lazy wiring
```

---

### `org.gradle.api.publish.ivy.IvyModuleDescriptorSpec`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `branch` | `String` | `Property<String>` | `setBranch(String)` |
| `status` | `String` | `Property<String>` | `setStatus(String)` |

**Migration examples:**

```groovy
task.branch.set("value")  // also: status
task.branch.set(provider { computeValue() })
task.branch.set(otherTask.branch)  // lazy wiring
```

---

### `org.gradle.api.publish.ivy.IvyPublication`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `module` | `String` | `Property<String>` | `setModule(String)` |
| `organisation` | `String` | `Property<String>` | `setOrganisation(String)` |
| `revision` | `String` | `Property<String>` | `setRevision(String)` |

**Migration examples:**

```groovy
task.module.set("value")  // also: organisation, revision
task.module.set(provider { computeValue() })
task.module.set(otherTask.module)  // lazy wiring
```

---

### `org.gradle.api.publish.ivy.tasks.GenerateIvyDescriptor`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `destination` | `File` | `RegularFileProperty` | `setDestination(File)`, `setDestination(Object)` |

**Migration examples:**

```groovy
task.destination.set(layout.buildDirectory.file("output.txt"))
task.destination.set(otherTask.destination)  // lazy wiring
```

---

### `org.gradle.api.publish.maven.MavenArtifact`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classifier` | `String` | `Property<String>` | `setClassifier(String)` |
| `extension` | `String` | `Property<String>` | `setExtension(String)` |

**Migration examples:**

```groovy
task.classifier.set("value")  // also: extension
task.classifier.set(provider { computeValue() })
task.classifier.set(otherTask.classifier)  // lazy wiring
```

---

### `org.gradle.api.publish.maven.MavenPom`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `packaging` | `String` | `Property<String>` | `setPackaging(String)` |

**Migration examples:**

```groovy
task.packaging.set("value")
task.packaging.set(provider { computeValue() })
task.packaging.set(otherTask.packaging)  // lazy wiring
```

---

### `org.gradle.api.publish.maven.MavenPublication`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `artifactId` | `String` | `Property<String>` | `setArtifactId(String)` |
| `groupId` | `String` | `Property<String>` | `setGroupId(String)` |
| `version` | `String` | `Property<String>` | `setVersion(String)` |

**Migration examples:**

```groovy
task.artifactId.set("value")  // also: groupId, version
task.artifactId.set(provider { computeValue() })
task.artifactId.set(otherTask.artifactId)  // lazy wiring
```

---

### `org.gradle.api.publish.maven.tasks.GenerateMavenPom`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `destination` | `File` | `RegularFileProperty` | `setDestination(File)`, `setDestination(Object)` |

**Migration examples:**

```groovy
task.destination.set(layout.buildDirectory.file("output.txt"))
task.destination.set(otherTask.destination)  // lazy wiring
```

---

### `org.gradle.api.tasks.AbstractExecTask`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `args` | `List<String>` | `ListProperty<String>` | `setArgs(List<String>)`, `setArgs(Iterable<?>)`, `setArgs(Iterable)`, `setArgs(List)` |
| `errorOutput` | `OutputStream` | `Property<OutputStream>` | `setErrorOutput(OutputStream)`, `setErrorOutput(OutputStream)` |
| `ignoreExitValue` | `boolean` | `Property<Boolean>` | `setIgnoreExitValue(boolean)`, `setIgnoreExitValue(boolean)`, `isIgnoreExitValue()` |
| `standardInput` | `InputStream` | `Property<InputStream>` | `setStandardInput(InputStream)`, `setStandardInput(InputStream)` |
| `standardOutput` | `OutputStream` | `Property<OutputStream>` | `setStandardOutput(OutputStream)`, `setStandardOutput(OutputStream)` |

**Migration examples:**

```groovy
task.ignoreExitValue.set(true)
task.ignoreExitValue.set(otherTask.ignoreExitValue)  // lazy wiring
task.args.add("item")
task.args.addAll(otherTask.args)  // lazy wiring
task.errorOutput.set(someValue)  // also: standardInput, standardOutput
task.errorOutput.set(otherTask.errorOutput)  // lazy wiring
```

---

### `org.gradle.api.tasks.Delete`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `followSymlinks` | `boolean` | `Property<Boolean>` | `setFollowSymlinks(boolean)`, `isFollowSymlinks()` |
| `targetFiles` | `FileCollection` | `ConfigurableFileCollection` | — |

**Migration examples:**

```groovy
task.followSymlinks.set(true)
task.followSymlinks.set(otherTask.followSymlinks)  // lazy wiring
task.targetFiles.from(configurations.someConfig)
task.targetFiles.from(otherTask.targetFiles)  // lazy wiring
```

---

### `org.gradle.api.tasks.Exec`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `args` | `List<String>` | `ListProperty<String>` | `setArgs(List<String>)`, `setArgs(Iterable<?>)`, `setArgs(Iterable)`, `setArgs(List)`, `setArgs(Iterable)`, `setArgs(List)` |
| `errorOutput` | `OutputStream` | `Property<OutputStream>` | `setErrorOutput(OutputStream)`, `setErrorOutput(OutputStream)`, `setErrorOutput(OutputStream)` |
| `ignoreExitValue` | `boolean` | `Property<Boolean>` | `setIgnoreExitValue(boolean)`, `setIgnoreExitValue(boolean)`, `setIgnoreExitValue(boolean)`, `isIgnoreExitValue()` |
| `standardInput` | `InputStream` | `Property<InputStream>` | `setStandardInput(InputStream)`, `setStandardInput(InputStream)`, `setStandardInput(InputStream)` |
| `standardOutput` | `OutputStream` | `Property<OutputStream>` | `setStandardOutput(OutputStream)`, `setStandardOutput(OutputStream)`, `setStandardOutput(OutputStream)` |

**Migration examples:**

```groovy
task.ignoreExitValue.set(true)
task.ignoreExitValue.set(otherTask.ignoreExitValue)  // lazy wiring
task.args.add("item")
task.args.addAll(otherTask.args)  // lazy wiring
task.errorOutput.set(someValue)  // also: standardInput, standardOutput
task.errorOutput.set(otherTask.errorOutput)  // lazy wiring
```

---

### `org.gradle.api.tasks.JavaExec`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `args` | `List<String>` | `ListProperty<String>` | `setArgs(List<String>)`, `setArgs(Iterable<?>)`, `setArgs(Iterable)`, `setArgs(List)` |
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `setClasspath(FileCollection)`, `setClasspath(FileCollection)` |
| `errorOutput` | `OutputStream` | `Property<OutputStream>` | `setErrorOutput(OutputStream)`, `setErrorOutput(OutputStream)` |
| `ignoreExitValue` | `boolean` | `Property<Boolean>` | `setIgnoreExitValue(boolean)`, `setIgnoreExitValue(boolean)`, `isIgnoreExitValue()` |
| `javaVersion` | `JavaVersion` | `Provider<JavaVersion>` | — |
| `standardInput` | `InputStream` | `Property<InputStream>` | `setStandardInput(InputStream)`, `setStandardInput(InputStream)` |
| `standardOutput` | `OutputStream` | `Property<OutputStream>` | `setStandardOutput(OutputStream)`, `setStandardOutput(OutputStream)` |

**Migration examples:**

```groovy
task.ignoreExitValue.set(true)
task.ignoreExitValue.set(otherTask.ignoreExitValue)  // lazy wiring
task.classpath.from(configurations.someConfig)
task.classpath.from(otherTask.classpath)  // lazy wiring
task.args.add("item")
task.args.addAll(otherTask.args)  // lazy wiring
task.errorOutput.set(someValue)  // also: standardInput, standardOutput
task.errorOutput.set(otherTask.errorOutput)  // lazy wiring

// Read-only (javaVersion) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.javaVersion)
```

---

### `org.gradle.api.tasks.WriteProperties`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `comment` | `String` | `Property<String>` | `setComment(String)` |
| `encoding` | `String` | `Property<String>` | `setEncoding(String)` |
| `lineSeparator` | `String` | `Property<String>` | `setLineSeparator(String)` |
| `properties` | `Map<String, String>` | `MapProperty<String, Object>` | `setProperties(Map<String, Object>)` |

**Migration examples:**

```groovy
task.comment.set("value")  // also: encoding, lineSeparator
task.comment.set(provider { computeValue() })
task.comment.set(otherTask.comment)  // lazy wiring
task.properties.put("key", "value")
task.properties.putAll(otherTask.properties)  // lazy wiring
```

---

### `org.gradle.api.tasks.ant.AntTarget`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `baseDir` | `File` | `DirectoryProperty` | `setBaseDir(File)` |
| `target` | `org.apache.tools.ant.Target` | `Property<org.apache.tools.ant.Target>` | `setTarget(org.apache.tools.ant.Target)` |

**Migration examples:**

```groovy
task.baseDir.set(layout.projectDirectory.dir("src"))
task.baseDir.set(otherTask.baseDir)  // lazy wiring
task.target.set(someValue)
task.target.set(otherTask.target)  // lazy wiring
```

---

### `org.gradle.api.tasks.bundling.AbstractArchiveTask`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `preserveFileTimestamps` | `boolean` | `Property<Boolean>` | `setPreserveFileTimestamps(boolean)`, `isPreserveFileTimestamps()` |
| `reproducibleFileOrder` | `boolean` | `Property<Boolean>` | `setReproducibleFileOrder(boolean)`, `isReproducibleFileOrder()` |

**Migration examples:**

```groovy
task.preserveFileTimestamps.set(true)  // also: reproducibleFileOrder
task.preserveFileTimestamps.set(otherTask.preserveFileTimestamps)  // lazy wiring
```

---

### `org.gradle.api.tasks.bundling.Tar`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `compression` | `Compression` | `Property<Compression>` | `setCompression(Compression)` |

**Migration examples:**

```groovy
task.compression.set(someValue)
task.compression.set(otherTask.compression)  // lazy wiring
```

---

### `org.gradle.api.tasks.bundling.War`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `setClasspath(FileCollection)`, `setClasspath(Object)` |
| `webXml` | `File` | `RegularFileProperty` | `setWebXml(File)` |

**Migration examples:**

```groovy
task.webXml.set(layout.buildDirectory.file("output.txt"))
task.webXml.set(otherTask.webXml)  // lazy wiring
task.classpath.from(configurations.someConfig)
task.classpath.from(otherTask.classpath)  // lazy wiring
```

---

### `org.gradle.api.tasks.bundling.Zip`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `entryCompression` | `ZipEntryCompression` | `Property<ZipEntryCompression>` | `setEntryCompression(ZipEntryCompression)` |
| `metadataCharset` | `String` | `Property<String>` | `setMetadataCharset(String)` |
| `zip64` | `boolean` | `Property<Boolean>` | `setZip64(boolean)`, `isZip64()` |

**Migration examples:**

```groovy
task.zip64.set(true)
task.zip64.set(otherTask.zip64)  // lazy wiring
task.metadataCharset.set("value")
task.metadataCharset.set(provider { computeValue() })
task.metadataCharset.set(otherTask.metadataCharset)  // lazy wiring
task.entryCompression.set(someValue)
task.entryCompression.set(otherTask.entryCompression)  // lazy wiring
```

---

### `org.gradle.api.tasks.compile.AbstractCompile`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `setClasspath(FileCollection)` |
| `destinationDirectory` | `DirectoryProperty` | `DirectoryProperty` | — |

**Migration examples:**

```groovy
task.destinationDirectory.set(layout.projectDirectory.dir("src"))
task.destinationDirectory.set(otherTask.destinationDirectory)  // lazy wiring
task.classpath.from(configurations.someConfig)
task.classpath.from(otherTask.classpath)  // lazy wiring
```

---

### `org.gradle.api.tasks.compile.BaseForkOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `jvmArgs` | `List<String>` | `ListProperty<String>` | `setJvmArgs(List<String>)` |
| `memoryInitialSize` | `String` | `Property<String>` | `setMemoryInitialSize(String)` |
| `memoryMaximumSize` | `String` | `Property<String>` | `setMemoryMaximumSize(String)` |

**Migration examples:**

```groovy
task.memoryInitialSize.set("value")  // also: memoryMaximumSize
task.memoryInitialSize.set(provider { computeValue() })
task.memoryInitialSize.set(otherTask.memoryInitialSize)  // lazy wiring
task.jvmArgs.add("item")
task.jvmArgs.addAll(otherTask.jvmArgs)  // lazy wiring
```

---

### `org.gradle.api.tasks.compile.CompileOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `allCompilerArgs` | `List<String>` | `Provider<List<String>>` | — |
| `annotationProcessorPath` | `FileCollection` | `ConfigurableFileCollection` | `setAnnotationProcessorPath(FileCollection)` |
| `bootstrapClasspath` | `FileCollection` | `ConfigurableFileCollection` | `setBootstrapClasspath(FileCollection)` |
| `compilerArgs` | `List<String>` | `ListProperty<String>` | `setCompilerArgs(List<String>)` |
| `compilerArgumentProviders` | `List<CommandLineArgumentProvider>` | `ListProperty<CommandLineArgumentProvider>` | — |
| `debug` | `boolean` | `Property<Boolean>` | `setDebug(boolean)`, `isDebug()` |
| `deprecation` | `boolean` | `Property<Boolean>` | `setDeprecation(boolean)`, `isDeprecation()` |
| `encoding` | `String` | `Property<String>` | `setEncoding(String)` |
| `extensionDirs` | `String` | `Property<String>` | `setExtensionDirs(String)` |
| `failOnError` | `boolean` | `Property<Boolean>` | `setFailOnError(boolean)`, `isFailOnError()` |
| `fork` | `boolean` | `Property<Boolean>` | `setFork(boolean)`, `isFork()` |
| `generatedSourceOutputDirectory` | `DirectoryProperty` | `DirectoryProperty` | — |
| `incremental` | `boolean` | `Property<Boolean>` | `setIncremental(boolean)`, `isIncremental()` |
| `listFiles` | `boolean` | `Property<Boolean>` | `setListFiles(boolean)`, `isListFiles()` |
| `sourcepath` | `FileCollection` | `ConfigurableFileCollection` | `setSourcepath(FileCollection)` |
| `verbose` | `boolean` | `Property<Boolean>` | `setVerbose(boolean)`, `isVerbose()` |
| `warnings` | `boolean` | `Property<Boolean>` | `setWarnings(boolean)`, `isWarnings()` |

**Migration examples:**

```groovy
task.debug.set(true)  // also: deprecation, failOnError, fork, incremental, listFiles, verbose, warnings
task.debug.set(otherTask.debug)  // lazy wiring
task.encoding.set("value")  // also: extensionDirs
task.encoding.set(provider { computeValue() })
task.encoding.set(otherTask.encoding)  // lazy wiring
task.generatedSourceOutputDirectory.set(layout.projectDirectory.dir("src"))
task.generatedSourceOutputDirectory.set(otherTask.generatedSourceOutputDirectory)  // lazy wiring
task.annotationProcessorPath.from(configurations.someConfig)  // also: bootstrapClasspath, sourcepath
task.annotationProcessorPath.from(otherTask.annotationProcessorPath)  // lazy wiring
task.compilerArgs.add("item")  // also: compilerArgumentProviders
task.compilerArgs.addAll(otherTask.compilerArgs)  // lazy wiring

// Read-only (allCompilerArgs) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.allCompilerArgs)
```

---

### `org.gradle.api.tasks.compile.DebugOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `debugLevel` | `String` | `Property<String>` | `setDebugLevel(String)` |

**Migration examples:**

```groovy
task.debugLevel.set("value")
task.debugLevel.set(provider { computeValue() })
task.debugLevel.set(otherTask.debugLevel)  // lazy wiring
```

---

### `org.gradle.api.tasks.compile.ForkOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `executable` | `String` | `Property<String>` | `setExecutable(String)` |
| `tempDir` | `String` | `Property<String>` | `setTempDir(String)` |

**Migration examples:**

```groovy
task.executable.set("value")  // also: tempDir
task.executable.set(provider { computeValue() })
task.executable.set(otherTask.executable)  // lazy wiring
```

---

### `org.gradle.api.tasks.compile.GroovyCompile`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `groovyClasspath` | `FileCollection` | `ConfigurableFileCollection` | `setGroovyClasspath(FileCollection)` |

**Migration examples:**

```groovy
task.groovyClasspath.from(configurations.someConfig)
task.groovyClasspath.from(otherTask.groovyClasspath)  // lazy wiring
```

---

### `org.gradle.api.tasks.compile.GroovyCompileOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `configurationScript` | `File` | `RegularFileProperty` | `setConfigurationScript(File)` |
| `encoding` | `String` | `Property<String>` | `setEncoding(String)` |
| `failOnError` | `boolean` | `Property<Boolean>` | `setFailOnError(boolean)`, `isFailOnError()` |
| `fileExtensions` | `List<String>` | `ListProperty<String>` | `setFileExtensions(List<String>)` |
| `fork` | `boolean` | `Property<Boolean>` | `setFork(boolean)`, `isFork()` |
| `javaAnnotationProcessing` | `boolean` | `Property<Boolean>` | `setJavaAnnotationProcessing(boolean)`, `isJavaAnnotationProcessing()` |
| `keepStubs` | `boolean` | `Property<Boolean>` | `setKeepStubs(boolean)`, `isKeepStubs()` |
| `listFiles` | `boolean` | `Property<Boolean>` | `setListFiles(boolean)`, `isListFiles()` |
| `optimizationOptions` | `Map<String, Boolean>` | `MapProperty<String, Boolean>` | `setOptimizationOptions(Map<String, Boolean>)` |
| `parameters` | `boolean` | `Property<Boolean>` | `setParameters(boolean)`, `isParameters()` |
| `stubDir` | `File` | `DirectoryProperty` | `setStubDir(File)` |
| `verbose` | `boolean` | `Property<Boolean>` | `setVerbose(boolean)`, `isVerbose()` |

**Migration examples:**

```groovy
task.failOnError.set(true)  // also: fork, javaAnnotationProcessing, keepStubs, listFiles, parameters, verbose
task.failOnError.set(otherTask.failOnError)  // lazy wiring
task.encoding.set("value")
task.encoding.set(provider { computeValue() })
task.encoding.set(otherTask.encoding)  // lazy wiring
task.stubDir.set(layout.projectDirectory.dir("src"))
task.stubDir.set(otherTask.stubDir)  // lazy wiring
task.configurationScript.set(layout.buildDirectory.file("output.txt"))
task.configurationScript.set(otherTask.configurationScript)  // lazy wiring
task.fileExtensions.add("item")
task.fileExtensions.addAll(otherTask.fileExtensions)  // lazy wiring
task.optimizationOptions.put("key", "value")
task.optimizationOptions.putAll(otherTask.optimizationOptions)  // lazy wiring
```

---

### `org.gradle.api.tasks.compile.ProviderAwareCompilerDaemonForkOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `allJvmArgs` | `List<String>` | `Provider<List<String>>` | — |
| `jvmArgumentProviders` | `List<CommandLineArgumentProvider>` | `ListProperty<CommandLineArgumentProvider>` | — |

**Migration examples:**

```groovy
task.jvmArgumentProviders.add("item")
task.jvmArgumentProviders.addAll(otherTask.jvmArgumentProviders)  // lazy wiring

// Read-only (allJvmArgs) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.allJvmArgs)
```

---

### `org.gradle.api.tasks.diagnostics.AbstractDependencyReportTask`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `configurations` | `Set<Configuration>` | `SetProperty<Configuration>` | `setConfigurations(Set<Configuration>)` |
| `renderer` | `ReportRenderer` | `Property<DependencyReportRenderer>` | `setRenderer(DependencyReportRenderer)` |

**Migration examples:**

```groovy
task.configurations.add(item)
task.configurations.addAll(otherTask.configurations)  // lazy wiring
task.renderer.set(someValue)
task.renderer.set(otherTask.renderer)  // lazy wiring
```

---

### `org.gradle.api.tasks.diagnostics.ConventionReportTask`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `outputFile` | `File` | `RegularFileProperty` | `setOutputFile(File)` |
| `projects` | `Set<Project>` | `SetProperty<Project>` | `setProjects(Set<Project>)` |

**Migration examples:**

```groovy
task.outputFile.set(layout.buildDirectory.file("output.txt"))
task.outputFile.set(otherTask.outputFile)  // lazy wiring
task.projects.add(item)
task.projects.addAll(otherTask.projects)  // lazy wiring
```

---

### `org.gradle.api.tasks.diagnostics.DependencyInsightReportTask`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `configuration` | `Configuration` | `Property<Configuration>` | — |
| `dependencyNotation` | `String` | `Property<String>` | — |
| `showSinglePathToDependency` | `boolean` | `Property<Boolean>` | `setShowSinglePathToDependency(boolean)`, `isShowSinglePathToDependency()` |

**Migration examples:**

```groovy
task.showSinglePathToDependency.set(true)
task.showSinglePathToDependency.set(otherTask.showSinglePathToDependency)  // lazy wiring
task.dependencyNotation.set("value")
task.dependencyNotation.set(provider { computeValue() })
task.dependencyNotation.set(otherTask.dependencyNotation)  // lazy wiring
task.configuration.set(someValue)
task.configuration.set(otherTask.configuration)  // lazy wiring
```

---

### `org.gradle.api.tasks.diagnostics.PropertyReportTask`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `renderer` | `ReportRenderer` | `Property<PropertyReportRenderer>` | `setRenderer(PropertyReportRenderer)` |

**Migration examples:**

```groovy
task.renderer.set(someValue)
task.renderer.set(otherTask.renderer)  // lazy wiring
```

---

### `org.gradle.api.tasks.diagnostics.TaskReportTask`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `displayGroup` | `String` | `Property<String>` | `setDisplayGroup(String)` |
| `renderer` | `ReportRenderer` | `Property<TaskReportRenderer>` | `setRenderer(TaskReportRenderer)` |
| `showDetail` | `boolean` | `Property<Boolean>` | `setShowDetail(boolean)` |

**Migration examples:**

```groovy
task.showDetail.set(true)
task.showDetail.set(otherTask.showDetail)  // lazy wiring
task.displayGroup.set("value")
task.displayGroup.set(provider { computeValue() })
task.displayGroup.set(otherTask.displayGroup)  // lazy wiring
task.renderer.set(someValue)
task.renderer.set(otherTask.renderer)  // lazy wiring
```

---

### `org.gradle.api.tasks.javadoc.Groovydoc`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `setClasspath(FileCollection)` |
| `destinationDir` | `File` | `DirectoryProperty` | `setDestinationDir(File)` |
| `docTitle` | `String` | `Property<String>` | `setDocTitle(String)` |
| `footer` | `String` | `Property<String>` | `setFooter(String)` |
| `groovyClasspath` | `FileCollection` | `ConfigurableFileCollection` | `setGroovyClasspath(FileCollection)` |
| `header` | `String` | `Property<String>` | `setHeader(String)` |
| `links` | `Set<Groovydoc$Link>` | `SetProperty<Groovydoc$Link>` | `setLinks(Set<Groovydoc$Link>)` |
| `noTimestamp` | `boolean` | `Property<Boolean>` | `setNoTimestamp(boolean)`, `isNoTimestamp()` |
| `noVersionStamp` | `boolean` | `Property<Boolean>` | `setNoVersionStamp(boolean)`, `isNoVersionStamp()` |
| `use` | `boolean` | `Property<Boolean>` | `setUse(boolean)`, `isUse()` |
| `windowTitle` | `String` | `Property<String>` | `setWindowTitle(String)` |

**Migration examples:**

```groovy
task.noTimestamp.set(true)  // also: noVersionStamp, use
task.noTimestamp.set(otherTask.noTimestamp)  // lazy wiring
task.docTitle.set("value")  // also: footer, header, windowTitle
task.docTitle.set(provider { computeValue() })
task.docTitle.set(otherTask.docTitle)  // lazy wiring
task.destinationDir.set(layout.projectDirectory.dir("src"))
task.destinationDir.set(otherTask.destinationDir)  // lazy wiring
task.classpath.from(configurations.someConfig)  // also: groovyClasspath
task.classpath.from(otherTask.classpath)  // lazy wiring
task.links.add(item)
task.links.addAll(otherTask.links)  // lazy wiring
```

---

### `org.gradle.api.tasks.javadoc.Javadoc`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `setClasspath(FileCollection)` |
| `destinationDir` | `File` | `DirectoryProperty` | `setDestinationDir(File)` |
| `executable` | `String` | `Property<String>` | `setExecutable(String)` |
| `failOnError` | `boolean` | `Property<Boolean>` | `setFailOnError(boolean)`, `isFailOnError()` |
| `maxMemory` | `String` | `Property<String>` | `setMaxMemory(String)` |
| `optionsFile` | `File` | `Provider<RegularFile>` | — |
| `title` | `String` | `Property<String>` | `setTitle(String)` |

**Migration examples:**

```groovy
task.failOnError.set(true)
task.failOnError.set(otherTask.failOnError)  // lazy wiring
task.executable.set("value")  // also: maxMemory, title
task.executable.set(provider { computeValue() })
task.executable.set(otherTask.executable)  // lazy wiring
task.destinationDir.set(layout.projectDirectory.dir("src"))
task.destinationDir.set(otherTask.destinationDir)  // lazy wiring
task.classpath.from(configurations.someConfig)
task.classpath.from(otherTask.classpath)  // lazy wiring

// Read-only (optionsFile) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.optionsFile)
```

---

### `org.gradle.api.tasks.scala.ScalaCompile`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `scalaClasspath` | `FileCollection` | `ConfigurableFileCollection` | `setScalaClasspath(FileCollection)` |
| `scalaCompilerPlugins` | `FileCollection` | `ConfigurableFileCollection` | `setScalaCompilerPlugins(FileCollection)` |
| `zincClasspath` | `FileCollection` | `ConfigurableFileCollection` | `setZincClasspath(FileCollection)` |

**Migration examples:**

```groovy
task.scalaClasspath.from(configurations.someConfig)  // also: scalaCompilerPlugins, zincClasspath
task.scalaClasspath.from(otherTask.scalaClasspath)  // lazy wiring
```

---

### `org.gradle.api.tasks.scala.ScalaDoc`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `setClasspath(FileCollection)` |
| `destinationDir` | `File` | `DirectoryProperty` | `setDestinationDir(File)` |
| `scalaClasspath` | `FileCollection` | `ConfigurableFileCollection` | `setScalaClasspath(FileCollection)` |
| `title` | `String` | `Property<String>` | `setTitle(String)` |

**Migration examples:**

```groovy
task.title.set("value")
task.title.set(provider { computeValue() })
task.title.set(otherTask.title)  // lazy wiring
task.destinationDir.set(layout.projectDirectory.dir("src"))
task.destinationDir.set(otherTask.destinationDir)  // lazy wiring
task.classpath.from(configurations.someConfig)  // also: scalaClasspath
task.classpath.from(otherTask.classpath)  // lazy wiring
```

---

### `org.gradle.api.tasks.scala.ScalaDocOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `additionalParameters` | `List<String>` | `ListProperty<String>` | `setAdditionalParameters(List<String>)` |
| `bottom` | `String` | `Property<String>` | `setBottom(String)` |
| `deprecation` | `boolean` | `Property<Boolean>` | `setDeprecation(boolean)`, `isDeprecation()` |
| `docTitle` | `String` | `Property<String>` | `setDocTitle(String)` |
| `footer` | `String` | `Property<String>` | `setFooter(String)` |
| `header` | `String` | `Property<String>` | `setHeader(String)` |
| `top` | `String` | `Property<String>` | `setTop(String)` |
| `unchecked` | `boolean` | `Property<Boolean>` | `setUnchecked(boolean)`, `isUnchecked()` |
| `windowTitle` | `String` | `Property<String>` | `setWindowTitle(String)` |

**Migration examples:**

```groovy
task.deprecation.set(true)  // also: unchecked
task.deprecation.set(otherTask.deprecation)  // lazy wiring
task.bottom.set("value")  // also: docTitle, footer, header, top, windowTitle
task.bottom.set(provider { computeValue() })
task.bottom.set(otherTask.bottom)  // lazy wiring
task.additionalParameters.add("item")
task.additionalParameters.addAll(otherTask.additionalParameters)  // lazy wiring
```

---

### `org.gradle.api.tasks.testing.JUnitXmlReport`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `outputPerTestCase` | `boolean` | `Property<Boolean>` | `setOutputPerTestCase(boolean)`, `isOutputPerTestCase()` |

**Migration examples:**

```groovy
task.outputPerTestCase.set(true)
task.outputPerTestCase.set(otherTask.outputPerTestCase)  // lazy wiring
```

---

### `org.gradle.api.tasks.testing.Test`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `setClasspath(FileCollection)` |
| `forkEvery` | `long` | `Property<java.lang.Long>` | `setForkEvery(long)` |
| `javaVersion` | `JavaVersion` | `Provider<JavaVersion>` | — |
| `maxParallelForks` | `int` | `Property<Integer>` | `setMaxParallelForks(int)` |
| `scanForTestClasses` | `boolean` | `Property<Boolean>` | `setScanForTestClasses(boolean)`, `isScanForTestClasses()` |
| `testClassesDirs` | `FileCollection` | `ConfigurableFileCollection` | `setTestClassesDirs(FileCollection)` |
| `testFramework` | `TestFramework` | `Property<TestFramework>` | — |

**Migration examples:**

```groovy
task.scanForTestClasses.set(true)
task.scanForTestClasses.set(otherTask.scanForTestClasses)  // lazy wiring
task.forkEvery.set(4)  // also: maxParallelForks
task.forkEvery.set(provider { computeValue() })
task.forkEvery.set(otherTask.forkEvery)  // lazy wiring
task.classpath.from(configurations.someConfig)  // also: testClassesDirs
task.classpath.from(otherTask.classpath)  // lazy wiring
task.testFramework.set(someValue)
task.testFramework.set(otherTask.testFramework)  // lazy wiring

// Read-only (javaVersion) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.javaVersion)
```

---

### `org.gradle.api.tasks.testing.TestFilter`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `excludePatterns` | `Set<String>` | `SetProperty<String>` | `setExcludePatterns(String...)` |
| `failOnNoMatchingTests` | `boolean` | `Property<Boolean>` | `setFailOnNoMatchingTests(boolean)`, `isFailOnNoMatchingTests()` |
| `includePatterns` | `Set<String>` | `SetProperty<String>` | `setIncludePatterns(String...)` |

**Migration examples:**

```groovy
task.failOnNoMatchingTests.set(true)
task.failOnNoMatchingTests.set(otherTask.failOnNoMatchingTests)  // lazy wiring
task.excludePatterns.add(item)  // also: includePatterns
task.excludePatterns.addAll(otherTask.excludePatterns)  // lazy wiring
```

---

### `org.gradle.api.tasks.testing.TestReport`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `destinationDirectory` | `DirectoryProperty` | `DirectoryProperty` | — |

**Migration examples:**

```groovy
task.destinationDirectory.set(layout.projectDirectory.dir("src"))
task.destinationDirectory.set(otherTask.destinationDirectory)  // lazy wiring
```

---

### `org.gradle.api.tasks.testing.junit.JUnitOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `excludeCategories` | `Set<String>` | `SetProperty<String>` | `setExcludeCategories(Set<String>)` |
| `includeCategories` | `Set<String>` | `SetProperty<String>` | `setIncludeCategories(Set<String>)` |

**Migration examples:**

```groovy
task.excludeCategories.add(item)  // also: includeCategories
task.excludeCategories.addAll(otherTask.excludeCategories)  // lazy wiring
```

---

### `org.gradle.api.tasks.testing.junitplatform.JUnitPlatformOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `excludeEngines` | `Set<String>` | `SetProperty<String>` | `setExcludeEngines(Set<String>)` |
| `excludeTags` | `Set<String>` | `SetProperty<String>` | `setExcludeTags(Set<String>)` |
| `includeEngines` | `Set<String>` | `SetProperty<String>` | `setIncludeEngines(Set<String>)` |
| `includeTags` | `Set<String>` | `SetProperty<String>` | `setIncludeTags(Set<String>)` |

**Migration examples:**

```groovy
task.excludeEngines.add(item)  // also: excludeTags, includeEngines, includeTags
task.excludeEngines.addAll(otherTask.excludeEngines)  // lazy wiring
```

---

### `org.gradle.api.tasks.testing.logging.TestLogging`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `displayGranularity` | `int` | `Property<Integer>` | `setDisplayGranularity(int)` |
| `events` | `Set<TestLogEvent>` | `SetProperty<TestLogEvent>` | `setEvents(Set<TestLogEvent>)`, `setEvents(Iterable<?>)` |
| `exceptionFormat` | `TestExceptionFormat` | `Property<TestExceptionFormat>` | `setExceptionFormat(TestExceptionFormat)`, `setExceptionFormat(Object)` |
| `maxGranularity` | `int` | `Property<Integer>` | `setMaxGranularity(int)` |
| `minGranularity` | `int` | `Property<Integer>` | `setMinGranularity(int)` |
| `showCauses` | `boolean` | `Property<Boolean>` | `setShowCauses(boolean)` |
| `showExceptions` | `boolean` | `Property<Boolean>` | `setShowExceptions(boolean)` |
| `showStackTraces` | `boolean` | `Property<Boolean>` | `setShowStackTraces(boolean)` |
| `showStandardStreams` | `boolean` | `Property<Boolean>` | `setShowStandardStreams(boolean)` |
| `stackTraceFilters` | `Set<TestStackTraceFilter>` | `SetProperty<TestStackTraceFilter>` | `setStackTraceFilters(Set<TestStackTraceFilter>)`, `setStackTraceFilters(Iterable<?>)` |

**Migration examples:**

```groovy
task.showCauses.set(true)  // also: showExceptions, showStackTraces, showStandardStreams
task.showCauses.set(otherTask.showCauses)  // lazy wiring
task.displayGranularity.set(4)  // also: maxGranularity, minGranularity
task.displayGranularity.set(provider { computeValue() })
task.displayGranularity.set(otherTask.displayGranularity)  // lazy wiring
task.events.add(item)  // also: stackTraceFilters
task.events.addAll(otherTask.events)  // lazy wiring
task.exceptionFormat.set(someValue)
task.exceptionFormat.set(otherTask.exceptionFormat)  // lazy wiring
```

---

### `org.gradle.api.tasks.testing.testng.TestNGOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `configFailurePolicy` | `String` | `Property<String>` | `setConfigFailurePolicy(String)` |
| `excludeGroups` | `Set<String>` | `SetProperty<String>` | `setExcludeGroups(Set<String>)` |
| `groupByInstances` | `boolean` | `Property<Boolean>` | `setGroupByInstances(boolean)`, `isGroupByInstances()` |
| `includeGroups` | `Set<String>` | `SetProperty<String>` | `setIncludeGroups(Set<String>)` |
| `listeners` | `Set<String>` | `SetProperty<String>` | `setListeners(Set<String>)` |
| `outputDirectory` | `File` | `DirectoryProperty` | `setOutputDirectory(File)` |
| `parallel` | `String` | `Property<String>` | `setParallel(String)` |
| `preserveOrder` | `boolean` | `Property<Boolean>` | `setPreserveOrder(boolean)`, `isPreserveOrder()` |
| `suiteName` | `String` | `Property<String>` | `setSuiteName(String)` |
| `suiteXmlBuilder` | `groovy.xml.MarkupBuilder` | `Property<groovy.xml.MarkupBuilder>` | `setSuiteXmlBuilder(groovy.xml.MarkupBuilder)` |
| `suiteXmlFiles` | `List<File>` | `ConfigurableFileCollection` | `setSuiteXmlFiles(List<File>)` |
| `suiteXmlWriter` | `java.io.StringWriter` | `Property<java.io.StringWriter>` | `setSuiteXmlWriter(java.io.StringWriter)` |
| `testName` | `String` | `Property<String>` | `setTestName(String)` |
| `threadCount` | `int` | `Property<Integer>` | `setThreadCount(int)` |
| `threadPoolFactoryClass` | `String` | `Property<String>` | `setThreadPoolFactoryClass(String)` |
| `useDefaultListeners` | `boolean` | `Property<Boolean>` | `setUseDefaultListeners(boolean)`, `isUseDefaultListeners()` |

**Migration examples:**

```groovy
task.groupByInstances.set(true)  // also: preserveOrder, useDefaultListeners
task.groupByInstances.set(otherTask.groupByInstances)  // lazy wiring
task.configFailurePolicy.set("value")  // also: parallel, suiteName, testName, threadCount, threadPoolFactoryClass
task.configFailurePolicy.set(provider { computeValue() })
task.configFailurePolicy.set(otherTask.configFailurePolicy)  // lazy wiring
task.outputDirectory.set(layout.projectDirectory.dir("src"))
task.outputDirectory.set(otherTask.outputDirectory)  // lazy wiring
task.suiteXmlFiles.from(configurations.someConfig)
task.suiteXmlFiles.from(otherTask.suiteXmlFiles)  // lazy wiring
task.excludeGroups.add(item)  // also: includeGroups, listeners
task.excludeGroups.addAll(otherTask.excludeGroups)  // lazy wiring
task.suiteXmlBuilder.set(someValue)  // also: suiteXmlWriter
task.suiteXmlBuilder.set(otherTask.suiteXmlBuilder)  // lazy wiring
```

---

### `org.gradle.api.tasks.wrapper.Wrapper`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `archiveBase` | `Wrapper$PathBase` | `Property<Wrapper$PathBase>` | `setArchiveBase(Wrapper$PathBase)` |
| `archivePath` | `String` | `Property<String>` | `setArchivePath(String)` |
| `batchScript` | `File` | `Provider<RegularFile>` | — |
| `distributionBase` | `Wrapper$PathBase` | `Property<Wrapper$PathBase>` | `setDistributionBase(Wrapper$PathBase)` |
| `distributionPath` | `String` | `Property<String>` | `setDistributionPath(String)` |
| `distributionSha256Sum` | `String` | `Property<String>` | `setDistributionSha256Sum(String)` |
| `distributionType` | `Wrapper$DistributionType` | `Property<Wrapper$DistributionType>` | `setDistributionType(Wrapper$DistributionType)` |
| `distributionUrl` | `String` | `Property<String>` | `setDistributionUrl(String)` |
| `gradleVersion` | `String` | `Property<String>` | `setGradleVersion(String)` |
| `jarFile` | `File` | `RegularFileProperty` | `setJarFile(File)`, `setJarFile(Object)` |
| `propertiesFile` | `File` | `Provider<RegularFile>` | — |
| `scriptFile` | `File` | `RegularFileProperty` | `setScriptFile(File)`, `setScriptFile(Object)` |

**Migration examples:**

```groovy
task.archivePath.set("value")  // also: distributionPath, distributionSha256Sum, distributionUrl, gradleVersion
task.archivePath.set(provider { computeValue() })
task.archivePath.set(otherTask.archivePath)  // lazy wiring
task.jarFile.set(layout.buildDirectory.file("output.txt"))  // also: scriptFile
task.jarFile.set(otherTask.jarFile)  // lazy wiring
task.archiveBase.set(someValue)  // also: distributionBase, distributionType
task.archiveBase.set(otherTask.archiveBase)  // lazy wiring

// Read-only (batchScript, propertiesFile) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.batchScript)
```

---

## General Migration Patterns

| 9.4 Pattern | 10 — Configuration (lazy) | 10 — Execution time only |
|-------------|---------------------------|--------------------------|
| `taskB.setFoo(taskA.getFoo())` | `taskB.foo.set(taskA.foo)` | — |
| `task.setFoo(value)` | `task.foo.set(value)` | — |
| `task.setFoo(computed)` | `task.foo.set(provider { computed })` | — |
| `val x = task.getFoo()` | Pass `task.foo` as a `Provider` | `task.foo.get()` in a task action |
| `task.isFoo()` | Wire `task.foo` as `Provider<Boolean>` | `task.foo.get()` in a task action |
| `task.getFoo()` → `File` | Wire `task.foo` as `Provider<Directory>` | `task.foo.get().asFile` in a task action |
| `task.getFoo()` → `List<T>` | `task.foo.add(item)` / `.addAll(provider)` | `task.foo.get()` in a task action |
| `task.getFoo()` → `Set<T>` | `task.foo.add(item)` / `.addAll(provider)` | `task.foo.get()` in a task action |
| `task.getFoo()` → `Map<K,V>` | `task.foo.put(k, v)` / `.putAll(provider)` | `task.foo.get()` in a task action |
| `task.getFoo()` → `FileCollection` | `task.foo.from(source)` | Iterate in a task action |

> **Key principle**: `Property` extends `Provider`. Anywhere a `Provider<T>` is accepted, you can pass the `Property<T>` directly — no `.get()` needed. Reserve `.get()` for task actions and `doLast {}` blocks where you need the resolved value.
