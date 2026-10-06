@echo off
setlocal
call "%~dp0scripts\ambiente.bat"
title openEMS Lab - NAO FECHE ESTA JANELA enquanto usa o Jupyter
"%PYTHON%" "%RAIZ%\scripts\abrir.py" %*
if errorlevel 1 (
    echo.
    echo Algo deu errado. Mande uma foto desta janela ao orientador.
    pause
)
