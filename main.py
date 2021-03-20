from paraloop import ParaLoop, Variable
from paraloop.aggregation_strategies import Sum


def main():
    a = Variable(0.0, aggregation_strategy=Sum)
    c = []
    print(int())

    for n in ParaLoop(list(range(10))):
        a += 3
        c.append(n)

    print(a)


if __name__ == "__main__":
    main()
