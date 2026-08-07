#!/usr/bin/env python3
"""每日晨报网站服务

- 托管 site/ 下的静态页面
- 启动时若数据不是当天则自动更新
- 每天 08:00（北京时间）自动重新生成数据
- 手动刷新：浏览器访问 /refresh
"""

import json
import os
import socket
import sys
import threading
import time
from datetime import datetime, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate

PORT = int(os.environ.get("PORT", "8000"))
SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
UPDATE_HOUR, UPDATE_MINUTE = 8, 0


def is_stale():
    try:
        with open(os.path.join(SITE_DIR, "data.json"), encoding="utf-8") as f:
            data = json.load(f)
        today = datetime.now(generate.TZ).strftime("%Y-%m-%d")
        return data.get("date") != today
    except Exception:
        return True


def update_once():
    try:
        generate.main()
    except Exception as exc:
        print(f"[update] 更新失败：{exc}", flush=True)


def scheduler_loop():
    while True:
        now = datetime.now(generate.TZ)
        nxt = now.replace(hour=UPDATE_HOUR, minute=UPDATE_MINUTE, second=0, microsecond=0)
        if nxt <= now:
            nxt += timedelta(days=1)
        print(f"[scheduler] 下次自动更新：{nxt.strftime('%Y-%m-%d %H:%M')}（北京时间）", flush=True)
        time.sleep((nxt - now).total_seconds())
        update_once()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SITE_DIR, **kwargs)

    def do_GET(self):
        if self.path.rstrip("/") == "/refresh":
            update_once()
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        print("[http] " + (fmt % args), flush=True)


def main():
    if is_stale():
        print("[startup] 数据不是当天，正在更新……", flush=True)
        update_once()
    threading.Thread(target=scheduler_loop, daemon=True).start()
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[server] 每日晨报已启动", flush=True)
    print(f"[server] 电脑访问：http://127.0.0.1:{PORT}", flush=True)
    ips = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ":" not in ip and not ip.startswith("127."):
                ips.add(ip)
    except Exception:
        pass
    for ip in sorted(ips):
        print(f"[server] 手机访问（需同一 Wi-Fi）：http://{ip}:{PORT}", flush=True)
    print("[server] 若手机无法访问，请在 Windows 防火墙中允许 Python 通过（入站规则）", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
