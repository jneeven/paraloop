from abc import ABC, abstractclassmethod


class AggregationStrategy(ABC):
    @abstractclassmethod
    def aggregate(values):
        pass

    def is_compatible(object):
        """Check if the object is compatible with this aggregation strategy."""
        return True


class Sum(AggregationStrategy):
    def aggregate(values):
        return sum(values)

    def is_compatible(object):
        if isinstance(object, dict):
            return False
        return True
