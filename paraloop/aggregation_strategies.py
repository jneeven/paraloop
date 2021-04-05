import collections.abc as cabc
from abc import ABC, abstractclassmethod
from itertools import chain
from numbers import Number
from typing import Any, Sequence

import numpy as np


class AggregationStrategy(ABC):
    @abstractclassmethod
    def aggregate(original: Any, new_values: Sequence[Any]) -> Any:
        """Given the original value and a sequence of new values, return an aggregated
        result value."""
        pass

    def is_compatible(object: Any) -> bool:
        """Check if the object is compatible with this aggregation strategy."""
        return True


class Sum(AggregationStrategy):
    """Sums the cross-process results and the original value, subtracting the original
    from each result to replicate single-process behaviour. In case the aggregated
    object is a mapping, keys that didn't exist on the original object will be created.

    Currently supports any default Python or Numpy number type and mappings of these
    types.
    """

    def aggregate(original: Any, new_values: Sequence[Any]) -> Any:
        # Special Mapping case
        if isinstance(original, cabc.Mapping):
            summed = new_values[0]
            for result in new_values[1:]:
                for k, v in result.items():
                    if k in summed:
                        summed[k] += v
                    else:
                        summed[k] = v

            return summed

        # Default case
        return original + sum([value - original for value in new_values])

    def is_compatible(object: Any) -> bool:
        if isinstance(object, cabc.Mapping):
            if len(object.keys()) != 0:
                raise TypeError(
                    "Can't use `Sum` as an aggregation strategy for objects of "
                    "type `Mapping` with non-empty initialization!"
                )
        elif isinstance(object, np.ndarray):
            if not np.issubdtype(object.dtype, np.number):
                raise TypeError(
                    "Aggregation strategy `Sum` does not support numpy arrays with type"
                    f" `{object.dtype}`!"
                )
        elif not isinstance(object, (Number, np.number)):
            raise TypeError(
                f"Aggregation strategy `Sum` currently does not support objects of type {type(object)}."
            )
        return True


class Concatenate(AggregationStrategy):
    """Concatenates the mappings, collections or `np.ndarray`s obtained from each worker
    process.

    The wrapped variable must be empty upon initialization. If the aggregated object is
    a mapping, an error will be thrown if duplicate keys are encountered with different
    values. Note: this does not preserve ordering!
    """

    def aggregate(original: Any, new_values: Sequence[Any]) -> Any:
        # Special Mapping case
        if isinstance(original, cabc.Mapping):
            aggregated = new_values[0]
            for result in new_values[1:]:
                for k, v in result.items():
                    if k in aggregated and v != aggregated[k]:
                        raise ValueError(
                            f"Key {k} was returned by multiple workers, but with "
                            "different values!"
                        )
                    aggregated[k] = v

            return aggregated

        if isinstance(original, np.ndarray):
            return np.concatenate(new_values, axis=0)

        if isinstance(original, cabc.Collection):
            return original.__class__(chain(*new_values))

        raise NotImplementedError(
            f"Aggregation strategy `Concatenate` does not (yet) support type {type(original)}! "
            "This error should never be thrown, did you modify the type of your Variable "
            "after initializing it?"
        )

    def is_compatible(object: Any) -> bool:
        non_empty_error = (
            "Can't use `Concatenate` as an aggregation strategy for objects "
            "with non-empty initialization!"
        )
        if isinstance(object, cabc.Mapping) and len(object.keys()) != 0:
            raise TypeError(non_empty_error)
        elif isinstance(object, (cabc.Collection, np.ndarray)) and len(object) != 0:
            raise TypeError(non_empty_error)

        if not isinstance(object, (cabc.Collection, cabc.Mapping, np.ndarray)):
            raise TypeError(
                f"Aggregation strategy `Concatenate` doesn't support object type {type(object)}!"
            )

        return True
