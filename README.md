# 每日晨报

一个每天北京时间 08:00 自动更新的晨报网页，包含：

1. 一句不超过 30 词的早安问候（中文 / English / Français 随机三选一）
2. 过去 24 小时国内要闻 5 条 + 国际要闻 5 条，均标注来源
   （国内聚焦科技/国防/政治/经济；国际聚焦科技与政治，每天至少包含 1 条 AI 相关新闻）
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
3. 把网页文件放在仓库**根目录**（`index.html`、`style.css`、`app.js`、`data.json`
   直接在根目录，不需要 `site` 文件夹）；
4. 创建自动更新任务：仓库页面点 **Add file → Create new file**，文件名填
   `.github/workflows/morning-brief.yml`，把本项目里同名文件的内容粘贴进去，提交；
5. 上传最新的 `generate.py`（Upload files 页面直接拖入同名文件即可覆盖）；
6. 进入仓库 Settings → Pages，Source 选 **Deploy from a branch**，
   分支选 `main`，目录选 **/(root)**，保存；
7. 等 1～2 分钟后，访问 `https://你的用户名.github.io/仓库名/` 即可；
8. 想立刻更新今天的数据：仓库 **Actions** 页 → 左侧“每日更新晨报” →
   右侧 **Run workflow** 按钮；以后每天 08:00 会自动更新，无需电脑开机。

> 仓库必须为 Public（公开），免费账号的公开网页才能正常显示。

## 更新机制

- 服务运行期间，每天 08:00（北京时间）自动重新抓取新闻和天气；
- 每次启动时，若 `site/data.json` 不是当天的数据，会立即更新；
- 想手动刷新，访问 <http://127.0.0.1:8000/refresh>。

如需更换端口，设置环境变量 `PORT`，例如 `set PORT=8080` 后运行 `python server.py`。

## 数据来源

- 国内新闻信源（20+ 家）：中国新闻网、央视网、澎湃新闻、环球网、
  人民日报、新华社、参考消息、中国政府网及工信部/发改委/教育部/央行/国资委/
  商务部等部委、江苏/浙江/湖南/四川/北京等省级政府网、中国日报、CGTN 等
- 国际新闻信源（12 家）：BBC News、The Guardian（含 AI 专题）、Al Jazeera、
  NPR、France 24、RT、TASS、DW、Sky News、ABC News、SCMP 等
- 天气：Open-Meteo（免费接口，无需密钥）

> 部分信源经 RSSHub 公共实例转发，个别时段可能限流；抓取时会自动换备用实例
> 并跳过失败的源，保证每天仍有足量新闻可用。

## 自定义

- 修改问候语：编辑 `generate.py` 中的 `GREETINGS` 字典；
- 修改城市：编辑 `generate.py` 中的 `CITIES`；
- 修改新闻源：编辑 `generate.py` 中的 `NEWS_SOURCES`。

修改后重新运行 `python server.py` 即可生效（启动时会自动更新当天数据）。
