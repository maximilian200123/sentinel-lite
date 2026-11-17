# B-05: malformed and oversized bodies, before and after

`scripts/probes/b05_input.py`, in-process. The same nine bodies are sent to `POST /ingest` with a valid key. A 500 means the app trusted the input. A 201 for a bad body means garbage was stored.

## Before: `baseline-vulnerable`
```
valid event        -> HTTP 201
array body         -> HTTP 500
not JSON           -> HTTP 400
missing fields     -> HTTP 500
bad timestamp      -> HTTP 500
bad IP             -> HTTP 201
number as message  -> HTTP 201
object as user     -> HTTP 500
2 MB message       -> HTTP 201
```

## After: `fix/b-05-input-validation`
```
valid event        -> HTTP 201
array body         -> HTTP 400
not JSON           -> HTTP 400
missing fields     -> HTTP 400
bad timestamp      -> HTTP 400
bad IP             -> HTTP 400
number as message  -> HTTP 400
object as user     -> HTTP 400
2 MB message       -> HTTP 413
```
