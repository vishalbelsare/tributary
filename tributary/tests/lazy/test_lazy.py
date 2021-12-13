import tributary.lazy as t
import random


class Func1(t.LazyGraph):
    def __init__(self, *args, **kwargs):
        self.x = self.node("x", readonly=False, value=1)


class Func2(t.LazyGraph):
    def __init__(self, *args, **kwargs):
        self.y = self.node("y", readonly=False, value=2)

        # ensure no __nodes clobber
        self.test = self.node("test", readonly=False, value=2)
        self.x = self.node("x", readonly=False, value=2)


class Func3(t.LazyGraph):
    @t.node()
    def func1(self):
        return self.random()  # test self access

    def random(self):
        return random.random()

    @t.node()
    def func3(self, x=4):
        return 3 + x


class Func4(t.LazyGraph):
    @t.node()
    def func1(self):
        return self.func2() + 1

    @t.node()
    def func2(self):
        return random.random()


class TestLazy:
    def test_misc(self):
        f4 = Func4()
        z = f4.func1()
        assert z.print()
        assert z.graph()
        assert z.graphviz()

    def test_lazy_default_func_arg(self):
        def func(val, prev_val=0):
            print("val:\t{}\t{}".format(val, val.value()))
            print("prev_val:\t{}\t{}".format(prev_val, prev_val.value()))
            return val.value() + prev_val.value()

        n = t.Node(callable=func)
        n.set(val=5)

        assert n() == 5

        n.set(prev_val=100)

        assert n() == 105

    def test_lazy_args_by_name_and_arg(self):
        # see the extended note in lazy.node about callable_args_mapping
        n = t.Node(name="Test", value=5)
        n2 = n + 1

        print(n2._callable_args_mapping)
        print(n2._callable_args_mapping[0]["node"])
        print(n2._callable_args_mapping[0]["arg"])
        assert n2._callable_args_mapping[0]["node"] == "Test"
        assert n2._callable_args_mapping[0]["arg"] == "x"
