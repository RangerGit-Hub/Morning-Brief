@echo off
cd /d "%~dp0"
echo 正在推送到 GitHub，如果弹出登录窗口请完成登录...
git push origin main
echo.
if %errorlevel%==0 (
  echo 推送成功！可以关闭本窗口。
) else (
  echo 推送失败，请把窗口里的提示发给 Codex。
)
pause
