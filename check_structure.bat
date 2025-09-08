@echo off
echo.
echo ================================================================
echo                LeafIQ - File Structure Maintenance
echo ================================================================
echo.

REM Create necessary directories if they don't exist
if not exist "uploads" mkdir uploads
if not exist "results" mkdir results
if not exist "templates" mkdir templates
if not exist "model" mkdir model

echo ✅ Directory structure verified
echo.

REM Check if essential files exist
set "missing_files="

if not exist "app.py" set "missing_files=%missing_files% app.py"
if not exist "requirements.txt" set "missing_files=%missing_files% requirements.txt"
if not exist "model\best.pt" set "missing_files=%missing_files% model\best.pt"
if not exist "templates\index.html" set "missing_files=%missing_files% templates\index.html"
if not exist ".env.example" set "missing_files=%missing_files% .env.example"

if defined missing_files (
    echo ❌ Missing essential files: %missing_files%
    echo Please ensure all required files are present.
) else (
    echo ✅ All essential files present
)

echo.
echo ================================================================
echo Current LeafIQ Structure:
echo ================================================================
tree /F /A
echo.
echo ✅ LeafIQ file structure maintenance complete!
pause
