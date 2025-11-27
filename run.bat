@echo off
setlocal

set "DALI="
set "SRC="

:parse_args
if "%~1"=="" goto end_parse_args

if /I "%~1"=="--src" (
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

if "%SRC%"=="" (
    echo Devi specificare --src
    exit /b 1
)
if "%DALI%"=="" (
    echo Devi specificare --dali
    exit /b 1
)

python "%~dp0main.py" --dali "%DALI%" --src "%SRC%"

endlocal