以下是README，真正网页界面请点击上方“Morning Brief”蓝色链接
# 每日晨报

一个每天北京时间 08:00 自动更新的晨报网页，包含：

1. 一句早安问候（中文 / English / Français ）
2. 过去 24 小时全球重大新闻 5 条
3. 南京、武汉、南宁的当日天气


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
