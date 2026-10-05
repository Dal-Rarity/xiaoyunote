from ai_app.services.cache import fingerprint


def test_fingerprint_deterministic():
    a = fingerprint("三体", ["x1", "x2"])
    b = fingerprint("三体", ["x2", "x1"])
    assert a == b


def test_fingerprint_differs_by_question():
    assert fingerprint("三体", ["x1"]) != fingerprint("活着", ["x1"])


def test_fingerprint_differs_by_chunks():
    assert fingerprint("三体", ["x1"]) != fingerprint("三体", ["x2"])