# Gradle 10 Lazy Property Migration Report

Properties annotated with `@ReplacesEagerProperty` in the target distribution, compared against the baseline. Distro pair: **Gradle 9.5.1 → provider-api preview (2026-06-09)** (`g951-to-PAPI-20260609`).

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
   ```
   For `ConfigurableFileCollection` properties migrated from `setX(FileCollection)`, use `.setFrom(...)` to replace — `.from(...)` appends and is not a migration for the old setter.

---

## Summary

| # | Class | Properties Changed |
|---|-------|--------------------|
| 1 | `UrlArtifactRepository` | 2 |
| 2 | `JavaApplication` | 3 |
| 3 | `AntlrTask` | 8 |
| 4 | `Checkstyle` | 7 |
| 5 | `CheckstyleExtension` | 4 |
| 6 | `CodeNarc` | 5 |
| 7 | `CodeNarcExtension` | 4 |
| 8 | `CodeQualityExtension` | 3 |
| 9 | `Pmd` | 6 |
| 10 | `PmdExtension` | 3 |
| 11 | `PublicationArtifact` | 1 |
| 12 | `IvyArtifact` | 5 |
| 13 | `IvyModuleDescriptorSpec` | 2 |
| 14 | `IvyPublication` | 3 |
| 15 | `MavenArtifact` | 2 |
| 16 | `MavenPom` | 1 |
| 17 | `MavenPublication` | 3 |
| 18 | `Delete` | 2 |
| 19 | `JavaExec` | 1 |
| 20 | `WriteProperties` | 4 |
| 21 | `AntTarget` | 2 |
| 22 | `AbstractArchiveTask` | 2 |
| 23 | `Tar` | 1 |
| 24 | `War` | 1 |
| 25 | `Zip` | 3 |
| 26 | `AbstractCompile` | 2 |
| 27 | `BaseForkOptions` | 3 |
| 28 | `CompileOptions` | 17 |
| 29 | `DebugOptions` | 1 |
| 30 | `ForkOptions` | 2 |
| 31 | `GroovyCompile` | 1 |
| 32 | `GroovyCompileOptions` | 10 |
| 33 | `ProviderAwareCompilerDaemonForkOptions` | 2 |
| 34 | `AbstractDependencyReportTask` | 1 |
| 35 | `ConventionReportTask` | 2 |
| 36 | `DependencyInsightReportTask` | 2 |
| 37 | `TaskReportTask` | 2 |
| 38 | `Groovydoc` | 10 |
| 39 | `Javadoc` | 6 |
| 40 | `ScalaCompile` | 3 |
| 41 | `ScalaDoc` | 3 |
| 42 | `ScalaDocOptions` | 9 |
| 43 | `JUnitXmlReport` | 1 |
| 44 | `Test` | 7 |
| 45 | `TestFilter` | 3 |
| 46 | `TestReport` | 1 |
| 47 | `JUnitOptions` | 2 |
| 48 | `JUnitPlatformOptions` | 4 |
| 49 | `TestLogging` | 10 |
| 50 | `TestNGOptions` | 16 |
| 51 | `Wrapper` | 12 |
| 52 | `InitBuild` | 8 |
| 53 | `BuildCache` | 2 |
| 54 | `HttpBuildCache` | 4 |
| 55 | `DirectoryBuildCache` | 1 |
| 56 | `MinimalJavadocOptions` | 20 |
| 57 | `StandardJavadocDocletOptions` | 32 |
| 58 | `CreateStartScripts` | 5 |
| 59 | `Jar` | 1 |
| 60 | `BaseScalaCompileOptions` | 11 |
| 61 | `PluginDeclaration` | 4 |
| 62 | `Ear` | 1 |
| 63 | `DeploymentDescriptor` | 9 |
| 64 | `EarModule` | 2 |
| 65 | `EarSecurityRole` | 2 |
| 66 | `EarWebModule` | 1 |
| 67 | `BaseExecSpec` | 5 |
| 68 | `ExecSpec` | 2 |
| 69 | `JavaExecSpec` | 4 |
| 70 | `JavaForkOptions` | 10 |
| 71 | `ProcessForkOptions` | 2 |
| 72 | `JacocoPluginExtension` | 1 |
| 73 | `JacocoTaskExtension` | 13 |
| 74 | `JacocoBase` | 1 |
| 75 | `VersionControlRepository` | 1 |
| 76 | `VersionControlSpec` | 3 |
| 77 | `GitVersionControlSpec` | 1 |
| | **Total** | **356** |

---

## Detailed Migration Guide

### `org.gradle.api.artifacts.repositories.UrlArtifactRepository`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `allowInsecureProtocol` | `boolean` | `Property<Boolean>` | `isAllowInsecureProtocol()` |
| `url` | `URI` | `Property<URI>` | `getUrl()` (return type changed) |

**Migration examples:**

```groovy
task.allowInsecureProtocol.set(true)
task.allowInsecureProtocol.set(otherTask.allowInsecureProtocol)  // lazy wiring
task.url.set(someValue)
task.url.set(otherTask.url)  // lazy wiring
```

---

### `org.gradle.api.plugins.JavaApplication`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `applicationDefaultJvmArgs` | `Iterable<String>` | `ListProperty<String>` | `getApplicationDefaultJvmArgs()` (return type changed) |
| `applicationName` | `String` | `Property<String>` | `getApplicationName()` (return type changed) |
| `executableDir` | `String` | `Property<String>` | `getExecutableDir()` (return type changed) |

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
| `antlrClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getAntlrClasspath()` (return type changed) |
| `arguments` | `List<String>` | `ListProperty<String>` | `getArguments()` (return type changed) |
| `maxHeapSize` | `String` | `Property<String>` | `getMaxHeapSize()` (return type changed) |
| `outputDirectory` | `File` | `DirectoryProperty` | `getOutputDirectory()` (return type changed) |
| `trace` | `boolean` | `Property<Boolean>` | `isTrace()` |
| `traceLexer` | `boolean` | `Property<Boolean>` | `isTraceLexer()` |
| `traceParser` | `boolean` | `Property<Boolean>` | `isTraceParser()` |
| `traceTreeWalker` | `boolean` | `Property<Boolean>` | `isTraceTreeWalker()` |

**Migration examples:**

```groovy
task.trace.set(true)  // also: traceLexer, traceParser, traceTreeWalker
task.trace.set(otherTask.trace)  // lazy wiring
task.maxHeapSize.set("value")
task.maxHeapSize.set(provider { computeValue() })
task.maxHeapSize.set(otherTask.maxHeapSize)  // lazy wiring
task.outputDirectory.set(layout.projectDirectory.dir("src"))
task.outputDirectory.set(otherTask.outputDirectory)  // lazy wiring
task.antlrClasspath.setFrom(configurations.someConfig)
task.antlrClasspath.setFrom(otherTask.antlrClasspath)  // lazy wiring
task.arguments.add("item")
task.arguments.addAll(otherTask.arguments)  // lazy wiring
```

---

### `org.gradle.api.plugins.quality.Checkstyle`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `checkstyleClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getCheckstyleClasspath()` (return type changed) |
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `getClasspath()` (return type changed) |
| `configProperties` | `Map<String, Object>` | `MapProperty<String, Object>` | `getConfigProperties()` (return type changed) |
| `isIgnoreFailures` | `boolean` | `Property<Boolean>` | — |
| `maxErrors` | `int` | `Property<Integer>` | `getMaxErrors()` (return type changed) |
| `maxWarnings` | `int` | `Property<Integer>` | `getMaxWarnings()` (return type changed) |
| `showViolations` | `boolean` | `Property<Boolean>` | `isShowViolations()` |

**Migration examples:**

```groovy
task.isIgnoreFailures.set(true)  // also: showViolations
task.isIgnoreFailures.set(otherTask.isIgnoreFailures)  // lazy wiring
task.maxErrors.set(4)  // also: maxWarnings
task.maxErrors.set(provider { computeValue() })
task.maxErrors.set(otherTask.maxErrors)  // lazy wiring
task.checkstyleClasspath.setFrom(configurations.someConfig)  // also: classpath
task.checkstyleClasspath.setFrom(otherTask.checkstyleClasspath)  // lazy wiring
task.configProperties.put("key", "value")
task.configProperties.putAll(otherTask.configProperties)  // lazy wiring
```

---

### `org.gradle.api.plugins.quality.CheckstyleExtension`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `configProperties` | `Map<String, Object>` | `MapProperty<String, Object>` | `getConfigProperties()` (return type changed) |
| `maxErrors` | `int` | `Property<Integer>` | `getMaxErrors()` (return type changed) |
| `maxWarnings` | `int` | `Property<Integer>` | `getMaxWarnings()` (return type changed) |
| `showViolations` | `boolean` | `Property<Boolean>` | `isShowViolations()` |

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
| `codenarcClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getCodenarcClasspath()` (return type changed) |
| `compilationClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getCompilationClasspath()` (return type changed) |
| `maxPriority1Violations` | `int` | `Property<Integer>` | `getMaxPriority1Violations()` (return type changed) |
| `maxPriority2Violations` | `int` | `Property<Integer>` | `getMaxPriority2Violations()` (return type changed) |
| `maxPriority3Violations` | `int` | `Property<Integer>` | `getMaxPriority3Violations()` (return type changed) |

**Migration examples:**

```groovy
task.maxPriority1Violations.set(4)  // also: maxPriority2Violations, maxPriority3Violations
task.maxPriority1Violations.set(provider { computeValue() })
task.maxPriority1Violations.set(otherTask.maxPriority1Violations)  // lazy wiring
task.codenarcClasspath.setFrom(configurations.someConfig)  // also: compilationClasspath
task.codenarcClasspath.setFrom(otherTask.codenarcClasspath)  // lazy wiring
```

---

### `org.gradle.api.plugins.quality.CodeNarcExtension`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `maxPriority1Violations` | `int` | `Property<Integer>` | `getMaxPriority1Violations()` (return type changed) |
| `maxPriority2Violations` | `int` | `Property<Integer>` | `getMaxPriority2Violations()` (return type changed) |
| `maxPriority3Violations` | `int` | `Property<Integer>` | `getMaxPriority3Violations()` (return type changed) |
| `reportFormat` | `String` | `Property<String>` | `getReportFormat()` (return type changed) |

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
| `ignoreFailures` | `boolean` | `Property<Boolean>` | `isIgnoreFailures()` |
| `sourceSets` | `java.util.Collection<SourceSet>` | `ListProperty<SourceSet>` | `getSourceSets()` (return type changed) |
| `toolVersion` | `String` | `Property<String>` | `getToolVersion()` (return type changed) |

**Migration examples:**

```groovy
task.ignoreFailures.set(true)
task.ignoreFailures.set(otherTask.ignoreFailures)  // lazy wiring
task.toolVersion.set("value")
task.toolVersion.set(provider { computeValue() })
task.toolVersion.set(otherTask.toolVersion)  // lazy wiring
task.sourceSets.add("item")
task.sourceSets.addAll(otherTask.sourceSets)  // lazy wiring
```

---

### `org.gradle.api.plugins.quality.Pmd`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `getClasspath()` (return type changed) |
| `consoleOutput` | `boolean` | `Property<Boolean>` | `isConsoleOutput()` |
| `incrementalCacheFile` | `File` | `Provider<RegularFile>` | `getIncrementalCacheFile()` (return type changed) |
| `pmdClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getPmdClasspath()` (return type changed) |
| `ruleSetFiles` | `FileCollection` | `ConfigurableFileCollection` | `getRuleSetFiles()` (return type changed) |
| `ruleSets` | `List<String>` | `ListProperty<String>` | `getRuleSets()` (return type changed) |

**Migration examples:**

```groovy
task.consoleOutput.set(true)
task.consoleOutput.set(otherTask.consoleOutput)  // lazy wiring
task.classpath.setFrom(configurations.someConfig)  // also: pmdClasspath, ruleSetFiles
task.classpath.setFrom(otherTask.classpath)  // lazy wiring
task.ruleSets.add("item")
task.ruleSets.addAll(otherTask.ruleSets)  // lazy wiring

