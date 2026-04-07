#!/bin/bash

# --- CONFIGURATION ---
VENV_NAME="venv"
REQ_FILE="requirements.txt"

echo "🚀 Starting Migration Analysis Environment Setup..."

# 1. Check if venv exists, if not create it
if [ ! -d "$VENV_NAME" ]; then
    echo "📦 Creating virtual environment: $VENV_NAME..."
    python3 -m venv $VENV_NAME
else
    echo "✅ Virtual environment already exists."
fi

# 2. Activate the environment
source $VENV_NAME/bin/activate

# 3. Upgrade pip and install requirements
echo "📥 Updating dependencies..."
pip install --upgrade pip
if [ -f "$REQ_FILE" ]; then
    pip install -r $REQ_FILE
else
    echo "⚠️  $REQ_FILE not found!"
    exit 1
fi

# 4. Launch Jupyter Lab
echo "----------------------------------------------------"
echo "✨ Setup Complete. Launching Jupyter Lab..."
echo "💡 Hint: Open your .ipynb file from the sidebar."
echo "----------------------------------------------------"

jupyter lab migration_analysis.ipynb
