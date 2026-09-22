@echo off
cd /d C:\Users\nazza\Desktop\fuel-finder
.venv\Scripts\python.exe load_db.py >> pipeline.log 2>&1
exit /b %ERRORLEVEL%