import math
import tributary.streaming as ts


def func():
    yield 1
    yield 2
    yield 3
    yield 4
    yield 5


def funcfloat():
    yield 1.11
    yield 2.22
    yield 3.33
    yield 4.44
    yield 5.55


def func2():
    yield 1
    yield 4
    yield 9


def func3():
    yield -1
    yield -2


def func4():
    yield [1]
    yield [1, 2]
    yield [1, 2, 3]


class TestOps:
    def test_Noop(self):
        t = ts.Timer(func, count=2)
        out = ts.Noop(t)
        assert ts.run(out) == [1, 2]

    def test_Negate(self):
        t = ts.Timer(func, count=2)
        out = ts.Negate(t)
        assert ts.run(out) == [-1, -2]

    def test_Invert(self):
        t = ts.Timer(func, count=2)
        out = ts.Invert(t)
        assert ts.run(out) == [1 / 1, 1 / 2]

    def test_Add(self):
        t = ts.Timer(func, count=2)
        out = ts.Add(t, t)
        assert ts.run(out) == [2, 4]

    def test_Sub(self):
        t = ts.Timer(func, count=2)
        out = ts.Sub(t, t)
        assert ts.run(out) == [0, 0]

    def test_Mult(self):
        t = ts.Timer(func, count=2)
        out = ts.Mult(t, t)
        assert ts.run(out) == [1, 4]

    def test_Div(self):
        t = ts.Timer(func, count=2)
        out = ts.Div(t, t)
        assert ts.run(out) == [1, 1]

    def test_RDiv(self):
        t = ts.Timer(func, count=2)
        out = ts.RDiv(t, t)
        assert ts.run(out) == [1, 1]

    def test_Mod(self):
        t = ts.Timer(func, count=5)
        c = ts.Const(3)
        out = ts.Mod(t, c)
        assert ts.run(out) == [1, 2, 0, 1, 2]

    def test_Pow(self):
        t = ts.Timer(func, count=2)
        c = ts.Const(2)
        out = ts.Pow(t, c)
        assert ts.run(out) == [1, 4]

    def test_Sum(self):
        t = ts.Timer(func, count=2)
        t2 = ts.Timer(func, count=2)
        c = ts.Const(2)
        out = ts.Sum(t, t2, c)
        assert ts.run(out) == [4, 6]

    def test_Average(self):
        t = ts.Timer(func, count=1)
        t2 = ts.Timer(func, count=1)
        c = ts.Const(1)
        out = ts.Average(t, t2, c)
        assert ts.run(out) == [1]

    def test_Not(self):
        t = ts.Timer(func, count=2)
        out = ts.Not(t)
        assert ts.run(out) == [False, False]

    def test_And(self):
        t = ts.Timer(func, count=2)
        out = ts.And(t, t)
        assert ts.run(out) == [1, 2]

    def test_Or(self):
        t = ts.Timer(func, count=2)
        out = ts.Or(t, t)
        assert ts.run(out) == [1, 2]

    def test_Equal(self):
        t = ts.Timer(func, count=2)
        c = ts.Const(1)
        out = ts.Equal(t, c)
        assert ts.run(out) == [True, False]

    def test_NotEqual(self):
        t = ts.Timer(func, count=2)
        c = ts.Const(1)
        out = ts.NotEqual(t, c)
        assert ts.run(out) == [False, True]

    def test_Lt(self):
        t = ts.Timer(func, count=2)
        c = ts.Const(1)
        out = ts.Lt(c, t)
        assert ts.run(out) == [False, True]

    def test_Le(self):
        t = ts.Timer(func, count=2)
        c = ts.Const(2)
        out = ts.Le(c, t)
        assert ts.run(out) == [False, True]

    def test_Gt(self):
        t = ts.Timer(func, count=2)
        c = ts.Const(1)
        out = ts.Gt(t, c)
        assert ts.run(out) == [False, True]

    def test_Ge(self):
        t = ts.Timer(func, count=2)
        c = ts.Const(2)
        out = ts.Ge(t, c)
        assert ts.run(out) == [False, True]

    def test_Log(self):
        t = ts.Timer(func, count=2)
        out = ts.Log(t)
        assert ts.run(out) == [math.log(1), math.log(2)]

    def test_Sin(self):
        t = ts.Timer(func, count=2)
        out = ts.Sin(t)
        assert ts.run(out) == [math.sin(1), math.sin(2)]

    def test_Cos(self):
        t = ts.Timer(func, count=2)
        out = ts.Cos(t)
        assert ts.run(out) == [math.cos(1), math.cos(2)]

    def test_Tan(self):
        t = ts.Timer(func, count=2)
        out = ts.Tan(t)
        assert ts.run(out) == [math.tan(1), math.tan(2)]

    def test_Arcsin(self):
        t = ts.Timer(func, count=2)
        c = ts.Const(value=3)
        out = ts.Arcsin(ts.Div(t, c))
        assert ts.run(out) == [math.asin(1 / 3), math.asin(2 / 3)]

    def test_Arccos(self):
        t = ts.Timer(func, count=2)
        c = ts.Const(value=3)
        out = ts.Arccos(ts.Div(t, c))
        assert ts.run(out) == [math.acos(1 / 3), math.acos(2 / 3)]

    def test_Arctan(self):
        t = ts.Timer(func, count=2)
        out = ts.Arctan(t)
        assert ts.run(out) == [math.atan(1), math.atan(2)]

    def test_Sqrt(self):
        t = ts.Timer(func2, count=3)
        out = ts.Sqrt(t)
        assert ts.run(out) == [1.0, 2.0, 3.0]

    def test_Abs(self):
        t = ts.Timer(func3, count=2)
        out = ts.Abs(t)
        assert ts.run(out) == [1, 2]

    def test_Exp(self):
        t = ts.Timer(func, count=2)
        out = ts.Exp(t)
        assert ts.run(out) == [math.exp(1), math.exp(2)]

    def test_Erf(self):
        t = ts.Timer(func, count=2)
        out = ts.Erf(t)
        assert ts.run(out) == [math.erf(1), math.erf(2)]

    def test_Floor(self):
        t = ts.Timer(funcfloat, count=2)
        out = ts.Floor(t)
        assert ts.run(out) == [1.0, 2.0]

    def test_Ceil(self):
        t = ts.Timer(funcfloat, count=2)
        out = ts.Ceil(t)
        assert ts.run(out) == [2.0, 3.0]

    def test_Round(self):
        t = ts.Timer(funcfloat, count=2)
        out = ts.Round(t, 1)
        assert ts.run(out) == [1.1, 2.2]

    def test_Int(self):
        t = ts.Timer(func, count=2)
        out = ts.Int(t)
        assert ts.run(out) == [1, 2]

    def test_Float(self):
        t = ts.Timer(func, count=2)
        out = ts.Float(t)
        assert ts.run(out) == [1.0, 2.0]

    def test_Bool(self):
        t = ts.Timer(func, count=2)
        out = ts.Bool(t)
        assert ts.run(out) == [True, True]

    def test_Str(self):
        t = ts.Timer(func, count=2)
        out = ts.Str(t)
        assert ts.run(out) == ["1", "2"]
