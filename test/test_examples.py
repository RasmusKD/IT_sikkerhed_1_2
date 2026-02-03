import pytest


def test_pass():
    # Denne test vil passere
    assert 1 + 1 == 2


def test_fail():
    # Denne test vil fejle
    assert 1 * 1 == 3


@pytest.mark.skip(reason="Springes over med vilje")  # Denne test bliver slet ikke kørt
def test_skip():
    assert False  # failed test bliver ignoreret
    raise RuntimeError("Test crashede med vilje")  # crash bliver også ignoreret


def test_crash():
    # Denne test crasher med en exception
    raise RuntimeError("Test crashede med vilje")

    assert False  # failed test bliver ignoreret
