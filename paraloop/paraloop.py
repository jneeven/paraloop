import inspect

from paraloop.syntax import LoopFinder, LoopTransformer


class ParaLoop:
    """Wraps an iterable and executes its iterations in parallel over multiple
    processes."""

    def __init__(self, iterable, length=None):
        self.iterable = iter(iterable)
        self.length = length or len(iterable)
        self.index = 0

    def __iter__(self):
        # Find the source code of the calling loop and transform it into a function
        caller = inspect.stack()[1]
        loop_source = LoopFinder(caller.lineno, filename=caller.filename).find_loop()
        function = LoopTransformer(
            loop_source, caller.frame.f_globals, caller.frame.f_locals
        ).build_loop_function()

        function(3)

        # TODO: perform initialization of the processes
        return self

    def __next__(self):
        # return next(self.iterable)
        raise StopIteration
