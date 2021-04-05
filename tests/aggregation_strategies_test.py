import numpy as np
import pytest

from paraloop.aggregation_strategies import Concatenate, Sum


class TestSum:
    def test_compatible(self):
        for object in [0, {}, np.zeros(3)]:
            assert Sum.is_compatible(object)
        for object in [{"test": 1}, None, [], tuple(), np.array(["string"])]:
            with pytest.raises(TypeError):
                Sum.is_compatible(object)

    def test_agregation(self):
        # Plain numeral, 5 + (2 + 4.5 + 3)
        assert Sum.aggregate(5.0, [7.0, 9.5, 8.0]) == 14.5

        # Dictionary
        assert Sum.aggregate({}, [{"k1": 1, "k2": 3}, {"k1": 1, "k3": 4}]) == {
            "k1": 2,
            "k2": 3,
            "k3": 4,
        }

        # Numpy array
        assert np.all(
            Sum.aggregate(
                np.ones(5), [np.array([1, 2, 3, 4, 5]), np.array([2, 3, 4, 5, 6])]
            )
            == [2, 4, 6, 8, 10]
        )


class TestConcatenate:
    def test_compatible(self):
        for object in [{}, [], tuple(), np.array([])]:
            assert Concatenate.is_compatible(object)
        for object in [{"test": 1}, None, np.array(["string"]), np.zeros(3)]:
            with pytest.raises(TypeError):
                Concatenate.is_compatible(object)

    def test_agregation(self):
        # List
        assert Concatenate.aggregate([], ([3, 4], [5, 6], [6, 7])) == [3, 4, 5, 6, 6, 7]

        # Tuple
        assert Concatenate.aggregate(tuple(), [(True, False), (False, False)]) == (
            True,
            False,
            False,
            False,
        )

        # Dictionary
        assert Concatenate.aggregate(
            {}, ({"key1": True, "key2": False}, {"key2": False, "key3": 4})
        ) == {"key1": True, "key2": False, "key3": 4}

        with pytest.raises(ValueError, match="different values"):
            Concatenate.aggregate({}, [{"key1": 0}, {"key1": 1}])

        # Numpy array
        first = np.ones((5, 10))
        second = np.ones((3, 10)) * 2
        agg = Concatenate.aggregate(np.array([]), [first, second])
        assert np.all(agg == np.concatenate([first, second]))
