import pytest

from pymdtools.common import Constant


class TestConstant:
    def test_constant_access_via_class(self):
        class A:
            X = Constant(42)

        assert A.X == 42

    def test_constant_access_via_instance(self):
        class A:
            X = Constant("value")

        a = A()
        assert a.X == "value"

    def test_constant_value_property(self):
        c = Constant(10)
        assert c.value == 10

    def test_constant_cannot_be_modified_on_instance(self):
        class A:
            X = Constant(1)

        a = A()
        with pytest.raises(ValueError):
            a.X = 2

    def test_constant_can_be_shadowed_on_class_assignment(self):
        class A:
            X = Constant(1)

        A.X = 2
        assert A.X == 2

    def test_constant_cannot_be_deleted(self):
        class A:
            X = Constant(1)

        a = A()
        with pytest.raises(ValueError):
            del a.X