// Read-only (incrementalCacheFile) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.incrementalCacheFile)
```

---

### `org.gradle.api.plugins.quality.PmdExtension`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `consoleOutput` | `boolean` | `Property<Boolean>` | `isConsoleOutput()` |
| `ruleSetFiles` | `FileCollection` | `ConfigurableFileCollection` | `getRuleSetFiles()` (return type changed) |
| `ruleSets` | `List<String>` | `ListProperty<String>` | `getRuleSets()` (return type changed) |

**Migration examples:**

```groovy
task.consoleOutput.set(true)
task.consoleOutput.set(otherTask.consoleOutput)  // lazy wiring
task.ruleSetFiles.setFrom(configurations.someConfig)
task.ruleSetFiles.setFrom(otherTask.ruleSetFiles)  // lazy wiring
task.ruleSets.add("item")
task.ruleSets.addAll(otherTask.ruleSets)  // lazy wiring
```

---

### `org.gradle.api.publish.PublicationArtifact`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `file` | `File` | `Provider<RegularFile>` | `getFile()` (return type changed) |

**Migration examples:**

```groovy
// Read-only (file) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.file)
```

---

### `org.gradle.api.publish.ivy.IvyArtifact`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classifier` | `String` | `Property<String>` | `getClassifier()` (return type changed) |
| `conf` | `String` | `Property<String>` | `getConf()` (return type changed) |
| `extension` | `String` | `Property<String>` | `getExtension()` (return type changed) |
| `name` | `String` | `Property<String>` | `getName()` (return type changed) |
| `type` | `String` | `Property<String>` | `getType()` (return type changed) |

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
| `branch` | `String` | `Property<String>` | `getBranch()` (return type changed) |
| `status` | `String` | `Property<String>` | `getStatus()` (return type changed) |

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
| `module` | `String` | `Property<String>` | `getModule()` (return type changed) |
| `organisation` | `String` | `Property<String>` | `getOrganisation()` (return type changed) |
| `revision` | `String` | `Property<String>` | `getRevision()` (return type changed) |

**Migration examples:**

```groovy
task.module.set("value")  // also: organisation, revision
task.module.set(provider { computeValue() })
task.module.set(otherTask.module)  // lazy wiring
```

---

### `org.gradle.api.publish.maven.MavenArtifact`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classifier` | `String` | `Property<String>` | `getClassifier()` (return type changed) |
| `extension` | `String` | `Property<String>` | `getExtension()` (return type changed) |

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
| `packaging` | `String` | `Property<String>` | `getPackaging()` (return type changed) |

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
| `artifactId` | `String` | `Property<String>` | `getArtifactId()` (return type changed) |
| `groupId` | `String` | `Property<String>` | `getGroupId()` (return type changed) |
| `version` | `String` | `Property<String>` | `getVersion()` (return type changed) |

**Migration examples:**

```groovy
task.artifactId.set("value")  // also: groupId, version
task.artifactId.set(provider { computeValue() })
task.artifactId.set(otherTask.artifactId)  // lazy wiring
```

---

### `org.gradle.api.tasks.Delete`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `followSymlinks` | `boolean` | `Property<Boolean>` | `isFollowSymlinks()` |
| `targetFiles` | `FileCollection` | `ConfigurableFileCollection` | `getTargetFiles()` (return type changed) |

**Migration examples:**

```groovy
task.followSymlinks.set(true)
task.followSymlinks.set(otherTask.followSymlinks)  // lazy wiring
task.targetFiles.setFrom(configurations.someConfig)
task.targetFiles.setFrom(otherTask.targetFiles)  // lazy wiring
```

---

### `org.gradle.api.tasks.JavaExec`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `javaVersion` | `JavaVersion` | `Provider<JavaVersion>` | `getJavaVersion()` (return type changed) |

**Migration examples:**

```groovy
// Read-only (javaVersion) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.javaVersion)
```

---

### `org.gradle.api.tasks.WriteProperties`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `comment` | `String` | `Property<String>` | `getComment()` (return type changed) |
| `encoding` | `String` | `Property<String>` | `getEncoding()` (return type changed) |
| `lineSeparator` | `String` | `Property<String>` | `getLineSeparator()` (return type changed) |
| `properties` | `Map<String, String>` | `MapProperty<String, Object>` | `getProperties()` (return type changed) |

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
| `baseDir` | `File` | `DirectoryProperty` | `getBaseDir()` (return type changed) |
| `target` | `org.apache.tools.ant.Target` | `Property<org.apache.tools.ant.Target>` | `getTarget()` (return type changed) |

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
| `preserveFileTimestamps` | `boolean` | `Property<Boolean>` | `isPreserveFileTimestamps()` |
| `reproducibleFileOrder` | `boolean` | `Property<Boolean>` | `isReproducibleFileOrder()` |

