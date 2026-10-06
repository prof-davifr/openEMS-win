@echo off
rem Instalador do openEMS Lab (openEMS + Python + Jupyter), sem administrador.
rem
rem - Com internet: baixa o pacote do ultimo release no GitHub.
rem - Sem internet: coloque openEMS-lab-windows.zip na mesma pasta deste arquivo.
rem
rem Instala em %LOCALAPPDATA%\openEMS-lab. Os notebooks do aluno ficam em
rem Documentos\openEMS-notebooks e nunca sao apagados por este instalador.
rem A variavel EMSLAB_TESTE=1 tira as perguntas (teste automatico).

setlocal EnableExtensions
title Instalador do openEMS Lab
cd /d "%~dp0"

set "REPO=prof-davifr/openEMS-win"
set "PACOTE=openEMS-lab-windows.zip"
set "URL=https://github.com/%REPO%/releases/latest/download/%PACOTE%"
set "DESTINO=%LOCALAPPDATA%\openEMS-lab"
set "TRABALHO=%TEMP%\openEMS-lab-instalacao"
set "LOG=%LOCALAPPDATA%\openEMS-lab-instalacao.log"

echo ============================================================
echo   Instalador do openEMS Lab
echo ============================================================
echo.
echo O pacote vai para: %DESTINO%
echo Registro da instalacao: %LOG%
echo.
echo Instalacao iniciada em %DATE% %TIME% > "%LOG%"

if not exist "%TRABALHO%" mkdir "%TRABALHO%"

rem ---------------------------------------------------------------- 1. pacote
if exist "%~dp0%PACOTE%" (
    echo [1/4] Pacote encontrado ao lado do instalador. Nada a baixar.
    set "ZIP=%~dp0%PACOTE%"
    if exist "%~dp0%PACOTE%.sha256" (
        set "SHA=%~dp0%PACOTE%.sha256"
    ) else (
        set "SHA="
    )
    goto conferir
)

echo [1/4] Baixando o pacote, cerca de 400 MB. Isso pode levar varios minutos...
set "ZIP=%TRABALHO%\%PACOTE%"
set "SHA=%TRABALHO%\%PACOTE%.sha256"
curl.exe -L --fail --retry 3 --progress-bar -o "%ZIP%" "%URL%"
if errorlevel 1 goto baixar_powershell
curl.exe -L --fail --retry 3 -o "%SHA%" "%URL%.sha256" >> "%LOG%" 2>&1
if errorlevel 1 goto baixar_powershell
goto conferir

:baixar_powershell
rem O curl nao usa o proxy do sistema; o PowerShell usa.
echo       O curl falhou. Tentando de novo pelo PowerShell, com o proxy do sistema...
powershell -NoProfile -NonInteractive -Command ^
  "$ProgressPreference = 'SilentlyContinue';" ^
  "[Net.ServicePointManager]::SecurityProtocol = 'Tls12';" ^
  "[Net.WebRequest]::DefaultWebProxy.Credentials = [Net.CredentialCache]::DefaultNetworkCredentials;" ^
  "Invoke-WebRequest -UseBasicParsing -Uri $env:URL -OutFile $env:ZIP;" ^
  "Invoke-WebRequest -UseBasicParsing -Uri ($env:URL + '.sha256') -OutFile $env:SHA" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo.
    echo [ERRO] Nao foi possivel baixar o pacote.
    echo        Baixe o arquivo pelo navegador neste endereco:
    echo        %URL%
    echo        Coloque o arquivo na mesma pasta deste instalador e rode o instalador de novo.
    goto falha
)

:conferir
if not defined SHA (
    echo       Sem o arquivo .sha256: a integridade do pacote nao foi conferida.
    goto extrair
)
echo [2/4] Conferindo a integridade do pacote...
set "SHA_ARQUIVO=%SHA%"
powershell -NoProfile -NonInteractive -Command ^
  "$esperado = ((Get-Content -Raw $env:SHA_ARQUIVO).Trim() -split '\s+')[0];" ^
  "$real = (Get-FileHash -Algorithm SHA256 $env:ZIP).Hash;" ^
  "if ($real -ne $esperado) { Write-Output ('esperado ' + $esperado + ', obtido ' + $real); exit 1 }" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERRO] O pacote baixado esta corrompido. Apague a pasta abaixo e rode o instalador de novo:
    echo        %TRABALHO%
    goto falha
)

:extrair
echo [3/4] Extraindo o pacote. Isso pode levar alguns minutos...
if exist "%DESTINO%" rmdir /s /q "%DESTINO%"
if exist "%DESTINO%" (
    echo [ERRO] Nao foi possivel apagar a versao antiga em %DESTINO%.
    echo        Feche o Jupyter e as janelas do openEMS e rode o instalador de novo.
    goto falha
)
mkdir "%DESTINO%"
tar.exe -xf "%ZIP%" -C "%DESTINO%" --strip-components 1 >> "%LOG%" 2>&1
if errorlevel 1 (
    echo       O tar falhou. Tentando pelo PowerShell, que e mais lento...
    powershell -NoProfile -NonInteractive -Command ^
      "$tmp = Join-Path $env:TRABALHO 'extraido'; Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue;" ^
      "Expand-Archive -Path $env:ZIP -DestinationPath $tmp -Force;" ^
      "Get-ChildItem (Join-Path $tmp 'openEMS-lab') | Move-Item -Destination $env:DESTINO" >> "%LOG%" 2>&1
)
if not exist "%DESTINO%\python\python.exe" (
    echo [ERRO] A extracao falhou. Veja o registro: %LOG%
    goto falha
)

echo [4/4] Preparando a pasta de notebooks e o atalho na Area de Trabalho...
"%DESTINO%\python\python.exe" "%DESTINO%\scripts\abrir.py" --preparar
echo.
set "EMSLAB_SEM_PAUSA=1"
call "%DESTINO%\VERIFICAR.bat"
if errorlevel 1 (
    echo.
    echo [ERRO] A verificacao falhou. Mande uma foto desta janela e o arquivo
    echo        %LOG% ao orientador.
    goto falha
)

echo.
echo ============================================================
echo   INSTALACAO OK
echo   Para usar: dois cliques no atalho "openEMS Lab"
echo   na Area de Trabalho.
echo ============================================================
echo Instalacao terminada em %DATE% %TIME% >> "%LOG%"
if exist "%TRABALHO%\%PACOTE%" del /q "%TRABALHO%\%PACOTE%"
echo.
if defined EMSLAB_TESTE exit /b 0
choice /c SN /m "Abrir o Jupyter agora"
if errorlevel 2 exit /b 0
start "" "%DESTINO%\ABRIR.bat"
exit /b 0

:falha
echo Instalacao falhou em %DATE% %TIME% >> "%LOG%"
echo.
if not defined EMSLAB_TESTE pause
exit /b 1
