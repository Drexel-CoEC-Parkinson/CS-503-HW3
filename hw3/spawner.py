#!/usr/bin/env python3
"""
spawner.py — Process creation, signals, orphans, and zombies.

Usage:
    ./spawner.py family <num_children> <sleep_seconds>
    ./spawner.py zombie [hold_seconds]

Modes:
    family   Fork N child processes that each sleep for the given duration.
             Used for the family/signals/orphan demos: send signals to the
             children, or kill the parent and watch the children get adopted
             by init (PID 1).

    zombie   Fork a single child that exits immediately. The parent
             intentionally does NOT call wait(), so the child becomes a
             zombie. The parent then sleeps so you can observe the zombie
             state in ps. After the hold period the parent exits, at which
             point init reaps the zombie.

This script uses os.fork() and only runs on Unix-like systems.
"""

import argparse
import os
import sys
import time


def family(num_children: int, sleep_seconds: int) -> None:
    """Parent forks num_children children, each sleeping sleep_seconds."""
    print(f"[parent] PID={os.getpid()}")
    child_pids = []

    for i in range(num_children):
        pid = os.fork()
        if pid == 0:
            # We are the child. os.fork() returned 0 in the child.
            print(f"[child {i}] PID={os.getpid()} PPID={os.getppid()} sleeping {sleep_seconds}s")
            time.sleep(sleep_seconds)
            print(f"[child {i}] PID={os.getpid()} exiting")
            sys.exit(0)
        else:
            # We are the parent. os.fork() returned the child's PID.
            child_pids.append(pid)
            print(f"[parent] forked child {i} with PID {pid}")

    print(f"[parent] {num_children} children spawned, waiting for them to finish")
    print(f"[parent] (try: ps -ef | grep spawner   or:   pstree -p {os.getpid()})")

    # Wait for each child. If the parent is killed externally during this loop
    # (the orphan demo), the children become orphans and continue running
    # until they exit on their own; init (PID 1) then reaps them.
    for pid in child_pids:
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            # Already reaped somehow — skip.
            pass

    print("[parent] all children finished, exiting")


def zombie(hold_seconds: int) -> None:
    """Fork one child that exits immediately; parent does NOT call wait()."""
    print(f"[parent] PID={os.getpid()}")

    pid = os.fork()
    if pid == 0:
        # Child exits immediately. With no wait() from the parent, this
        # process becomes a zombie (state Z) until something reaps it.
        print(f"[child] PID={os.getpid()} exiting immediately (will become a zombie)")
        sys.exit(0)

    # Parent: deliberately do NOT call wait(). Sleep so the zombie is observable.
    print(f"[parent] forked child {pid} and will NOT call wait() on it")
    print(f"[parent] observe the zombie with:")
    print(f"[parent]   ps -o pid,ppid,stat,cmd | grep -E 'Z|spawner'")
    print(f"[parent] holding for {hold_seconds}s, then exiting (init reaps the zombie)")
    time.sleep(hold_seconds)
    print("[parent] exiting now")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    family_p = sub.add_parser("family", help="fork N children that sleep")
    family_p.add_argument("num_children", type=int)
    family_p.add_argument("sleep_seconds", type=int)

    zombie_p = sub.add_parser("zombie", help="fork a child that becomes a zombie")
    zombie_p.add_argument("hold_seconds", type=int, nargs="?", default=60)

    args = parser.parse_args()

    if args.mode == "family":
        if args.num_children < 1 or args.sleep_seconds < 1:
            sys.exit("num_children and sleep_seconds must be positive")
        family(args.num_children, args.sleep_seconds)
    elif args.mode == "zombie":
        if args.hold_seconds < 1:
            sys.exit("hold_seconds must be positive")
        zombie(args.hold_seconds)


if __name__ == "__main__":
    main()
