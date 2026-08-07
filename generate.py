#!/usr/bin/env python3
"""每日晨报数据生成器

抓取全球新闻（RSS）与南京/武汉/南宁天气，生成 site/data.json。
仅使用 Python 标准库。
"""

import email.utils
import html
import json
import os
import random
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Shanghai")
except Exception:
    TZ = timezone(timedelta(hours=8))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "site", "data.json")
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MorningBrief/1.0)"}

# 早安问候语池（中文/英文/法语，均不超过 30 词）
GREETINGS = {
    "中文": [
        "早安！愿今天的心情像清晨的阳光一样明亮，祝你一切顺利。",
        "早安！新的一天，新的开始，愿你元气满满，笑容常在。",
        "早安！愿你在今天的每个瞬间都能感受到生活的美好。",
        "早安！阳光正好，微风不燥，愿你今天过得开心。",
        "早安！愿好运气跟着你，好心情陪着你，度过愉快的一天。",
        "早安！生活明朗，万物可爱，愿你今天也被温柔以待。",
        "早安！每个清晨都是新的机会，愿你把握今天，不负自己。",
        "早安！愿你抬头有阳光，心中有梦想，脚下有力量。",
    ],
    "English": [
        "Good morning! May your day be as bright and full of promise as the sunrise. Have a wonderful day!",
        "Good morning! Wishing you a day filled with joy, energy, and small happy moments.",
        "Good morning! Every sunrise brings a new chance. Make today count!",
        "Good morning! May today bring you good news, warm smiles, and peaceful moments.",
        "Good morning! Here's to a fresh start and a day full of possibilities. Enjoy it!",
        "Good morning! Let the light of this new day guide you to something great.",
        "Good morning! Stay curious, stay kind, and make the most of this beautiful day.",
        "Good morning! May your coffee be strong and your day be wonderful!",
    ],
    "Français": [
        "Bonjour ! Que cette nouvelle journée vous apporte joie, énergie et de belles surprises.",
        "Bonjour ! Chaque matin est une nouvelle chance. Passez une excellente journée !",
        "Bonjour ! Que le soleil de ce matin éclaire votre chemin et illumine votre journée.",
        "Bonjour ! Prenez le temps d'apprécier les petits bonheurs du jour. Bonne journée !",
        "Bonjour ! Je vous souhaite une journée pleine de sourires et de réussites.",
        "Bonjour ! Que cette journée commence bien et finisse encore mieux. Profitez-en !",
        "Bonjour ! L'avenir appartient à ceux qui se lèvent tôt. Que la journée vous sourie !",
        "Bonjour ! Douceur, bonne humeur et réussite au programme de cette belle journée.",
    ],
}

