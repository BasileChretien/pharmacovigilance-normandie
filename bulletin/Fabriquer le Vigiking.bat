@echo off
rem Fabriquer le Vigiking : deposez le fichier Word du numero sur cette icone.
rem Le PDF, la page web et la liste des points a verifier arrivent a cote du fichier Word.
rem (Installer.bat met en place Quarto et uv la premiere fois.)
chcp 65001 >nul
setlocal
set "ICI=%~dp0"
if "%~1"=="" (
  echo.
  echo   Deposez le fichier Word du numero sur cette icone pour fabriquer le bulletin.
  echo.
  goto fin
)
where uv >nul 2>nul
if errorlevel 1 (
  echo.
  echo   uv n'est pas installe sur cet ordinateur : lancez d'abord Installer.bat
  echo   dans le dossier du bulletin, puis recommencez.
  echo.
  goto fin
)
uv run --quiet --project "%ICI%.." python "%ICI%fabriquer.py" "%~1"
:fin
if not defined VIGIKING_SANS_PAUSE pause
