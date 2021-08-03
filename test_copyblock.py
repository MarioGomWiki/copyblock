from copyblock import *


def test_is_ip():
    assert is_ip("127.0.0.1")
    assert is_ip("::1")
    assert not is_ip("Foo")
