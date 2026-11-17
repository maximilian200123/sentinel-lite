# B-04: a Python-tagged rule file, before and after

`scripts/probes/b04_yaml.py`, in-process. The payload is `os.makedirs` of a marker folder in a temp dir (harmless). If the folder exists afterwards, loading the YAML ran Python.

## Before: `baseline-vulnerable`
```
[2026-11-17 19:50:06,376] ERROR in app: Exception on /admin/rules/reload [POST]
TypeError: 'NoneType' object is not subscriptable
rules active before: {'loaded': ['SL-0002', 'SL-0001']}
rule file: !!python/object/apply:os.makedirs ["<tmp>/B04-MARKER"]
reload -> HTTP 500 {}
marker folder created (Python code ran): True
detection still working after the reload attempt: True
```

## After: `fix/b-04-safe-yaml`
```
rules reload refused, keeping 2 active rules: evil.yaml: not plain YAML data (ConstructorError)
rules active before: {'loaded': ['SL-0002', 'SL-0001']}
rule file: !!python/object/apply:os.makedirs ["<tmp>/B04-MARKER"]
reload -> HTTP 400 {'error': 'evil.yaml: not plain YAML data (ConstructorError)'}
marker folder created (Python code ran): False
detection still working after the reload attempt: True
```
