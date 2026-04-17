# Task: Swap Gradle Distribution

@tasks/CONTEXT.md

## Preconditions

- Clone directory exists with the fork checked out on the migration branch
- Gradle version is 9.x (either already was, or upgraded by the previous task)
- JAVA_HOME is set to a working JDK

## Gradle execution authorized

This task requires running Gradle commands (`./gradlew`). Gradle execution and distribution downloads are pre-authorized for this task.

## Resume check

1. Read `gradle/wrapper/gradle-wrapper.properties`
2. If `distributionUrl` already points to `https://github.com/asodja/gradle-dev-distributions/releases/download/v1.1.0/gradle-provider-api-20260204140400.zip`, this task is already complete
3. Also check `git log` for a commit message matching "Swap Gradle Distribution" (the task title)

## Instructions

1. Edit `gradle/wrapper/gradle-wrapper.properties` to set:
   ```
   distributionUrl=https://github.com/asodja/gradle-dev-distributions/releases/download/v1.1.0/gradle-provider-api-20260204140400.zip
   ```
   Also remove `distributionSha256Sum` if present, and set `validateDistributionUrl=false`.

2. Run `./gradlew help` **once** to confirm that the custom distribution downloads and Gradle starts up. That is the only goal here.

   **Success criterion is invocation, not build success.** The build is expected to fail at this point. As long as the wrapper was able to fetch the distribution and Gradle began executing (you see Gradle output, configuration starts, etc.), this step is done — even if `./gradlew help` exits non-zero.

   Do **not**:
   - Re-run `./gradlew` to see if it passes
   - Try to fix build errors, deprecation warnings, or configuration failures reported by this run
   - Iterate on any output from this command
   - Run any other Gradle task (`assemble`, `build`, `tasks`, etc.)

   Fixing the build is the job of task 04 (static transformations) followed by tasks 05 and 06 (validation and iteration).

3. **Commit**: use the task title "Swap Gradle Distribution" as the commit message subject — include the `Assistant:` trailer (see CONTEXT.md)

## Done when

- `gradle-wrapper.properties` points to the custom Provider API distribution
- `distributionSha256Sum` is removed (if it was present)
- `validateDistributionUrl=false` is set
- `./gradlew help` was invoked exactly once, the distribution downloaded, and Gradle started executing (pass/fail of the `help` task itself is irrelevant)
- Changes are committed
