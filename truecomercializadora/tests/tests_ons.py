from unittest import TestCase

from truecomercializadora import ons

def test_get_semanas_operativas():
    s = ons.get_semanas_operativas(2020,2)
    assert isinstance(s, list)

