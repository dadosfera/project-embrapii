from backend.cache import TTLCache


def test_cache_hit_e_expira():
    now = [0.0]
    c = TTLCache(ttl=10, clock=lambda: now[0])
    calls = []

    def load():
        calls.append(1)
        return [1]

    assert c.get_or_load(("k",), load) == [1]
    assert c.get_or_load(("k",), load) == [1]
    assert len(calls) == 1
    now[0] = 11
    c.get_or_load(("k",), load)
    assert len(calls) == 2


def test_ttl_zero_desliga():
    c = TTLCache(ttl=0)
    calls = []
    c.get_or_load(("k",), lambda: calls.append(1))
    c.get_or_load(("k",), lambda: calls.append(1))
    assert len(calls) == 2
