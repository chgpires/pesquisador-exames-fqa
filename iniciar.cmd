@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "FQA_PYTHON=.venv\Scripts\python.exe"
  goto run
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  set "FQA_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  goto run
)
where py >nul 2>nul
if not errorlevel 1 (
  set "FQA_PYTHON=py"
  goto run
)
where python >nul 2>nul
if not errorlevel 1 (
  set "FQA_PYTHON=python"
  goto run
)
echo Instale Python 3.10 ou superior e siga o README.md.
pause
exit /b 1
:run
"%FQA_PYTHON%" -c "import pypdf" >nul 2>nul
if errorlevel 1 (
  echo Falta a biblioteca pypdf. Consulte a instalacao no README.md.
  pause
  exit /b 1
)
echo Abra http://localhost:8787 no browser. Para terminar, prima Ctrl+C.
"%FQA_PYTHON%" pesquisador.py
endlocal
