"""
Udvidede tests - inspireret af test_examples.py
"""
import pytest


def test_pass_udvidet():
    # Denne test vil også passere
    assert 2 + 2 == 4


def test_fail_udvidet():
    # Denne test vil fejle
    assert 5 - 2 == 10


@pytest.mark.skip(reason="Under udvikling")
def test_skip_udvidet():
    # Denne test springes over
    assert True
