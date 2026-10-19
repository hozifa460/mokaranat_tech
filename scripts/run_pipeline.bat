@echo off
setlocal enabledelayedexpansion
title Tech Comparisons Pipeline Runner
chcp 65001 >nul

echo ========================================================
echo   Tech Comparisons pSEO Pipeline Runner (Windows Workstation)
echo ========================================================
echo.

set "PROJECT_DIR=%~dp0.."
set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Virtual environment not found at: %PYTHON_EXE%
    echo Please make sure .venv is created.
    pause
    exit /b 1
)

echo [1/3] Seeding hardware specs into SQLite (hardware.db)...
"%PYTHON_EXE%" "%PROJECT_DIR%\scripts\seed_database.py"
if %errorlevel% neq 0 (
    echo [ERROR] Seeding failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Generating Programmatic SEO Comparisons & AI Editorials...
"%PYTHON_EXE%" "%PROJECT_DIR%\scripts\generate_comparisons.py"
if %errorlevel% neq 0 (
    echo [ERROR] Comparison generation failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Building Astro SSG Web Portal for Cloudflare Pages...
cd /d "%PROJECT_DIR%\web"
call npm.cmd run build
if %errorlevel% neq 0 (
    echo [ERROR] Astro build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================================
echo [SUCCESS] Pipeline completed successfully!
echo Astro SSG static dist is ready in: %PROJECT_DIR%\web\dist
echo ========================================================
pause
