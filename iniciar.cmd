@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if not errorlevel 1 (
  node previsualizar.cjs
  exit /b
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" (
  "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" previsualizar.cjs
  exit /b
)
echo Abra a aplicacao no GitHub Pages, ou instale Node.js para a pre-visualizacao local.
pause
endlocal
