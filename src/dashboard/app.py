#!/usr/bin/env python3
# Project: sysadmin-lab – System Dashboard
# Purpose: Provide a web interface for system monitoring.
# Created: 2026-06-26
# Updated: 2026-07-09 (added top 10 CPU process monitoring endpoint)

import sys
import os
import socket
import psutil
from flask import Flask, jsonify, render_template

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import system_inventory

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    """Return live OS metrics as a JSON payload, including CPU, Disk, and Network stats."""
    try:
        info = system_inventory.get_system_info()
        mem = psutil.virtual_memory()
        info['memory_used_percent'] = mem.percent
        info['cpu_percent'] = psutil.cpu_percent(interval=1)

        # Disk Info
        disks = []
        for part in psutil.disk_partitions():
            # Skip loop devices and CD-ROMs
            if 'loop' in part.device or part.fstype == '':
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    'device': part.device,
                    'mount': part.mountpoint,
                    'used_percent': usage.percent,
                    'total_gb': round(usage.total / (1024**3), 1),
                    'used_gb': round(usage.used / (1024**3), 1),
                    'free_gb': round(usage.free / (1024**3), 1)
                })
            except PermissionError:
                continue
        info['disks'] = disks

        # Network Interfaces (IPv4)
        net = {}
        for iface, addrs in psutil.net_if_addrs().items():
            if iface == 'lo':
                continue
            ipv4_addrs = [addr.address for addr in addrs if addr.family == socket.AF_INET]
            if ipv4_addrs:
                net[iface] = ipv4_addrs
        info['network'] = net

        return jsonify(info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/processes')
def processes():
    """Return the top 10 processes sorted by CPU utilization descending."""
    try:
        procs = []
        # Iterate over all running processes, fetching only required attributes
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Ignore processes that terminate or deny access during iteration
                continue
        
        # Sort by CPU percentage descending and slice the top 10
        procs_sorted = sorted(procs, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]
        return jsonify(procs_sorted), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)