# 全球新闻 RSS 源（按来源标记）
NEWS_SOURCES = [
    ("BBC News", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("NPR", "https://feeds.npr.org/1004/rss.xml"),
    ("France 24", "https://www.france24.com/en/rss"),
    ("NYT", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
]

CITIES = [
    ("南京", 32.06, 118.80),
    ("武汉", 30.59, 114.31),
    ("南宁", 22.82, 108.32),
]

# WMO 天气代码 -> (中文描述, 图标)
WMO = {
    0: ("晴", "☀️"), 1: ("大部晴朗", "🌤️"), 2: ("多云", "⛅"), 3: ("阴", "☁️"),
    45: ("雾", "🌫️"), 48: ("雾凇", "🌫️"),
    51: ("毛毛雨", "🌦️"), 53: ("毛毛雨", "🌦️"), 55: ("毛毛雨", "🌧️"),
    56: ("冻毛毛雨", "🌧️"), 57: ("冻毛毛雨", "🌧️"),
    61: ("小雨", "🌧️"), 63: ("中雨", "🌧️"), 65: ("大雨", "🌧️"),
    66: ("冻雨", "🌧️"), 67: ("冻雨", "🌧️"),
    71: ("小雪", "🌨️"), 73: ("中雪", "🌨️"), 75: ("大雪", "❄️"), 77: ("雪粒", "🌨️"),
    80: ("阵雨", "🌦️"), 81: ("强阵雨", "🌦️"), 82: ("暴雨", "⛈️"),
    85: ("阵雪", "🌨️"), 86: ("阵雪", "🌨️"),
    95: ("雷阵雨", "⛈️"), 96: ("雷阵雨伴冰雹", "⛈️"), 99: ("雷阵雨伴冰雹", "⛈️"),
}


def fetch_bytes(url, timeout=15, retries=2):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HTTP_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:
            last = exc
            time.sleep(1)
    raise last


def strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def local_name(node):
    return node.tag.rsplit("}", 1)[-1]


def child_text(item, name):
    for sub in item:
        if local_name(sub) == name:
            return (sub.text or "").strip()
    return ""


def parse_rss(source, content):
    root = ET.fromstring(content)
    items = []
    for el in root.iter():
        if local_name(el) != "item":
            continue
        title = child_text(el, "title") or "(无标题)"
        link = child_text(el, "link")
        raw_pub = child_text(el, "pubDate")
        published = None
        if raw_pub:
            try:
                published = email.utils.parsedate_to_datetime(raw_pub)
            except Exception:
                published = None
        summary = strip_html(child_text(el, "description"))[:120]
        items.append({
            "title": title,
            "link": link,
            "published": published,
            "summary": summary,
            "source": source,
        })
    return items


def is_live_blog(title):
    return bool(re.search(r"(?i)(news live|politics live|\blive$)", title))


def pick_news(now):
    all_items = []
    for source, url in NEWS_SOURCES:
        try:
            for item in parse_rss(source, fetch_bytes(url)):
                if not is_live_blog(item["title"]):
                    all_items.append(item)
        except Exception as exc:
            print(f"[news] {source} 抓取失败：{exc}", file=sys.stderr)
    # 按标题去重
    seen = set()
    unique = []
    for item in all_items:
        key = re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", item["title"].lower())
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    # 发布时间从新到旧（缺失时间的排最后）
    unique.sort(key=lambda it: it["published"] or datetime.min.replace(tzinfo=TZ), reverse=True)
    cutoff = now - timedelta(hours=24)
    fresh = [it for it in unique if it["published"] and it["published"] >= cutoff]
    picked = fresh[:5]
    relaxed = len(picked) < 5
    if relaxed:
        for it in unique:
            if len(picked) >= 5:
                break
            if it not in picked:
                picked.append(it)
    news = []
    for rank, it in enumerate(picked, start=1):
        pub = it["published"].astimezone(TZ) if it["published"] else None
        news.append({
            "rank": rank,
            "title": it["title"],
            "source": it["source"],
            "link": it["link"],
            "published": pub.strftime("%Y-%m-%d %H:%M") if pub else "时间未知",
            "summary": it["summary"],
        })
    return news, relaxed


def fetch_weather():
    result = []
    for city, lat, lon in CITIES:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,weather_code"
            "&daily=temperature_2m_max,temperature_2m_min,weather_code"
            "&timezone=Asia%2FShanghai&forecast_days=1"
        )
        try:
            data = json.loads(fetch_bytes(url).decode("utf-8"))
            current = data["current"]
            daily = data["daily"]
            code = current.get("weather_code") or daily["weather_code"][0]
            label, icon = WMO.get(code, ("天气未知", "🌡️"))
            result.append({
                "city": city,
                "current": round(current["temperature_2m"]),
                "min": round(daily["temperature_2m_min"][0]),
                "max": round(daily["temperature_2m_max"][0]),
                "condition": label,
                "icon": icon,
            })
        except Exception as exc:
            print(f"[weather] {city} 获取失败：{exc}", file=sys.stderr)
            result.append({
                "city": city,
                "current": None,
                "min": None,
                "max": None,
                "condition": "暂不可用",
                "icon": "🌡️",
            })
    return result


def pick_greeting():
    lang = random.choice(list(GREETINGS))
    text = random.choice(GREETINGS[lang])
    count = len(text.split()) if lang != "中文" else len(re.sub(r"\s", "", text))
    if count > 30:
        raise ValueError(f"问候语超过 30 词：{lang}: {text}")
    return {"text": text, "language": lang, "words": count}


def main():
    now = datetime.now(TZ)
    news, relaxed = pick_news(now)
    data = {
        "date": now.strftime("%Y-%m-%d"),
        "updated_at": now.strftime("%Y-%m-%d %H:%M"),
        "timezone": "Asia/Shanghai（北京时间）",
        "greeting": pick_greeting(),
        "news": news,
        "news_relaxed": relaxed,
        "weather": fetch_weather(),
    }
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    tmp = DATA_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_PATH)
    print(
        f"[generate] 已更新：{len(news)} 条新闻 / {len(data['weather'])} 城天气 "
        f"/ 问候语语言：{data['greeting']['language']}",
        flush=True,
    )
    return data


if __name__ == "__main__":
    main()
