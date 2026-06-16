The repository to migrate is: $ARGUMENTS

Run the full migration workflow in **brute-force mode**: treat `SKIP_BUILD_SCRIPTS` as set, so task 06 (build-script migration) is skipped entirely. Instead, ensure no `MIGRATION_NOTES.md` exists (`@tasks/06-skip-build-scripts.md`), then go straight to verification (07, 08) and reporting (09) — letting those tasks fix every build error from scratch, with no data-driven scaffolding.

@MIGRATION.md
