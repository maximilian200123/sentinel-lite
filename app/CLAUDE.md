# app/: module conventions

Loaded in addition to the root `CLAUDE.md` when working in this folder.

- `__init__.py` holds the app factory and routes only. Logic lives in `pipeline.py`, `store.py`,
  `rules.py`, `intel.py`, and routes call it.
- `pipeline.py` steps take and return the event dict (`normalize -> enrich -> detect`). A new
  enrichment is a new step, not a branch inside an existing one.
- `store.py` is the only module that touches SQLite. Every query uses `?` placeholders.
- `config.py` reads settings from the environment once, in `load_settings()`. Nothing else reads
  `os.environ`.
- Every request handler must return JSON or a 4xx for bad input, never a 500 for something a
  client sent.
