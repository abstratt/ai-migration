# Task: Swap Gradle Distribution

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- Gradle version is 9.x (either already was, or upgraded by the previous task)
- JAVA_HOME is set to a working JDK

## Resume check

1. Read `gradle/wrapper/gradle-wrapper.properties`
2. If `distributionUrl` already points to `https://github.com/asodja/gradle-dev-distributions/releases/download/v1.1.0/gradle-provider-api-20260204140400.zip`, this task is already complete
3. Also check `git log` for a commit message matching "Update Gradle distribution"

## Instructions

1. Edit `gradle/wrapper/gradle-wrapper.properties` to set:
   ```
   distributionUrl=https://github.com/asodja/gradle-dev-distributions/releases/download/v1.1.0/gradle-provider-api-20260204140400.zip
   ```
   Also remove `distributionSha256Sum` if present, and set `validateDistributionUrl=false`.

2. Validate with `./gradlew help` **only** to ensure Gradle actually runs. The build will probably fail — do not do anything about it yet.

3. **Commit**: present tense message (e.g. "Update Gradle distribution to custom Provider API build")

## Done when

- `gradle-wrapper.properties` points to the custom Provider API distribution
- `distributionSha256Sum` is removed (if it was present)
- `validateDistributionUrl=false` is set
- `./gradlew help` was run (it may fail — that's expected)
- Changes are committed
