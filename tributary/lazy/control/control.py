from .utils import _CONTROL_GRAPHVIZSHAPE
from ..node import Node
from ...base import TributaryException


def If(if_node, satisfied_node, unsatisfied_node=None, *elseifs):
    """Node to return satisfied if if_node else unsatisfied

    Args:
        if_node (Node): input booleans
        satisfied_node (Node): input to return if true
        unsatisfied_node (Node): input to return if False
        elseifs (Tuple(Node)): input of boolean/value pairs to evaluate as else if statements
    """
    if len(elseifs) % 2 != 0:
        raise TributaryException("Else ifs must be in pairs")

    if elseifs:
        # TODO else ifs
        raise NotImplementedError()

    def func(cond, if_, else_=None):
        # TODO else ifs
        if cond:
            return if_
        return else_ if else_ is not None else None

    if isinstance(if_node._self_reference, Node):
        return if_node._gennode(
            "If",
            func,
            [if_node, satisfied_node, unsatisfied_node],
            graphvizshape=_CONTROL_GRAPHVIZSHAPE,
        )
    return if_node._gennode(
        "If",
        func,
        [if_node, satisfied_node, unsatisfied_node],
        graphvizshape=_CONTROL_GRAPHVIZSHAPE,
    )


Node.if_ = If
