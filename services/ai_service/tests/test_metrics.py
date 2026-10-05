from ai_app.services import metrics


def test_metrics_record_and_snapshot():
    metrics.reset()
    metrics.record(100, refused=False, cache_hit=False)
    metrics.record(200, refused=True)
    metrics.record(150, cache_hit=True)

    snap = metrics.snapshot()
    assert snap["requests"] == 3
    assert snap["refused"] == 1
    assert snap["cache_hit"] == 1
    assert 0 < snap["refusal_rate"] < 1
    assert snap["p50_ms"] > 0
    assert snap["p95_ms"] >= snap["p50_ms"]