#!/bin/bash

# 1. Navigate to the directory where this script (and the python script) is located
cd "$(dirname "$0")"

# 2. Activate the virtual environment
# (Assumes you created one named 'venv' inside this folder)
source venv/bin/activate

# 3. Run the Python script
python3 arc_event_tracker.py >> cron_log.txt 2>&1