**Migration examples:**

```groovy
task.preserveFileTimestamps.set(true)  // also: reproducibleFileOrder
task.preserveFileTimestamps.set(otherTask.preserveFileTimestamps)  // lazy wiring
```

---

### `org.gradle.api.tasks.bundling.Tar`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `compression` | `Compression` | `Property<Compression>` | `getCompression()` (return type changed) |

**Migration examples:**

```groovy
task.compression.set(someValue)
task.compression.set(otherTask.compression)  // lazy wiring
```

---

### `org.gradle.api.tasks.bundling.War`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `getClasspath()` (return type changed) |

**Migration examples:**

```groovy
task.classpath.setFrom(configurations.someConfig)
task.classpath.setFrom(otherTask.classpath)  // lazy wiring
```

---

### `org.gradle.api.tasks.bundling.Zip`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `entryCompression` | `ZipEntryCompression` | `Property<ZipEntryCompression>` | `getEntryCompression()` (return type changed) |
| `metadataCharset` | `String` | `Property<String>` | `getMetadataCharset()` (return type changed) |
| `zip64` | `boolean` | `Property<Boolean>` | `isZip64()` |

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
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `getClasspath()` (return type changed) |
| `destinationDirectory` | `DirectoryProperty` | `DirectoryProperty` | — |

**Migration examples:**

```groovy
task.destinationDirectory.set(layout.projectDirectory.dir("src"))
task.destinationDirectory.set(otherTask.destinationDirectory)  // lazy wiring
task.classpath.setFrom(configurations.someConfig)
task.classpath.setFrom(otherTask.classpath)  // lazy wiring
```

---

### `org.gradle.api.tasks.compile.BaseForkOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `jvmArgs` | `List<String>` | `ListProperty<String>` | `getJvmArgs()` (return type changed) |
| `memoryInitialSize` | `String` | `Property<String>` | `getMemoryInitialSize()` (return type changed) |
| `memoryMaximumSize` | `String` | `Property<String>` | `getMemoryMaximumSize()` (return type changed) |

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
| `allCompilerArgs` | `List<String>` | `Provider<List<String>>` | `getAllCompilerArgs()` (return type changed) |
| `annotationProcessorPath` | `FileCollection` | `ConfigurableFileCollection` | `getAnnotationProcessorPath()` (return type changed) |
| `bootstrapClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getBootstrapClasspath()` (return type changed) |
| `compilerArgs` | `List<String>` | `ListProperty<String>` | `getCompilerArgs()` (return type changed) |
| `compilerArgumentProviders` | `List<CommandLineArgumentProvider>` | `ListProperty<CommandLineArgumentProvider>` | `getCompilerArgumentProviders()` (return type changed) |
| `debug` | `boolean` | `Property<Boolean>` | `isDebug()` |
| `deprecation` | `boolean` | `Property<Boolean>` | `isDeprecation()` |
| `encoding` | `String` | `Property<String>` | `getEncoding()` (return type changed) |
| `extensionDirs` | `String` | `Property<String>` | `getExtensionDirs()` (return type changed) |
| `failOnError` | `boolean` | `Property<Boolean>` | `isFailOnError()` |
| `fork` | `boolean` | `Property<Boolean>` | `isFork()` |
| `generatedSourceOutputDirectory` | `DirectoryProperty` | `DirectoryProperty` | — |
| `incremental` | `boolean` | `Property<Boolean>` | `isIncremental()` |
| `listFiles` | `boolean` | `Property<Boolean>` | `isListFiles()` |
| `sourcepath` | `FileCollection` | `ConfigurableFileCollection` | `getSourcepath()` (return type changed) |
| `verbose` | `boolean` | `Property<Boolean>` | `isVerbose()` |
| `warnings` | `boolean` | `Property<Boolean>` | `isWarnings()` |

**Migration examples:**

```groovy
task.debug.set(true)  // also: deprecation, failOnError, fork, incremental, listFiles, verbose, warnings
task.debug.set(otherTask.debug)  // lazy wiring
task.encoding.set("value")  // also: extensionDirs
task.encoding.set(provider { computeValue() })
task.encoding.set(otherTask.encoding)  // lazy wiring
task.generatedSourceOutputDirectory.set(layout.projectDirectory.dir("src"))
task.generatedSourceOutputDirectory.set(otherTask.generatedSourceOutputDirectory)  // lazy wiring
task.annotationProcessorPath.setFrom(configurations.someConfig)  // also: bootstrapClasspath, sourcepath
task.annotationProcessorPath.setFrom(otherTask.annotationProcessorPath)  // lazy wiring
task.compilerArgs.add("item")  // also: compilerArgumentProviders
task.compilerArgs.addAll(otherTask.compilerArgs)  // lazy wiring

// Read-only (allCompilerArgs) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.allCompilerArgs)
```

---

### `org.gradle.api.tasks.compile.DebugOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `debugLevel` | `String` | `Property<String>` | `getDebugLevel()` (return type changed) |

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
| `executable` | `String` | `Property<String>` | `getExecutable()` (return type changed) |
| `tempDir` | `String` | `Property<String>` | `getTempDir()` (return type changed) |

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
| `groovyClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getGroovyClasspath()` (return type changed) |

**Migration examples:**

```groovy
task.groovyClasspath.setFrom(configurations.someConfig)
task.groovyClasspath.setFrom(otherTask.groovyClasspath)  // lazy wiring
```

---

### `org.gradle.api.tasks.compile.GroovyCompileOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `encoding` | `String` | `Property<String>` | `getEncoding()` (return type changed) |
| `failOnError` | `boolean` | `Property<Boolean>` | `isFailOnError()` |
| `fileExtensions` | `List<String>` | `ListProperty<String>` | `getFileExtensions()` (return type changed) |
| `fork` | `boolean` | `Property<Boolean>` | `isFork()` |
| `javaAnnotationProcessing` | `boolean` | `Property<Boolean>` | `isJavaAnnotationProcessing()` |
| `keepStubs` | `boolean` | `Property<Boolean>` | `isKeepStubs()` |
| `listFiles` | `boolean` | `Property<Boolean>` | `isListFiles()` |
| `optimizationOptions` | `Map<String, Boolean>` | `MapProperty<String, Boolean>` | `getOptimizationOptions()` (return type changed) |
| `parameters` | `boolean` | `Property<Boolean>` | `isParameters()` |
| `verbose` | `boolean` | `Property<Boolean>` | `isVerbose()` |

**Migration examples:**

```groovy
task.failOnError.set(true)  // also: fork, javaAnnotationProcessing, keepStubs, listFiles, parameters, verbose
task.failOnError.set(otherTask.failOnError)  // lazy wiring
task.encoding.set("value")
task.encoding.set(provider { computeValue() })
task.encoding.set(otherTask.encoding)  // lazy wiring
task.fileExtensions.add("item")
task.fileExtensions.addAll(otherTask.fileExtensions)  // lazy wiring
task.optimizationOptions.put("key", "value")
task.optimizationOptions.putAll(otherTask.optimizationOptions)  // lazy wiring
```

---

### `org.gradle.api.tasks.compile.ProviderAwareCompilerDaemonForkOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `allJvmArgs` | `List<String>` | `Provider<List<String>>` | `getAllJvmArgs()` (return type changed) |
| `jvmArgumentProviders` | `List<CommandLineArgumentProvider>` | `ListProperty<CommandLineArgumentProvider>` | `getJvmArgumentProviders()` (return type changed) |

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
| `configurations` | `Set<Configuration>` | `SetProperty<Configuration>` | `getConfigurations()` (return type changed) |

**Migration examples:**

```groovy
task.configurations.add(item)
task.configurations.addAll(otherTask.configurations)  // lazy wiring
```

---

### `org.gradle.api.tasks.diagnostics.ConventionReportTask`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `outputFile` | `File` | `RegularFileProperty` | `getOutputFile()` (return type changed) |
| `projects` | `Set<Project>` | `SetProperty<Project>` | `getProjects()` (return type changed) |

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
| `configuration` | `Configuration` | `Property<Configuration>` | `getConfiguration()` (return type changed) |
| `showSinglePathToDependency` | `boolean` | `Property<Boolean>` | `isShowSinglePathToDependency()` |

