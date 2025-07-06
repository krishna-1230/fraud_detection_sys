@echo off
echo ======================================
echo Fraud Detection System - Startup
echo ======================================
echo.

REM Check if virtual environment exists
if not exist venv\Scripts\activate (
    echo Virtual environment not found. Creating new environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        goto :error
    )
)

echo Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo Failed to activate virtual environment.
    goto :error
)

echo Checking requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements.
    goto :error
)

echo.
echo Starting Fraud Detection System...
echo.
python run.py
if errorlevel 1 (
    echo Application exited with an error.
    goto :error
)

goto :end

:error
echo.
echo Error occurred. Please check the output above.
pause
exit /b 1

:end
echo.
echo Application closed successfully.
pause
