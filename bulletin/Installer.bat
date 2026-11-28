@echo off
rem Installe Quarto et uv pour l'utilisateur, puis pose l'icone "Fabriquer le Vigiking"
rem sur le bureau (installer.ps1). A lancer une fois, par un double-clic.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1" %*
if not defined VIGIKING_SANS_PAUSE pause
