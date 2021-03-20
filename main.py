from paraloop import ParaLoop, Variable
from paraloop.aggregation_strategies import Sum


def main():
    a = Variable(5.0, aggregation_strategy=Sum)
    c = []

    for n in ParaLoop(list(range(10))):
        a += 3
        c.append(n)

    print(a)


if __name__ == "__main__":
    main()
