# CS 503 HW3: Systems Investigation Lab Report


---

## Overview

The first two assignments asked you to **do** things — write commands, build scripts. This one asks you to **see** things. You'll run a series of provided programs that exercise specific parts of the operating system, observe how Linux responds using the tools you've been collecting (`ps`, `htop`, `/proc`, `time`), and write up what you saw and what it means.

You are not writing code for this assignment. You're producing a lab report. The grade is on the quality of your observations and the depth of your explanations — not on whether your code "works."

There are three experiments. Each one takes roughly **60–90 minutes** if you're paying attention. Plan accordingly.

---

## What you'll need

You'll be working on Tux. The experiments use commands you've used before (`ps`, `htop`, `kill`, `time`) plus a few new ones (`pstree`, examining `/proc/[pid]/maps`).

**Two terminal windows on Tux** is the minimum. You'll often run a program in one and observe it from the other. A `tmux` session with split panes is ideal — you can use the workflow you'd use for any long-running remote task.

**A shared-system note.** Tux is a shared machine. Several of these experiments could be made dramatic by allocating enormous amounts of memory or spawning enormous numbers of processes. **Don't.** The numbers and limits in each experiment are deliberately chosen to be informative without disrupting other users. Stay within them. If you find a result interesting and want to push further, ask me first.

---

## Setup

From inside the `hw3/` directory:

```bash
./setup.sh
```

This verifies that Python 3.8+ is available, checks that required modules import, confirms the system tools you'll need are on `PATH`, makes the scripts executable, and creates the `output/` directory tree where you'll save evidence.

If setup reports problems, fix them before continuing — most experiments depend on the Python environment being correct.

The setup script also copies `report-template.md` to `report.md` on first run. **Edit `report.md`, not the template.**

---

## Deliverables

A single file: **`hw3/report.md`**, based on the structure in `report-template.md`.

Each experiment section in the template has spaces for your observations, references to captured output, and your answers to the questions.

You will also produce **supporting files in `output/`**:

- Command output saved with `>` redirection or `tee`
- Output from `script` sessions if you used them
- Screenshots — only if a screenshot makes a point that text can't (e.g., a snapshot of `htop` showing core utilization)

Reference these files by path in your report (e.g., "see `output/exp2/maps.txt`"). Don't paste enormous outputs directly into the report.

---

# Experiments

## Experiment 1: Process Creation and Observation (28 points)

**Goal:** Develop a working mental model of what a "process" is — how Linux represents it, what states it can be in, how it relates to other processes, and what signals do to it.

**Tools:** `ps`, `pstree`, `htop`, `kill`, `scripts/spawner.py`

### Procedure

1. In Terminal A, run:
   ```bash
   ./scripts/spawner.py family 3 60
   ```
   This creates a parent process that spawns 3 child processes, each of which sleeps 60 seconds.

2. In Terminal B, use `ps -ef` to find the parent and children. Identify the **PID** and **PPID** for each. Verify the relationships with `pstree -p <parent-pid>`. Save the output:
   ```bash
   pstree -p <parent-pid> > output/exp1/family-tree.txt
   ps -ef | grep spawner >> output/exp1/family-tree.txt
   ```

3. Send `SIGTERM` to one of the children:
   ```bash
   kill -TERM <child-pid>
   ```
   Observe it disappear from `ps`.

4. Send `SIGSTOP` to another child:
   ```bash
   kill -STOP <child-pid>
   ps -o pid,stat,cmd -p <child-pid>
   ```
   Note the state code in the `STAT` column. Then resume it with `kill -CONT <child-pid>` and check again. Save before/after to `output/exp1/`.

5. **The orphan demo.** Re-run the spawner. In Terminal B, kill **only the parent process**. The surviving children should still be running. Run `ps -ef | grep spawner` and look at their new PPID. **What is it? What does that process do?** Save the output to `output/exp1/orphan.txt`.

6. **The zombie demo.** Run:
   ```bash
   ./scripts/spawner.py zombie
   ```
   This forks a child that exits quickly while the parent intentionally fails to call `wait()`. In Terminal B, observe the zombie:
   ```bash
   ps -o pid,ppid,stat,cmd | grep -E 'Z|spawner'
   ```
   Save the output to `output/exp1/zombie.txt`. Then let the parent exit and confirm the zombie disappears.

### Questions

1. Why does Linux distinguish between `SIGTERM` and `SIGKILL`? What can a process do with `SIGTERM` that it cannot do with `SIGKILL`?
2. When you killed the parent in step 5, the children kept running. What process became their new parent, and why?
3. Describe what a zombie process is in your own words. Why does it exist at all — why doesn't the OS just remove the entry when a process exits?

---

## Experiment 2: Virtual Memory and Physical Memory (28 points)

**Goal:** Understand the distinction between an address-space reservation (VSZ) and physical RAM use (RSS), and develop a working intuition for how the memory hierarchy affects program performance.

**Tools:** `ps`, `/proc/[pid]/maps`, `time`, `scripts/memory_eater.py`

> **Shared-system note.** Do **not** intentionally drive Tux into swap thrashing — that affects every user on the system. The script's defaults stay well below that point. Stick with the numbers below.

### Procedure

1. **Lazy allocation.** Run:
   ```bash
   ./scripts/memory_eater.py lazy 2000 --hold 60
   ```
   This allocates a 2 GB array and immediately sleeps without touching it.

   In another terminal:
   ```bash
   ps -o pid,vsz,rss,cmd -p <pid> > output/exp2/lazy.txt
   ```
   Record VSZ and RSS.

