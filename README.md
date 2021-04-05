# Automatically parallelizing simple python for-loops
This is currently still in a pretty experimental stage, and I can guarantee that it is full of horrendous bugs. There are only two `AggregationStrategy` types with support for a limited set of objects for now, but the library can definitely be used (especially for loops that don't "return" any values at all). Have a look at the [aggregation strategies](./paraloop/aggregation_strategies.py) to see what is currently supported!

## How it works
Given a for-loop, e.g.
```python
from paraloop import ParaLoop, Variable
from paraloop import aggregation_strategies

counter = Variable(3, aggregation_strategy=aggregation_strategies.Sum)
dictionary = Variable({}, aggregation_strategy=aggregation_strategies.Concatenate)

for i in ParaLoop(range(0, 100), num_processes=8):
    counter += i
    dictionary[f"key_{i}"] = "Hi!"

print(counter)
print(dictionary)
```

`paraloop` will turn it into a function, e.g.
```python
def loop_iterator(i):
    counter.assign(counter + 1)
    dictionary[f"key_{i}"] = "Hi"!
```

And will call the function once for every iteration of the loop across multiple processes, instead of the original loop body.
Once the processes have finished, `paraloop` will handle the aggregation based on the chosen [AggregationStrategy](./paraloop/aggregation_strategies.py), so that you can access your variable as if no multiprocessing ever happened.

## When would I use this?
`paraloop` is intended to be used for parallelizing for-loops that take an annoying amount of time, but are not worth spending the time and effort of proper multiprocessing on. These are usually fairly simple loops in research-style code that involve many web or file operations, but the goal of `paraloop` is to support parallelizing *any* Python for-loop by simply wrapping the variables and calling `ParaLoop`, without other modifications to the source code.

`paraloop` is **not** intended to be optimally efficient or provide a robust multiprocessing framework, and you probably shouldn't want to use this in a production environment. If you're looking for a robust multiprocessing framework that does require a bit of setup (i.e. rewriting your loop to a function with some specific return value and then aggregating those values yourself), have a look at [`joblib`](https://joblib.readthedocs.io/en/latest/).

## Practical example
Have a look at [example.py](./example.py).
It queries some WikiPedia pages and counts the frequency of each word.
The output of the script is as follows:
```
13882 57495
The original loop took 18.553406238555908 seconds.
13882 paraloop.Variable(57495)
The ParaLoop took 1.689873456954956 seconds.
```
Which is of course because most of the time is spent waiting for the WikiPedia server to respond.


## Roadmap
- [ ] Write unit tests for the `ParaLoop` class and the loop transformer
- [ ] Automatically determine the optimal number of processes if none was specified
- [ ] Add an optional progress bar
- [ ] Add a timeout in case a worker silently fails
- [ ] Add `SharedVariable`s that are stored in shared memory and hence don't need to be aggregated at all
