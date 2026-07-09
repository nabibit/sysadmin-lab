# Learning Log – sysadmin-lab

*This log is a continuation of my daily progress documentation. Days 1–14 cover the development of my [Network Toolkit](https://github.com/bcyberly/Network_Toolkit) and foundational networking concepts. You can find those entries in the [Network_Toolkit LEARNING_LOG.md](https://github.com/bcyberly/Network_Toolkit/blob/main/docs/LEARNING_LOG.md).*

---

## [2026-03-01] – Day 15: Environment Setup

### Tasks Completed
- Created two new GitHub repositories: [`sysadmin-lab`](https://github.com/bcyberly/sysadmin-lab) and [`ctf-writeups`](https://github.com/bcyberly/ctf-writeups).
- Cloned `sysadmin-lab` locally and set up the basic folder structure (`src/`, `docs/`, `tests/`, `src/scripts/`).
- Added `psutil` to `requirements.txt` for future system monitoring scripts.
- Made the initial commit: `chore: initial repo structure for OS internals`.
- Set up a Linux Ubuntu 22.04 LTS virtual machine using VirtualBox.
- Ensured SSH was enabled and tested connectivity from the Windows host.
- Installed essential monitoring and debugging tools inside the VM: `strace`, `lsof`, `sysstat`, and (attempted) `htop` (accidentally typed `hotp` but corrected later).
- On the Windows side, downloaded and extracted the **Sysinternals Suite** to `C:\Tools\Sysinternals` and added it to the system PATH.

### Commands Used

**Linux VM setup (inside VM):**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install openssh-server -y
sudo apt install htop strace lsof sysstat -y
```

**Windows side (PowerShell as Admin):**
```powershell
# Enable WSL2 (if not already)
wsl --install
wsl --set-default-version 2

# Extract Sysinternals Suite (example)
Expand-Archive -Path .\SysinternalsSuite.zip -DestinationPath C:\Tools\Sysinternals
```

### Screenshots

- **System update in Ubuntu VM:**  
  ![Ubuntu update](images/linux_update_system.png)
- **Installing basic monitoring tools:**  
  ![Installing tools](images/basic_tools_monitoring_and_debugging.png)  
  *(Note: I typed `hotp` by mistake, but the actual tool is `htop`. I corrected it later.)*

### Reflection
- The repository structure follows the same pattern I used for the `Network_Toolkit` project – keeping code, docs, and tests separate feels natural now.
- Setting up the Linux VM was straightforward; the key takeaway is to use a generic hostname (`user-VirtualBox` in the screenshots) to avoid leaking personal info when sharing screenshots.
- Installing the Sysinternals Suite gives me access to powerful Windows internals tools like Process Explorer and Process Monitor – I’ll explore them in later labs.
- This environment is now ready for deeper exploration of processes, system calls, and filesystem internals.

---
## [2026-03-02] – Day 16: Quick strace Exploration

### Concept
- Using `strace` to trace system calls made by a command.
- Understanding how programs interact with the Linux kernel.

### Artifact
- Ran `strace -o ls_strace.txt ls -l /tmp` to capture all system calls made by `ls`.
- Examined the trace with `less`.
- Counted the number of system calls:  

```bash
wc -l ls_strace.txt
```

  Output: **195** lines (each line is one system call).

- Ran `strace echo hello` to see a simpler trace directly in the terminal.

### Key Observations
- The first system call is always `execve` – it loads the program into memory.
- `openat`, `read`, `write`, `close` appear frequently – they handle file access and output.
- `mmap` and `brk` manage memory allocation (e.g., for shared libraries and heap).
- For `ls`, many calls are related to loading `libc.so.6` and reading directory contents.
- The actual directory listing is printed via a `write` to file descriptor 1 (stdout).
- `echo hello` produced a shorter trace, ending with `write(1, "hello\n", 6)`.

### Reflection
- Even a simple command like `ls` makes nearly **200 system calls**. This shows the complexity hidden behind everyday tools.
- `strace` is invaluable for debugging, performance analysis, and learning how programs work at the system level.
- This quick session reinforced the boundary between user space (where our programs run) and kernel space (which provides services via syscalls).

### Commands Used
```bash
strace -o ls_strace.txt ls -l /tmp
less ls_strace.txt
wc -l ls_strace.txt
strace echo hello
```
---
## [2026-03-03] – Day 17: Quick strace Filter Exercise

### Concept
- Using `strace` with the `-e` flag to trace only specific system calls.
- Counting how many times a particular syscall is invoked.

### Artifact
- Ran `strace -e write echo "hello" 2>&1 | head -10` to see only `write` syscalls made by `echo`.
  - Output showed a single `write` call writing `"hello\n"` to file descriptor 1 (stdout).

- Counted the number of `write` syscalls:

```bash
strace -e write echo "hello" 2>&1 | grep write | wc -l
```

  Result: **1** (exactly one `write` call).

### Key Observations
- The `-e write` filter makes `strace` output only the `write` system calls, cutting through the noise of dozens of other syscalls (like memory mapping and library loading).
- `echo "hello"` results in exactly one `write` to stdout – the string plus newline.
- Redirecting stderr to stdout (`2>&1`) is necessary to pipe the trace output to `grep` and `wc`.

### Reflection
- This tiny exercise demonstrates how filtering makes `strace` a precise tool: you can focus on exactly the syscalls you care about (e.g., monitoring file writes or network activity).
- It reinforces that even trivial commands involve kernel interaction – and that you can measure that interaction quantitatively.

### Commands Used
```bash
strace -e write echo "hello" 2>&1 | head -10
strace -e write echo "hello" 2>&1 | grep write | wc -l
```
---
## [2026-03-04] – Day 18: `strace` Deep Dive

### Goal
Use `strace` to observe the system calls of a Python script writing to a file, and understand the interaction between user space and the kernel.

### Tasks Completed
- Created a Python script that writes ten lines to `/tmp/test.log`, with a 1-second delay between writes.
- Attempted to attach `strace` to a background process – encountered `Operation not permitted` due to kernel security restrictions.
- Successfully ran `strace` directly on the script to capture all `write` system calls.
- Examined the output, counted the `write` calls, and verified the file content.
- Used a full strace trace to locate the `openat` call that created the log file.
- Captured a screenshot of the `strace` output for documentation.

### Commands Used

```bash
# Create the script (indentation corrected with nano)
nano /tmp/writer.py
```

```python
import time
with open("/tmp/test.log", "w") as f:
    for i in range(10):
        f.write(f"Line {i}\n")
        f.flush()
        time.sleep(1)
```

```bash
# Run strace directly (no background attach issues)
strace -e write -o strace_output.txt python3 /tmp/writer.py

# View the captured write calls
less strace_output.txt

# Count how many write calls occurred
grep -c write strace_output.txt

# Verify the file content
cat /tmp/test.log

# Full trace to see the open call (optional)
strace -o full_strace.txt python3 /tmp/writer.py
grep open full_strace.txt
```

### Observations
- The `strace_output.txt` contained exactly 10 lines of the form:

```text
write(3, "Line 0\n", 7) = 7
write(3, "Line 1\n", 7) = 7
...
write(3, "Line 9\n", 7) = 7
+++ exited with 0 +++
```

- File descriptor `3` was used for all writes. The full trace showed the file being opened:

```text
openat(AT_FDCWD, "/tmp/test.log", O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC, 0666) = 3
```

  confirming that descriptor 3 pointed to `/tmp/test.log`.

- Each write transferred exactly 7 bytes (`"Line X\n"`) and the kernel returned 7, indicating all bytes were written successfully.
- The script ran for about 10 seconds because of the `sleep(1)` inside the loop; `strace` captured each call as it happened.
- The final file content matched the written lines:

```text
Line 0
Line 1
...
Line 9
```

### Screenshot
Below is a screenshot of the `strace` output as viewed with `less`:

![strace output](images/strace_output.png)

### Reflection
This lab made the boundary between a program and the operating system visible. Every simple file write translates directly into a `write` system call, and the kernel returns the number of bytes actually written. Understanding this is crucial for debugging performance (e.g., too many small writes can slow down an application) and for building mental models of how programs interact with the OS.

The failed attempts to attach to a background process also taught me about Linux security restrictions (`ptrace` scoping) – a useful lesson in itself.

---
## [2026-03-05] – Day 19: PowerShell Scripting & Windows Internals

### Concepts Mastered
- **PowerShell fundamentals:** Cmdlets, object pipeline, parameterized scripts.
- **Windows process introspection:** `Get-Process`, sorting and filtering objects directly.
- **Registry as a filesystem drive:** Accessing `HKLM:` and `HKCU:` Run keys.
- **Building reusable administration tools:** Using `param` blocks for flexible scripts.
- **Error handling in registry queries:** `-ErrorAction SilentlyContinue` for missing keys.

### Artifacts Updated/Created
- Created `src/scripts/ps_process_report.ps1` – exports all running processes to CSV, displays top 5 by CPU and memory, and accepts an optional output path.
- Created `src/scripts/ps_startup.ps1` – queries both HKLM and HKCU Run keys, combines the results, exports to CSV, and prints them to the console.

### Testing – Happy Path
Ran both scripts with default parameters to verify functionality:

```powershell
.\src\scripts\ps_process_report.ps1
```

Expected console output (sample):

```
Total processes: 123
Top 5 by CPU:
Name         CPU
----         ---
ProcessA     45.2
ProcessB     32.1
...
Top 5 by memory (WorkingSet):
Name         WorkingSet
----         ----------
ProcessC     12345678
...
```

CSV file `process_report.csv` generated successfully.

```powershell
.\src\scripts\ps_startup.ps1
```

Expected console output (sample):

```
Key        Name             Value
---        ----             -----
HKLM:Run   SecurityHealth   "C:\Program Files\Windows Defender\..."
HKCU:Run   OneDrive         "C:\Users\user\AppData\Local\Microsoft\..."
...
```

CSV file `startup_programs.csv` generated successfully.

### Testing – Edge Cases (Chaos Monkey)

Intentionally tested script robustness:

- **Missing registry keys:**  

```powershell
# Simulate missing key by temporarily renaming it, or run on a clean VM
.\src\scripts\ps_startup.ps1
```

→ Script runs without error, exports empty CSV (thanks to `-ErrorAction SilentlyContinue`).

- **Invalid output path:**  

```powershell
.\src\scripts\ps_process_report.ps1 -Path "Z:\nonexistent\report.csv"
```

→ Error: `Export-Csv : Could not find a part of the path` – acceptable, as the user should provide a valid path. (Future improvement: add directory creation/validation.)

- **No arguments:** Both scripts default to sensible filenames in the current directory, so they never fail due to missing parameters.

### Reflection
Crossing into Windows scripting felt like learning a new language, but the object‑oriented pipeline is a revelation. Sorting processes by CPU directly on the `CPU` property is far cleaner than parsing text columns in bash. The registry scripts give a practical autoruns tool – directly applicable to security investigations. Learned to handle missing registry keys with `-ErrorAction SilentlyContinue`, making scripts robust. Using the `param` block makes them reusable, and CSV export turns raw data into shareable intelligence. 

### Evidence
**Commits:**

``` 
feat: add PowerShell script to report processes (ps_process_report)
feat: add PowerShell script to list startup programs from registry
```
---
## [2026-03-06] – Day 20: Linux Filesystem Monitoring with inotify

### Concepts Mastered
- **inotify:** Linux kernel subsystem for monitoring filesystem events in real time.
- **Event types:** `CREATE`, `MODIFY`, `DELETE`, `MOVED_FROM`, `MOVED_TO`.
- **inotifywait:** Command‑line tool to wait for events and act on them.
- **Permissions:** Understanding how file ownership affects access (solved with `sudo chown`).

### Artifact
- Created `src/scripts/inotify_logger.sh` – a bash script that monitors a directory and logs all file events with timestamps.

### Commands Used

```bash
# Install inotify-tools
sudo apt update && sudo apt install inotify-tools -y

# Run the monitor (first terminal)
sudo src/scripts/inotify_logger.sh /tmp/test_monitor

# In a second terminal, generate test events
touch /tmp/test_monitor/file1
echo "hello" > /tmp/test_monitor/file1
mv /tmp/test_monitor/file1 /tmp/test_monitor/file2
rm /tmp/test_monitor/file2
```

### Sample Log Output

```
2026-03-06 21:08:52 /tmp/test_monitor/file1 CREATE
2026-03-06 21:14:51 /tmp/test_monitor/file1 MODIFY
2026-03-06 21:22:56 /tmp/test_monitor/file2 CREATE
2026-03-06 21:25:27 /tmp/test_monitor/file1 MOVED_FROM
2026-03-06 21:25:27 /tmp/test_monitor/file2 MOVED_TO
2026-03-06 21:25:41 /tmp/test_monitor/file2 DELETE
```

### Reflection
`inotify` provides real‑time insight into filesystem activity – invaluable for security (file integrity monitoring), automation (triggering backups on file change), and debugging. The script taught me to handle absolute paths, manage permissions (using `sudo chown` to avoid repeated `sudo`), and use `inotifywait` effectively. This complements my earlier `strace` work: both reveal how programs interact with the OS, but `inotify` is event-driven and persistent.

### Evidence
- **Commit (script):** `feat: add inotify filesystem monitoring script`

---

## [2026-03-08] – Day 21: Quick System Stats with vmstat & iostat

### Concepts Mastered
- **vmstat:** Reports virtual memory statistics, including processes, memory, paging, block I/O, traps, and CPU activity.
- **iostat:** Monitors system input/output device load by observing the time devices are active and their transfer rates.
- **Key metrics:** `r` (runnable processes), `free` (free memory), `si/so` (swap in/out), `us/sy` (user/system CPU), `wa` (I/O wait), `%util` (disk utilization), `await` (average I/O response time).

### Artifact
- No new script – this was a hands-on exploration of built-in Linux performance tools.
- Captured real-time output from `vmstat` and `iostat` to understand system behaviour.

### Commands Used
```bash
# Show system statistics every 2 seconds (stop with Ctrl+C)
vmstat 2

# Show extended disk statistics every 1 second
iostat -x 1
```

### Sample Log Output
```
$ vmstat 2
procs -----------memory---------- ---swap-- -----io---- -system-- -------cpu-------
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0      4 141212  24140 1053280    0    0 25203   641 1888   45 14 32 53  1  0
 0  0      4 158264  24156 1053224    0    0     0    92 1265  420  1  1 99  0  0
```

```
$ iostat -x 1
avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           6.81    0.55   17.42    0.79    0.00   74.44

Device            r/s     rkB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wkB/s   wrqm/s  %wrqm w_await wareq-sz     %util
sda            142.45  14275.64    57.21  28.65    0.64   100.21   12.66    395.13    48.93  79.45    1.10    31.22    8.43
```

### Reflection
Running `vmstat` and `iostat` gave me a quick, real-time view of system health. I saw that CPU usage was mostly idle (`id` around 90-99%), memory was plentiful (`free` in the hundreds of MB), and disk I/O was low (`%util` under 10%). The `wa` (I/O wait) column in `vmstat` stayed near zero, confirming no disk bottleneck. These tools are invaluable for spotting performance issues at a glance – high `r` could mean CPU overload, high `si/so` indicates swapping (low memory), and high `%util` suggests a disk bottleneck. This mini-lab adds two more commands to my sysadmin toolkit, complementing `htop`, `strace`, and `inotify`.

---

## [2026-03-09] – Day 22: auditd Introduction

### Concept
- **auditd:** Linux audit daemon that logs security-relevant events (file accesses, system calls, etc.) for monitoring and compliance.
- **Audit rules:** Can be added with `auditctl` to watch files/directories for specific permissions (`r` = read, `w` = write, `a` = attribute change, `x` = execute).
- **ausearch:** Tool to query audit logs based on a key, time, or other criteria.

### Artifact
- Installed `auditd` and `audispd-plugins`.
- Added a rule to monitor `/etc/passwd` for write and attribute changes (`-p wa`).
- Added a test rule on `/tmp/testfile` and generated a write event with `tee`.
- Verified the rule was active and searched the logs with `ausearch`.

### Commands Used
```bash
# Install auditd and plugins
sudo apt update && sudo apt install auditd audispd-plugins -y

# Enable and start the service
sudo systemctl enable auditd && sudo systemctl start auditd

# Add a rule to watch /etc/passwd for write/attribute changes
sudo auditctl -w /etc/passwd -p wa -k passwd_monitor

# Verify active rules
sudo auditctl -l

# Add a test rule on a temporary file
sudo auditctl -w /tmp/testfile -p wa -k test

# Generate an event
echo "hello" | sudo tee /tmp/testfile

# Search the audit log for events with key "test"
sudo ausearch -k test
```

### Observations
- The rule on `/etc/passwd` was added successfully (visible with `auditctl -l`).
- Writing to `/tmp/testfile` via `tee` generated an audit event, which `ausearch` displayed.
- The audit log shows detailed information: timestamp, process name (`tee`), user ID (`auid=1000`), success status, file path, and the rule key.
- The event includes the system call number, arguments, and path information – invaluable for forensics.

### Reflection
`auditd` is a powerful tool for security monitoring. Unlike `inotify` (which is per-process), `auditd` works system-wide and logs events with rich metadata. This makes it ideal for compliance (e.g., monitoring access to sensitive files) and intrusion detection. I now understand how to create rules and query the logs. Next steps: explore `audit.rules` for persistent rules, monitor critical system files, and integrate with log analysis tools.

---

## [2026-03-15] – Day 23: Extending inotify – Action on CREATE

### Goal
Enhance the existing `inotify_logger.sh` script to trigger a custom action (a message) whenever a file is created in the monitored directory, turning a passive logger into an active responder.

### Task Completed
- Modified the `while read event` loop in `inotify_logger.sh` to check for `CREATE` events.
- When a `CREATE` is detected, an extra line is printed to both console and log file.
- Tested by creating a file in `/tmp/test_monitor` and verified the extra message appeared.
- Documented the change in this log.

### Testing Output
```
2026-03-15 22:21:44 /tmp/test_monitor/testfile.txt CREATE
  → A new file was created! (You could run a backup here.)
```

### Troubleshooting & Lessons Learned
During the lab, I ran into three common Linux pitfalls and resolved them:

1. **Error: "Text file busy" (VirtualBox Shared Folder Quirks)**
   - **What happened:** When trying to save the script using a graphical text editor directly inside the `/media/sf_sysadmin-lab/...` shared folder, it failed to save.
   - **Why it happened:** VirtualBox shared folders (`vboxsf`) have strict file locking and permission rules. Graphical editors often try to create hidden temporary backup files when saving, which the shared folder blocks.
   - **The Fix:** Copied the script to my local home directory (`cp ... ~/inotify_logger.sh`), edited it there using the terminal-based `nano` editor, and then copied it back with `sudo cp`.

2. **Error: "command not found" (Execution Path)**
   - **What happened:** Attempted to run `sudo ./inotify_logger.sh` but the terminal threw a "command not found" error.
   - **Why it happened:** The `./` prefix tells Linux to look for the script in the *current working directory*. I was in my home directory (`~`), but the script was in the shared folder.
   - **The Fix:** Navigated to the exact directory where the script lived using `cd /media/sf_sysadmin-lab/src/scripts/` before executing it.

3. **Error: "No such file or directory" (The Typo)**
   - **What happened:** When copying the file, the terminal couldn't find the source path.
   - **Why it happened:** A simple typo in the directory name: I typed `sf_syadmin-lab` instead of `sf_sysadmin-lab` (missing the first 's'). Linux is case‑sensitive and literal.
   - **The Fix:** Double‑checked the spelling and corrected the path in the `cp` command.

### Reflection
This small enhancement demonstrates how a basic monitoring script can be extended to perform actions based on events. The same pattern can be used to trigger backups, send alerts, or start automated workflows. The troubleshooting session reinforced the importance of understanding path resolution, permissions, and the quirks of shared folders.

### Evidence
- **Commit (script):** `feat: inotify logger triggers action on CREATE`

---
## [2026-03-24] – Day 24: System Inventory Tool – Phase 1

### Goal
Create a Python script that gathers basic system information (hostname, OS, CPU, memory) using the `psutil` library, laying the foundation for a cross-platform diagnostic tool.

---

### Task Completed

- Created `src/system_inventory.py` with functions:
  - `get_system_info()` – returns a dict of hostname, OS, architecture, CPU count, memory stats, boot time.
  - `bytes_to_human()` – converts bytes to human-readable MB/GB.
  - `main()` – prints a formatted report.
- Used `platform` module for hostname, OS, architecture.
- Used `psutil` for CPU count, memory, and boot time.
- Installed `psutil` with `pip3 install --user psutil` (system-wide install also possible).
- Tested on Linux VM; output matches expectations.
- Noted cross-platform intent (script works on Windows with same code).

---

### Commands Used

```
# Install psutil (if missing)
pip3 install --user psutil

# Make script executable
chmod +x src/system_inventory.py

# Run the script
python3 src/system_inventory.py
```

---

### Sample Output

```
============================================================
SYSTEM INVENTORY REPORT
============================================================
Hostname          : user-VirtualBox
OS                : Linux 6.8.0-31-generic
Architecture      : x86_64
CPU cores (phys)  : 2
CPU cores (logical): 2
Memory total      : 3.85 GB
Memory available  : 2.14 GB
Memory used       : 1.71 GB
Memory percent    : 44.5%
Boot time         : 2026-03-24 10:15:42
============================================================
```

---

### Reflection

This script is the first step toward a comprehensive inventory tool. The `psutil` library makes it straightforward to retrieve low-level system data, and the `platform` module provides consistent cross-platform identifiers.

Next phases can include:
- Disk usage
- Network interfaces
- Exporting to JSON/CSV

The code is clean, reusable, and human-readable.

### Evidence

- **Commit:** `feat: system inventory tool – basic info`
---

## [2026-06-04] – Day 25: System Inventory Tool – Phase 2 & CLI Routing

### Goal

Upgrade the `system_inventory.py` script from a basic hardware monitor into a scalable, SIEM-ready CLI tool. Fix existing logic bugs in process iteration and implement `argparse` for dynamic JSON and CSV data routing.

### Tasks Completed

* **VirtualBox Shared Folder Troubleshooting:** Resolved `Permission denied` and `Protocol error` roadblocks when accessing the host machine from the Ubuntu VM. Added my user to the `vboxsf` group and manually mounted the shared folder using correct UID/GID mapping and a simplified share name.
* **Bug Fixes:**

  * Corrected the indentation in `get_disk_info()` to ensure the script iterates through all disk partitions rather than exiting after the first loop.
  * Completed the `try/except` block inside `get_top_processes()` to properly handle `psutil.NoSuchProcess`, `psutil.AccessDenied`, and `psutil.ZombieProcess` exceptions, preventing the script from crashing during execution.
* **Argparse Integration:** Added CLI flags to route output formats (`--json`, `--csv`) and control data verbosity (`--limit N`).
* **Data Structuring:** Implemented `json.dumps()` for automated SIEM ingestion and utilized the `csv` module to structure telemetry into discrete columns.

### Commands Used
```bash
**VirtualBox Mount Resolution:**

# Add user to VirtualBox share group

sudo usermod -aG vboxsf $USER


# Manually mount the shared folder bypassing protocol errors

sudo mount -t vboxsf -o uid=$USER,gid=$USER sysadmin /mnt/sysadmin
```

```bash
**Script Execution & Testing:**

# Default human-readable execution

python3 src/system_inventory.py

# Test CLI limit flag

python3 src/system_inventory.py --limit 3

# Output raw JSON for data pipelines

python3 src/system_inventory.py --json
'''

### Sample Output

**Human-Readable (Truncated):**

## ```

## DISK USAGE

/               | ext4     | Total: 24.44 GB   | Used: 46.6%

---

## TOP 3 PROCESSES (by CPU)

PID      | Name                      | CPU %    | Memory %
1        | systemd                   | 0.0      | 0.7
2        | kthreadd                  | 0.0      | 0.0
3        | pool_workqueue_release    | 0.0      | 0.0
=====================================================

'''

**JSON Output (Truncated):**


{
"system": {
"hostname": "user-VirtualBox",
"os_name": "Linux",
"architecture": "x86_64",
"memory_percent": 57.9
},
"disks": [
{
"mountpoint": "/",
"fstype": "ext4",
"percent": 46.6
}
]
}
```

### Reflection

Getting back into the lab environment required overcoming some immediate friction with VirtualBox file permissions, but manually mounting the directory reinforced my understanding of Linux group policies and UID enforcement.

From a coding perspective, Phase 2 transformed the script from a passive script into a highly functional tool. Catching process-level exceptions (`AccessDenied`, `ZombieProcess`) highlighted the chaotic nature of OS scheduling—processes die or change privileges while the script runs, and the code must be resilient enough to handle that. Finally, mapping the output to `--json` was a critical upgrade; in a true Blue Team environment, raw text is useless, but structured JSON can be instantly piped into Splunk, Elastic, or a centralized logging server.

### Evidence

* **Commit:** `enhancement: add disk info, top processes, and CLI options`
---
## [2026-06-11] – Day 26: Network Stats & Disk Alert

### Goal

Extend the system inventory tool to collect network interface statistics and warn when disk usage exceeds a configurable threshold.

### Tasks Completed

- Added `get_network_stats()` – retrieves per-interface bytes sent/received, packets, and errors (skips loopback).
- Integrated network stats into the human-readable report (new section after memory).
- Added `--alert-threshold` argument (e.g., `--alert-threshold 80`). The script checks all disk partitions and prints a warning on console if usage exceeds the threshold.
- Tested by temporarily creating a large file to push disk usage over the threshold – warning appeared as expected.
- Email alert was considered but deferred; console warning is sufficient for now and can be extended later.

### Commands Used

```
# Standard report (includes network stats)
python3 src/system_inventory.py

# Check with alert threshold 50%
python3 src/system_inventory.py --alert-threshold 50
```

### Sample Output (Partial)

```
------------------------------------------------------------
NETWORK INTERFACES
------------------------------------------------------------
enp0s3:
  bytes sent: 2.45 MB
  bytes recv: 1.23 MB
  packets sent: 4567
  packets recv: 4321
  errors in: 0
  errors out: 0
```

When threshold exceeded:

```bash
 WARNING: / is at 85.3% usage (threshold 80%)
```

### Reflection

This turns the passive inventory script into a proactive monitoring tool. Network stats help spot anomalies (e.g., unexpected high traffic on a quiet interface). The disk alert is an early-warning system for low-storage conditions. Future enhancements could include email/SMS alerts and running the script periodically via cron or a systemd timer.

### Evidence

* **Commit:** `feat: add network stats and disk usage alert to inventory`

---

## [2026-06-22] – Day 27: Telemetry Time-Series & Stream Routing

### Goal

Upgrade the static inventory script into a continuous monitoring agent capable of capturing time-series snapshots, streaming flat CSV telemetry to disk, and isolating view logic.

### Tasks Completed

- **The Sampling Subsystem:** Implemented `--repeat N` and `--delay SECONDS` arguments in `argparse` to wrap data collection in an automated time loop.
- **Stream Routing:** Added the `--output FILE` flag to dynamically pipe generated CSV or JSON payloads directly into persistent disk storage.
- **Architecture Refactor:** Decoupled the data-gathering logic from the UI by extracting the heavy console print block out of `main()` and isolating it inside a dedicated `print_report()` view helper.
- **Data Flattening:** Wrote `flatten_snapshot_for_csv()` to map complex, multi-level nested OS objects into a standardized 1D database row.
- **Buffer Safety:** Added smart CSV header detection (`os.path.getsize`) to ensure the agent only writes column headers if the target file is 0 bytes or newly instantiated.

### Commands Used

```
# 1. Visual console heartbeat (3 snapshots, 2s interval)
python3 src/system_inventory.py --repeat 3 --delay 2

# 2. Time-series CSV stream routing to disk (4 snapshots, 1s interval)
python3 src/system_inventory.py --repeat 4 --delay 1 --csv --output metrics_trend.csv

# 3. Batch SIEM JSON gathering
python3 src/system_inventory.py --repeat 2 --delay 1 --json
```

### Sample Output (CSV Telemetry Stream)

```
timestamp,hostname,cpu_logical_cores,memory_used_percent,disk_root_percent,net_total_sent_mb
2026-06-22T17:20:08.461337,user-VirtualBox,1,65.4,49.0,2.08
2026-06-22T17:20:09.525949,user-VirtualBox,1,65.4,49.0,2.08
2026-06-22T17:20:10.580351,user-VirtualBox,1,65.6,48.9,2.08
2026-06-22T17:20:11.624029,user-VirtualBox,1,65.3,48.9,2.08
```

### Reflection

Today marked the definitive transition from writing "scripts" to engineering "agents." Observing live OS scheduling in the terminal—like catching a background package manager spiking the CPU to 53% during pass #2, or watching the RAM micro-fluctuate by 0.2% every second—proved that infrastructure telemetry is a living, breathing stream. Decoupling the view layer made the main loop vastly more readable, and getting the non-blocking file append logic right means this tool can now safely sit as a background daemon scraper in a real production environment.

### Evidence

* **Commit:** `feat: add repeat mode for performance trending`

---

## [2026-06-23] – Day 28: Trend Analysis & HTML Dashboards

### Goal

Create a separate analysis script that ingests the flat CSV telemetry generated by `system_inventory.py` and compiles it into a visual, executive-level HTML dashboard.

### Tasks Completed

- Created `src/trend_report.py` using `argparse` for modular file routing (`--input`, `--output`).
- Implemented a robust CSV parser that automatically scrubs text strings back into mathematical floats.
- Built a statistical engine to compute Minimum, Maximum, and Average utilization for critical infrastructure metrics.
- Utilized `matplotlib` in `Agg` (headless) mode to safely generate graphical line charts on a server without an active GUI display manager.
- Engineered a function to encode the generated PNG chart directly into a Base64 string, allowing the final HTML file to be 100% self-contained with no external image dependencies.
- **Troubleshooting:** Encountered the PEP 668 `externally-managed-environment` error when trying to use `pip3 install matplotlib`. Resolved it securely by using the OS-native package manager (`apt install python3-matplotlib`) to protect the Linux kernel's global Python environment.

### Commands Used

```
# Securely install matplotlib on modern Ubuntu (PEP 668 compliant)
sudo apt update && sudo apt install python3-matplotlib -y

# Generate the executive dashboard from previously collected telemetry
python3 src/trend_report.py --input src/metrics_trend.csv --output src/trend_report.html
```

### Reflection

This script closes the loop on the monitoring pipeline: **Collect → Store → Analyze → Visualize.** Figuring out how to bypass the need for external `.png` files by injecting Base64 text directly into the HTML was a major breakthrough—it means I can email this single `.html` file to a manager or security lead, and the graphs will render perfectly offline. Also, dealing with PEP 668 was a great lesson in modern Linux environment management; overriding system protections with pip is a bad habit, and using `apt` for system-wide libraries is the proper sysadmin approach.

### Evidence

* **Commit:** `feat: add trend analysis and base64 HTML dashboard`

---

## [2026-06-26] – Day 29: Telemetry Dashboard & OverTheWire Bandit

### Goal

Create a web dashboard for real-time system monitoring using Flask, overcoming local networking security blocks, and initiate foundational cybersecurity wargames (OverTheWire).

### Tasks Completed

- Structured a new `src/dashboard/` directory with a Flask backend (`app.py`) and an HTML/JS frontend (`index.html`).
- Engineered a REST API endpoint (`/api/stats`) that serves live OS data from the `system_inventory` module as a JSON payload.
- Designed a minimal, dark-themed "Onyx Ace" UI that polls the API every 5 seconds using the JavaScript Fetch API.
- **Troubleshooting:** Encountered and bypassed `SSL_ERROR_RX_RECORD_TOO_LONG` caused by Firefox's aggressive HTTPS-Only mode forcing an SSL handshake onto a local HTTP server. Verified the backend health using raw `curl` commands.
- Established a professional `.gitignore` ruleset to prevent `venv/` and `__pycache__/` pollution in the repository.
- Successfully connected to OverTheWire wargames via SSH on port `2220` and retrieved the Level 0 flag.
- Drafted a formal SOC-style incident write-up for Bandit Level 0.

### Commands Used

```
# Safely create and activate a virtual environment (Ubuntu)
sudo apt install python3-venv
python3 -m venv ~/moteur_dashboard
source ~/moteur_dashboard/bin/activate

# Install dependencies from requirements
pip install -r requirements.txt

# Start the Flask telemetry server
python3 src/dashboard/app.py

# Verify API payload bypassing browser SSL interference
curl http://127.0.0.1:5000/api/stats

# Connect to OverTheWire Bandit Level 0
ssh bandit0@bandit.labs.overthewire.org -p 2220
```

### Reflection

Today was a massive leap from writing local scripts to building actual network-facing services. The biggest lesson wasn't writing the Python code, but understanding how modern browsers enforce security protocols (HTTPS) and how to bypass them for local development using `curl`. Seeing my raw Linux kernel metrics visually update on a web page via an API I built is incredibly satisfying. Furthermore, completing the first OverTheWire challenge officially kicks off the offensive security (Red Team) side of my training.

### Evidence

* **Commits:**
  * `feat: implement telemetry dashboard and Bandit Level 0 writeup`
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
---

## [2026-07-07] – Day 31: Real-Time Charts & Bandit Level 2

### Goal

Add dynamic line charts for CPU and memory usage using Chart.js to visualize live telemetry over time. Complete OverTheWire Bandit Level 2.

### Tasks Completed

- Integrated the Chart.js library via CDN into the frontend dashboard (`index.html`).
- Updated the `/api/stats` endpoint in `app.py` to calculate real-time CPU utilization using `psutil.cpu_percent(interval=1)`, avoiding meaningless instantaneous 0% readings.
- Added standard project versioning headers (`Created`/`Updated` timestamps) across modified scripts to maintain strict documentation standards.
- Injected two canvas elements into `index.html` to house the CPU and RAM visualization charts within the responsive grid layout.
- Engineered a JavaScript rolling-window array engine (`MAX_POINTS = 20`) that shifts out legacy timestamps as new telemetry arrives every 5 seconds, preventing client-side memory leaks.
- Verified DOM rendering, API polling, and chart responsiveness against local port 5000.
- Connected to OverTheWire Bandit Level 2 via SSH; navigated bash word-splitting rules by quoting filenames with spaces (`cat "spaces in this filename"`).
- Published formal SOC-style incident write-up for Bandit Level 2.

### Commands Used

```
# Execute local test server
python3 run_dashboard.py

# OverTheWire Level 2 execution
ssh bandit2@bandit.labs.overthewire.org -p 2220
ls -la
cat "spaces in this filename"

# Alternative method verified using escape characters
cat "./--spaces in this filename--"
```

### Reflection

Adding Chart.js transformed the dashboard from a static snapshot tool into an active observability monitor. Implementing the rolling data window in JavaScript (`shift()` and `push()`) was a great practical lesson in managing memory footprint on the client side—without capping the array at 20 points, a long-running dashboard tab would eventually cause browser performance degradation. On the Linux side, Bandit Level 2 reinforced the mechanics of bash argument parsing and why robust system administration scripts must always quote variable expansions and file paths.

### Evidence

* **Commits:**
  * `feat: add real-time CPU and memory charts`
  * `docs: add bandit level 2 writeup`

---


## [2026-07-08] – Day 32: Disk & Network Telemetry, Bandit Level 3

### Goal

Extend the Flask dashboard to monitor storage partition utilization and active IPv4 network interfaces. Complete OverTheWire Bandit Level 3.

### Tasks Completed

- Updated `/api/stats` in `app.py` to iterate over system disk partitions using `psutil.disk_partitions()`.
- Added logic to ignore loopback storage mounts (`loop`) and handle `PermissionError` gracefully on restricted system mounts.
- Integrated `psutil.net_if_addrs()` with `socket.AF_INET` filtering to isolate active IPv4 network interface allocations while excluding the loopback interface (`lo`).
- Added standard project versioning headers (`Created`/`Updated` timestamps) across modified files.
- Injected dedicated DOM cards for Disk Usage and Network Interfaces into `index.html`.
- Implemented responsive JavaScript progress bars that dynamically adjust colour based on storage utilization thresholds (<60% green, >60% orange, >80% red).
- Verified API polling and DOM manipulation against the local test server on port 5000 (confirmed disk threshold warnings on `/dev/sr0` and `/`).
- Connected to OverTheWire Bandit Level 3 via SSH, navigated the directory structure, and used `ls -la` to reveal the hidden file `...Hiding-From-You`.
- Published a formal SOC-style incident write-up for Bandit Level 3.

### Commands Used

```
# Execute local test server
python3 run_dashboard.py

# OverTheWire Level 3 execution
ssh bandit3@bandit.labs.overthewire.org -p 2220
cd inhere
ls -la
cat ...Hiding-From-You
```

### Reflection

Expanding the dashboard to monitor disk usage and network interfaces transformed it into a more practical systems administration tool. Handling `PermissionError` while iterating over disk partitions reinforced that some system mounts remain inaccessible even to the current user and must be handled gracefully. On the security side, Bandit Level 3 highlighted the importance of the `-a` option with `ls`; hidden files are commonly overlooked during manual inspections, making thorough enumeration an essential habit.

### Evidence

* **Commits:**
  * `feat: add disk and network stats to dashboard`
  * `docs: add bandit level 3 writeup`

---
## [2026-07-09] – Day 33: Top Processes Monitoring & Bandit Level 4

### Goal
Extend the Flask telemetry dashboard with a live Top CPU Processes monitor to improve observability during performance investigations. Complete OverTheWire Bandit Level 4.

### Tasks Completed
- Added a new `/api/processes` REST endpoint to expose live process information as JSON.
- Used `psutil.process_iter()` to enumerate running processes while safely handling `NoSuchProcess`, `AccessDenied`, and `ZombieProcess` exceptions.
- Sorted running processes by CPU utilization and returned the top 10 entries.
- Added a responsive "Top Processes" table to the dashboard frontend displaying:
  - PID
  - Process Name
  - CPU Usage
  - Memory Usage
- Implemented asynchronous JavaScript polling to refresh process information independently from the hardware telemetry.
- Added a Pause/Resume button allowing the operator to temporarily stop automatic dashboard refreshes while inspecting live data.
- Verified dashboard behaviour against the Ubuntu VM, confirming live CPU spikes matched the processes consuming resources.
- Connected to OverTheWire Bandit Level 4 and identified the only human-readable file using the Linux `file` utility.
- Documented the complete investigation inside the Bandit Level 4 write-up.

### Commands Used

```bash
# Start dashboard
python3 run_dashboard.py
```

### Reflection

Today's improvements transformed the dashboard from a hardware monitoring page into a practical troubleshooting tool. CPU graphs immediately become actionable when paired with a live process table because resource spikes can be traced back to the exact running process. Adding the pause/resume functionality also improved usability by allowing telemetry to be frozen during investigations without stopping the backend server.

Bandit Level 4 reinforced another essential Linux administration concept: filenames cannot be trusted. Instead of relying on names or extensions, the `file` utility inspects the actual file contents, making it an indispensable command for system administration, incident response, and digital forensics.

### Evidence

**Commits:**

- `feat: add top processes view`
- `docs(ctf): add bandit level 4 writeup`
---