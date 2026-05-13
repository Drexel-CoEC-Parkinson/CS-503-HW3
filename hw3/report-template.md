# CS 503 HW3 — Systems Investigation Lab Report

**Name:**  
**Date:**  
**Repo commit:**

> Copy this template to `report.md` (the `setup.sh` script does this on first run) and fill it in.  
> Leave the section headers intact — the grader uses them to navigate.  
> Reference supporting files in `output/` by path rather than pasting large outputs inline.

---

## Experiment 1: Process Creation and Observation

### Observations

Describe what you saw. Include PIDs and PPIDs, state codes, what happened when you sent each signal. Reference saved output files in `output/exp1/`.

### Saved output

- `output/exp1/family-tree.txt` — pstree + ps -ef output for the family run
- `output/exp1/orphan.txt` — ps output showing the new PPID after killing the parent
- `output/exp1/zombie.txt` — ps output showing the zombie state
- _(add the rest of your files here)_

### Question 1.1 — SIGTERM vs SIGKILL

_Why does Linux distinguish between them? What can a process do with SIGTERM that it cannot do with SIGKILL?_

### Question 1.2 — The orphan's new parent

_When you killed the parent, the children kept running. What process became their new parent, and why?_

### Question 1.3 — Zombies

_Describe what a zombie process is in your own words. Why does it exist at all — why doesn't the OS just remove the entry when a process exits?_

---

## Experiment 2: Virtual Memory and Physical Memory

### Observations

Record VSZ and RSS for the lazy and eager runs. Record wall clock times for sequential vs random. Note one or two interesting regions from `/proc/<pid>/maps`.

### Saved output

- `output/exp2/lazy.txt` — ps output during the lazy run
- `output/exp2/eager.txt` — ps output during the eager run
- `output/exp2/maps.txt` — /proc/<pid>/maps excerpt
- `output/exp2/timings.txt` — sequential vs random wall clock times
- _(add the rest)_

### Question 2.1 — VSZ vs RSS, and demand paging

_RSS was much smaller than VSZ in the lazy run but close to it in the eager run. Walk through what was actually allocated in each case, and define demand paging using your lazy-mode observations as evidence._

### Question 2.2 — Random vs sequential access

_Explain why random access was substantially slower than sequential access on the same amount of data. Specifically reference cache lines._

### Question 2.3 — Memory regions

_From the /proc/<pid>/maps output, describe one region with permissions `r-xp` and one with `rw-p`. What kind of content lives in each, and why do they have those specific permissions?_

---

## Experiment 3: Threads, Multiprocessing, and the GIL

### Observations

Record wall clock times for each of the six runs (serial / threading / multiprocessing × CPU / I/O). Note what htop showed during each. Record the race demo counts across the five no-lock and five with-lock runs.

### Saved output

- `output/exp3/cpu-serial.txt`, `cpu-threading.txt`, `cpu-multiprocessing.txt`
- `output/exp3/io-serial.txt`, `io-threading.txt`, `io-multiprocessing.txt`
- `output/exp3/race-no-lock.txt`, `race-with-lock.txt`
- _(htop screenshots if you took them)_

### Timings table

| Workload | Mode | Wall clock time (s) |
|---|---|---|
| CPU | serial | |
| CPU | threading | |
| CPU | multiprocessing | |
| I/O | serial | |
| I/O | threading | |
| I/O | multiprocessing | |

### Question 3.1 — The asymmetry: CPU-bound vs I/O-bound

_Threading speeds up I/O-bound work but not CPU-bound work. Why? What is the GIL doing differently in each case?_

### Question 3.2 — What multiprocessing buys you

_Looking at htop during the multiprocessing CPU run, how many CPU cores were active? How does this differ from the threading run? Explain in terms of what multiprocessing does that threading doesn't._

### Question 3.3 — Tracing the race

_Trace through what could happen at the level of individual reads, additions, and writes that produces an incorrect count in the no-lock case._

---

## Reflection

_(1–2 paragraphs)_

_Which experiment most changed your mental model? What will you remember the next time you write even a high-level program? What would you want to investigate next?_
