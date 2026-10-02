#!/usr/bin/env bash
# Chạy toàn bộ ứng dụng (backend + giao diện). Lần đầu sẽ tự cài thư viện.
set -e
cd "$(dirname "$0")/.."

if [ ! -d backend/.venv ]; then
  echo ">> Cài thư viện backend..."
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -q -r backend/requirements.txt
fi
if [ ! -d frontend/node_modules ]; then
  echo ">> Cài thư viện giao diện..."
  (cd frontend && npm install)
fi

trap 'kill 0' EXIT
(cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000) &
(cd frontend && npm run dev -- --port 3000) &
echo ">> Mở trình duyệt: http://localhost:3000   (Ctrl+C để dừng)"
wait
