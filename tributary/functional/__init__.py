from __future__ import print_function
import os

if os.name != "nt":
    from gevent import monkey

    _PATCHED = False

    if not _PATCHED:
        monkey.patch_all(thread=False, select=False)
        _PATCHED = True

from functools import partial  # noqa: E402
from concurrent.futures.thread import _WorkItem, BrokenThreadPool  # noqa: E402
from concurrent.futures import ThreadPoolExecutor, _base  # noqa: E402
import concurrent.futures.thread as cft  # noqa: E402
from .input import *  # noqa: F401, F403, E402
from .utils import *  # noqa: F401, F403, E402


_EXECUTOR = ThreadPoolExecutor(max_workers=10)


def submit(fn, *args, **kwargs):
    """Submit a function to be run on the executor (internal)

    Args:
        fn (callable): function to call
        args (tuple): args to pass to function
        kwargs (dict): kwargs to pass to function
    """
    if _EXECUTOR is None:
        raise RuntimeError("Already stopped!")
    self = _EXECUTOR
    with self._shutdown_lock:
        if hasattr(self, "_broken") and self._broken:
            raise BrokenThreadPool(self._broken)

        if hasattr(self, "_shutdown") and self._shutdown:
            raise RuntimeError("cannot schedule new futures after shutdown")
        if cft._shutdown:
            raise RuntimeError(
                "cannot schedule new futures after" "interpreter shutdown"
            )

        f = _base.Future()
        w = _WorkItem(f, fn, args, kwargs)

        self._work_queue.put(w)
        self._adjust_thread_count()
        return f


def run_submit(fn, function_to_call, *args, **kwargs):
    try:
        f = submit(fn, *args, **kwargs)
    except RuntimeError:
        # means we've shutdown, stop
        return

    if function_to_call:
        f.add_done_callback(
            lambda fut: function_to_call(fut.result()) if fut.result() else None
        )


def pipeline(
    funcs, func_callbacks, func_kwargs=None, on_data=print, on_data_kwargs=None
):
    """Pipeline a sequence of functions together via callbacks

    Args:
        funcs (list of callables): list of functions to pipeline
        func_callbacks (List[str]): list of strings indicating the callback names (kwargs of the funcs)
        func_kwargs (List[dict]):
        on_data (callable): callable to call at the end of the pipeline
        on_data_kwargs (dict): kwargs to pass to the on_data function>?
    """
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = ThreadPoolExecutor(max_workers=2)

    func_kwargs = func_kwargs or []
    on_data_kwargs = on_data_kwargs or {}

    # organize args for functional pipeline
    assembled = []
    for i, func in enumerate(funcs):
        cb = func_callbacks[i] if i < len(func_callbacks) else "on_data"
        kwargs = func_kwargs[i] if i < len(func_kwargs) else {}
        assembled.append((func, cb, kwargs))

    # assemble pipeline
    assembled.reverse()
    lambdas = [lambda d, f=on_data: run_submit(f, None, d, **on_data_kwargs)]
    for i, a in enumerate(assembled):
        func, cb, kwargs = a
        function_to_call = lambdas[i]
        kwargs[cb] = function_to_call

        if i != len(assembled) - 1:
            lambdas.append(
                lambda d, kw=kwargs, f=func: run_submit(f, function_to_call, d, **kw)
            )
            lambdas[-1].__name__ = func.__name__
        else:
            lambdas.append(
                lambda kw=kwargs, f=func: run_submit(f, function_to_call, **kw)
            )
            lambdas[-1].__name__ = func.__name__

    # start entrypoint
    lambdas[-1]()


def stop():
    """Stop the executor for the pipeline runtime"""
    global _EXECUTOR
    _EXECUTOR.shutdown(False)
    _EXECUTOR._threads.clear()
    cft._threads_queues.clear()
    _EXECUTOR = None


def wrap(function, *args, **kwargs):
    """Wrap a function in a partial"""
    func = partial(function, *args, **kwargs)
    func.__name__ = function.__name__
    return func
