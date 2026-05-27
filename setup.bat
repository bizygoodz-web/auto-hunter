@echo off
echo ============================================
echo   Full Auto Job Hunter - Setup
echo ============================================
echo.

echo [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Download from https://python.org and install with "Add to PATH" checked.
    pause
    exit /b 1
)

echo.
echo [2/4] Installing Python packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

echo.
echo [3/4] Installing Playwright Chrome browser...
python -m playwright install chromium
if errorlevel 1 (
    echo ERROR: Playwright install failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Checking career_vault.json...
if not exist career_vault.json (
    echo ERROR: career_vault.json not found in this folder.
    echo Make sure all files are in the same folder.
    pause
    exit /b 1
)

if not exist resume.pdf (
    echo WARNING: resume.pdf not found.
    echo Rename your resume to resume.pdf and put it in this folder.
)

echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo Next steps:
echo.
echo 1. Open PowerShell in this folder
echo    (click address bar, type powershell, press Enter)
echo.
echo 2. Set your Groq API key:
echo    $env:GROQ_API_KEY="your_key_here"
echo    Get free key at: console.groq.com
echo.
echo 3. Test run (no applying, just scoring):
echo    python main.py --dry-run
echo.
echo 4. Full run (opens browser to apply):
echo    python main.py
echo.
echo 5. Optional - email digest:
echo    $env:SMTP_EMAIL="kilaritirumalarao@gmail.com"
echo    $env:SMTP_APP_PASSWORD="your_gmail_app_password"
echo    Get app password: myaccount.google.com/apppasswords
echo.
pause
