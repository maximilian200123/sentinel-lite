# B-03: path traversal probes before and after

`scripts/probes/b03_traversal.py`, in-process. A marker file sits next to `reports/`, where `instance/events.db` and `.env` sit in a real checkout. Run on Windows, which is why the backslash form (`%5c`) also works on the baseline.

## Before: `baseline-vulnerable`
```
/reports/daily.txt                        -> HTTP 200
/reports/..%2foutside-marker.txt          -> HTTP 200  LEAKED marker
/reports/..%5coutside-marker.txt          -> HTTP 200  LEAKED marker
/reports/%2e%2e%2foutside-marker.txt      -> HTTP 200  LEAKED marker
/reports/....%2f%2foutside-marker.txt     -> HTTP 404
```

## After: `fix/b-03-path-traversal`
```
/reports/daily.txt                        -> HTTP 200
/reports/..%2foutside-marker.txt          -> HTTP 404
/reports/..%5coutside-marker.txt          -> HTTP 404
/reports/%2e%2e%2foutside-marker.txt      -> HTTP 404
/reports/....%2f%2foutside-marker.txt     -> HTTP 404
```
