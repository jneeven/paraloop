from paraloop import ParaLoop, Variable


def main():
    a = Variable(5)
    b = Variable(0.5)
    c = Variable([])

    for n in ParaLoop(list(range(10))):
        b = a + 12
        print(b)
        # a += 3
        c.append(n)
        print(n)
        print(c)


if __name__ == "__main__":
    main()
