@echo off
echo ========================================================
echo Starting PayPulse - Employee Salary & Payroll Management
echo ========================================================

REM Add local portable tools to PATH if present
set "PATH=C:\Users\ganes\tools\python;C:\Users\ganes\tools\python\Scripts;C:\Users\ganes\tools\node;%PATH%"

echo Starting FastAPI Backend Server on http://127.0.0.1:8000 ...
start "PayPulse Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo Starting Vite React Frontend on http://localhost:5173 ...
start "PayPulse Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Application started! Open http://localhost:5173 in your browser.
echo ========================================================
pause
