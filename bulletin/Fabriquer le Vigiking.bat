@echo off
rem Fabriquer le Vigiking : deposez le fichier Word du numero sur cette icone.
rem Le PDF, la page web et la liste a verifier arrivent a cote du fichier Word.
rem (Installer.bat met en place Quarto et uv la premiere fois.)
title Fabriquer le Vigiking
chcp 65001 >nul
setlocal
set "ICI=%~dp0"
rem Where Installer.bat puts the tools: found even before Windows refreshes the PATH
rem (until the next sign-in, a new install may not be on it yet).
set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%LOCALAPPDATA%\Programs\Quarto\bin;%ProgramFiles%\Quarto\bin"
if "%~1"=="" (
  echo.
  echo   Pour fabriquer le bulletin : fermez cette fenetre, puis faites glisser
  echo   le fichier Word du numero sur l'icone "Fabriquer le Vigiking", et lachez-le.
  echo.
  goto fin
)
where uv >nul 2>nul
if errorlevel 1 (
  echo.
  echo   L'installation n'est pas faite sur cet ordinateur : double-cliquez d'abord
  echo   sur le fichier Installer, dans le dossier du bulletin, puis recommencez.
  echo.
  goto fin
)
if not "%~2"=="" (
  echo.
  echo   Un seul fichier a la fois : seul "%~nx1" est fabrique.
)
uv run --quiet --project "%ICI%.." python "%ICI%fabriquer.py" "%~1"
:fin
if not defined VIGIKING_SANS_PAUSE pause
