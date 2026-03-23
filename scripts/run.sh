#!/bin/bash

# --- CONFIGURATION ---
VENV_DIR="venv"
REQ_FILE="requirements.txt"
NS_SCRIPT="scripts/namespace-inventory.py"
WL_SCRIPT="scripts/workloads-inventory.py"

echo "-------------------------------------------------------"
echo "🚀 Starting Kubernetes Inventory Audit"
echo "-------------------------------------------------------"

# 1. Check/Create Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# 2. Activate Environment
echo "🔄 Activating environment..."
source $VENV_DIR/bin/activate

# 3. Update Dependencies
if [ -f "$REQ_FILE" ]; then
    echo "📥 Installing dependencies from $REQ_FILE..."
    pip install -q -r $REQ_FILE
else
    echo "⚠️  $REQ_FILE not found. Installing base requirements..."
    pip install -q kubernetes pandas
fi

# 4. Check Minikube Connection
echo "☸️  Checking Kubernetes connection..."
if ! kubectl cluster-info > /dev/null 2>&1; then
    echo "❌ Error: Cannot connect to Kubernetes. Is Minikube running?"
    exit 1
fi

# 5. Execute Scripts
echo "-------------------------------------------------------"
echo "📊 Running Namespace Audit..."
python3 $NS_SCRIPT

echo ""
echo "📊 Running Workload Audit..."
python3 $WL_SCRIPT
echo "-------------------------------------------------------"

# 6. Summary
echo "✅ Audit Complete!"
echo "📂 Files generated in current directory:"
ls -lh *.csv *.json 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'
echo "-------------------------------------------------------"

# Deactivate venv
deactivate
