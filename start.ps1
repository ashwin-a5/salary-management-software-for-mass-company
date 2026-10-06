# PayPulse PowerShell Launcher
$env:PATH = "C:\Users\ganes\tools\python;C:\Users\ganes\tools\python\Scripts;C:\Users\ganes\tools\node;" + $env:PATH

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Starting PayPulse - Employee Salary & Payroll System" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PATH='C:\Users\ganes\tools\python;C:\Users\ganes\tools\python\Scripts;C:\Users\ganes\tools\node;' + `$env:PATH; cd 'backend'; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PATH='C:\Users\ganes\tools\python;C:\Users\ganes\tools\python\Scripts;C:\Users\ganes\tools\node;' + `$env:PATH; cd 'frontend'; npm run dev"

Write-Host "`nBackend API: http://127.0.0.1:8000 (Swagger docs at http://127.0.0.1:8000/docs)" -ForegroundColor Yellow
Write-Host "Frontend App: http://localhost:5173" -ForegroundColor Yellow
