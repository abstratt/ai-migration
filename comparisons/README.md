# Migration comparisons

This folder collects comparisons between different migration runs for the same repository.

Comparing relies exclusively on inspecting the MIGRATION_NOTES.md and REPORT-<timestamp>.md files. 

Comparisons should:
- show the repository migrated (with link)
- show a table with a column for each migration run:
  - the branches compared (with links)
  - links to the reports and migration notes for each migration
  - the distro pairs
  - the number of files and lines changed
  - whether the migration succeeded
Note that the columns should be ordered by distro pair name.

Comparison results should be stored in files named COMPARISON-<repository-name>-<distro-pair-1>-vs-<distro-pair-2>.md.

If a comparison file with the required name already exists, replace the file.

Note:
- Never inspect local state of the repositories migrated, rely uniquely on GIT URL provided by the user.
- Do not make observations about the quality of the migration (other than succeeded/failed status). We only care about the number of changes (files and lines). 