**Migration examples:**

```groovy
task.showSinglePathToDependency.set(true)
task.showSinglePathToDependency.set(otherTask.showSinglePathToDependency)  // lazy wiring
task.configuration.set(someValue)
task.configuration.set(otherTask.configuration)  // lazy wiring
```

---

### `org.gradle.api.tasks.diagnostics.TaskReportTask`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `displayGroup` | `String` | `Property<String>` | `getDisplayGroup()` (return type changed) |
| `showDetail` | `boolean` | `Property<Boolean>` | `isDetail()` |

**Migration examples:**

```groovy
task.showDetail.set(true)
task.showDetail.set(otherTask.showDetail)  // lazy wiring
task.displayGroup.set("value")
task.displayGroup.set(provider { computeValue() })
task.displayGroup.set(otherTask.displayGroup)  // lazy wiring
```

---

### `org.gradle.api.tasks.javadoc.Groovydoc`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `getClasspath()` (return type changed) |
| `docTitle` | `String` | `Property<String>` | `getDocTitle()` (return type changed) |
| `footer` | `String` | `Property<String>` | `getFooter()` (return type changed) |
| `groovyClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getGroovyClasspath()` (return type changed) |
| `header` | `String` | `Property<String>` | `getHeader()` (return type changed) |
| `links` | `Set<Groovydoc$Link>` | `SetProperty<Groovydoc$Link>` | `getLinks()` (return type changed) |
| `noTimestamp` | `boolean` | `Property<Boolean>` | `isNoTimestamp()` |
| `noVersionStamp` | `boolean` | `Property<Boolean>` | `isNoVersionStamp()` |
| `use` | `boolean` | `Property<Boolean>` | `isUse()` |
| `windowTitle` | `String` | `Property<String>` | `getWindowTitle()` (return type changed) |

**Migration examples:**

```groovy
task.noTimestamp.set(true)  // also: noVersionStamp, use
task.noTimestamp.set(otherTask.noTimestamp)  // lazy wiring
task.docTitle.set("value")  // also: footer, header, windowTitle
task.docTitle.set(provider { computeValue() })
task.docTitle.set(otherTask.docTitle)  // lazy wiring
task.classpath.setFrom(configurations.someConfig)  // also: groovyClasspath
task.classpath.setFrom(otherTask.classpath)  // lazy wiring
task.links.add(item)
task.links.addAll(otherTask.links)  // lazy wiring
```

---

### `org.gradle.api.tasks.javadoc.Javadoc`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `getClasspath()` (return type changed) |
| `executable` | `String` | `Property<String>` | `getExecutable()` (return type changed) |
| `failOnError` | `boolean` | `Property<Boolean>` | `isFailOnError()` |
| `maxMemory` | `String` | `Property<String>` | `getMaxMemory()` (return type changed) |
| `optionsFile` | `File` | `Provider<RegularFile>` | `getOptionsFile()` (return type changed) |
| `title` | `String` | `Property<String>` | `getTitle()` (return type changed) |

**Migration examples:**

```groovy
task.failOnError.set(true)
task.failOnError.set(otherTask.failOnError)  // lazy wiring
task.executable.set("value")  // also: maxMemory, title
task.executable.set(provider { computeValue() })
task.executable.set(otherTask.executable)  // lazy wiring
task.classpath.setFrom(configurations.someConfig)
task.classpath.setFrom(otherTask.classpath)  // lazy wiring

// Read-only (optionsFile) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.optionsFile)
```

---

### `org.gradle.api.tasks.scala.ScalaCompile`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `scalaClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getScalaClasspath()` (return type changed) |
| `scalaCompilerPlugins` | `FileCollection` | `ConfigurableFileCollection` | `getScalaCompilerPlugins()` (return type changed) |
| `zincClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getZincClasspath()` (return type changed) |

**Migration examples:**

```groovy
task.scalaClasspath.setFrom(configurations.someConfig)  // also: scalaCompilerPlugins, zincClasspath
task.scalaClasspath.setFrom(otherTask.scalaClasspath)  // lazy wiring
```

---

### `org.gradle.api.tasks.scala.ScalaDoc`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `getClasspath()` (return type changed) |
| `scalaClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getScalaClasspath()` (return type changed) |
| `title` | `String` | `Property<String>` | `getTitle()` (return type changed) |

**Migration examples:**

```groovy
task.title.set("value")
task.title.set(provider { computeValue() })
task.title.set(otherTask.title)  // lazy wiring
task.classpath.setFrom(configurations.someConfig)  // also: scalaClasspath
task.classpath.setFrom(otherTask.classpath)  // lazy wiring
```

---

### `org.gradle.api.tasks.scala.ScalaDocOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `additionalParameters` | `List<String>` | `ListProperty<String>` | `getAdditionalParameters()` (return type changed) |
| `bottom` | `String` | `Property<String>` | `getBottom()` (return type changed) |
| `deprecation` | `boolean` | `Property<Boolean>` | `isDeprecation()` |
| `docTitle` | `String` | `Property<String>` | `getDocTitle()` (return type changed) |
| `footer` | `String` | `Property<String>` | `getFooter()` (return type changed) |
| `header` | `String` | `Property<String>` | `getHeader()` (return type changed) |
| `top` | `String` | `Property<String>` | `getTop()` (return type changed) |
| `unchecked` | `boolean` | `Property<Boolean>` | `isUnchecked()` |
| `windowTitle` | `String` | `Property<String>` | `getWindowTitle()` (return type changed) |

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
| `outputPerTestCase` | `boolean` | `Property<Boolean>` | `isOutputPerTestCase()` |

**Migration examples:**

```groovy
task.outputPerTestCase.set(true)
task.outputPerTestCase.set(otherTask.outputPerTestCase)  // lazy wiring
```

---

### `org.gradle.api.tasks.testing.Test`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `getClasspath()` (return type changed) |
| `forkEvery` | `long` | `Property<java.lang.Long>` | `getForkEvery()` (return type changed) |
| `javaVersion` | `JavaVersion` | `Provider<JavaVersion>` | `getJavaVersion()` (return type changed) |
| `maxParallelForks` | `int` | `Property<Integer>` | `getMaxParallelForks()` (return type changed) |
| `scanForTestClasses` | `boolean` | `Property<Boolean>` | `isScanForTestClasses()` |
| `testClassesDirs` | `FileCollection` | `ConfigurableFileCollection` | `getTestClassesDirs()` (return type changed) |
| `testFramework` | `TestFramework` | `Property<TestFramework>` | `getTestFramework()` (return type changed) |

**Migration examples:**

```groovy
task.scanForTestClasses.set(true)
task.scanForTestClasses.set(otherTask.scanForTestClasses)  // lazy wiring
task.forkEvery.set(4)  // also: maxParallelForks
task.forkEvery.set(provider { computeValue() })
task.forkEvery.set(otherTask.forkEvery)  // lazy wiring
task.classpath.setFrom(configurations.someConfig)  // also: testClassesDirs
task.classpath.setFrom(otherTask.classpath)  // lazy wiring
task.testFramework.set(someValue)
task.testFramework.set(otherTask.testFramework)  // lazy wiring

// Read-only (javaVersion) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.javaVersion)
```

---

### `org.gradle.api.tasks.testing.TestFilter`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `excludePatterns` | `Set<String>` | `SetProperty<String>` | `getExcludePatterns()` (return type changed) |
| `failOnNoMatchingTests` | `boolean` | `Property<Boolean>` | `isFailOnNoMatchingTests()` |
| `includePatterns` | `Set<String>` | `SetProperty<String>` | `getIncludePatterns()` (return type changed) |

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
| `excludeCategories` | `Set<String>` | `SetProperty<String>` | `getExcludeCategories()` (return type changed) |
| `includeCategories` | `Set<String>` | `SetProperty<String>` | `getIncludeCategories()` (return type changed) |

**Migration examples:**

```groovy
task.excludeCategories.add(item)  // also: includeCategories
task.excludeCategories.addAll(otherTask.excludeCategories)  // lazy wiring
```

---

