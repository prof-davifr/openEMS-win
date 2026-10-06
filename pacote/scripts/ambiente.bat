@rem Define as variaveis de ambiente do pacote. Chamado por ABRIR.bat e VERIFICAR.bat.
for %%I in ("%~dp0..") do set "RAIZ=%%~fI"
set "CSXCAD_INSTALL_PATH=%RAIZ%\openEMS"
set "OPENEMS_INSTALL_PATH=%RAIZ%\openEMS"
set "PATH=%RAIZ%\python;%RAIZ%\openEMS;%PATH%"
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "PYTHON=%RAIZ%\python\python.exe"
