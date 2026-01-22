@echo off
setlocal

set "DALI="
set "SRC="
set "TOKEN="

:parse_args
if "%~1"=="" goto end_parse_args

if /I "%~1"=="--src" (
    for %%F in ("%~2") do set "SRC=%%~fF"
    shift
) else if /I "%~1"=="--dali" (
    set "DALI=%~2"
    shift
) else if /I "%~1"=="--token" (
    set "TOKEN=%~2"
    shift
) else (
    echo Parametro sconosciuto: %~1
    exit /b 1
)
shift
goto :parse_args

:end_parse_args

echo "SRC: %SRC%"
echo "DALI: %DALI%"
if not "%TOKEN%"=="" echo "TOKEN: (impostato)"

docker info > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Docker non è in esecuzione. Avvia Docker Desktop e attendi che sia pronto.
    exit /b 1
)

docker container prune -f 

set "src=%SRC%"
set "dali=%DALI%"
:: Impostiamo la variabile d'ambiente che Docker Compose leggerà
set "OPENAI_API_KEY=%TOKEN%"

echo Avvio dei container...
docker compose down --remove-orphans
docker compose up -d --build --force-recreate --no-deps

echo Visualizzazione dei log...
docker compose logs -f

endlocal