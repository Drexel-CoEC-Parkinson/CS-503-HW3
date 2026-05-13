#!/usr/bin/env python3
"""
race_demo.py — Demonstrate a race condition on a shared counter.

Usage:
    ./race_demo.py --no-lock
    ./race_demo.py --with-lock

Four threads each increment a shared counter 100,000 times. With perfect
synchronization the final value is 400,000. Without a lock, increments are
sometimes lost to interleaving: thread A reads N, thread B reads N, both
write N+1 — and one increment vanishes.

Output is a single summary line:
    mode=no-lock threads=4 expected=400000 actual=203076 lost=196924
"""

import argparse
import threading


def increment_no_lock(counter: list, n: int) -> None:
    """Increment counter[0] n times with no synchronization."""
    for _ in range(n):
        # An increment in real code is always at least three steps:
        #   1. read the current value
        #   2. compute the new value
        #   3. write the new value back
        # The small loop in step (2) represents the work you'd normally do
        # between the read and the write — validation, transformation, logging,
        # any non-trivial computation. On modern CPython the GIL does not
        # release inside a very tight loop, so without some work in the
        # critical section the race window is too narrow to observe. Real
        # critical sections in real code always have some amount of work in
        # them, which is exactly when races become visible.
        current = counter[0]                # (1) read
        new_value = current + 1             # (2) compute
        for _ in range(50):                 # (2 cont'd) — represent real work
            pass
        counter[0] = new_value              # (3) write


def increment_with_lock(counter: list, n: int, lock: threading.Lock) -> None:
    """Increment counter[0] n times, holding a lock around each increment."""
    for _ in range(n):
        with lock:
            current = counter[0]
            new_value = current + 1
            for _ in range(50):
                pass
            counter[0] = new_value


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--no-lock", action="store_true")
    group.add_argument("--with-lock", action="store_true")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument(
        "--increments", type=int, default=100000,
        help="increments per thread; default 100000",
    )
    args = parser.parse_args()

    # A single-element list — a mutable container that all threads can share.
    # A bare int wouldn't work because Python ints are immutable; each thread
    # rebinding `counter = counter + 1` would create a new local int and not
    # affect the others.
    counter = [0]
    expected = args.threads * args.increments

    if args.no_lock:
        mode = "no-lock"
        threads = [
            threading.Thread(target=increment_no_lock,
                             args=(counter, args.increments))
            for _ in range(args.threads)
        ]
    else:
        mode = "with-lock"
        lock = threading.Lock()
        threads = [
            threading.Thread(target=increment_with_lock,
                             args=(counter, args.increments, lock))
            for _ in range(args.threads)
        ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    actual = counter[0]
    lost = expected - actual
    print(f"mode={mode} threads={args.threads} "
          f"expected={expected} actual={actual} lost={lost}")


if __name__ == "__main__":
    main()
