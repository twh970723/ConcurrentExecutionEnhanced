import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import repeat
from typing import Any, Callable, Iterable, Optional, Sequence, Tuple, Dict, Union

_ArgItem = Union[Any, Sequence[Any], Tuple[Sequence[Any], Dict[str, Any]], Dict[str, Any]]


class ConcurrentProcessEnhanced:
    def __init__(self):
        pass

    def _mapped_call(self, func: Callable, item: _ArgItem) -> Any:
        if isinstance(item, tuple) and len(item) == 2 and isinstance(item[1], dict):
            args, kwargs = item
            return func(*args, **kwargs)
        if isinstance(item, dict):
            return func(**item)
        if isinstance(item, (list, tuple)):
            return func(*item)
        return func(item)

    def concurrent_process(
            self,
            func: Callable,
            args: Iterable[_ArgItem],
            *,
            max_workers: Optional[int] = None,
            ordered: bool = True,
            chunksize: int = 1,
            timeout: Optional[float] = None,
    ) -> list[Any]:
        args_list = list(args)
        ctx = mp.get_context("fork")  # <- request fork here (macOS/Linux)

        if ordered:
            with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as ex:
                return list(ex.map(self._mapped_call, repeat(func), args_list, chunksize=chunksize, timeout=timeout))

        results = []
        with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as ex:
            futures = [ex.submit(self._mapped_call, func, it) for it in args_list]
            for fut in as_completed(futures, timeout=timeout):
                results.append(fut.result())
        return results
