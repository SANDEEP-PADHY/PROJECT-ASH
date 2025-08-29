@echo off
echo Building Code Monk - Secure Formatter executable...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build the executable
pyinstaller CodeMonk_SecureFormatter.spec

echo.
if exist "dist\CodeMonk_SecureFormatter.exe" (
    echo Build successful!
    echo Executable created: dist\CodeMonk_SecureFormatter.exe
    echo.
    echo To run the application, navigate to the dist folder and run CodeMonk_SecureFormatter.exe
) else (
    echo Build failed! Check the output above for errors.
)

pause
