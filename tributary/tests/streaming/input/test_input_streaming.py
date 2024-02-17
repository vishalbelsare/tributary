import time
import tributary.streaming as ts


class TestConst:
    def setup_method(self):
        time.sleep(0.5)

    def test_const_1(self):
        t = ts.Const(value=1, count=1)
        assert ts.run(t) == [1]

    def test_const_2(self):
        t = ts.Const(value=1, count=5)
        assert ts.run(t) == [1, 1, 1, 1, 1]


class TestTimer:
    def setup_method(self):
        time.sleep(0.5)

    def test_timer(self):
        val = 0

        def func():
            nonlocal val
            val += 1
            return val

        t = ts.Timer(func, count=5)
        assert ts.run(t) == [1, 2, 3, 4, 5]

        t = ts.Timer(func, count=5)

    def test_timer_delay(self):
        val = 0

        def func():
            nonlocal val
            val += 1
            return val

        t = ts.Timer(func, count=5, interval=0.1)
        assert ts.run(t) == [1, 2, 3, 4, 5]

        t = ts.Timer(func, count=5)

    def test_timer_generator(self):
        def func():
            yield 1
            yield 2
            yield 3
            yield 4
            yield 5

        t = ts.Timer(func)
        assert ts.run(t) == [1]

        t = ts.Timer(func, count=3)
        assert ts.run(t) == [1, 2, 3]

        t = ts.Timer(func, count=5)
        assert ts.run(t) == [1, 2, 3, 4, 5]

        t = ts.Timer(func, count=6)
        assert ts.run(t) == [1, 2, 3, 4, 5]

    def test_timer_generator_delay(self):
        def func():
            yield 1
            yield 2
            yield 3
            yield 4
            yield 5

        t = ts.Timer(func, interval=0.1)
        assert ts.run(t) == [1]

        t = ts.Timer(func, count=3, interval=0.1)
        assert ts.run(t) == [1, 2, 3]

        t = ts.Timer(func, count=5, interval=0.1)
        assert ts.run(t) == [1, 2, 3, 4, 5]

        t = ts.Timer(func, count=6, interval=0.1)
        assert ts.run(t) == [1, 2, 3, 4, 5]


class TestFunc:
    def setup_method(self):
        time.sleep(0.5)

    def test_timer(self):
        val = 0

        def func():
            nonlocal val
            val += 1
            return val

        t = ts.Timer(func, count=5)
        assert ts.run(t) == [1, 2, 3, 4, 5]

        t = ts.Timer(func, count=5)

    def test_timer_delay(self):
        val = 0

        def func():
            nonlocal val
            val += 1
            return val

        t = ts.Timer(func, count=5, interval=0.1)
        assert ts.run(t) == [1, 2, 3, 4, 5]

        t = ts.Timer(func, count=5)

    def test_func_generator(self):
        def func():
            yield 1
            yield 2
            yield 3
            yield 4
            yield 5

        t = ts.Func(func)
        assert ts.run(t) == [1, 2, 3, 4, 5]
