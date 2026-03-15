#!/usr/bin/env bash
set -euo pipefail

# run_ui.sh — start Streamlit app and optionally ngrok, with virtualenv support
# Usage: ./run_ui.sh

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "Project dir: $PROJECT_DIR"

# Load .env if present (export variables into the environment)
if [ -f ".env" ]; then
  echo "Loading .env file..."
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

# Activate virtualenv if it exists
if [ -f "project_env/bin/activate" ]; then
  echo "Activating virtualenv project_env..."
  # shellcheck source=/dev/null
  source project_env/bin/activate
else
  echo "No virtualenv found at project_env; continuing with system Python"
fi

echo "Installing Python dependencies (this is no-op if already installed)..."
pip install -r requirements.txt

mkdir -p runs/logs

echo "Starting Streamlit (background)..."
nohup /usr/bin/python3 -m streamlit run app.py --server.headless true --server.port 8501 --server.address 0.0.0.0 > runs/logs/streamlit.log 2>&1 &
echo $! > runs/streamlit.pid
sleep 2

# Start ngrok if NGROK_AUTHTOKEN provided (either in env or .env file)
if [ -n "${NGROK_AUTHTOKEN:-}" ]; then
  echo "NGROK_AUTHTOKEN is set — starting ngrok (background)..."
  # ensure authtoken is configured (idempotent)
  ngrok config add-authtoken "$NGROK_AUTHTOKEN" || true
  nohup ngrok http 8501 > runs/logs/ngrok.log 2>&1 &
  echo $! > runs/ngrok.pid
  echo "ngrok started (logs: runs/logs/ngrok.log)"
else
  echo "NGROK_AUTHTOKEN not set — skipping ngrok startup. To enable, set NGROK_AUTHTOKEN in your environment or .env file."
fi

echo "Started. Streamlit log: runs/logs/streamlit.log"
echo "To stop: kill $(cat runs/streamlit.pid) ; if ngrok started, kill $(cat runs/ngrok.pid)"
