@echo off
SETLOCAL ENABLEEXTENSIONS

REM Check if argument is provided
SET MODE=%1

GOTO :MAIN

REM Functions for installation
:INSTALL_UV
REM Install uv
echo Checking if uv is installed...
WHERE uv >nul 2>nul
IF ERRORLEVEL 1 (
    ECHO uv is not installed. Installing uv...
    pip install uv
    IF ERRORLEVEL 1 (
        ECHO Failed to install uv. Please check your Python and pip installation.
        EXIT /B 1
    )
    ECHO uv installed successfully.
) ELSE (
    ECHO uv is already installed.
)
EXIT /B 0

:INSTALL_PNPM
REM Install pnpm
echo Checking if pnpm is installed...
WHERE pnpm >nul 2>nul
IF ERRORLEVEL 1 (
    ECHO pnpm is not installed. Installing pnpm...
    npm install -g pnpm
    IF ERRORLEVEL 1 (
        ECHO Failed to install pnpm. Please check your Node.js and npm installation.
        EXIT /B 1
    )
    ECHO pnpm installed successfully.
) ELSE (
    ECHO pnpm is already installed.
)
EXIT /B 0

:INSTALL_BUN
REM Install bun
echo Checking if bun is installed...
WHERE bun >nul 2>nul
IF ERRORLEVEL 1 (
    ECHO bun is not installed. Installing bun...
    powershell -Command "Invoke-WebRequest -Uri https://bun.sh/install.ps1 -UseBasicParsing | Invoke-Expression"
    IF ERRORLEVEL 1 (
        ECHO Failed to install bun. Please check your internet connection and try again.
        EXIT /B 1
    )
    ECHO bun installed successfully.
) ELSE (
    ECHO bun is already installed.
)
EXIT /B 0

REM Functions for modes
:DEV_MODE
REM Development mode with pnpm
echo Starting DeerFlow in [DEVELOPMENT] mode with pnpm...
start /B cmd /c "uv run server.py --reload"
cd web
start /B cmd /c "pnpm dev"
echo Press Ctrl+C to stop all processes
cmd /c pause
taskkill /F /IM python.exe /IM node.exe 2>nul
cd ..
EXIT /B 0

:BUN_DEV_MODE
REM Development mode with bun
echo Starting DeerFlow in [DEVELOPMENT] mode with bun...
start /B cmd /c "uv run server.py --reload"
cd web
start /B cmd /c "bun dev"
echo Press Ctrl+C to stop all processes
cmd /c pause
taskkill /F /IM python.exe /IM bun.exe 2>nul
cd ..
EXIT /B 0

:PROD_MODE
REM Production mode
echo Starting DeerFlow in [PRODUCTION] mode...
uv run server.py
cd web
pnpm start
EXIT /B 0

REM Main Logic
IF "%MODE%"=="--cli" (
    ECHO Running DeerFlow CLI...
    CALL :INSTALL_UV
    uv run main.py
    EXIT /B 0
)

IF "%MODE%"=="--install" GOTO INSTALL
IF "%MODE%"=="-i" GOTO INSTALL
IF "%MODE%"=="install" GOTO INSTALL

IF "%MODE%"=="--install-bun" GOTO INSTALL_BUN
IF "%MODE%"=="--install-pnpm" GOTO INSTALL_PNPM
IF "%MODE%"=="--install-uv" GOTO INSTALL_UV
IF "%MODE%"=="--i-bun" GOTO INSTALL_BUN
IF "%MODE%"=="--i-pnpm" GOTO INSTALL_PNPM
IF "%MODE%"=="--i-uv" GOTO INSTALL_UV

IF "%MODE%"=="--dev" GOTO DEV_MODE
IF "%MODE%"=="-d" GOTO DEV_MODE
IF "%MODE%"=="dev" GOTO DEV_MODE
IF "%MODE%"=="development" GOTO DEV_MODE
IF "%MODE%"=="--development" GOTO DEV_MODE

IF "%MODE%"=="--prod" GOTO PROD_MODE
IF "%MODE%"=="-p" GOTO PROD_MODE
IF "%MODE%"=="prod" GOTO PROD_MODE
IF "%MODE%"=="production" GOTO PROD_MODE
IF "%MODE%"=="--production" GOTO PROD_MODE

