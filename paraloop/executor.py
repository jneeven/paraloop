import functools
import os
from concurrent.futures import (
    Future,
    ProcessPoolExecutor,
    TimeoutError,
    _base,
    as_completed,
)
from concurrent.futures.process import _ExceptionWithTraceback, _sendback_result
from typing import Callable, Dict, Sequence


class Finished(Future):
    """This specific class of Future will be used to signal the end of the iterator and
    to retrieve the results."""

    pass


def stub_function():
    pass


class ParaLoopExecutor(ProcessPoolExecutor):
    def __init__(self, function: Callable, variables: Dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.function = function
        self.variables = variables

    def get_max_workers(self):
        return self._max_workers

    def submit(self, fn, *args, **kwargs):
        """We pass a stub function, since the actual function is registered on the
        class.

        This removes the need for the function to be pickleable.
        """
        if isinstance(fn, functools.partial):
            fn = fn.args[0]

        if fn is not stub_function:
            raise TypeError(
                f"ParaLoopExecutor.submit() should only be called internally! Received "
                "an incorrect function argument. Try using map() instead."
            )
        return super().submit(stub_function, *args, **kwargs)

    def map(self, *iterables, timeout=None):
        """Same modifications as for self.submit, with an added call to
        self.get_results() to retrieve only the final results (the variables)."""
        iterator = super().map(stub_function, *iterables, timeout=timeout)
        # Loop through all the futures so that they'll be canceled correctly.
        # TODO: add optional progress bar here.
        try:
            for r in iterator:
                assert r is None  # We don't expect any return values here!
        except TimeoutError as e:
            # Trigger force shutdown of all workers
            self.shutdown(wait=False)
            # Hacky way to set an error message, the original has none.
            e.args = [
                f"One of the loop iterations took longer than the timeout of {timeout}s!"
            ]
            raise e

        # Signal that there won't be any further items, obtain thhe final results, and
        # and yield them.
        for f in as_completed(self.get_results()):
            yield f.result()

    def get_results(self) -> Sequence[Future]:
        # Signal the workers that no more items will be coming and request the results.
        futures = [
            self.submit(stub_function, Finished())
            for _ in range(self.get_max_workers())
        ]
        print(futures)
        return futures

    def shutdown(self, wait=True):
        # This code makes sure that all the worker processes close succesfully when
        # this is called.
        if not wait:
            for _ in range(self.get_max_workers()):
                self._call_queue.put_nowait(None)

        super().shutdown(wait)

    def _process_worker(self):
        """Hard-forked from concurrent.futures.python in order to access class variables
        and only return something once all iterations have finished."""
        if self._initializer is not None:
            try:
                self._initializer(*self._initargs)
            except BaseException:
                _base.LOGGER.critical("Exception in initializer:", exc_info=True)
                # The parent will notice that the process stopped and
                # mark the pool broken
                return
        while True:
            call_item = self._call_queue.get(block=True)
            if call_item is None:
                # Wake up queue management thread
                return self._result_queue.put(os.getpid())

            if len(call_item.args) == 1 and isinstance(call_item.args[0], Finished):
                print(f"{os.getpid()} done!")
                # When the iterator is depleted, return the variables with potential
                # local changes.
                _sendback_result(
                    self._result_queue, call_item.work_id, result=self.variables
                )
                # Wake up queue management thread
                return self._result_queue.put(os.getpid())

            try:
                self.function(*call_item.args, **call_item.kwargs)
            except BaseException as e:
                exc = _ExceptionWithTraceback(e, e.__traceback__)
                _sendback_result(self._result_queue, call_item.work_id, exception=exc)

            # Liberate the resource as soon as possible, to avoid holding onto
            # open files or shared memory that is not needed anymore
            del call_item

    def _adjust_process_count(self):
        # The only thing I've changed here is the target function.
        for _ in range(len(self._processes), self._max_workers):
            p = self._mp_context.Process(target=self._process_worker)
            p.start()
            self._processes[p.pid] = p
