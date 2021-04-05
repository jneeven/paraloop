from multiprocessing import Queue
from typing import Callable, Dict


class Finished:
    """Used to signal the workers that there is no more work to be done."""

    pass


class Worker:
    """Worker process used to execute the loop iterations assigned to it.

    Inputs and results are communicated through the specified Queues. Any exceptions
    will be passed to the master process.
    """

    def __init__(
        self,
        function: Callable,
        in_queue: Queue,
        out_queue: Queue,
        variables: Dict,
        id: int,
    ):
        self.function = function
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.variables = variables
        self.id = id

        self.done = False

    def start(self):
        while not self.done:
            try:
                # TODO: we probably want to cache a few items at a time so we don't need to
                # wait for the queue lock.
                index, args = self.in_queue.get()
                if args is Finished:
                    self.out_queue.put(self.variables)
                    self.done = True
                    return

                if isinstance(args, (list, tuple)):
                    self.function(*args)
                else:
                    self.function(args)
            except Exception as e:
                # Pass exception on to the master process.
                self.out_queue.put(e)
                return


def create_worker(*args, **kwargs):
    worker = Worker(*args, **kwargs)
    worker.start()
