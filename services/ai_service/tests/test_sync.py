from ai_app.services.vector_store import point_id


def test_point_id_deterministic():
    assert point_id(1, "article", 10, 0) == point_id(1, "article", 10, 0)


def test_point_id_differs_by_user():
    assert point_id(1, "article", 10, 0) != point_id(2, "article", 10, 0)


def test_point_id_differs_by_type():
    assert point_id(1, "article", 10, 0) != point_id(1, "favorite", 10, 0)


def test_point_id_differs_by_source():
    assert point_id(1, "comment", 10, 0, 1) != point_id(1, "comment", 10, 0, 2)