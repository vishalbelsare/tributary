import asyncio
import types
import uuid
from collections import deque
from .dd3 import _DagreD3Mixin
from .graph import StreamingGraph
from .serialize import NodeSerializeMixin
from ..base import StreamEnd, StreamNone, StreamRepeat
from ..base import TributaryException
from ..utils import _agen_to_func, _gen_to_func


class Node(NodeSerializeMixin, _DagreD3Mixin, object):
    def __init__(
        self,
        func,
        func_kwargs=None,
        name=None,
        inputs=0,
        drop=False,
        replace=False,
        repeat=False,
        graphvizshape="ellipse",
        delay_interval=0,
        execution_max=0,
        use_dual=False,
        **kwargs
    ):
        """A representation of a node in the forward propogating graph.

        Args:
            func (callable); the python callable to wrap in a forward propogating node, can be:
                                - function
                                - generator
                                - async function
                                - async generator
            func_kwargs (dict); kwargs for the wrapped callables, should be static call-to-call
            name (str); name of the node
            inputs (int); number of upstream inputs
            drop (bool); on mismatched tick timing, drop new ticks
            replace (bool); on mismatched tick timing, replace new ticks
            repeat (bool); on mismatched tick timing, replay old tick
            graphvizshape (str); graphviz shape to use
            delay_interval (int/float); rate limit
            execution_max (int); max number of times to execute callable
            use_dual (bool); use dual numbers for arithmetic

            internal only:
                _id_override (int); RESTORE ONLY. override default id allocation mechanism

        """
        # ID is unique identifier of the node
        self._id = str(uuid.uuid4())

        # Graphviz shape
        self._graphvizshape = graphvizshape

        # dagred3 node if live updating
        self._dd3g = None

        # Every node gets a name so it can be uniquely identified in the graph
        self._name = "{}#{}".format(name or self.__class__.__name__, self._id[:5])
        self._name_only = name

        # Inputs are async queues from upstream nodes
        self._input = [deque() for _ in range(inputs)]

        # Active are currently valid inputs, since inputs
        # may come at different rates
        self._active = [StreamNone() for _ in range(inputs)]

        # Downstream nodes so we can traverse graph, push
        # results to downstream nodes
        self._downstream = []

        # Upstream nodes so we can traverse graph, plot and optimize
        self._upstream = []

        # The function we are wrapping, can be:
        #    - vanilla function
        #    - vanilla generator
        #    - async function
        #    - async generator
        self._func = func

        # Any kwargs necessary for the function.
        # These should be static call-to-call.
        self._func_kwargs = func_kwargs or {}

        # Delay between executions, useful for rate-limiting
        # default is no rate limiting
        self._delay_interval = delay_interval

        # max number of times to execute callable
        self._execution_max = execution_max

        # current execution count
        self._execution_count = 0

        # last value pushed downstream
        self._last = StreamNone()

        # stream is in a finished state, will only propogate StreamEnd instances
        self._finished = False

        # check if dual number
        self._use_dual = use_dual

        # Replacement policy #
        # drop ticks
        self._drop = drop

        # replace ticks
        self._replace = replace

        assert not (self._drop and self._replace)

        # repeat last if input is StreamNone
        self._repeat = repeat

        # coroutines to run on graph start
        self._onstarts = ()

        # coroutines to run on graph stop
        self._onstops = ()

        # for safety
        self._initial_attrs = dir(self) + ["_old_func", "_initial_attrs"]

    # ***********************
    # Public interface
    # ***********************
    def __repr__(self):
        return "{}".format(self._name)

    def has(self, key):
        """Use this method to check attributes (convenience for hasattr)"""
        return hasattr(self, key)

    def set(self, key, value):
        """Use this method to set attributes

        Since we often use attributes to track node state, let's make sure we don't clobber any important ones
        """
        if hasattr(self, "_initial_attrs") and key in self._initial_attrs:
            # if we've completed our construction, ensure critical attrs arent overloaded
            raise TributaryException(
                "Overloading node-critical attribute: {}".format(key)
            )

        self._initial_attrs.append(key)
        super().__setattr__(key, value)

    def __setattr__(self, key, value):
        if hasattr(self, "_initial_attrs") and key not in self._initial_attrs:
            # if we've completed our construction, ensure critical attrs arent overloaded
            raise TributaryException(
                "Use set() to set attribute, to avoid overloading node-critical attribute: {}".format(
                    key
                )
            )

        super().__setattr__(key, value)

    def upstream(self, node=None):
        """Access list of upstream nodes"""
        return self._upstream

    def downstream(self, node=None):
        """Access list of downstream nodes"""
        return self._downstream

    def value(self):
        """get value from node"""
        return self._last

    async def __call__(self):
        """execute the callable if possible, and propogate values downstream"""
        # Previously ended stream
        if self._finished:
            return await self._finish()

        # Downstream nodes can't process
        if self._backpressure():
            await self._waitdd3g()
            return StreamNone()

        # dd3g
        await self._startdd3g()

        # Sleep if needed
        if self._delay_interval:
            await asyncio.sleep(self._delay_interval)

        # Stop executing
        if self._execution_max > 0 and self._execution_count >= self._execution_max:
            self._func = lambda: StreamEnd()
            self._old_func = lambda: StreamEnd()

        ready = True
        # iterate through inputs
        for i, inp in enumerate(self._input):
            # if input hasn't received value
            if isinstance(self._active[i], StreamNone):
                if len(inp) > 0:
                    # get from input queue
                    val = inp.popleft()

                    while isinstance(val, StreamRepeat):
                        # Skip entry
                        val = inp.popleft()

                    if isinstance(val, StreamEnd):
                        return await self._finish()

                    # set as active
                    self._active[i] = val
                else:
                    # wait for value
                    self._active[i] = StreamNone()
                    ready = False

        if ready:
            # execute function
            return await self._execute()

    # ***********************

    # ***********************
    # Private interface
    # ***********************
    def __hash__(self):
        return hash(self._id)

    def __rshift__(self, other):
        """wire self to other"""
        self.downstream().append((other, len(other.upstream())))
        other.upstream().append(self)

    def __lshift__(self, other):
        """wire other to self"""
        other.downstream().append((self, len(self.upstream())))
        self.upstream().append(other)

    async def _push(self, inp, index):
        """push value to downstream nodes"""
        self._input[index].append(inp)

    async def _empty(self, index):
        """check if value"""
        return len(self._input[index]) == 0 or self._active[index] != StreamNone()

    async def _pop(self, index):
        """pop value from downstream nodes"""
        if len(self._input[index]) > 0:
            return self._input[index].popleft()

    async def _execute(self):
        """execute callable"""
        # assume no valid input
        valid = False

        # wait for valid input
        while not valid:
            # await if its a coroutine
            if asyncio.iscoroutine(self._func):
                _last = await self._func(*self._active, **self._func_kwargs)

            # else call it
            elif isinstance(self._func, types.FunctionType):
                try:
                    # could be a generator
                    try:
                        _last = self._func(*self._active, **self._func_kwargs)
                    except ZeroDivisionError:
                        _last = float("inf")

                except ValueError:
                    # Swap back to function to get a new generator next iteration
                    self._func = self._old_func
                    continue

            else:
                raise TributaryException("Cannot use type:{}".format(type(self._func)))

            # calculation was valid
            valid = True

            # increment execution count
            self._execution_count += 1

        if isinstance(_last, types.AsyncGeneratorType):

            async def _func(g=_last):
                return await _agen_to_func(g)

            self._func = _func
            _last = await self._func()

        elif isinstance(_last, types.GeneratorType):
            # Swap to generator unroller
            self._old_func = self._func
            self._func = lambda g=_last: _gen_to_func(g)
            _last = self._func()

        elif asyncio.iscoroutine(_last):
            _last = await _last

        if self._repeat:
            if isinstance(_last, (StreamNone, StreamRepeat)):
                # NOOP
                self._last = self._last
            else:
                self._last = _last
        else:
            self._last = _last

        await self._enddd3g()
        await self._output(self._last)

        for i in range(len(self._active)):
            self._active[i] = StreamNone()

        if isinstance(self._last, StreamEnd):
            await self._finish()

    async def _finish(self):
        """mark this node as finished"""
        self._finished = True
        self._last = StreamEnd()
        await self._finishdd3g()
        await self._output(self._last)

    def _backpressure(self):
        """check if downstream() are all empty, if not then don't propogate"""
        if self._drop or self._replace:
            return False

        ret = not all(len(n._input[i]) == 0 for n, i in self.downstream())
        return ret

    async def _output(self, ret):
        """output value to downstream nodes"""
        # if downstreams, output
        if not isinstance(ret, (StreamNone, StreamRepeat)):
            for down, i in self.downstream():
                if self._drop:
                    if len(down._input[i]) > 0:
                        # do nothing
                        pass

                    elif not isinstance(down._active[i], StreamNone):
                        # do nothing
                        pass

                    else:
                        await down._push(ret, i)

                elif self._replace:
                    if len(down._input[i]) > 0:
                        _ = await down._pop(i)

                    elif not isinstance(down._active[i], StreamNone):
                        down._active[i] = ret

                    else:
                        await down._push(ret, i)

                else:
                    await down._push(ret, i)
        return ret

    # ***********************

    # ***********************
    # Graph operations
    # ***********************
    def constructGraph(self):
        from .output import Collect

        return StreamingGraph(Collect(self))

    def _collect(self, visited=None):
        """return a set of all nodes in the graph"""
        visited = visited or []

        for node in visited:
            if self._id == node._id:
                # already visited
                return visited

        visited.append(self)

        # collect all nodes above
        for node in self.upstream():
            node._collect(visited)

        for node, _ in self.downstream():
            node._collect(visited)

        return visited

    def _graph(self):
        pass

    def _deep_bfs(self, reverse=True, tops_only=False):
        """get nodes by level in tree, reversed relative to output node.
           e.g. given a tree that looks like:
        A -> B -> D -> F
         \\-> C -> E /
         the result will be: [[A], [B, C], [D, E], [F]]

         This will be the order we synchronously execute, so that within a
         level nodes' execution will be asynchronous but from level to level
         they will be synchronous
        """
        # collect all nodes
        all_nodes = self._collect()

        # the list of lists of nodes representing layers in the graph
        nodes = []

        # we want to collect all the "top" nodes in the graph
        tops = set(n._id for n in all_nodes if len(n.upstream()) == 0)
        tops = [n for n in all_nodes if n._id in tops]

        if tops_only:
            return tops

        # now descend the graph in layers.
        nodes_seen = set()
        to_visit = tops
        while to_visit:
            nodes.append([])

            next_to_visit = []
            for node in to_visit:
                if node._id in nodes_seen:
                    # TODO allow cycles?
                    continue

                nodes[-1].append(node)
                nodes_seen.add(node._id)

                if node.downstream():
                    next_to_visit.extend([x[0] for x in node.downstream()])

            to_visit = next_to_visit

        if not reverse:
            nodes.reverse()

        return nodes

    # ***********************
