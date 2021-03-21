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
        # Special dictionary case
        if isinstance(original, dict):
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

    def is_compatible(object):
        # TODO: find a better way to figure out if this is a number, including e.g.
        # numpy arrays.
        if isinstance(object, dict):
            if len(object.keys()) != 0:
                raise TypeError(
                    "Can't use paraloop.Sum as an aggregation strategy for dictionaries "
                    "with non-empty initialization!"
                )
        return True


"""
TODO:
- implement append (for sequences), merge (for collections) and average (for numbers and sequences thereof)
"""