2. **Eager allocation.** Run:
   ```bash
   ./scripts/memory_eater.py eager 2000 --hold 60
   ```
   This fills the allocated memory before sleeping. Capture VSZ and RSS again to `output/exp2/eager.txt`.

3. **Memory map.** While the eager version is still running, examine its memory map:
   ```bash
   cat /proc/<pid>/maps | head -30 > output/exp2/maps.txt
   ```
   Identify regions you recognize — code (`r-xp`), heap (`rw-p`), stack.

4. **Sequential vs random access.** Run:
   ```bash
   time ./scripts/memory_eater.py sequential 500
   time ./scripts/memory_eater.py random 500
   ```
   Both walk through a 500 MB array, performing the same number of reads — but one in order and one in random order. Record the wall clock times in `output/exp2/timings.txt`.

### Questions

1. RSS was much smaller than VSZ in the lazy run but close to it in the eager run. Walk through what was actually allocated in each case, and define **demand paging** using your lazy-mode observations as evidence.
2. Your timings should show random access being substantially slower than sequential access on the same amount of data. Explain why, using what you know about the memory hierarchy. Specifically reference **cache lines**.
3. From the `/proc/<pid>/maps` output, identify and describe one region with permissions `r-xp` and one with `rw-p`. What kind of content lives in each, and why do they have those specific permissions?

---

## Experiment 3: Threads, Multiprocessing, and the GIL (28 points)

**Goal:** Experience the difference between threading and multiprocessing in Python, and understand why the same parallelism strategy works for some workloads and not others.

**Tools:** `time`, `htop`, `scripts/parallel_bench.py`, `scripts/race_demo.py`

### Procedure

1. **Baseline (serial).**
   ```bash
   ./scripts/parallel_bench.py --workload cpu --mode serial --workers 4
   ```
   Note the wall clock time and CPU usage in `htop`. Save the output to `output/exp3/cpu-serial.txt`.

2. **CPU-bound with threading and multiprocessing.**
   ```bash
   ./scripts/parallel_bench.py --workload cpu --mode threading --workers 4
   ./scripts/parallel_bench.py --workload cpu --mode multiprocessing --workers 4
   ```
   Save outputs as `cpu-threading.txt` and `cpu-multiprocessing.txt`.

3. **I/O-bound, same three modes.**
   ```bash
   ./scripts/parallel_bench.py --workload io --mode serial --workers 4
   ./scripts/parallel_bench.py --workload io --mode threading --workers 4
   ./scripts/parallel_bench.py --workload io --mode multiprocessing --workers 4
   ```
   Save outputs as `io-serial.txt`, `io-threading.txt`, `io-multiprocessing.txt`.

4. **Watch `htop` during each parallel run.** Note how many CPU cores show meaningful activity. A screenshot or a sentence is fine.

5. **The race-condition demo.** Each run starts 4 threads that each increment a shared counter 100,000 times. With perfect synchronization, the result is always 400,000. Without a lock, it usually isn't:
   ```bash
   for i in 1 2 3 4 5; do ./scripts/race_demo.py --no-lock; done > output/exp3/race-no-lock.txt
   for i in 1 2 3 4 5; do ./scripts/race_demo.py --with-lock; done > output/exp3/race-with-lock.txt
   ```

### Questions

1. Compare your CPU-bound and I/O-bound results. Threading speeds up I/O-bound work but not CPU-bound work. Why? What is the GIL doing differently in each case?
2. Looking at `htop` during the multiprocessing CPU run, how many CPU cores were active? How does this differ from the threading run? Explain in terms of what `multiprocessing` does that `threading` doesn't.
3. Trace through what could happen at the level of individual reads, additions, and writes that produces an incorrect count in the no-lock case. (Hint: the increment isn't a single instruction — it's a read, an add, and a write, and the threads can interleave those steps.)

---

## Reflection (16 points)

In one or two paragraphs, answer:

- Which experiment most changed your mental model of how computers work?
- What's one thing you learned that you'll remember the next time you write a program — even a high-level one in Python or a Jupyter notebook?
- What would you want to investigate next that the experiments here didn't cover?

There are no wrong answers in this section. It's graded on whether your reflection is specific and connected to what you actually saw — not on its conclusions.

---

# Grading rubric

| Section | Points |
|---|---|
| Experiment 1: Process creation and observation | 28 |
| Experiment 2: Virtual vs physical memory | 28 |
| Experiment 3: Threads, multiprocessing, GIL | 28 |
| Reflection | 16 |
| **Total** | **100** |

Within each experiment:

| Component | Points |
|---|---|
| Captured output and observations | 10 |
| Answers to the three questions | 15 |
| Output files referenced and present | 3 |

**A complete observation does more than note that the experiment ran.** "The PIDs were 12847 (parent) and 12848, 12849, 12850 (children), all with PPID 12847" is a good observation. "I ran the script" is not.

**A complete answer connects observation to course concepts.** "Random access was slower" is not an answer. "Random access was about 8× slower because each access misses the cache and must fetch a new 64-byte line from RAM, and there's no spatial locality to amortize that fetch over neighboring accesses" is.

---

# Submission

This assignment lives in the `hw3/` directory of your CS 503 course repository. To submit:

```bash
git add hw3/
git commit -m "HW3 submission"
git push
```

Your push timestamp is your submission timestamp. Make sure your final commit is in well before the deadline — don't fight Git in the last 10 minutes.

# Late policy

Standard course policy: late passes apply automatically. See the syllabus for details.

# Help

Questions about the assignment, the tools, or what a question is really asking: bring them to office hours, post on the course channel, or email me. Don't sit stuck for hours — these experiments are meant to be illuminating, not painful.
