from git_utils.util import LazySet


def range_and_raise(*args):
    for item in range(*args):
        yield item
    raise Exception


def test_lazy_set():
    xs = LazySet(range_and_raise(3))
    assert 2 in xs
    assert 1 in xs
