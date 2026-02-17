#!/bin/bash

# -----------------------------------
# Script to run FatCheck and log output
# -----------------------------------

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create logs folder if it doesn't exist
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Set log file name with timestamp
LOG_FILE="$LOG_DIR/app_$(date +'%Y%m%d_%H%M%S').log"

# Run Python directly from venv (safer than source for .desktop)
"$SCRIPT_DIR/mp_env/bin/python" "$SCRIPT_DIR/main.py" >> "$LOG_FILE" 2>&1

