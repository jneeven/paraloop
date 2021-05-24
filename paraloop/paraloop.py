import inspect
import itertools
from typing import Dict, Iterable, Optional, Sequence

from paraloop.executor import ParaLoopExecutor
from paraloop.syntax import LoopFinder, LoopTransformer
from paraloop.variable import Variable


class ParaLoop:
    """Wraps an iterable and executes its iterations in parallel over multiple
    processes."""

    def __init__(
        self,
        iterable: Iterable,
        max_workers: Optional[int] = None,
        iteration_timeout: Optional[int] = None,
    ):
        self.iterable = iter(iterable)
        self.max_workers = max_workers
        self.iteration_timeout = iteration_timeout

    def __iter__(self):
        # Find the source code of the calling loop and transform it into a function
        caller = inspect.stack()[1]
        loop_source = LoopFinder(caller.lineno, filename=caller.filename).find_loop()
        function = LoopTransformer(
            loop_source, caller.frame.f_globals, caller.frame.f_locals
        ).build_loop_function()

        # Keep track of the Variables that need to be aggregated properly
        variables = {
            key: value
            for key, value in itertools.chain(
                caller.frame.f_locals.items(), caller.frame.f_globals.items()
            )
            if isinstance(value, Variable)
        }
        executor = ParaLoopExecutor(function, variables, max_workers=self.max_workers)
        # Wait for the results and aggregate them
        self._process_results(
            executor.map(self.iterable, timeout=self.iteration_timeout), variables
        )
        return self

    def _process_results(self, results: Sequence[Dict], variables: Dict):
        for name, variable in variables.items():
            aggregated = variable.aggregation_strategy.aggregate(
                variable.wrapped, [result[name] for result in results]
            )
            variable.assign(aggregated)

    def __next__(self):
        # We already looped over the iterable ourselves, so we don't need to loop
        # over the original.
        raise StopIteration
