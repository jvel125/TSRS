#!/usr/bin/env bash
# Start the TrustedSky backend API server
set -e

cd "$(dirname "$0")/backend"

echo "→ Installing dependencies…"
pip install -r requirements.txt -q

echo "→ Seeding database with demo data…"
python seed.py

echo "→ Starting API server on http://127.0.0.1:8000"
echo "   Frontend served at http://127.0.0.1:8000"
echo ""
echo "   Demo credentials:"
echo "     Email:    demo@trustedsky.com"
echo "     Password: demo1234"
echo ""
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
