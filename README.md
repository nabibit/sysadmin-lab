# sysadmin-lab

A hands‑on practice repository for system administration fundamentals, focusing on Linux and Windows internals, process management, resource monitoring, and OS‑level debugging. This lab accompanies my self‑study in preparation for security and operations roles.

## Purpose
- Explore core OS concepts: processes, filesystems, permissions, system calls.
- Practice with essential tools: `htop`, `strace`, `lsof`, `ps`, `kill`, and the Sysinternals Suite.
- Document daily progress, commands, and observations in the [learning log](docs/LEARNING_LOG.md).

## Repository Structure
- `src/` – Python scripts and small utilities used during experiments.
- `docs/` – Learning log and screenshots from lab exercises.
- `tests/` – (future) Unit tests for any tools developed.
- `requirements.txt` – Python dependencies (currently only `psutil`).

## Getting Started
1. Clone the repo:
```bash
git clone https://github.com/bcyberly/sysadmin-lab.git
cd sysadmin-lab
```

2. (Optional) Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

3. Explore the Linux VM as described in the learning log.

## Tools & Environments
- **Linux VM**: Ubuntu 22.04 LTS (VirtualBox) for process tracing and filesystem exploration.
- **Sysinternals Suite**: Process Explorer, Process Monitor, and other advanced Windows tools.

---
## Scripts

Located in `src/scripts/`:

| Script | Purpose | Example Usage |
|--------|---------|---------------|
| `ps_process_report.ps1` | Exports all running processes to CSV and prints the top 5 by CPU and memory usage. | ```.\src\scripts\ps_process_report.ps1 -Path "report.csv"``` |
| `ps_startup.ps1` | Queries both HKLM and HKCU Run keys for startup programs, exports to CSV, and displays them. | ```.\src\scripts\ps_startup.ps1 -Path "startup.csv"``` |
| `inotify_logger.sh` | Monitors a directory (default `/tmp/test_monitor`) for file events (create, modify, delete, move) and logs them with timestamps. | ```sudo ./src/scripts/inotify_logger.sh /path/to/watch``` |

**Dependencies:**
- PowerShell scripts require **PowerShell** (built into Windows).  
- `inotify_logger.sh` requires **inotify-tools** (install via ```bash sudo apt install inotify-tools -y ``` on Linux).  

**Usage examples:**

- **PowerShell:**
```powershell
.\src\scripts\ps_process_report.ps1 -Path "my_report.csv"
.\src\scripts\ps_startup.ps1 -Path "startup.csv"
```

- **Bash (Linux):**
```bash
sudo ./src/scripts/inotify_logger.sh /tmp/watch_dir
```

## Python Tools

Located in `src/` (Python scripts that can be run directly or imported as modules):

| Script | Purpose | Example Usage |
|--------|---------|---------------|
| `system_inventory.py` | Gathers point-in-time system info or runs continuous time-series telemetry (OS, CPU, memory, disk, network). Includes CLI routing (`--json`, `--csv`, `--output`, `--repeat`, `--delay`). | `python3 src/system_inventory.py --repeat 60 --delay 1 --csv --output trend.csv` |
| `trend_report.py` | Ingests telemetry CSVs and compiles a standalone, executive HTML dashboard with Base64-encoded `matplotlib` trend charts and summary statistics. | `python3 src/trend_report.py --input trend.csv --output report.html` |
| `dashboard/app.py` | Modernised Flask web interface exposing live OS metrics via REST API (`/api/stats`). Features a responsive, two-column grid UI with a dynamic colour-changing progress bar for RAM utilisation. | `python3 run_dashboard.py` then open `http://127.0.0.1:5000` |

**Dependencies:**

- `psutil` – Install via `pip install psutil`.
- `matplotlib` – Used for headless graph generation in `trend_report.py`.
  - *Note for modern Linux users (PEP 668 compliance):* Install via OS package manager instead of pip to protect global environments:
    `sudo apt install python3-matplotlib -y`
- `Flask` – Used for the telemetry web dashboard (install via `pip install flask`).
---

## [2026-06-29] – Day 30: Dashboard UI & Bandit Level 1

### Goal

Enhance the Flask dashboard with a modern UI, grid layout, and dynamic progress bar. Complete Bandit Level 1.

---

### Tasks Completed

- Updated the `/api/stats` endpoint in `app.py` to calculate `memory_used_percent` using `psutil`.
- Redesigned `index.html` with:
  - Responsive two-column grid layout.
  - Memory usage progress bar with dynamic colouring:
    - Green: under 60%
    - Orange: over 60%
    - Red: over 80%
  - Automatic refresh every five seconds using `setInterval()`.
- Tested the dashboard on `http://127.0.0.1:5000` and verified live updates from the API.
- Connected to Bandit Level 1 over SSH and learned how to read a file named `-` using:
  - `cat ./-`
- Wrote a formal Bandit Level 1 walkthrough.

---

### Commands Used

```
# Install dependencies
pip install flask psutil

# Launch dashboard
python3 run_dashboard.py

# Connect to Bandit Level 1
ssh bandit1@bandit.labs.overthewire.org -p 2220

# List files
ls -la

# Read file named "-"
cat ./-
```

---

### Reflection

Today's work highlighted the difference between simply making code run and designing software properly.

Completing Bandit Level 1 also reinforced how Unix interprets `-` as standard input and why relative paths such as `./-` are required when filenames would otherwise be ambiguous.

---

### Evidence

- **Commits:**
  - `feat: display basic system stats with progress bar`
  - `docs: add Bandit Level 1 write-up`