### `org.gradle.api.tasks.testing.junitplatform.JUnitPlatformOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `excludeEngines` | `Set<String>` | `SetProperty<String>` | `getExcludeEngines()` (return type changed) |
| `excludeTags` | `Set<String>` | `SetProperty<String>` | `getExcludeTags()` (return type changed) |
| `includeEngines` | `Set<String>` | `SetProperty<String>` | `getIncludeEngines()` (return type changed) |
| `includeTags` | `Set<String>` | `SetProperty<String>` | `getIncludeTags()` (return type changed) |

**Migration examples:**

```groovy
task.excludeEngines.add(item)  // also: excludeTags, includeEngines, includeTags
task.excludeEngines.addAll(otherTask.excludeEngines)  // lazy wiring
```

---

### `org.gradle.api.tasks.testing.logging.TestLogging`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `displayGranularity` | `int` | `Property<Integer>` | `getDisplayGranularity()` (return type changed) |
| `events` | `Set<TestLogEvent>` | `SetProperty<TestLogEvent>` | `getEvents()` (return type changed) |
| `exceptionFormat` | `TestExceptionFormat` | `Property<TestExceptionFormat>` | `getExceptionFormat()` (return type changed) |
| `maxGranularity` | `int` | `Property<Integer>` | `getMaxGranularity()` (return type changed) |
| `minGranularity` | `int` | `Property<Integer>` | `getMinGranularity()` (return type changed) |
| `showCauses` | `boolean` | `Property<Boolean>` | `getShowCauses()` (return type changed) |
| `showExceptions` | `boolean` | `Property<Boolean>` | `getShowExceptions()` (return type changed) |
| `showStackTraces` | `boolean` | `Property<Boolean>` | `getShowStackTraces()` (return type changed) |
| `showStandardStreams` | `boolean` | `Property<Boolean>` | `getShowStandardStreams()` (return type changed) |
| `stackTraceFilters` | `Set<TestStackTraceFilter>` | `SetProperty<TestStackTraceFilter>` | `getStackTraceFilters()` (return type changed) |

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
| `configFailurePolicy` | `String` | `Property<String>` | `getConfigFailurePolicy()` (return type changed) |
| `excludeGroups` | `Set<String>` | `SetProperty<String>` | `getExcludeGroups()` (return type changed) |
| `groupByInstances` | `boolean` | `Property<Boolean>` | `isGroupByInstances()`, `getGroupByInstances()` (return type changed) |
| `includeGroups` | `Set<String>` | `SetProperty<String>` | `getIncludeGroups()` (return type changed) |
| `listeners` | `Set<String>` | `SetProperty<String>` | `getListeners()` (return type changed) |
| `outputDirectory` | `File` | `DirectoryProperty` | `getOutputDirectory()` (return type changed) |
| `parallel` | `String` | `Property<String>` | `getParallel()` (return type changed) |
| `preserveOrder` | `boolean` | `Property<Boolean>` | `isPreserveOrder()`, `getPreserveOrder()` (return type changed) |
| `suiteName` | `String` | `Property<String>` | `getSuiteName()` (return type changed) |
| `suiteXmlBuilder` | `groovy.xml.MarkupBuilder` | `Property<groovy.xml.MarkupBuilder>` | `getSuiteXmlBuilder()` (return type changed) |
| `suiteXmlFiles` | `List<File>` | `ConfigurableFileCollection` | `getSuiteXmlFiles()` (return type changed) |
| `suiteXmlWriter` | `java.io.StringWriter` | `Property<java.io.StringWriter>` | `getSuiteXmlWriter()` (return type changed) |
| `testName` | `String` | `Property<String>` | `getTestName()` (return type changed) |
| `threadCount` | `int` | `Property<Integer>` | `getThreadCount()` (return type changed) |
| `threadPoolFactoryClass` | `String` | `Property<String>` | `getThreadPoolFactoryClass()` (return type changed) |
| `useDefaultListeners` | `boolean` | `Property<Boolean>` | `isUseDefaultListeners()`, `getUseDefaultListeners()` (return type changed) |

**Migration examples:**

```groovy
task.groupByInstances.set(true)  // also: preserveOrder, useDefaultListeners
task.groupByInstances.set(otherTask.groupByInstances)  // lazy wiring
task.configFailurePolicy.set("value")  // also: parallel, suiteName, testName, threadCount, threadPoolFactoryClass
task.configFailurePolicy.set(provider { computeValue() })
task.configFailurePolicy.set(otherTask.configFailurePolicy)  // lazy wiring
task.outputDirectory.set(layout.projectDirectory.dir("src"))
task.outputDirectory.set(otherTask.outputDirectory)  // lazy wiring
task.suiteXmlFiles.setFrom(configurations.someConfig)
task.suiteXmlFiles.setFrom(otherTask.suiteXmlFiles)  // lazy wiring
task.excludeGroups.add(item)  // also: includeGroups, listeners
task.excludeGroups.addAll(otherTask.excludeGroups)  // lazy wiring
task.suiteXmlBuilder.set(someValue)  // also: suiteXmlWriter
task.suiteXmlBuilder.set(otherTask.suiteXmlBuilder)  // lazy wiring
```

---

### `org.gradle.api.tasks.wrapper.Wrapper`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `archiveBase` | `Wrapper$PathBase` | `Property<Wrapper$PathBase>` | `getArchiveBase()` (return type changed) |
| `archivePath` | `String` | `Property<String>` | `getArchivePath()` (return type changed) |
| `batchScript` | `File` | `Provider<RegularFile>` | `getBatchScript()` (return type changed) |
| `distributionBase` | `Wrapper$PathBase` | `Property<Wrapper$PathBase>` | `getDistributionBase()` (return type changed) |
| `distributionPath` | `String` | `Property<String>` | `getDistributionPath()` (return type changed) |
| `distributionSha256Sum` | `String` | `Property<String>` | `getDistributionSha256Sum()` (return type changed) |
| `distributionType` | `Wrapper$DistributionType` | `Property<Wrapper$DistributionType>` | `getDistributionType()` (return type changed) |
| `distributionUrl` | `String` | `Property<String>` | `getDistributionUrl()` (return type changed) |
| `gradleVersion` | `String` | `Property<String>` | `getGradleVersion()` (return type changed) |
| `jarFile` | `File` | `RegularFileProperty` | `getJarFile()` (return type changed) |
| `propertiesFile` | `File` | `Provider<RegularFile>` | `getPropertiesFile()` (return type changed) |
| `scriptFile` | `File` | `RegularFileProperty` | `getScriptFile()` (return type changed) |

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

### `org.gradle.buildinit.tasks.InitBuild`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `availableBuildTypes` | `List<String>` | `Provider<List<String>>` | `getAvailableBuildTypes()` (return type changed) |
| `availableDSLs` | `List<String>` | `Provider<List<String>>` | `getAvailableDSLs()` (return type changed) |
| `availableTestFrameworks` | `List<String>` | `Provider<List<String>>` | `getAvailableTestFrameworks()` (return type changed) |
| `dsl` | `String` | `Property<String>` | `getDsl()` (return type changed) |
| `packageName` | `String` | `Property<String>` | `getPackageName()` (return type changed) |
| `projectName` | `String` | `Property<String>` | `getProjectName()` (return type changed) |
| `testFramework` | `String` | `Property<String>` | `getTestFramework()` (return type changed) |
| `type` | `String` | `Property<String>` | `getType()` (return type changed) |

**Migration examples:**

```groovy
task.dsl.set("value")  // also: packageName, projectName, testFramework, type
task.dsl.set(provider { computeValue() })
task.dsl.set(otherTask.dsl)  // lazy wiring

// Read-only (availableBuildTypes, availableDSLs, availableTestFrameworks) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.availableBuildTypes)
```

---

### `org.gradle.caching.configuration.BuildCache`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `enabled` | `boolean` | `Property<Boolean>` | `isEnabled()` |
| `push` | `boolean` | `Property<Boolean>` | `isPush()` |

**Migration examples:**

```groovy
task.enabled.set(true)  // also: push
task.enabled.set(otherTask.enabled)  // lazy wiring
```

---

### `org.gradle.caching.http.HttpBuildCache`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `allowInsecureProtocol` | `boolean` | `Property<Boolean>` | `isAllowInsecureProtocol()` |
| `allowUntrustedServer` | `boolean` | `Property<Boolean>` | `isAllowUntrustedServer()` |
| `url` | `URI` | `Property<URI>` | `getUrl()` (return type changed) |
| `useExpectContinue` | `boolean` | `Property<Boolean>` | `isUseExpectContinue()` |

