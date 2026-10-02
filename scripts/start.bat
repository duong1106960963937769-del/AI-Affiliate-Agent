@echo off
chcp 65001 >nul
cd /d "%~dp0.."

where python >nul 2>nul
if errorlevel 1 (
  echo [LOI] Chua cai Python. Tai tai https://www.python.org/downloads/ va tick "Add python.exe to PATH" khi cai.
  pause & exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo [LOI] Chua cai Node.js. Tai ban LTS tai https://nodejs.org roi chay lai file nay.
  pause & exit /b 1
)

if not exist "backend\.venv" (
  echo ^>^> Cai thu vien backend, vui long cho...
  python -m venv backend\.venv || (echo [LOI] Tao moi truong Python that bai & pause & exit /b 1)
  backend\.venv\Scripts\python.exe -m pip install -q -r backend\requirements.txt || (echo [LOI] Cai thu vien backend that bai & pause & exit /b 1)
)
if not exist "frontend\node_modules" (
  echo ^>^> Cai thu vien giao dien, vui long cho...
  pushd frontend
  call npm install || (echo [LOI] npm install that bai & popd & pause & exit /b 1)
  popd
)

start "AI Affiliate - Backend" cmd /k "cd /d "%cd%\backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "AI Affiliate - Giao dien" cmd /k "cd /d "%cd%\frontend" && npm run dev -- --port 3000"

echo Dang khoi dong... se tu mo trinh duyet sau vai giay.
timeout /t 12 >nul
start http://localhost:3000
echo Dong 2 cua so den (Backend va Giao dien) de dung ung dung.
