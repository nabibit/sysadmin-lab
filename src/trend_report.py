#!/usr/bin/env python3
# Project: sysadmin-lab - Trend Report Generator
# Purpose: Parse telemetry CSVs into a visual executive HTML dashboard
# Created: 2026-06-23

import argparse
import csv
import os
import base64
import io
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Headless mode for servers (no GUI required)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# DATA INGESTION
def read_csv(filename: str) -> list:
    """Reads the telemetry CSV and converts numeric strings to floats."""
    if not os.path.exists(filename):
        print(f"[!] Error: Could not find {filename}")
        return []
        
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        data = [row for row in reader]
        
    # Scrub the data: convert string numbers to actual floats
    for row in data:
        for key, val in row.items():
            if key == 'timestamp' or key == 'hostname':
                continue
            try:
                row[key] = float(val)
            except ValueError:
                pass
    return data


# 2. ANALYSIS & VISUALIZATION
def compute_summary(data: list, key: str):
    """Calculates min, max, and average for a specific metric."""
    values = [row[key] for row in data if key in row and isinstance(row[key], float)]
    if not values:
        return None, None, None
    return min(values), max(values), sum(values) / len(values)

def create_chart(data: list) -> str:
    """Plots memory and disk trends, returning a Base64 image string."""
    timestamps = [datetime.fromisoformat(row['timestamp']) for row in data]
    memory = [row.get('memory_used_percent', 0) for row in data]
    disk = [row.get('disk_root_percent', 0) for row in data]

    # Build the graph
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(timestamps, memory, label='Memory Used %', color='blue', marker='o', linewidth=2)
    ax.plot(timestamps, disk, label='Root Disk %', color='red', marker='s', linewidth=2)
    
    # Format the graph
    ax.set_title('Infrastructure Telemetry Trends', fontsize=14, fontweight='bold')
    ax.set_xlabel('Timestamp', fontsize=12)
    ax.set_ylabel('Utilization (%)', fontsize=12)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save chart to RAM instead of disk, encode to Base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return img_base64

# 3. HTML GENERATION & EXECUTION
def generate_html(data: list, img_base64: str, output_file: str):
    """Compiles the metrics and chart into a standalone HTML dashboard."""
    metrics = ['memory_used_percent', 'disk_root_percent', 'net_total_sent_mb']
    
    summary_rows = ""
    for metric in metrics:
        minv, maxv, avgv = compute_summary(data, metric)
        if minv is not None:
            summary_rows += f"<tr><td>{metric}</td><td>{minv:.2f}</td><td>{maxv:.2f}</td><td>{avgv:.2f}</td></tr>\n"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>System Telemetry Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 40px; }}
            .container {{ background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 900px; margin: auto; }}
            h1, h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #3498db; color: white; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .chart-container {{ text-align: center; margin-top: 30px; }}
            img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; padding: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1> System Telemetry Report</h1>
            <p><strong>Total Snapshots Analyzed:</strong> {len(data)}</p>
            
            <h2> Summary Statistics</h2>
            <table>
                <tr><th>Metric</th><th>Minimum</th><th>Maximum</th><th>Average</th></tr>
                {summary_rows}
            </table>
            
            <h2> Trend Chart</h2>
            <div class="chart-container">
                <img src="data:image/png;base64,{img_base64}" alt="Telemetry Trend Chart">
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html)
    print(f"[+] Executive report successfully generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate Executive HTML Trend Report")
    parser.add_argument('--input', required=True, help='Input CSV telemetry file')
    parser.add_argument('--output', default='trend_report.html', help='Output HTML file')
    args = parser.parse_args()

    print(f"[*] Analyzing telemetry data from {args.input}...")
    data = read_csv(args.input)
    
    if not data:
        print("[!] Aborting: No telemetry data to process.")
        return
        
    print("[*] Rendering Base64 trend charts...")
    img_b64 = create_chart(data)
    
    print("[*] Compiling HTML dashboard...")
    generate_html(data, img_b64, args.output)

if __name__ == "__main__":
    main()