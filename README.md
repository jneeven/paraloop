# Automatically parallelizing simple python for-loops
This is very much an experimental work in progress, and is only a proof of concept for now.
I can guarantee that it is full of horrendous bugs, and there is only one `AggregationStrategy` with support for a limited set of objects for now.

## How it works
Given a for-loop, e.g.
```python
from paraloop import ParaLoop, Variable
from paraloop import aggregation_strategies

counter = Variable(3, aggregation_strategy=aggregation_strategies.Sum)

for i in ParaLoop(range(0, 100000), num_processes=8):
    counter += i

print(counter)
```

`paraloop` will turn it into a function, e.g.
```python
def loop_iterator_2414(i):
    counter.assign(counter + 1)
```

And will call the function once for every iteration of the loop across multiple processes, instead of the original loop body.
Once the processes have finished, `paraloop` will handle the aggregation based on the chosen [AggregationStrategy](./paraloop/aggregation_strategies.py).

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
