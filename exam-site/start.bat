@echo off
chcp 65001 >nul
echo ==========================================
echo   AI训练师初赛题库 - 智能答题平台
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)

echo [1/4] Installing backend dependencies...
cd backend
pip install -r requirements.txt -q
echo [OK] Backend dependencies installed

echo.
echo [2/4] Parsing PDF questions...
python questions/parse_pdf.py
echo [OK] Questions parsed

echo.
echo [3/4] Installing frontend dependencies...
cd ../frontend
call npm install
echo [OK] Frontend dependencies installed

echo.
echo [4/4] Starting services...
echo.
echo ==========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ==========================================
echo.

REM Start backend in background
start "Backend Server" cmd /c "cd %~dp0backend && python run.py"

REM Wait for backend
timeout /t 3 /nobreak >nul

REM Start frontend
start "Frontend Server" cmd /c "cd %~dp0frontend && npm run dev"

echo.
echo Services started! Check the browser windows.
echo.
pause