**Migration examples:**

```groovy
task.allowInsecureProtocol.set(true)  // also: allowUntrustedServer, useExpectContinue
task.allowInsecureProtocol.set(otherTask.allowInsecureProtocol)  // lazy wiring
task.url.set(someValue)
task.url.set(otherTask.url)  // lazy wiring
```

---

### `org.gradle.caching.local.DirectoryBuildCache`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `directory` | `Object` | `DirectoryProperty` | `getDirectory()` (return type changed) |

**Migration examples:**

```groovy
task.directory.set(layout.projectDirectory.dir("src"))
task.directory.set(otherTask.directory)  // lazy wiring
```

---

### `org.gradle.external.javadoc.MinimalJavadocOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `bootClasspath` | `List<File>` | `ConfigurableFileCollection` | `getBootClasspath()` (return type changed) |
| `breakIterator` | `boolean` | `Property<Boolean>` | `isBreakIterator()` |
| `classpath` | `List<File>` | `ConfigurableFileCollection` | `getClasspath()` (return type changed) |
| `destinationDirectory` | `File` | `DirectoryProperty` | `getDestinationDirectory()` (return type changed) |
| `doclet` | `String` | `Property<String>` | `getDoclet()` (return type changed) |
| `docletpath` | `List<File>` | `ConfigurableFileCollection` | `getDocletpath()` (return type changed) |
| `encoding` | `String` | `Property<String>` | `getEncoding()` (return type changed) |
| `extDirs` | `List<File>` | `ConfigurableFileCollection` | `getExtDirs()` (return type changed) |
| `header` | `String` | `Property<String>` | `getHeader()` (return type changed) |
| `jFlags` | `List<String>` | `ListProperty<String>` | `getJFlags()` (return type changed) |
| `locale` | `String` | `Property<String>` | `getLocale()` (return type changed) |
| `memberLevel` | `JavadocMemberLevel` | `Property<JavadocMemberLevel>` | `getMemberLevel()` (return type changed) |
| `modulePath` | `List<File>` | `ConfigurableFileCollection` | `getModulePath()` (return type changed) |
| `optionFiles` | `List<File>` | `ConfigurableFileCollection` | `getOptionFiles()` (return type changed) |
| `outputLevel` | `JavadocOutputLevel` | `Property<JavadocOutputLevel>` | `getOutputLevel()` (return type changed) |
| `overview` | `String` | `Property<String>` | `getOverview()` (return type changed) |
| `source` | `String` | `Property<String>` | `getSource()` (return type changed) |
| `sourceNames` | `List<String>` | `ListProperty<String>` | `getSourceNames()` (return type changed) |
| `verbose` | `boolean` | `Provider<Boolean>` | `isVerbose()` |
| `windowTitle` | `String` | `Property<String>` | `getWindowTitle()` (return type changed) |

**Migration examples:**

```groovy
task.breakIterator.set(true)
task.breakIterator.set(otherTask.breakIterator)  // lazy wiring
task.doclet.set("value")  // also: encoding, header, locale, overview, source, windowTitle
task.doclet.set(provider { computeValue() })
task.doclet.set(otherTask.doclet)  // lazy wiring
task.destinationDirectory.set(layout.projectDirectory.dir("src"))
task.destinationDirectory.set(otherTask.destinationDirectory)  // lazy wiring
task.bootClasspath.setFrom(configurations.someConfig)  // also: classpath, docletpath, extDirs, modulePath, optionFiles
task.bootClasspath.setFrom(otherTask.bootClasspath)  // lazy wiring
task.jFlags.add("item")  // also: sourceNames
task.jFlags.addAll(otherTask.jFlags)  // lazy wiring
task.memberLevel.set(someValue)  // also: outputLevel
task.memberLevel.set(otherTask.memberLevel)  // lazy wiring

// Read-only (verbose) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.verbose)
```

---

### `org.gradle.external.javadoc.StandardJavadocDocletOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `author` | `boolean` | `Property<Boolean>` | `isAuthor()` |
| `bottom` | `String` | `Property<String>` | `getBottom()` (return type changed) |
| `charSet` | `String` | `Property<String>` | `getCharSet()` (return type changed) |
| `docEncoding` | `String` | `Property<String>` | `getDocEncoding()` (return type changed) |
| `docFilesSubDirs` | `boolean` | `Property<Boolean>` | `isDocFilesSubDirs()` |
| `docTitle` | `String` | `Property<String>` | `getDocTitle()` (return type changed) |
| `excludeDocFilesSubDir` | `List<String>` | `ListProperty<String>` | `getExcludeDocFilesSubDir()` (return type changed) |
| `footer` | `String` | `Property<String>` | `getFooter()` (return type changed) |
| `groups` | `Map<String, List<String>>` | `MapProperty<String, List<String>>` | `getGroups()` (return type changed) |
| `helpFile` | `File` | `RegularFileProperty` | `getHelpFile()` (return type changed) |
| `keyWords` | `boolean` | `Property<Boolean>` | `isKeyWords()` |
| `linkSource` | `boolean` | `Property<Boolean>` | `isLinkSource()` |
| `links` | `List<String>` | `ListProperty<String>` | `getLinks()` (return type changed) |
| `linksOffline` | `List<JavadocOfflineLink>` | `ListProperty<JavadocOfflineLink>` | `getLinksOffline()` (return type changed) |
| `noComment` | `boolean` | `Property<Boolean>` | `isNoComment()` |
| `noDeprecated` | `boolean` | `Property<Boolean>` | `isNoDeprecated()` |
| `noDeprecatedList` | `boolean` | `Property<Boolean>` | `isNoDeprecatedList()` |
| `noHelp` | `boolean` | `Property<Boolean>` | `isNoHelp()` |
| `noIndex` | `boolean` | `Property<Boolean>` | `isNoIndex()` |
| `noNavBar` | `boolean` | `Property<Boolean>` | `isNoNavBar()` |
| `noQualifiers` | `List<String>` | `ListProperty<String>` | `getNoQualifiers()` (return type changed) |
| `noSince` | `boolean` | `Property<Boolean>` | `isNoSince()` |
| `noTimestamp` | `boolean` | `Property<Boolean>` | `isNoTimestamp()` |
| `noTree` | `boolean` | `Property<Boolean>` | `isNoTree()` |
| `serialWarn` | `boolean` | `Property<Boolean>` | `isSerialWarn()` |
| `splitIndex` | `boolean` | `Property<Boolean>` | `isSplitIndex()` |
| `stylesheetFile` | `File` | `RegularFileProperty` | `getStylesheetFile()` (return type changed) |
| `tagletPath` | `List<File>` | `ConfigurableFileCollection` | `getTagletPath()` (return type changed) |
| `taglets` | `List<String>` | `ListProperty<String>` | `getTaglets()` (return type changed) |
| `tags` | `List<String>` | `ListProperty<String>` | `getTags()` (return type changed) |
| `use` | `boolean` | `Property<Boolean>` | `isUse()` |
| `version` | `boolean` | `Property<Boolean>` | `isVersion()` |

**Migration examples:**

```groovy
task.author.set(true)  // also: docFilesSubDirs, keyWords, linkSource, noComment, noDeprecated, noDeprecatedList, noHelp, noIndex, noNavBar, noSince, noTimestamp, noTree, serialWarn, splitIndex, use, version
task.author.set(otherTask.author)  // lazy wiring
task.bottom.set("value")  // also: charSet, docEncoding, docTitle, footer
task.bottom.set(provider { computeValue() })
task.bottom.set(otherTask.bottom)  // lazy wiring
task.helpFile.set(layout.buildDirectory.file("output.txt"))  // also: stylesheetFile
task.helpFile.set(otherTask.helpFile)  // lazy wiring
task.tagletPath.setFrom(configurations.someConfig)
task.tagletPath.setFrom(otherTask.tagletPath)  // lazy wiring
task.excludeDocFilesSubDir.add("item")  // also: links, linksOffline, noQualifiers, taglets, tags
task.excludeDocFilesSubDir.addAll(otherTask.excludeDocFilesSubDir)  // lazy wiring
task.groups.put("key", "value")
task.groups.putAll(otherTask.groups)  // lazy wiring
```

---

