from datetime import datetime
import tributary.lazy as tl


class ExamplePoint(tl.LazyGraph):
    def __init__(self):
        self._now = datetime.now()
        self._curve = {self._now: 1, -1: 2}
        super().__init__()

    @tl.node()
    def now(self):
        return self._now

    @tl.node()
    def asof(self, date=None):
        if date is None:
            # return last
            return self._curve[-1]
        return self._curve[date]


class TestMethod:
    def test_args_kwargs(self):
        pt = ExamplePoint()
        # FIXME changed during lazy rewrite, no idea what i was testing originally
        assert pt.asof(date=None) == 2
        assert pt.asof(date=pt.now()) == 1
