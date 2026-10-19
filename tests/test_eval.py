import pandas as pd

from evaluation.run_eval import matches


def test_matches_ignores_extra_columns():
    expected = pd.Series({"a": 5.0})
    actual = pd.DataFrame({"name": ["a"], "total": [5.0], "extra": [1]})
    assert matches(expected, actual)


def test_matches_rejects_wrong_number():
    assert not matches(5.0, pd.DataFrame({"value": [9.0]}))


def test_matches_rejects_wrong_label():
    expected = pd.Series({"a": 5.0})
    assert not matches(expected, pd.DataFrame({"name": ["b"], "total": [5.0]}))
