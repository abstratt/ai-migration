# Next Repositories to Migrate

Candidate Gradle projects for exercising the Gradle 9 → 10 Provider-API migration harness, with a checklist to track what we've tried.

**Selection criterion:** the harness only produces interesting results where a project's code touches a Gradle property whose **type changed** under the Provider API. Two categories maximize that signal:

- **Tier 1 — Gradle plugins**: use Gradle types in their *own* source, so changes surface as real compile errors in tasks 07/08 (densest Provider-API signal, fast builds).
- **Tier 2 — large multi-module builds**: heavier `buildSrc`/convention-plugin logic + the predictable preview-distro infra relaxations (exercises task 06).

**Cheap pre-screen:** clone a candidate and run `migration-reference/scan_usages.py` against it — `[CONFIRMED]` hits ⇒ real migration work; all-`[unconfirmed]` ⇒ likely a no-op (as `gradle-lint-plugin` turned out to be).

Legend: `[x]` = run completed (both distro pairs + comparison) · `[ ]` = not yet tried.

## Completed runs

- [x] [androidx/androidx](https://github.com/androidx/androidx) — [comparison](comparisons/COMPARISON-androidx-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md)
- [x] [elastic/elasticsearch](https://github.com/elastic/elasticsearch) — [comparison](comparisons/COMPARISON-elasticsearch-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md)
- [x] [gradle/gradle](https://github.com/gradle/gradle) — [comparison](comparisons/COMPARISON-gradle-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md)
- [x] [abstratt/gradle-lint-plugin](https://github.com/abstratt/gradle-lint-plugin) — [comparison](comparisons/COMPARISON-gradle-lint-plugin-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md) (no-op: 0 confirmed hits)
- [x] [apache/groovy](https://github.com/apache/groovy) — [comparison](comparisons/COMPARISON-groovy-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md)
- [x] [hibernate/hibernate-orm](https://github.com/hibernate/hibernate-orm) — [comparison](comparisons/COMPARISON-hibernate-orm-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md)
- [x] [junit-team/junit-framework](https://github.com/junit-team/junit-framework) — [comparison](comparisons/COMPARISON-junit-framework-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md)
- [x] [apache/kafka](https://github.com/apache/kafka) — [comparison](comparisons/COMPARISON-kafka-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md)
- [x] [kotest/kotest](https://github.com/kotest/kotest) — [comparison](comparisons/COMPARISON-kotest-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md)
- [x] [JetBrains/kotlin](https://github.com/JetBrains/kotlin) — [comparison](comparisons/COMPARISON-kotlin-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md)
- [x] [spring-projects/spring-boot](https://github.com/spring-projects/spring-boot) — [comparison](comparisons/COMPARISON-spring-boot-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md)
- [x] [spring-projects/spring-framework](https://github.com/spring-projects/spring-framework) — [comparison](comparisons/COMPARISON-spring-framework-g94-to-PAPI-20260204-vs-g951-to-PAPI-20260609.md)

## Tier 1 — Gradle plugins (densest Provider-API signal)

- [ ] [GradleUp/shadow](https://github.com/GradleUp/shadow) (formerly `johnrengelman/shadow`) — shadow-jar plugin; hammers `Jar`/archive/`CopySpec` APIs (`archiveFileName`, `destinationDirectory`) — exactly the lazified properties. **Top pick: fastest path to a non-trivial result.**
- [ ] [diffplug/spotless](https://github.com/diffplug/spotless) — many custom tasks/extensions on lazy properties; large, mature, Kotlin+Java. **Top pick.**
- [ ] [spotbugs/spotbugs-gradle-plugin](https://github.com/spotbugs/spotbugs-gradle-plugin) — modern, almost entirely `Property`/`Provider`-based; clean lazy-API stress test.
- [ ] [detekt/detekt](https://github.com/detekt/detekt) — Kotlin static-analysis plugin + multi-module build.
- [ ] [vanniktech/gradle-maven-publish-plugin](https://github.com/vanniktech/gradle-maven-publish-plugin) — publishing plugin; hits `MavenPom`/`RegularFileProperty` (the `GenerateMavenPom.getDestination()` `.map`→`.flatMap` case seen in the kotest run).
- [ ] [gradle-nexus/publish-plugin](https://github.com/gradle-nexus/publish-plugin) — same publishing-API surface, smaller.
- [ ] [micronaut-projects/micronaut-gradle-plugin](https://github.com/micronaut-projects/micronaut-gradle-plugin) — quick coverage.
- [ ] [node-gradle/gradle-node-plugin](https://github.com/node-gradle/gradle-node-plugin) — small, quick.
- [ ] [ben-manes/gradle-versions-plugin](https://github.com/ben-manes/gradle-versions-plugin) — small, quick.

## Tier 2 — large multi-module builds (task 06 + infra relaxations)

- [ ] [apache/beam](https://github.com/apache/beam) — huge build with a big custom `BeamModulePlugin` in `buildSrc`; strong build-script test (slow). **Top pick.**
- [ ] [ktorio/ktor](https://github.com/ktorio/ktor) — Kotlin Multiplatform, complex convention logic.
- [ ] [Kotlin/kotlinx.coroutines](https://github.com/Kotlin/kotlinx.coroutines) — KMP, convention-plugin heavy.
- [ ] [grpc/grpc-java](https://github.com/grpc/grpc-java) — protobuf plugin + lots of `Test`/`JavaCompile`/`Jar` configuration.
- [ ] [micronaut-projects/micronaut-core](https://github.com/micronaut-projects/micronaut-core) — large, convention-plugin heavy.

## Decided not to try

- [ ] ~~[netty/netty](https://github.com/netty/netty)~~ — Maven build, not Gradle.
- [ ] ~~[quarkusio/quarkus](https://github.com/quarkusio/quarkus)~~ — primarily Maven.
- [ ] ~~[google/guava](https://github.com/google/guava)~~ — Maven build.
- [ ] ~~[assertj/assertj](https://github.com/assertj/assertj)~~ — Maven build.
- [ ] ~~[JetBrains/intellij-community](https://github.com/JetBrains/intellij-community)~~ — JPS-based build, not a standard Gradle build.

_(Add rows here as we rule candidates out, with a one-line reason.)_
