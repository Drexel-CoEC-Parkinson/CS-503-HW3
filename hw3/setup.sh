#!/bin/bash
#
# CS 503 HW3 — Environment verification and setup
#
# Run this once after cloning the assignment to verify your environment
# is ready and to create the output directory tree. Safe to re-run.

set -u

cd "$(dirname "$0")"

echo "=== CS 503 HW3 setup ==="
echo

# ---------------------------------------------------------------------
# 1. Find Python 3
# ---------------------------------------------------------------------
PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
fi

if [ -z "$PYTHON" ]; then
    echo "ERROR: No python3 found on PATH."
    echo "       On Tux this should be available by default — let your instructor know."
    exit 1
fi

# ---------------------------------------------------------------------
# 2. Check Python version (need 3.8+ to keep parity with course tooling)
# ---------------------------------------------------------------------
"$PYTHON" - <<'PYEOF' || exit 1
import sys
if sys.version_info < (3, 8):
    print(f"ERROR: Python 3.8 or later required (found {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}).")
    sys.exit(1)
print(f"OK : Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
PYEOF

# ---------------------------------------------------------------------
# 3. Check required Python modules
# ---------------------------------------------------------------------
"$PYTHON" - <<'PYEOF' || exit 1
import importlib, sys
missing = []
for mod in ["multiprocessing", "threading", "numpy"]:
    try:
        importlib.import_module(mod)
    except ImportError:
        missing.append(mod)
if missing:
    print(f"ERROR: Missing Python modules: {', '.join(missing)}")
    print("       Install with: pip install --user <module>")
    sys.exit(1)
print("OK : required Python modules importable")
PYEOF

# ---------------------------------------------------------------------
# 4. Check system tools
# ---------------------------------------------------------------------
echo
missing_tools=()
for cmd in ps htop pstree free time kill; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "OK : $cmd"
    else
        echo "WARN: $cmd not found on PATH"
        missing_tools+=("$cmd")
    fi
done

if [ ${#missing_tools[@]} -gt 0 ]; then
    echo
    echo "Note: some tools above were not found. Most experiments have alternates"
    echo "      (e.g. 'top' instead of 'htop'), but on Tux these should all exist."
    echo "      Let your instructor know if any are missing."
fi

# ---------------------------------------------------------------------
# 5. Make scripts executable
# ---------------------------------------------------------------------
echo
if [ -d scripts ]; then
    chmod +x scripts/*.py 2>/dev/null || true
    echo "OK : scripts/*.py made executable"
else
    echo "WARN: scripts/ directory not found — your repo may be incomplete."
fi

# ---------------------------------------------------------------------
# 6. Create output directory tree
# ---------------------------------------------------------------------
mkdir -p output/exp1 output/exp2 output/exp3
echo "OK : output/ directory tree ready"

# ---------------------------------------------------------------------
# 7. Copy report template if report.md doesn't exist
# ---------------------------------------------------------------------
if [ ! -f report.md ]; then
    if [ -f report-template.md ]; then
        cp report-template.md report.md
        echo "OK : report.md created from template — edit report.md, not the template"
    else
        echo "WARN: report-template.md not found — cannot create report.md"
    fi
else
    echo "OK : report.md already exists, leaving it alone"
fi

echo
echo "=== Setup complete ==="
echo
echo "Next steps:"
echo "  1. Read README.md"
echo "  2. Begin Experiment 1 — open two terminals on Tux to start"
echo
