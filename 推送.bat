@echo off
cd /d "%~dp0"
set "GIT=C:\Users\72721\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe"
echo Pushing to GitHub. If a login window opens, please finish it...
"%GIT%" push origin main
echo.
if %errorlevel%==0 (
  echo PUSH OK! You can close this window.
) else (
  echo PUSH FAILED. Please send the text in this window to Codex.
)
pause
