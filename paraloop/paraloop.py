import inspect
import itertools
from multiprocessing import Process, Queue
from typing import Callable, Dict, Iterable, Optional, Sequence

import paraloop.worker as worker
from paraloop.syntax import LoopFinder, LoopTransformer
from paraloop.variable import Variable


class ParaLoop:
    """Wraps an iterable and executes its iterations in parallel over multiple
    processes."""

    def __init__(
        self, iterable: Iterable, length: Optional[int] = None, num_processes: int = 8
    ):
        self.iterable = iter(iterable)
        self.length = length
        if self.length is None and hasattr(iterable, "__len__"):
            self.length = len(iterable)
        # TODO: add auto mode where we take num cores - 1.
        self.num_processes = num_processes
        if self.num_processes < 2:
            raise ValueError(
                "Paraloop must use at least two worker processes! "
                f"The current configuration specifies only {num_processes}."
            )

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

        # Spawn process and distribute the work
        processes, result_queue = self._distribute_work(function, variables)
        # Wait for the results and aggregate them
        self._process_results(processes, result_queue, variables)
        return self

    def _distribute_work(self, function: Callable, variables: Dict):
        # Create queues to communicate with workers and spawn worker processes
        in_queue, out_queue = (Queue(), Queue())
        processes = []
        for i in range(self.num_processes):
            process = Process(
                target=worker.create_worker,
                args=(function, in_queue, out_queue, variables, i),
                name=f"worker_{i}",
            )
            processes.append(process)
            process.start()

        # Distribute the work over the workers
        for i, x in enumerate(self.iterable):
            # TODO: after a certain amount, check how many jobs have been completed so
            # we can display a progress bar.
            in_queue.put((i, x))

        # Signal them to stop once there are no more values to iterate over
        for _ in processes:
            in_queue.put((0, worker.Finished))

        return processes, out_queue

    def _process_results(
        self, processes: Sequence[Process], result_queue: Queue, variables: Dict
    ):
        # Wait for the results
        results = []
        for _ in processes:
            # TODO: add a timeout here in case one of the workers has crashed.
            result = result_queue.get(block=True)
            if isinstance(result, Exception):
                print("An error has occured in one of the workers!")
                raise result

            results.append(result)

        # print(results)

        for name, variable in variables.items():
            aggregated = variable.aggregation_strategy.aggregate(
                variable.wrapped, [result[name] for result in results]
            )
            variable.assign(aggregated)

    def __next__(self):
        # We already looped over the iterable ourselves, so we don't need to loop
        # over the original.
        raise StopIteration
