import pytest
from ai_self_ext_engine.simple_test_module import add_one

def test_add_one():
    assert add_one(1) == 2
    assert add_one(0) == 1
    assert add_one(-1) == 0
