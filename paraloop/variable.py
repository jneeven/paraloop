from typing import Any

operators = [
    "__abs__",
    "__add__",
    "__and__",
    "__bool__",
    "__ceil__",
    "__divmod__",
    "__eq__",
    "__float__",
    "__floor__",
    "__floordiv__",
    "__format__",
    "__ge__",
    "__gt__",
    "__iadd__",
    "__imul__",
    "__int__",
    "__invert__",
    "__le__",
    "__lshift__",
    "__lt__",
    "__mod__",
    "__mul__",
    "__ne__",
    "__neg__",
    "__or__",
    "__pos__",
    "__pow__",
    "__radd__",
    "__rand__",
    "__rdivmod__",
    "__rfloordiv__",
    "__rlshift__",
    "__rmod__",
    "__rmul__",
    "__ror__",
    "__round__",
    "__rpow__",
    "__rrshift__",
    "__rshift__",
    "__rsub__",
    "__rtruediv__",
    "__rxor__",
    "__sub__",
    "__truediv__",
    "__trunc__",
    "__xor__",
]


def wrap_operators(cls):
    """This decorator registers each of the methods defined in `operators` above by
    simply forwarding the call to the `cls.wrapped` variable.

    This is necessary because these methods must be registered on the class, not on the
    instance, for operator overloading to work.
    """
    for operator in operators:
        setattr(
            cls,
            operator,
            lambda self, *args, **kwargs: getattr(self.wrapped, operator)(
                *args, **kwargs
            ),
        )
    return cls


@wrap_operators
class Variable:
    """Wraps any kind of variable and specifies how to aggregate it over the different
    processes."""

    __paraloop_attributes__ = set(["wrapped", "id", "__repr__"])

    def __init__(self, wrapped: Any) -> None:
        self.wrapped = wrapped

    def __getattribute__(self, name: str) -> Any:
        """Wrap all non-paraloop attributes automatically."""
        if name == "__paraloop_attributes__" or name in self.__paraloop_attributes__:
            return super().__getattribute__(name)
        return self.wrapped.__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Wrap all non-paraloop attributes automatically."""
        if name == "__paraloop_attributes__" or name in self.__paraloop_attributes__:
            return super().__setattr__(name, value)
        if name.startswith("__"):
            raise ValueError("You probably don't want to do this!")
        return self.wrapped.__setattr__(name, value)

    def __repr__(self):
        return f"paraloop.Variable({self.wrapped})"
