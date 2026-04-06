#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Bootstrapping inference-lab..."

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
python3 -m pip install --upgrade pip

# Install dependencies
python3 -m pip install -r requirements.txt

# Ensure app is a package
touch app/__init__.py

echo "✅ Bootstrap complete"
echo "👉 Run: source venv/bin/activate"
