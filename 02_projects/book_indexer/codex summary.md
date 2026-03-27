Task: Add logging for indexing results.

Context:
We have a file indexer with incremental behavior and safe cleanup already implemented.

Architecture:

* scan → build → storage
* Do NOT mix layers

Current behavior:

* build_book skips unchanged files (size + mtime)
* storage uses last_seen + cleanup (mark-and-sweep)
* mark_seen_bulk ensures all scanned files are marked

Goal:
Add logging summary after indexing.

Output example:
+2 added
~1 updated
-1 removed
=5 unchanged

Definitions:

* added: new records inserted
* updated: existing records changed (mtime/size)
* removed: deleted by cleanup
* unchanged: skipped files

Constraints:

* DO NOT break incremental logic
* DO NOT refactor architecture
* MINIMAL changes only
* Prefer implementing inside storage layer + returning stats to CLI

Focus on correctness and clarity.
