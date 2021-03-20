from abc import ABC, abstractclassmethod


class AggregationStrategy(ABC):
    @abstractclassmethod
    def aggregate(original, new_values):
        pass

    def is_compatible(object):
        """Check if the object is compatible with this aggregation strategy."""
        return True


class Sum(AggregationStrategy):
    def aggregate(original, new_values):
        return original + sum([value - original for value in new_values])

    def is_compatible(object):
        # TODO: find a better way to figure out if this is a number, including e.g.
        # numpy arrays.
        if isinstance(object, dict):
            return False
        return True
