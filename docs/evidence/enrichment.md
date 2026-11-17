# R-10: enrichment changes the outcome

In-process, against the shipped local feed (`data/intel_feed.json`, RFC 5737 documentation IPs) and the shipped rules. The same event is sent from a clean source and from a feed IP.

```
clean source         src=10.0.0.20     risk_score=10   tags=[]
feed IP              src=203.0.113.66  risk_score=60   tags=['threat.indicator.matched']
                     threat.indicator={"description": "SSH brute-force source seen across sensor fleet", "ip": "203.0.113.66", "provider": "local-feed"}
feed IP + SSH rule   src=203.0.113.66  risk_score=90   tags=['threat.indicator.matched', 'rule:SL-0001']
                     threat.indicator={"description": "SSH brute-force source seen across sensor fleet", "ip": "203.0.113.66", "provider": "local-feed"}
GET /intel/check?ip=203.0.113.66 -> {'ip': '203.0.113.66', 'matched': True, 'tag': 'threat.indicator.matched'}
```

Without enrichment both events would score 10 and sit side by side in the queue. With it, the feed IP scores 60, and 90 once the SSH rule also fires. It carries `threat.indicator`, so an analyst sees why. The behaviour is pinned by `tests/test_app.py::test_enrichment_changes_the_outcome`.
