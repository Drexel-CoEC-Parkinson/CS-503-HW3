#!/usr/bin/env python3
"""
memory_eater.py — Virtual memory vs physical memory; cache locality.

Usage:
    ./memory_eater.py lazy <size_mb> [--hold N]
    ./memory_eater.py eager <size_mb> [--hold N]
    ./memory_eater.py sequential <size_mb>
    ./memory_eater.py random <size_mb>

Modes:
    lazy        Allocate <size_mb> MB as an anonymous mmap mapping and
                immediately sleep without touching any of it. VSZ grows by
                <size_mb>; RSS stays small (just the Python interpreter).
                --hold controls the sleep duration (default 60s).

    eager       Allocate <size_mb> MB, then touch every page to force the
                kernel to actually allocate physical RAM. Both VSZ and RSS
                grow by <size_mb>. --hold also applies.

    sequential  Allocate a <size_mb> NumPy int64 array, then read every
                element in sequential order. Times the reads.

    random      Same as sequential, but reads elements in random order.
                Same amount of work; very different cache behavior.

Notes:
    - VSZ and RSS will also include ~30-50 MB of Python interpreter overhead.
    - Don't run with absurdly large sizes on a shared system.
"""

import argparse
import mmap
import os
import sys
import time

import numpy as np


PAGE_SIZE = mmap.PAGESIZE  # typically 4096 bytes


def lazy(size_mb: int, hold: int) -> None:
    """Allocate an anonymous mmap mapping and do not touch it."""
    size_bytes = size_mb * 1024 * 1024
    print(f"[lazy] allocating {size_mb} MB anonymous mmap (no pages touched)")
    buf = mmap.mmap(-1, size_bytes)
    print(f"[lazy] PID={os.getpid()}")
    print(f"[lazy] check with: ps -o pid,vsz,rss,cmd -p {os.getpid()}")
    print(f"[lazy] expected: VSZ ~= {size_mb} MB plus interpreter, RSS stays small")
    print(f"[lazy] holding {hold}s")
    time.sleep(hold)
    buf.close()


def eager(size_mb: int, hold: int) -> None:
    """Allocate, then write one byte to every page to force physical allocation."""
    size_bytes = size_mb * 1024 * 1024
    print(f"[eager] allocating {size_mb} MB anonymous mmap")
    buf = mmap.mmap(-1, size_bytes)
    print(f"[eager] touching every page (every {PAGE_SIZE} bytes) to force allocation")
    # Writing one byte per page is enough — the kernel allocates a full page
    # the first time any byte in it is touched. This is exactly what demand
    # paging means: physical pages are bound to virtual addresses on first
    # access, not at allocation time.
    for offset in range(0, size_bytes, PAGE_SIZE):
        buf[offset] = 1
    print(f"[eager] PID={os.getpid()}")
    print(f"[eager] check with: ps -o pid,vsz,rss,cmd -p {os.getpid()}")
    print(f"[eager] expected: VSZ AND RSS both ~= {size_mb} MB plus interpreter")
    print(f"[eager] holding {hold}s")
    time.sleep(hold)
    buf.close()


def access_test(mode: str, size_mb: int) -> None:
    """Read every element of a size_mb array, in sequential or random order.

    Both modes visit every element of the same array exactly once and produce
    the same sum. The only difference is the order. Sequential access is
    cache-friendly: the CPU's prefetcher loads cache lines (64 bytes = 8 int64
    values) ahead of where you are, so most reads hit cache. Random access
    defeats the prefetcher: every read goes to a different cache line, and
    once the array exceeds L3 cache (~30 MB on most modern CPUs), most reads
    must travel all the way to RAM.
    """
    bytes_per_element = 8  # int64
    n_elements = (size_mb * 1024 * 1024) // bytes_per_element

    print(f"[{mode}] building source array: {n_elements:,} int64 values ({size_mb} MB)")
    arr = np.arange(n_elements, dtype=np.int64)

    if mode == "sequential":
        # Warm up the array once so we're not measuring first-touch page faults.
        _ = arr.sum()
        print(f"[{mode}] reading {n_elements:,} elements in order; timing")
        start = time.perf_counter()
        result = int(arr.sum())
        elapsed = time.perf_counter() - start
    else:  # random
        # Build a permutation of all indices. Seeded so every student sees the
        # same permutation.
        print(f"[{mode}] building random permutation of {n_elements:,} indices")
        rng = np.random.default_rng(seed=42)
        indices = rng.permutation(n_elements)
        print(f"[{mode}] reading {n_elements:,} elements in random order; timing")
        start = time.perf_counter()
        # arr[indices] gathers values from arr in random order, then .sum()
        # reduces. The gather is where the cache misses happen.
        result = int(arr[indices].sum())
        elapsed = time.perf_counter() - start

    # Sanity check: the sum of arange(n) is n*(n-1)/2 regardless of access order.
    expected = n_elements * (n_elements - 1) // 2
    if result != expected:
        print(f"[{mode}] WARNING: sum mismatch (got {result}, expected {expected})")

    print(f"[{mode}] {size_mb} MB in {mode} order: {elapsed:.3f}s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("mode", choices=["lazy", "eager", "sequential", "random"])
    parser.add_argument("size_mb", type=int, help="allocation/array size in MB")
    parser.add_argument(
        "--hold", type=int, default=60,
        help="(lazy/eager only) seconds to sleep after allocation; default 60",
    )
    args = parser.parse_args()

    if args.size_mb < 1:
        sys.exit("size_mb must be positive")
    if args.hold < 1:
        sys.exit("--hold must be positive")

    if args.mode == "lazy":
        lazy(args.size_mb, args.hold)
    elif args.mode == "eager":
        eager(args.size_mb, args.hold)
    else:
        access_test(args.mode, args.size_mb)


if __name__ == "__main__":
    main()
