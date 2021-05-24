# pytype: skip-file

import time
from collections import defaultdict

import wikipedia  # pip install wikipedia

from paraloop import ParaLoop, Variable
from paraloop.aggregation_strategies import Sum


def wikipedia_names():
    return wikipedia.search("Python", results=20)[1:]


def original_code():
    frequencies = defaultdict(int)
    total = 0

    start = time.time()
    for name in wikipedia_names():
        try:
            content = wikipedia.page(name).content
        except (
            wikipedia.exceptions.DisambiguationError,
            wikipedia.exceptions.PageError,
        ):
            continue
        for line in content.splitlines():
            words = line.split(" ")
            for word in words:
                frequencies[word] += 1
                total += 1

    # We don't print the entire dictionary because it is too large, but let's just check
    # how many words we found.
    print(len(frequencies), total)
    print(f"The original loop took {time.time() - start} seconds.")


def paraloop_code():
    frequencies = Variable(defaultdict(int), aggregation_strategy=Sum)
    total = Variable(0, aggregation_strategy=Sum)

    start = time.time()
    # Note that the content of the loop is identical!
    for name in ParaLoop(wikipedia_names(), iteration_timeout=2):
        try:
            content = wikipedia.page(name).content
        except (
            wikipedia.exceptions.DisambiguationError,
            wikipedia.exceptions.PageError,
        ):
            continue
        for line in content.splitlines():
            words = line.split(" ")
            for word in words:
                frequencies[word] += 1
                total += 1

    # We don't print the entire dictionary because it is too large, but let's just check
    # how many words we found.
    print(len(frequencies), total)
    print(f"The ParaLoop took {time.time() - start} seconds.")


if __name__ == "__main__":
    paraloop_code()
    original_code()
