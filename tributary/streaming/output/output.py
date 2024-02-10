import copy
import logging
from aioconsole import aprint
from IPython.display import display
from ..node import Node
from ...base import StreamEnd, StreamNone, StreamRepeat
from ...utils import _gen_node


_OUTPUT_GRAPHVIZSHAPE = "box"


class Func(Node):
    """Streaming wrapper to send data to function

    Arguments:
        func (callable): callable to call
        func_kwargs (dict): kwargs for callable
    """

    def __init__(self, func, func_kwargs=None, **kwargs):
        super().__init__(
            func=func,
            func_kwargs=func_kwargs,
            graphvizshape=_OUTPUT_GRAPHVIZSHAPE,
            **kwargs
        )


def Print(node, text=""):
    """Streaming wrapper to print the result to stdout, along with a helpertext"""

    async def func(val):
        if getattr(Print, "_multiprocess", None):
            print(text + str(val))
        else:
            await aprint(text + str(val))
        return val

    node = _gen_node(node)
    ret = Node(
        func=func,
        func_kwargs=None,
        name="Print",
        inputs=1,
        graphvizshape=_OUTPUT_GRAPHVIZSHAPE,
    )
    node >> ret
    return ret


def Logging(node, level=logging.CRITICAL):
    """Streaming wrapper to log the result using a logger"""

    def func(val):
        if level == logging.DEBUG:
            logging.debug(node)
        elif level == logging.INFO:
            logging.info(node)
        elif level == logging.WARNING:
            logging.warn(val)
        elif level == logging.ERROR:
            logging.error(val)
        else:
            logging.critical(val)
        return val

    node = _gen_node(node)
    ret = Node(
        func=func,
        func_kwargs=None,
        name="Log",
        inputs=1,
        graphvizshape=_OUTPUT_GRAPHVIZSHAPE,
    )
    node >> ret
    return ret


def Collect(node, limit=None):
    ret = []

    def func(val, ret=ret):
        if not isinstance(val, (StreamEnd, StreamNone, StreamRepeat)):
            ret.append(copy.deepcopy(val))
            if limit:
                ret = ret[-limit:]
        return ret

    node = _gen_node(node)
    ret = Node(
        func=func,
        func_kwargs=None,
        name="Collect",
        inputs=1,
        graphvizshape=_OUTPUT_GRAPHVIZSHAPE,
    )
    node >> ret
    return ret


def Graph(node):
    if isinstance(node, list):
        return {n: n.graph() for n in node}

    if not node.upstream():
        # leaf node
        return {node: []}
    return {node: [_.graph() for _ in node.upstream()]}


def PPrint(node, level=0):
    ret = "    " * (level - 1) if level else ""

    if not node.upstream():
        # leaf node
        return ret + "  \\  " + repr(node)
    return (
        "    " * level
        + repr(node)
        + "\n"
        + "\n".join(_.pprint(level + 1) for _ in node.upstream())
    )


def GraphViz(node):
    d = Graph(node)

    from graphviz import Digraph

    dot = Digraph("Graph", strict=False)
    dot.format = "png"

    def rec(nodes, parent):
        for d in nodes:
            if not isinstance(d, dict):
                dot.node(d, shape=d._graphvizshape)
                dot.edge(d, parent)

            else:
                for k in d:
                    dot.node(k._name, shape=k._graphvizshape)
                    rec(d[k], k)
                    dot.edge(k._name, parent._name)

    for k in d:
        dot.node(k._name, shape=k._graphvizshape)
        rec(d[k], k)

    return dot


def Dagre(node):
    import ipydagred3 as dd3

    G = dd3.Graph()
    d = Graph(node)

    def rec(nodes, parent):
        for d in nodes:
            if not isinstance(d, dict):
                d._dd3g = G
                G.setNode(
                    d._name,
                    shape="rect" if d._graphvizshape == "box" else d._graphvizshape,
                )
                G.setEdge(d._name, parent)
            else:
                for k in d:
                    k._dd3g = G
                    G.setNode(
                        k._name,
                        shape="rect" if k._graphvizshape == "box" else k._graphvizshape,
                    )
                    G.setEdge(k._name, parent._name)
                    rec(d[k], k)

    for k in d:
        k._dd3g = G
        G.setNode(
            k._name, shape="rect" if k._graphvizshape == "box" else k._graphvizshape
        )
        rec(d[k], k)

    graph = dd3.DagreD3Widget(graph=G)
    return graph


def Perspective(node, text="", **psp_kwargs):
    psp_kwargs = psp_kwargs or {}
    from perspective import PerspectiveWidget

    p = PerspectiveWidget(psp_kwargs.pop("schema", []), **psp_kwargs)

    def func(val):
        p.update(val)
        return val

    node = _gen_node(node)
    ret = Node(
        func=func,
        func_kwargs=None,
        name="Perspective",
        inputs=1,
        graphvizshape=_OUTPUT_GRAPHVIZSHAPE,
    )

    display(p)
    node >> ret
    return ret


def Queue(node, queue):
    async def func(val):
        await queue.put(val)
        return val

    node = _gen_node(node)
    ret = Node(
        func=func,
        func_kwargs=None,
        name="Queue",
        inputs=1,
        graphvizshape=_OUTPUT_GRAPHVIZSHAPE,
    )
    node >> ret
    return ret


Node.func = Func
Node.collect = Collect
Node.graph = Graph
Node.pprint = PPrint
Node.graphviz = GraphViz
Node.dagre = Dagre
Node.print = Print
Node.logging = Logging
Node.perspective = Perspective
Node.queue = Queue
