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

    def load():
        calls.append(1)
        return len(calls)

    assert c.get_or_load(("k",), load) == 1
    assert c.get_or_load(("k",), load) == 2
    assert len(calls) == 2


def test_cache_limita_numero_de_entradas_e_descarta_a_mais_antiga():
    now = [0.0]
    c = TTLCache(ttl=1000, clock=lambda: now[0], max_entries=2)

    assert c.get_or_load(("a",), lambda: "va") == "va"
    assert c.get_or_load(("b",), lambda: "vb") == "vb"
    assert len(c._data) == 2

    assert c.get_or_load(("c",), lambda: "vc") == "vc"
    assert len(c._data) == 2
    assert ("a",) not in c._data
    assert ("c",) in c._data

    # "a" foi descartada: recarrega em vez de servir do cache.
    calls = []
    assert c.get_or_load(("a",), lambda: calls.append(1) or "va2") == "va2"
    assert len(calls) == 1