### `org.gradle.jvm.application.tasks.CreateStartScripts`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `applicationName` | `String` | `Property<String>` | `getApplicationName()` (return type changed) |
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `getClasspath()` (return type changed) |
| `defaultJvmOpts` | `Iterable<String>` | `ListProperty<String>` | `getDefaultJvmOpts()` (return type changed) |
| `executableDir` | `String` | `Property<String>` | `getExecutableDir()` (return type changed) |
| `optsEnvironmentVar` | `String` | `Property<String>` | `getOptsEnvironmentVar()` (return type changed) |

**Migration examples:**

```groovy
task.applicationName.set("value")  // also: executableDir, optsEnvironmentVar
task.applicationName.set(provider { computeValue() })
task.applicationName.set(otherTask.applicationName)  // lazy wiring
task.classpath.setFrom(configurations.someConfig)
task.classpath.setFrom(otherTask.classpath)  // lazy wiring
task.defaultJvmOpts.add("item")
task.defaultJvmOpts.addAll(otherTask.defaultJvmOpts)  // lazy wiring
```

---

### `org.gradle.jvm.tasks.Jar`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `manifestContentCharset` | `String` | `Property<String>` | `getManifestContentCharset()` (return type changed) |

**Migration examples:**

```groovy
task.manifestContentCharset.set("value")
task.manifestContentCharset.set(provider { computeValue() })
task.manifestContentCharset.set(otherTask.manifestContentCharset)  // lazy wiring
```

---

### `org.gradle.language.scala.tasks.BaseScalaCompileOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `additionalParameters` | `List<String>` | `ListProperty<String>` | `getAdditionalParameters()` (return type changed) |
| `debugLevel` | `String` | `Property<String>` | `getDebugLevel()` (return type changed) |
| `deprecation` | `boolean` | `Property<Boolean>` | `isDeprecation()` |
| `encoding` | `String` | `Property<String>` | `getEncoding()` (return type changed) |
| `failOnError` | `boolean` | `Property<Boolean>` | `isFailOnError()` |
| `force` | `boolean` | `Property<Boolean>` | `isForce()` |
| `listFiles` | `boolean` | `Property<Boolean>` | `isListFiles()` |
| `loggingLevel` | `String` | `Property<String>` | `getLoggingLevel()` (return type changed) |
| `loggingPhases` | `List<String>` | `ListProperty<String>` | `getLoggingPhases()` (return type changed) |
| `optimize` | `boolean` | `Property<Boolean>` | `isOptimize()` |
| `unchecked` | `boolean` | `Property<Boolean>` | `isUnchecked()` |

**Migration examples:**

```groovy
task.deprecation.set(true)  // also: failOnError, force, listFiles, optimize, unchecked
task.deprecation.set(otherTask.deprecation)  // lazy wiring
task.debugLevel.set("value")  // also: encoding, loggingLevel
task.debugLevel.set(provider { computeValue() })
task.debugLevel.set(otherTask.debugLevel)  // lazy wiring
task.additionalParameters.add("item")  // also: loggingPhases
task.additionalParameters.addAll(otherTask.additionalParameters)  // lazy wiring
```

---

### `org.gradle.plugin.devel.PluginDeclaration`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `description` | `String` | `Property<String>` | `getDescription()` (return type changed) |
| `displayName` | `String` | `Property<String>` | `getDisplayName()` (return type changed) |
| `id` | `String` | `Property<String>` | `getId()` (return type changed) |
| `implementationClass` | `String` | `Property<String>` | `getImplementationClass()` (return type changed) |

**Migration examples:**

```groovy
task.description.set("value")  // also: displayName, id, implementationClass
task.description.set(provider { computeValue() })
task.description.set(otherTask.description)  // lazy wiring
```

---

### `org.gradle.plugins.ear.Ear`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `libDirName` | `String` | `Property<String>` | `getLibDirName()` (return type changed) |

**Migration examples:**

```groovy
task.libDirName.set("value")
task.libDirName.set(provider { computeValue() })
task.libDirName.set(otherTask.libDirName)  // lazy wiring
```

---

### `org.gradle.plugins.ear.descriptor.DeploymentDescriptor`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `applicationName` | `String` | `Property<String>` | `getApplicationName()` (return type changed) |
| `description` | `String` | `Property<String>` | `getDescription()` (return type changed) |
| `displayName` | `String` | `Property<String>` | `getDisplayName()` (return type changed) |
| `initializeInOrder` | `Boolean` | `Property<Boolean>` | `getInitializeInOrder()` (return type changed) |
| `libraryDirectory` | `String` | `Property<String>` | `getLibraryDirectory()` (return type changed) |
| `moduleTypeMappings` | `Map<String, String>` | `MapProperty<String, String>` | `getModuleTypeMappings()` (return type changed) |
| `modules` | `Set<EarModule>` | `SetProperty<EarModule>` | `getModules()` (return type changed) |
| `securityRoles` | `Set<EarSecurityRole>` | `SetProperty<EarSecurityRole>` | `getSecurityRoles()` (return type changed) |
| `version` | `String` | `Property<String>` | `getVersion()` (return type changed) |

**Migration examples:**

```groovy
task.applicationName.set("value")  // also: description, displayName, libraryDirectory, version
task.applicationName.set(provider { computeValue() })
task.applicationName.set(otherTask.applicationName)  // lazy wiring
task.modules.add(item)  // also: securityRoles
task.modules.addAll(otherTask.modules)  // lazy wiring
task.moduleTypeMappings.put("key", "value")
task.moduleTypeMappings.putAll(otherTask.moduleTypeMappings)  // lazy wiring
task.initializeInOrder.set(someValue)
task.initializeInOrder.set(otherTask.initializeInOrder)  // lazy wiring
```

---

### `org.gradle.plugins.ear.descriptor.EarModule`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `altDeployDescriptor` | `String` | `Property<String>` | `getAltDeployDescriptor()` (return type changed) |
| `path` | `String` | `Property<String>` | `getPath()` (return type changed) |

**Migration examples:**

```groovy
task.altDeployDescriptor.set("value")  // also: path
task.altDeployDescriptor.set(provider { computeValue() })
task.altDeployDescriptor.set(otherTask.altDeployDescriptor)  // lazy wiring
```

---

### `org.gradle.plugins.ear.descriptor.EarSecurityRole`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `description` | `String` | `Property<String>` | `getDescription()` (return type changed) |
| `roleName` | `String` | `Property<String>` | `getRoleName()` (return type changed) |

**Migration examples:**

```groovy
task.description.set("value")  // also: roleName
task.description.set(provider { computeValue() })
task.description.set(otherTask.description)  // lazy wiring
```

---

### `org.gradle.plugins.ear.descriptor.EarWebModule`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `contextRoot` | `String` | `Property<String>` | `getContextRoot()` (return type changed) |

**Migration examples:**

```groovy
task.contextRoot.set("value")
task.contextRoot.set(provider { computeValue() })
task.contextRoot.set(otherTask.contextRoot)  // lazy wiring
```

---

### `org.gradle.process.BaseExecSpec`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `commandLine` | `List<String>` | `Provider<List<String>>` | `getCommandLine()` (return type changed) |
| `errorOutput` | `OutputStream` | `Property<OutputStream>` | `getErrorOutput()` (return type changed) |
| `ignoreExitValue` | `boolean` | `Property<Boolean>` | `isIgnoreExitValue()` |
| `standardInput` | `InputStream` | `Property<InputStream>` | `getStandardInput()` (return type changed) |
| `standardOutput` | `OutputStream` | `Property<OutputStream>` | `getStandardOutput()` (return type changed) |

**Migration examples:**

```groovy
task.ignoreExitValue.set(true)
task.ignoreExitValue.set(otherTask.ignoreExitValue)  // lazy wiring
task.errorOutput.set(someValue)  // also: standardInput, standardOutput
task.errorOutput.set(otherTask.errorOutput)  // lazy wiring

// Read-only (commandLine) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.commandLine)
```

---

### `org.gradle.process.ExecSpec`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `args` | `List<String>` | `ListProperty<String>` | `getArgs()` (return type changed) |
| `argumentProviders` | `List<CommandLineArgumentProvider>` | `ListProperty<CommandLineArgumentProvider>` | `getArgumentProviders()` (return type changed) |

**Migration examples:**

```groovy
task.args.add("item")  // also: argumentProviders
task.args.addAll(otherTask.args)  // lazy wiring
```

