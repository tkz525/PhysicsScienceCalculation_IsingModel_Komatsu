@echo off
title Computational Physics Documents Portal
echo ===================================================
echo  Computational Physics Documents Portal Server
echo ===================================================
echo.
echo Starting local web server on port 8080...
echo.
echo [URL] http://localhost:8080
echo.
echo Press Ctrl+C in this window to stop the server.
echo.
python -m http.server 8080 --directory "%~dp0portal_html"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python is not installed or not in PATH.
    echo Trying alternative with Node.js/npx...
    npx http-server "%~dp0portal_html" -p 8080
)
pause
