# B-02: the same SQL injection probes before and after

`scripts/probes/b02_sqli.py` runs in-process against the app with two stored events (alice, bob) and sends three
`user` values to `GET /events/search`. The UNION payload asks the database for its own version,
which proves arbitrary SELECTs, not just a widened filter.

## Before: `baseline-vulnerable`
```
user='alice'
  -> HTTP 200, count=1, user.name values=['alice']
user="x' OR '1'='1"
  -> HTTP 200, count=2, user.name values=['alice', 'bob']
user="x' UNION SELECT json_object('user', json_object('name', sqlite_version())) --"
  -> HTTP 200, count=1, user.name values=['3.45.3']
```

## After: `fix/b-02-sql-injection`
```
user='alice'
  -> HTTP 200, count=1, user.name values=['alice']
user="x' OR '1'='1"
  -> HTTP 200, count=0, user.name values=[]
user="x' UNION SELECT json_object('user', json_object('name', sqlite_version())) --"
  -> HTTP 200, count=0, user.name values=[]
```
