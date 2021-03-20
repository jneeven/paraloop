from paraloop import ParaLoop, Variable


def main():
    a = Variable(5.0)
    b = Variable(17)
    c = []

    for n in ParaLoop(list(range(10))):
        b = a + 12
        print(a, b)
        a += 3
        b *= 3.8
        print(a, b)
        c.append(n)
        print(n)
        print(c)


if __name__ == "__main__":
    main()
