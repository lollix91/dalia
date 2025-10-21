@echo off
setlocal

REM Inizializza le variabili
set "DALI="
set "SRC="

REM Parsing degli argomenti in stile loop
:parse_args
if "%~1"=="" goto end_parse_args

if /I "%~1"=="--src" (
    rem Converte il percorso relativo/parziale (%~2) in un percorso assoluto
    rem Questo è l'equivalente batch di (cd "$2" && pwd)
    for %%F in ("%~2") do set "SRC=%%~fF"
    shift
) else if /I "%~1"=="--dali" (
    set "DALI=%~2"
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

REM Controlla se Docker è in esecuzione
docker info > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Docker non è in esecuzione. Avvia Docker Desktop e attendi che sia pronto.
    exit /b 1
)

REM Pulisce Docker
docker system prune -f
docker container prune -f
docker image prune -f

REM Imposta le variabili d'ambiente che docker-compose leggerà
set "src=%SRC%"
set "dali=%DALI%"

REM Esegui i comandi di docker-compose
docker compose down --remove-orphans
docker compose up -d --build --force-recreate --no-deps
docker compose logs -f

endlocal