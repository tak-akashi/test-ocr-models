@echo off
REM Document Processing Docker Helper Script for Windows CMD
REM =========================================================
REM
REM Usage:
REM   docker-run.bat layout [models...]
REM   docker-run.bat ocr [models...]
REM   docker-run.bat jupyter
REM   docker-run.bat shell
REM   docker-run.bat build
REM   docker-run.bat help

setlocal enabledelayedexpansion

REM Get script directory and project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM Change to project directory
pushd "%PROJECT_ROOT%"

REM Check Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    exit /b 1
)

REM Ensure required directories exist
if not exist "data" mkdir data
if not exist "output" mkdir output
if not exist ".cache" mkdir .cache

REM Parse command
set "COMMAND=%~1"
if "%COMMAND%"=="" set "COMMAND=help"

if /i "%COMMAND%"=="layout" goto :layout
if /i "%COMMAND%"=="ocr" goto :ocr
if /i "%COMMAND%"=="preprocess" goto :preprocess
if /i "%COMMAND%"=="jupyter" goto :jupyter
if /i "%COMMAND%"=="shell" goto :shell
if /i "%COMMAND%"=="build" goto :build
if /i "%COMMAND%"=="help" goto :help
goto :help

:layout
echo Running layout analysis...
shift
set "MODELS="
:layout_loop
if "%~1"=="" goto :layout_run
set "MODELS=!MODELS! %~1"
shift
goto :layout_loop
:layout_run
if "!MODELS!"=="" set "MODELS=all"
echo Command: docker compose run --rm document-processor layout --models!MODELS!
docker compose run --rm document-processor layout --models!MODELS!
goto :end

:ocr
echo Running OCR processing...
shift
set "MODELS="
:ocr_loop
if "%~1"=="" goto :ocr_run
set "MODELS=!MODELS! %~1"
shift
goto :ocr_loop
:ocr_run
if "!MODELS!"=="" set "MODELS=all"
echo Command: docker compose run --rm document-processor ocr --models!MODELS!
docker compose run --rm document-processor ocr --models!MODELS!
goto :end

:preprocess
echo Running preprocessing...
shift
docker compose run --rm document-processor preprocess %*
goto :end

:jupyter
echo Starting Jupyter Lab...
echo Access at: http://localhost:8890
docker compose --profile jupyter up jupyter
goto :end

:shell
echo Starting interactive shell...
docker compose run --rm document-processor bash
goto :end

:build
echo Building Docker images...
docker compose build
goto :end

:help
echo.
echo Document Processing Docker Helper
echo ==================================
echo.
echo USAGE:
echo     docker-run.bat ^<command^> [arguments...]
echo.
echo COMMANDS:
echo     layout [models...]   Run layout analysis (default: all models)
echo     ocr [models...]      Run OCR-only processing (default: all models)
echo     preprocess [args]    Run PDF preprocessing utilities
echo     jupyter              Start Jupyter Lab server
echo     shell                Start interactive bash shell
echo     build                Build Docker images
echo     help                 Show this help message
echo.
echo AVAILABLE MODELS:
echo     upstage, azure, yomitoku, gemini, claude, qwen
echo     Use 'all' to run all models
echo.
echo EXAMPLES:
echo     docker-run.bat layout all
echo     docker-run.bat layout upstage azure
echo     docker-run.bat ocr upstage gemini
echo     docker-run.bat jupyter
echo     docker-run.bat shell
echo.
echo REQUIREMENTS:
echo     - Docker Desktop for Windows with WSL2 backend
echo     - .env file with API keys
echo.
echo For GPU support, use docker-run.ps1 with -GPU flag
echo.
goto :end

:end
popd
endlocal