IF "%MODE%"=="--bun-dev" GOTO BUN_DEV_MODE
IF "%MODE%"=="-b" GOTO BUN_DEV_MODE
IF "%MODE%"=="bundev" GOTO BUN_DEV_MODE
IF "%MODE%"=="bun-development" GOTO BUN_DEV_MODE
IF "%MODE%"=="--bun-development" GOTO BUN_DEV_MODE

IF "%MODE%"=="--install-dev" (
    ECHO Installing dependencies for development mode...
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_PNPM
    cd web
    pnpm install
    IF ERRORLEVEL 1 EXIT /B 1
    cd ..
    GOTO DEV_MODE
)

IF "%MODE%"=="--install-bun-dev" (
    ECHO Installing dependencies for development mode with bun...
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_BUN
    cd web
    bun install
    IF ERRORLEVEL 1 EXIT /B 1
    cd ..
    GOTO BUN_DEV_MODE
)

IF "%MODE%"=="--install-prod" (
    ECHO Installing dependencies for production mode...
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_PNPM
    cd web
    pnpm install
    IF ERRORLEVEL 1 EXIT /B 1
    cd ..
    GOTO PROD_MODE
)

IF "%MODE%"=="" (
    ECHO No argument provided. Defaulting to Install and Development mode with bun.
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_BUN
    cd web
    bun install
    IF ERRORLEVEL 1 EXIT /B 1
    cd ..
    GOTO BUN_DEV_MODE
)

:MAIN
REM Main Logic
IF "%MODE%"=="--install" (
    ECHO Installing all dependencies...
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_PNPM
    cd web
    pnpm install
    IF ERRORLEVEL 1 EXIT /B 1
    cd ..
    EXIT /B 0
)

IF "%MODE%"=="-i" (
    ECHO Installing all dependencies...
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_PNPM
    cd web
    pnpm install
    IF ERRORLEVEL 1 EXIT /B 1
    cd ..
    EXIT /B 0
)

IF "%MODE%"=="--install-bun" (
    CALL :INSTALL_BUN
    EXIT /B 0
)

IF "%MODE%"=="--install-pnpm" (
    CALL :INSTALL_PNPM
    EXIT /B 0
)

IF "%MODE%"=="--install-uv" (
    CALL :INSTALL_UV
    EXIT /B 0
)

IF "%MODE%"=="--i-bun" (
    CALL :INSTALL_BUN
    EXIT /B 0
)

IF "%MODE%"=="--i-pnpm" (
    CALL :INSTALL_PNPM
    EXIT /B 0
)

IF "%MODE%"=="--i-uv" (
    CALL :INSTALL_UV
    EXIT /B 0
)

IF "%MODE%"=="--dev" (
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_PNPM
    CALL :DEV_MODE
    EXIT /B 0
)

IF "%MODE%"=="-d" (
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_PNPM
    CALL :DEV_MODE
    EXIT /B 0
)

IF "%MODE%"=="--bun-dev" (
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_BUN
    CALL :BUN_DEV_MODE
    EXIT /B 0
)

IF "%MODE%"=="-b" (
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_BUN
    CALL :BUN_DEV_MODE
    EXIT /B 0
)

IF "%MODE%"=="--install-dev" (
    ECHO Installing dependencies for development mode...
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_PNPM
    cd web
    pnpm install
    IF ERRORLEVEL 1 EXIT /B 1
    cd ..
    CALL :DEV_MODE
    EXIT /B 0
)

IF "%MODE%"=="--install-bun-dev" (
    ECHO Installing dependencies for development mode with bun...
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_BUN
    cd web
    bun install
    IF ERRORLEVEL 1 EXIT /B 1
    cd ..
    CALL :BUN_DEV_MODE
    EXIT /B 0
)

IF "%MODE%"=="--install-prod" (
    ECHO Installing dependencies for production mode...
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_PNPM
    cd web
    pnpm install
    IF ERRORLEVEL 1 EXIT /B 1
    cd ..
    CALL :PROD_MODE
    EXIT /B 0
)

IF "%MODE%"=="" (
    ECHO No argument provided. Defaulting to Install and Development mode with bun.
    CALL :INSTALL_UV
    uv sync
    IF ERRORLEVEL 1 EXIT /B 1
    CALL :INSTALL_BUN
    cd web
    bun install
    IF ERRORLEVEL 1 EXIT /B 1
    cd ..
    CALL :BUN_DEV_MODE
    EXIT /B 0
)

REM Invalid argument
ECHO Invalid argument. Usage: bootstrap.bat [--dev | --prod | --install | --install-bun | --install-pnpm | --install-uv | --bun-dev]
EXIT /B 1
