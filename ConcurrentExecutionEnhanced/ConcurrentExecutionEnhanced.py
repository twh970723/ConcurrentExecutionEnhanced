import multiprocessing as mp
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from itertools import repeat
from typing import Any, Callable, Dict, Iterable, Optional, Sequence, Tuple, Union, List

_ArgItem = Union[Any, Sequence[Any], Tuple[Sequence[Any], Dict[str, Any]], Dict[str, Any]]


def _choose_mp_context(prefer_fork: bool = True) -> mp.context.BaseContext:
    methods = mp.get_all_start_methods()
    if prefer_fork and sys.platform != "win32" and "fork" in methods:
        return mp.get_context("fork")
    return mp.get_context("spawn")


def _mapped_call(func: Callable, item: _ArgItem) -> Any:
    if isinstance(item, tuple) and len(item) == 2 and isinstance(item[1], dict):
        args, kwargs = item
        return func(*args, **kwargs)
    if isinstance(item, dict):
        return func(**item)
    if isinstance(item, (list, tuple)):
        return func(*item)
    return func(item)


def concurrent_thread(
        func: Callable,
        args: Iterable[_ArgItem],
        *,
        max_workers: Optional[int] = None,
        sequence: bool = True,
        chunksize: int = 1,
        timeout: Optional[float] = None,
) -> List[Any]:
    args_list = list(args)
    if sequence:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            return list(ex.map(_mapped_call, repeat(func), args_list, timeout=timeout, chunksize=chunksize))
    results: List[Any] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_mapped_call, func, it) for it in args_list]
        for fut in as_completed(futures, timeout=timeout):
            results.append(fut.result())
    return results


def concurrent_process(
        func: Callable,
        args: Iterable[_ArgItem],
        *,
        max_workers: Optional[int] = None,
        sequence: bool = True,
        chunksize: int = 1,
        timeout: Optional[float] = None,
) -> list[Any]:
    args_list = list(args)
    ctx = _choose_mp_context()
    if sequence:
        with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as ex:
            return list(ex.map(_mapped_call, repeat(func), args_list, chunksize=chunksize, timeout=timeout))
    results = []
    with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as ex:
        futures = [ex.submit(_mapped_call, func, it) for it in args_list]
        for fut in as_completed(futures, timeout=timeout):
            results.append(fut.result())
    return results