---

### `org.gradle.process.JavaExecSpec`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `args` | `List<String>` | `ListProperty<String>` | `getArgs()` (return type changed) |
| `argumentProviders` | `List<CommandLineArgumentProvider>` | `ListProperty<CommandLineArgumentProvider>` | `getArgumentProviders()` (return type changed) |
| `classpath` | `FileCollection` | `ConfigurableFileCollection` | `getClasspath()` (return type changed) |
| `mainClass` | `Property<String>` | `Property<String>` | — |

**Migration examples:**

```groovy
task.classpath.setFrom(configurations.someConfig)
task.classpath.setFrom(otherTask.classpath)  // lazy wiring
task.args.add("item")  // also: argumentProviders
task.args.addAll(otherTask.args)  // lazy wiring
task.mainClass.set(someValue)
task.mainClass.set(otherTask.mainClass)  // lazy wiring
```

---

### `org.gradle.process.JavaForkOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `allJvmArgs` | `List<String>` | `Provider<List<String>>` | `getAllJvmArgs()` (return type changed) |
| `bootstrapClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getBootstrapClasspath()` (return type changed) |
| `debug` | `boolean` | `Property<Boolean>` | `getDebug()` (return type changed) |
| `defaultCharacterEncoding` | `String` | `Property<String>` | `getDefaultCharacterEncoding()` (return type changed) |
| `enableAssertions` | `boolean` | `Property<Boolean>` | `getEnableAssertions()` (return type changed) |
| `jvmArgs` | `List<String>` | `ListProperty<String>` | `getJvmArgs()` (return type changed) |
| `jvmArgumentProviders` | `List<CommandLineArgumentProvider>` | `ListProperty<CommandLineArgumentProvider>` | `getJvmArgumentProviders()` (return type changed) |
| `maxHeapSize` | `String` | `Property<String>` | `getMaxHeapSize()` (return type changed) |
| `minHeapSize` | `String` | `Property<String>` | `getMinHeapSize()` (return type changed) |
| `systemProperties` | `Map<String, Object>` | `MapProperty<String, Object>` | `getSystemProperties()` (return type changed) |

**Migration examples:**

```groovy
task.debug.set(true)  // also: enableAssertions
task.debug.set(otherTask.debug)  // lazy wiring
task.defaultCharacterEncoding.set("value")  // also: maxHeapSize, minHeapSize
task.defaultCharacterEncoding.set(provider { computeValue() })
task.defaultCharacterEncoding.set(otherTask.defaultCharacterEncoding)  // lazy wiring
task.bootstrapClasspath.setFrom(configurations.someConfig)
task.bootstrapClasspath.setFrom(otherTask.bootstrapClasspath)  // lazy wiring
task.jvmArgs.add("item")  // also: jvmArgumentProviders
task.jvmArgs.addAll(otherTask.jvmArgs)  // lazy wiring
task.systemProperties.put("key", "value")
task.systemProperties.putAll(otherTask.systemProperties)  // lazy wiring

// Read-only (allJvmArgs) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.allJvmArgs)
```

---

### `org.gradle.process.ProcessForkOptions`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `environment` | `Map<String, Object>` | `MapProperty<String, Object>` | `getEnvironment()` (return type changed) |
| `executable` | `String` | `Property<String>` | `getExecutable()` (return type changed) |

**Migration examples:**

```groovy
task.executable.set("value")
task.executable.set(provider { computeValue() })
task.executable.set(otherTask.executable)  // lazy wiring
task.environment.put("key", "value")
task.environment.putAll(otherTask.environment)  // lazy wiring
```

---

### `org.gradle.testing.jacoco.plugins.JacocoPluginExtension`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `toolVersion` | `String` | `Property<String>` | `getToolVersion()` (return type changed) |

**Migration examples:**

```groovy
task.toolVersion.set("value")
task.toolVersion.set(provider { computeValue() })
task.toolVersion.set(otherTask.toolVersion)  // lazy wiring
```

---

### `org.gradle.testing.jacoco.plugins.JacocoTaskExtension`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `address` | `String` | `Property<String>` | `getAddress()` (return type changed) |
| `asJvmArg` | `String` | `Provider<String>` | `getAsJvmArg()` (return type changed) |
| `destinationFile` | `File` | `RegularFileProperty` | `setDestinationFile(Provider<File>)`, `getDestinationFile()` (return type changed) |
| `dumpOnExit` | `boolean` | `Property<Boolean>` | `isDumpOnExit()` |
| `enabled` | `boolean` | `Property<Boolean>` | `isEnabled()` |
| `excludeClassLoaders` | `List<String>` | `ListProperty<String>` | `getExcludeClassLoaders()` (return type changed) |
| `excludes` | `List<String>` | `ListProperty<String>` | `getExcludes()` (return type changed) |
| `includeNoLocationClasses` | `boolean` | `Property<Boolean>` | `isIncludeNoLocationClasses()` |
| `includes` | `List<String>` | `ListProperty<String>` | `getIncludes()` (return type changed) |
| `jmx` | `boolean` | `Property<Boolean>` | `isJmx()` |
| `output` | `JacocoTaskExtension$Output` | `Property<JacocoTaskExtension$Output>` | `getOutput()` (return type changed) |
| `port` | `int` | `Property<Integer>` | `getPort()` (return type changed) |
| `sessionId` | `String` | `Property<String>` | `getSessionId()` (return type changed) |

**Migration examples:**

```groovy
task.dumpOnExit.set(true)  // also: enabled, includeNoLocationClasses, jmx
task.dumpOnExit.set(otherTask.dumpOnExit)  // lazy wiring
task.address.set("value")  // also: port, sessionId
task.address.set(provider { computeValue() })
task.address.set(otherTask.address)  // lazy wiring
task.destinationFile.set(layout.buildDirectory.file("output.txt"))
task.destinationFile.set(otherTask.destinationFile)  // lazy wiring
task.excludeClassLoaders.add("item")  // also: excludes, includes
task.excludeClassLoaders.addAll(otherTask.excludeClassLoaders)  // lazy wiring
task.output.set(someValue)
task.output.set(otherTask.output)  // lazy wiring

// Read-only (asJvmArg) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.asJvmArg)
```

---

### `org.gradle.testing.jacoco.tasks.JacocoBase`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `jacocoClasspath` | `FileCollection` | `ConfigurableFileCollection` | `getJacocoClasspath()` (return type changed) |

**Migration examples:**

```groovy
task.jacocoClasspath.setFrom(configurations.someConfig)
task.jacocoClasspath.setFrom(otherTask.jacocoClasspath)  // lazy wiring
```

---

### `org.gradle.vcs.VersionControlRepository`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `rootDir` | `String` | `Property<String>` | `getRootDir()` (return type changed) |

**Migration examples:**

```groovy
task.rootDir.set("value")
task.rootDir.set(provider { computeValue() })
task.rootDir.set(otherTask.rootDir)  // lazy wiring
```

---

### `org.gradle.vcs.VersionControlSpec`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `repoName` | `String` | `Provider<String>` | `getRepoName()` (return type changed) |
| `rootDir` | `String` | `Property<String>` | `getRootDir()` (return type changed) |
| `uniqueId` | `String` | `Provider<String>` | `getUniqueId()` (return type changed) |

**Migration examples:**

```groovy
task.rootDir.set("value")
task.rootDir.set(provider { computeValue() })
task.rootDir.set(otherTask.rootDir)  // lazy wiring

// Read-only (repoName, uniqueId) — no .set(); pass the Provider to consumers:
otherTask.someInput.set(task.repoName)
```

---

### `org.gradle.vcs.git.GitVersionControlSpec`

| Property | Gradle 9.4 Type | Gradle 10 Type | Removed Accessors |
|----------|----------------|----------------|-------------------|
| `url` | `URI` | `Property<URI>` | `getUrl()` (return type changed) |

**Migration examples:**

```groovy
task.url.set(someValue)
task.url.set(otherTask.url)  // lazy wiring
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
| `task.getFoo()` → `FileCollection` | `task.foo.setFrom(source)` | Iterate in a task action |

> **Key principle**: `Property` extends `Provider`. Anywhere a `Provider<T>` is accepted, you can pass the `Property<T>` directly — no `.get()` needed. Reserve `.get()` for task actions and `doLast {}` blocks where you need the resolved value.
