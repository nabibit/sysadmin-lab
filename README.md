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
| `system_inventory.py` | Gathers system information (hostname, OS, CPU, memory, disk, top processes, network stats) with CLI options (`--json`, `--csv`, `--output`, `--limit`, `--alert-threshold`). | `python src/system_inventory.py --json --alert-threshold 80` |

**Dependencies:**
- `psutil` – install with `pip install psutil` (or `pip3 install --user psutil`).
---