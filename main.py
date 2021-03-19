from paraloop import ParaLoop, Variable


class Test:
    def __add__(self, other):
        print(other)

    def assign(self, value):
        print("Assigned sumn")


def main():
    numbers = list(range(10))
    booster = ParaLoop(numbers)
    a = Variable(51)
    c = []
    for n in booster:
        a = a + 12
        a += 3
        c.append(n)
        print(n)
        print(c)


if __name__ == "__main__":
    main()
