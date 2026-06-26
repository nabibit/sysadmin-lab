#!/usr/bin/env python3
# Project: sysadmin-lab – System Dashboard
# Purpose: : Provide a web interface for system monitoring, visualising stats from system_inventory.py.
# Created: 2026-06-26

import sys
import os
from flask import Flask, jsonify, render_template

# Add the parent directory (src/) to the Python path so we can import system_inventory
# This works because app.py is in src/dashboard/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import system_inventory

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    """Return live OS metrics as a JSON payload."""
    try:
        data = system_inventory.get_system_info()
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # host='0.0.0.0' makes it accessible from other devices on the network.
    # debug=True auto-reloads on code changes (useful for development).
    app.run(host='0.0.0.0', port=5000, debug=True)