@echo off
cd /d "%~dp0"
echo Pushing to GitHub. If a login window opens, please finish it...
git push origin main
echo.
if %errorlevel%==0 (
  echo PUSH OK! You can close this window.
) else (
  echo PUSH FAILED. Please send the text in this window to Codex.
)
pause
