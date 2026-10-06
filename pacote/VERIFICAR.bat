@echo off
setlocal
call "%~dp0scripts\ambiente.bat"
title openEMS Lab - verificacao
echo Verificando a instalacao do openEMS. Aguarde...
echo.
"%PYTHON%" -c "import sys, emslab; sys.exit(0 if emslab.verificar() else 1)"
set "RESULTADO=%ERRORLEVEL%"
echo.
if not defined EMSLAB_SEM_PAUSA pause
exit /b %RESULTADO%
