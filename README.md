# 每日晨报

一个每天北京时间 08:00 自动更新的晨报网页，包含：

1. 一句不超过 30 词的早安问候（中文 / English / Français 随机三选一）
2. 过去 24 小时全球重大新闻 5 条，标注来源
3. 南京、武汉、南宁的当日天气

## 运行

双击 `start.bat`，或在项目目录执行：

```bash
python server.py
```

然后用浏览器打开 <http://127.0.0.1:8000>。

## 手机访问（同一 Wi-Fi）

服务启动后，窗口里会打印类似 `手机访问：http://192.168.x.x:8000` 的地址。
让手机连接和电脑相同的 Wi-Fi，在手机浏览器里打开该地址即可。

如果手机打不开，通常是 Windows 防火墙拦截了 Python：

1. 首次启动时，Windows 可能弹出“允许 Python 访问网络”的提示，勾选“专用网络”并允许；
2. 或者手动放行：以管理员身份打开 PowerShell，运行
   `netsh advfirewall firewall add rule name="MorningBrief 8000" dir=in action=allow protocol=TCP localport=8000`。

## 发布到公网（发给同学、父母）

推荐用 GitHub 免费托管：得到一个永久链接，任何人在任何地方都能打开，
且每天 08:00（北京时间）自动更新，不需要你的电脑一直开机。

步骤：

1. 注册一个 GitHub 账号（免费）：<https://github.com/signup>；
2. 登录后新建仓库（Repository）：名称随意（如 `morning-brief`），选择 **Public（公开）**；
3. 把这个文件夹里的所有文件（`generate.py`、`site/`、`.github/`、`README.md` 等）上传到仓库
   （可用网页“Add file → Upload files”，或用 GitHub Desktop）；
4. 进入仓库 Settings → Pages，在 Source 里选 **Deploy from a branch**，
   分支选 `main`，目录选 `/site`，保存；
5. 等 1～2 分钟后，访问 `https://你的用户名.github.io/仓库名/` 即可；
6. 仓库里的 `.github/workflows/morning-brief.yml` 会自动在每天 08:00 更新数据。

> 仓库必须为 Public（公开），免费账号的公开网页才能正常显示。

## 更新机制

- 服务运行期间，每天 08:00（北京时间）自动重新抓取新闻和天气；
- 每次启动时，若 `site/data.json` 不是当天的数据，会立即更新；
- 想手动刷新，访问 <http://127.0.0.1:8000/refresh>。

如需更换端口，设置环境变量 `PORT`，例如 `set PORT=8080` 后运行 `python server.py`。

## 数据来源

- 新闻 RSS：BBC News、The Guardian、Al Jazeera、NPR、France 24、NYT
- 天气：Open-Meteo（免费接口，无需密钥）

## 自定义

- 修改问候语：编辑 `generate.py` 中的 `GREETINGS` 字典；
- 修改城市：编辑 `generate.py` 中的 `CITIES`；
- 修改新闻源：编辑 `generate.py` 中的 `NEWS_SOURCES`。

修改后重新运行 `python server.py` 即可生效（启动时会自动更新当天数据）。
