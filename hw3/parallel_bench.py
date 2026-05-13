#!/usr/bin/env python3
"""
parallel_bench.py — Compare serial, threading, and multiprocessing execution
                    on CPU-bound and I/O-bound workloads.

Usage:
    ./parallel_bench.py --workload {cpu|io} \\
                        --mode {serial|threading|multiprocessing} \\
                        --workers N

Each worker performs the same amount of work. In serial mode they run one
after another. In threading mode they run in parallel threads, sharing one
Python interpreter and one GIL. In multiprocessing mode they run as separate
processes, each with its own Python interpreter and its own GIL.

Output ends with one summary line, e.g.
    workload=cpu mode=threading workers=4 cpu_work=200000 time=8.41s
"""

import argparse
import multiprocessing
import threading
import time


def cpu_task(work_amount: int) -> int:
    """CPU-bound: count primes up to work_amount via trial division.

    This is pure Python — no I/O, no NumPy, nothing that releases the GIL.
    Time is dominated by Python interpreter execution. That makes it a
    clean test of whether threading provides parallelism for CPU-bound work.
    """
    count = 0
    for i in range(2, work_amount):
        is_prime = True
        j = 2
        while j * j <= i:
            if i % j == 0:
                is_prime = False
                break
            j += 1
        if is_prime:
            count += 1
    return count


def io_task(sleep_seconds: float) -> None:
    """I/O-bound: simulate a blocking I/O call by sleeping.

    Crucially, time.sleep() releases the GIL while waiting. Real blocking
    I/O calls (socket reads, file reads) do the same. That's why threading
    works for I/O-bound code despite the GIL.
    """
    time.sleep(sleep_seconds)


def run_serial(target, args, workers):
    for _ in range(workers):
        target(*args)


def run_threading(target, args, workers):
    threads = [threading.Thread(target=target, args=args) for _ in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def run_multiprocessing(target, args, workers):
    procs = [multiprocessing.Process(target=target, args=args) for _ in range(workers)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--workload", required=True, choices=["cpu", "io"])
    parser.add_argument("--mode", required=True,
                        choices=["serial", "threading", "multiprocessing"])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--cpu-work", type=int, default=200000,
        help="(cpu workload) prime-counting upper limit per worker; default 200000",
    )
    parser.add_argument(
        "--io-time", type=float, default=1.0,
        help="(io workload) seconds to sleep per worker; default 1.0",
    )
    args = parser.parse_args()

    if args.workers < 1:
        parser.error("--workers must be positive")

    if args.workload == "cpu":
        target = cpu_task
        target_args = (args.cpu_work,)
        work_desc = f"counting primes up to {args.cpu_work}"
    else:
        target = io_task
        target_args = (args.io_time,)
        work_desc = f"sleeping {args.io_time}s"

    runners = {
        "serial": run_serial,
        "threading": run_threading,
        "multiprocessing": run_multiprocessing,
    }

    print(f"starting {args.workload} workload, {args.mode} mode, "
          f"{args.workers} workers ({work_desc} each)")
    print("(watch htop now if you want to see core utilization)")

    start = time.perf_counter()
    runners[args.mode](target, target_args, args.workers)
    elapsed = time.perf_counter() - start

    if args.workload == "cpu":
        print(f"workload=cpu mode={args.mode} workers={args.workers} "
              f"cpu_work={args.cpu_work} time={elapsed:.2f}s")
    else:
        print(f"workload=io mode={args.mode} workers={args.workers} "
              f"io_time={args.io_time} time={elapsed:.2f}s")


if __name__ == "__main__":
    main()
