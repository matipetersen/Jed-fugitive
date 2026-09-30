#!/bin/bash

# Launch script for Echoes of the Fallen (Jedi Fugitive)
# This ensures proper terminal setup and environment

cd "$(dirname "$0")"

# Set PYTHONPATH
export PYTHONPATH="$PYTHONPATH:$(pwd)/src"

# Ensure we have a proper terminal
if [ -z "$TERM" ]; then
    export TERM=xterm-256color
fi

# Clear screen first
clear

# Launch the game
python3 -m jedi_fugitive.main

# Return exit code
exit $?
