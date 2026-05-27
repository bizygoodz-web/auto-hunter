@echo off
echo Installing packages...
pip install groq httpx beautifulsoup4 playwright lxml
playwright install chromium
echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Put your resume.pdf in this folder
echo 2. Set your API key: set GROQ_API_KEY=your_key
echo 3. Run: python main.py --dry-run   (test without applying)
echo 4. Run: python main.py             (full run with browser review)
pause
