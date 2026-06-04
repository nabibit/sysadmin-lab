#!/usr/bin/env python3
# Project: sysadmin-lab - System Inventory Tool
# Purpose: Collect and display system information (OS, CPU, memory)
# Created: 2026-03-24
# Updated: 2026-06-04
# Complexity/Performance: O(1) - uses psutil to query kernel stats efficiently

import platform
import psutil
import datetime
import argparse
import json

def get_system_info() -> dict:
    """
    Gather core system hardware and OS information.

    Returns:
        dict: A dictionary containing hostname, OS details, CPU counts,
              memory statistics, and formatted system boot time.
    """
    # We query virtual_memory once and store it to avoid multiple expensive system calls
    mem = psutil.virtual_memory()

    info = {
        # Using the built-in 'platform' module here because it natively handles
        # OS-level string formatting better across Windows and Linux
        'hostname': platform.node(),
        'os_name': platform.system(),
        'os_release': platform.release(),
        'architecture': platform.machine(),

        # logical=True counts hyperthreaded/virtual cores, which is what the OS schedule tasks on
        'cpu_count_logical': psutil.cpu_count(logical=True),
        # logical=False counts only actual physical hardware cores
        'cpu_count_physical': psutil.cpu_count(logical=False),

        'memory_total': mem.total,
        'memory_available': mem.available,
        'memory_percent': mem.percent,

        # boot_time returns a raw Unix timestamp. We parse it into a datetime object
        # and format it to ISO 8601 standard so it's instantly readable by a human.
        'boot_time': datetime.datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
    }
    return info

def bytes_to_human(bytes_val: float) -> str:
    """
    Convert raw byte values into dynamically scaled human-readable formats.

    Args:
        bytes_val (foat/int): The raw size in bytes

    Returns: 
        str: A formatted string representing the scaled size with its appropiate unit (e.g., '16.00 GB').
    """
    # Using a loop here instead of hardcoded if/elif blocks makes the function
    # highly scalable. It automatically formats to the highest whole unit.
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        # We use 1024 instead of 1000 because operating systems calculate RAM and storage in base-2.
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024

    #Fallback for extremely large data sets (Petabytes)
    return f"{bytes_val:.2f} PB"

def get_disk_info() -> list:
    """
    Gather disk partition and usage information.
    Ignores loop devices and handles permission errors gracefully.
    """
    partitions = []
    for part in psutil.disk_partitions():
        # Skip loop devices (common in Linux snaps) to keep output clean
        if part.fstype and 'loop' not in part.device:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    'device': part.device,
                    'mountpoint': part.mountpoint,
                    'fstype': part.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except PermissionError:
                # Some system partitions deny access without admin/root rights
                continue
        return partitions
    
def get_top_processes(limit: int = 10, sort_by: str = 'cpu') -> list:
    """
    Get the top running processes sorted by CPU or memory usage.
    Handles processes that terminate during the query.
    """
    processes = []
    # process_iter is safer than grabbing all PIDs at once (prevents race conditions)
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            pinfo = proc.info
            # Ensure None values are converted to 0.0 for accurate sorting
            pinfo['cpu_percent'] = pinfo['cpu_percent'] or 0.0
            pinfo['memory_percent'] = pinfo['memory_percent'] or 0.0
            processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # Sort descending based on the requested metric
    if sort_by == 'memory':
        processes = sorted(processes, key=lambda p: p['memory_percent'], reverse=True)
    else:
        processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)
        
    return processes[:limit]

def main():
    """Main execution block configuring CLI arguments and report formatting."""
    # Add argparse for CLI options
    parser = argparse.ArgumentParser(description="System Inventory Tool")
    parser.add_argument('--json', action='store_true', help='Output report in JSON format')
    parser.add_argument('--csv', action='store_true', help='Output report in CSV format')
    parser.add_argument('--limit', type=int, default=10, help='Limit the number of top processes shown')
    args = parser.parse_args()

    # Aggregate all data
    inventory = {
        'system': get_system_info(),
        'disks': get_disk_info(),
        'processes': get_top_processes(limit=args.limit)
    }

    # Handle output routing based on CLI flags
    if args.json:
        print(json.dumps(inventory, indent=4))
        
    elif args.csv:
        writer = csv.writer(sys.stdout)
        writer.writerow(['Category', 'Metric', 'Value'])
        for key, val in inventory['system'].items():
            writer.writerow(['System', key, val])
        for disk in inventory['disks']:
            writer.writerow(['Disk', disk['mountpoint'], f"{disk['percent']}% used"])
        for proc in inventory['processes']:
            writer.writerow(['Process', proc['name'], f"CPU: {proc['cpu_percent']}%"])
            
    else:
        # Default Human-Readable Output
        print("=" * 60)
        print("SYSTEM INVENTORY REPORT")
        print("=" * 60)

        info = inventory['system']
        print(f"Hostname              : {info['hostname']}")
        print(f"OS                    : {info['os_name']} {info['os_release']}")
        print(f"Architecture          : {info['architecture']}")
        print(f"CPU cores (phys)      : {info['cpu_count_physical']}")
        print(f"CPU cores (logical)   : {info['cpu_count_logical']}")
        print(f"Memory total          : {bytes_to_human(info['memory_total'])}")
        print(f"Memory available      : {bytes_to_human(info['memory_available'])}")
        print(f"Memory percent        : {info['memory_percent']}%")
        print(f"Boot time             : {info['boot_time']}")
        
        print("\n" + "-" * 60)
        print("DISK USAGE")
        print("-" * 60)
        for disk in inventory['disks']:
            print(f"{disk['mountpoint']:<15} | {disk['fstype']:<8} | Total: {bytes_to_human(disk['total']):<10} | Used: {disk['percent']}%")
            
        print("\n" + "-" * 60)
        print(f"TOP {args.limit} PROCESSES (by CPU)")
        print("-" * 60)
        print(f"{'PID':<8} | {'Name':<25} | {'CPU %':<8} | {'Memory %':<8}")
        for proc in inventory['processes']:
            print(f"{proc['pid']:<8} | {proc['name'][:25]:<25} | {proc['cpu_percent']:<8.1f} | {proc['memory_percent']:<8.1f}")
        print("=" * 60)
    
if __name__ == "__main__":
    main()