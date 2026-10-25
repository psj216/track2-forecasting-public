@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\qfbench2.exe" (
  py -3.13 -m venv .venv
  if errorlevel 1 goto :fail
  ".venv\Scripts\python.exe" -m pip install "qfbench2-common @ git+https://github.com/Agenthon-2026/Agenthon2026-public.git@v2.6.1#subdirectory=common"
  if errorlevel 1 goto :fail
)
".venv\Scripts\qfbench2.exe" submission pack --descriptor submission.json --team-number 318 --out submission.zip
if errorlevel 1 goto :fail
echo Created submission.zip for Team 318. Upload manually to the official Track 2 Final competition.
exit /b 0
:fail
echo Preparation failed. No upload was attempted.
exit /b 1
