#!/usr/bin/env python3
# Project: sysadmin-lab - System Inventory Tool
# Purpose: Collect and display system information (OS, CPU, memory)
# Created: 2026-03-24
# Updated: 2026-06-22 (Day 27 Refactor - Repeat Mode & Stream Routing)
# Complexity/Performance: O(1) - uses psutil to query kernel stats efficiently

import platform
import psutil
import datetime
import argparse
import json
import os
import time

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

def get_network_stats() -> dict:
    """Gather network I/O statistics per interface, excluding loopback."""
    stats = {}
    counters = psutil.net_io_counters(pernic=True)
    for iface, data in counters.items():
        if iface == 'lo':  # Skip local loopback traffic to keep reports clean
            continue
        stats[iface] = {
            'bytes_sent': data.bytes_sent,
            'bytes_recv': data.bytes_recv,
            'packets_sent': data.packets_sent,
            'packets_recv': data.packets_recv,
            'errin': data.errin,
            'errout': data.errout,
        }
    return stats

def send_alert_email(subject: str, body: str):
    """
    Sends an SMTP email alert. 
    Currently configured to print to console as a mock for Mailtrap/SMTP testing.
    """
    print(f"\n[MOCK EMAIL ALERT TRIGGERED]")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print("[END MOCK EMAIL]\n")

def check_disk_threshold(disks: list, threshold: float):
    """Check if any disk exceeds the threshold and trigger warnings/alerts."""
    for disk in disks:
        if disk['percent'] > threshold:
            warning_msg = f"CRITICAL: {disk['mountpoint']} is at {disk['percent']}% usage (Threshold: {threshold}%)"
            print(f"  {warning_msg}")
            
            # Trigger the email alert subsystem
            send_alert_email(
                subject=f"Disk Usage Alert: {platform.node()}", 
                body=warning_msg
            )

def flatten_snapshot_for_csv(timestamp: str, info: dict, disks: list, network: dict) -> dict:
    """Transforms nested OS dictionaries into a single flat CSV row."""
    # Find the root disk '/' safely
    root_disk = next((d for d in disks if d['mountpoint'] == '/'), disks[0] if disks else {})
    total_sent = sum(d['bytes_sent'] for d in network.values())

    return {
        'timestamp': timestamp,
        'hostname': info['hostname'],
        'cpu_logical_cores': info['cpu_count_logical'],
        'memory_used_percent': info['memory_percent'],
        'disk_root_percent': root_disk.get('percent', 0.0),
        'net_total_sent_mb': round(total_sent / (1024 * 1024), 2)
    }

def print_report(info: dict, disks: list, network: dict, processes: list, limit: int):
    """Renders the standard visual dashboard to the console."""
    print(f"Hostname              : {info['hostname']}")
    print(f"OS                    : {info['os_name']} {info['os_release']}")
    print(f"Memory total          : {bytes_to_human(info['memory_total'])}")
    print(f"Memory available      : {bytes_to_human(info['memory_available'])}")
    print(f"Memory percent        : {info['memory_percent']}%")
    
    print("\n" + "-" * 60 + "\nDISK USAGE\n" + "-" * 60)
    for d in disks:
        print(f"{d['mountpoint']:<15} | {d['fstype']:<8} | Total: {bytes_to_human(d['total']):<10} | Used: {d['percent']}%")
        
    print("\n" + "-" * 60 + "\nACTIVE NETWORK INTERFACES\n" + "-" * 60)
    for iface, data in network.items():
        print(f"Interface: {iface} -> Recv: {bytes_to_human(data['bytes_recv'])} | Sent: {bytes_to_human(data['bytes_sent'])}")
        
    print("\n" + "-" * 60 + f"\nTOP {limit} PROCESSES (by CPU)\n" + "-" * 60)
    print(f"{'PID':<8} | {'Name':<25} | {'CPU %':<8} | {'Memory %':<8}")
    for p in processes:
        print(f"{p['pid']:<8} | {p['name'][:25]:<25} | {p['cpu_percent']:<8.1f} | {p['memory_percent']:<8.1f}")
    print("=" * 60)

def main():
    """Main execution block configuring CLI arguments and report formatting."""
    # Add argparse for CLI options
    parser = argparse.ArgumentParser(description="System Inventory Tool")
    parser.add_argument('--json', action='store_true', help='Output report in JSON format')
    parser.add_argument('--csv', action='store_true', help='Output report in CSV format')
    parser.add_argument('--limit', type=int, default=10, help='Limit the number of top processes shown')
    parser.add_argument('--alert-threshold', type=float, default=95.0, help='Disk usage % threshold to trigger alerts (Default: 95)')
    parser.add_argument('--output', type=str, help='Target file path to save CSV or JSON data')
    parser.add_argument('--repeat', type=int, default=1, help='Number of snapshots to execute')
    parser.add_argument('--delay', type=int, default=5, help='Seconds to pause between runs')
    args = parser.parse_args()

   # Create an empty box to catch JSON snapshots over time
    json_accumulator = []

    # START THE TIME LOOP
    for iteration in range(1, args.repeat + 1):
        timestamp = datetime.datetime.now().isoformat()
        
        # Grab live metrics for this exact second
        info = get_system_info()
        disks = get_disk_info()
        network = get_network_stats()
        processes = get_top_processes(limit=args.limit)

        if not args.json and not args.csv:
            check_disk_threshold(disks, args.alert_threshold)

        # ROUTE A: JSON Accumulator
        if args.json:
            json_accumulator.append({
                'timestamp': timestamp, 'system': info, 'disks': disks, 'network': network, 'processes': processes
            })

        # ROUTE B: Flat CSV stream
        elif args.csv:
            row = flatten_snapshot_for_csv(timestamp, info, disks, network)
            header_str = ",".join(row.keys()) + "\n"
            line_str = ",".join(str(val) for val in row.values()) + "\n"

            if args.output:
                # Check if file is completely new so we only write headers once
                needs_header = not os.path.exists(args.output) or os.path.getsize(args.output) == 0
                with open(args.output, 'a') as f:
                    if needs_header:
                        f.write(header_str)
                    f.write(line_str)
            else:
                if iteration == 1:
                    print(",".join(row.keys()))
                print(",".join(str(val) for val in row.values()))

        # ROUTE C: Human Console
        else:
            print(f"\n{' SNAPSHOT ' + str(iteration) + '/' + str(args.repeat) + ' ':=^60}")
            print_report(info, disks, network, processes, args.limit)

        # Enforce the delay (skip sleeping on the final loop)
        if iteration < args.repeat:
            time.sleep(args.delay)

    # If we were gathering JSON, dump the array to file or console
    if args.json:
        payload = json.dumps(json_accumulator, indent=4)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(payload)
        else:
            print(payload)
    
if __name__ == "__main__":
    main()