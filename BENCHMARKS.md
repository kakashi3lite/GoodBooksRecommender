# Benchmarks

| Target | Command | Notes |
|--------|---------|-------|
| Frontend load | `npm run performance` | Uses `scripts/performance_analytics.py` for dashboard metrics |
| API response time | `python scripts/performance_analytics.py` | Goal: <200ms for `/recommendations` |
| News expansion latency | `pytest tests/news/test_news_expansion_comprehensive.py -k benchmark` | Expect <1s per article |

## Known Bottlenecks
- Cold-start model loading in `src/models/model_manager.py`
- Expensive news expansion when external APIs are slow

## Tips
- Warm Redis cache before load tests
- Use Node 18+ and Python 3.10+
