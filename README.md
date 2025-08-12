# ConcurrentExecutionEnhanced

Small, zero-dependency **concurrent.futures** wrapper to run the **same function** across many inputs using
either **multiple processes** (for CPU‑bound work) or **multiple threads** (for I/O‑bound work).

- 🧠 Processes: `concurrent_process(...)` – uses all CPU cores.  
- 🔀 Threads: `concurrent_thread(...)` – great for HTTP/file/DB I/O.

> Requires **Python ≥ 3.11**. Works on macOS, Linux, and Windows (see notes below).


## Installation

```bash
pip install ConcurrentExecutionEnhanced
```

## Quick start

### CPU-bound work (use processes)

```bash
# hello_process.py
from ConcurrentExecutionEnhanced import concurrent_process

def power_sum(n: int, p: int = 2) -> int:
    return sum(i ** p for i in range(n))

items = [(100_000, 2), (120_000, 2), (140_000, 3)]
out = concurrent_process(power_sum, items, max_workers=None, sequence=True, chunksize=10)
print(out)
```

Run:
```bash
python hello_process.py
```

### I/O-bound work (use threads)

```bash
from ConcurrentExecutionEnhanced import concurrent_thread
import time

def fetch_one(url: str) -> tuple[str, float]:
    t0 = time.perf_counter()
    # pretend I/O
    time.sleep(0.1)
    return url, time.perf_counter() - t0

urls = ["https://a", "https://b", "https://c"]
out = concurrent_thread(fetch_one, urls, max_workers=20, sequence=False)
print(out)  
# sequence=False: capture as soon as each task completes, not following sequence
```


## Passing arguments

You can pass each task in four flexible shapes:

- Value → `func(value)`
- Tuple/list → `func(*item)`
- Dict → `func(**item)`
- Pair `(args_seq, kwargs_dict)` → `func(*args_seq, **kwargs_dict)`

```bash
from ConcurrentExecutionEnhanced import concurrent_thread

def f(a, b=2, *, scale=1):
    return (a ** b) * scale

items = [
    3,                  # f(3)
    (4, 3),             # f(4, 3)
    {"a": 5, "scale": 2},
    ((6,), {"b": 3, "scale": 10}),
]

print(concurrent_thread(f, items, sequence=True))
```


## API

Both helpers share the same signature:

```bash
from ConcurrentExecutionEnhanced import concurrent_process, concurrent_thread

concurrent_process(
    func,                        # Callable
    args,                        # Iterable of task items (see shapes above)
    *,                           # keyword-only params below
    max_workers: int | None = None,
    sequence: bool = True,       # True: preserve input order; False: return as tasks finish
    chunksize: int = 1,          # hint for batching (mainly useful for tiny, fast tasks)
    timeout: float | None = None # per-future timeout
) -> list

concurrent_thread(... same parameters ...)
```

**Return value**: `list` of results. When `sequence=True`, results match the input order.  
When `sequence=False`, results are pushed as soon as each task completes.


## Choosing threads vs processes

- Use **`concurrent_process`** for **CPU-bound** work (heavy Python loops, compression, crypto).
- Use **`concurrent_thread`** for **I/O-bound** work (HTTP/file/DB).

## Large inputs & DataFrames

- Both helpers accept any **picklable** item. For processes, each task’s input is **copied** to workers.
- For big data (e.g., a large `pandas.DataFrame`), prefer passing **chunks** rather than the whole object to every task.

Example (chunking a DataFrame):

```bash
import numpy as np
import pandas as pd
from ConcurrentExecutionEnhanced import concurrent_process

def work(df_chunk: pd.DataFrame) -> pd.DataFrame:
    df_chunk = df_chunk.copy()
    df_chunk["y"] = df_chunk["x"] ** 2
    return df_chunk

df = pd.DataFrame({"x": range(1_000_000)})
chunks = np.array_split(df, 8)  # pick a number near your CPU cores
out = concurrent_process(work, chunks, sequence=True)
df_result = pd.concat(out, ignore_index=True)
```