#!/bin/bash

set -e

VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"

# ---------------------------------
#  Create the Virtual Environment
# ---------------------------------

echo "Creating virtual environment in $VENV_DIR..."
python3 -m venv "$VENV_DIR"

# ---------------------------------
#  Activate the VENV
# ---------------------------------

echo "Activating virtual environment..."
source "$VENV_DIR"/bin/activate

# -------------------------------------------
#  Install Dependencies from requirments.txt
# -------------------------------------------

if [ -f "$REQUIREMENTS_FILE" ]; then
	echo "Installing dependencies from $REQUIREMENTS_FILE..."
	pip install -r "$REQUIREMENTS_FILE"
else
	echo "WARNING: the requirements file, $REQUIREMENTS_FILE, wasnot found."
fi

echo "Deployment of virtual environment complete, and activated"
