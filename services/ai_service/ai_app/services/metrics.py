"""
进程内指标：requests / refused / cache_hit / 耗时
单进程部署够用；生产多 worker 需换 Prometheus 或 Redis
"""
from collections import deque

_MAX_LAT = 1000

_counters = {"requests": 0, "refused": 0, "cache_hit": 0, "errors": 0}
_latencies: deque[float] = deque(maxlen=_MAX_LAT)


def record(elapsed_ms: float, refused: bool = False, cache_hit: bool = False, error: bool = False):
    _counters["requests"] += 1
    if refused:
        _counters["refused"] += 1
    if cache_hit:
        _counters["cache_hit"] += 1
    if error:
        _counters["errors"] += 1
    _latencies.append(elapsed_ms)


def _pct(sorted_list: list[float], p: int) -> float:
    if not sorted_list:
        return 0.0
    k = int(len(sorted_list) * p / 100)
    k = min(k, len(sorted_list) - 1)
    return round(sorted_list[k], 2)


def snapshot() -> dict:
    reqs = _counters["requests"]
    lat = sorted(_latencies)
    return {
        "requests": reqs,
        "refused": _counters["refused"],
        "cache_hit": _counters["cache_hit"],
        "errors": _counters["errors"],
        "refusal_rate": round(_counters["refused"] / reqs, 4) if reqs else 0,
        "cache_hit_rate": round(_counters["cache_hit"] / reqs, 4) if reqs else 0,
        "p50_ms": _pct(lat, 50),
        "p95_ms": _pct(lat, 95),
        "p99_ms": _pct(lat, 99),
    }


def reset():
    """测试用"""
    _counters.update({"requests": 0, "refused": 0, "cache_hit": 0, "errors": 0})
    _latencies.clear()