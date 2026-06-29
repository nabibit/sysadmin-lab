#!/usr/bin/env python3
# Project: sysadmin-lab – System Dashboard
# Purpose: Provide a web interface for system monitoring.
# Created: 2026-06-26
# Updated: 2026-06-29

import sys
import os
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
    """Return live OS metrics as a JSON payload."""
    try:
        info = system_inventory.get_system_info()
        mem = psutil.virtual_memory()
        info['memory_used_percent'] = mem.percent
        return jsonify(info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)