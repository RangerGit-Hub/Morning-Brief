#!/usr/bin/env python3
"""每日晨报数据生成器

抓取国内/国际新闻与南京/武汉/南宁天气，生成 site/data.json。
仅使用 Python 标准库。

- 国内新闻 5 条：信源为新华社、人民日报等权威主流媒体及部委/省级官媒（20+ 家），
  内容聚焦科技、国防、政治、经济；
- 国际新闻 5 条：信源为 BBC、RT、塔斯社等国际主流媒体（10+ 家），
  聚焦科技与政治，每天至少包含 1 条 AI 相关新闻。
"""

import email.utils
import html
import json
import os
import random
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
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

# ---------------- 早安问候语池（中文/英文/法语，均不超过 30 词） ----------------
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

# ---------------- RSSHub 公共实例（多实例互备） ----------------
RSSHUB_INSTANCES = [
    "https://rsshub.app",
    "https://rsshub.rssforever.com",
    "https://rsshub.ktachibana.party",
]


def hub(route):
    return [i + route for i in RSSHUB_INSTANCES]


# ---------------- 国内新闻信源（20+ 家权威主流媒体/部委/省级官媒） ----------------
DOMESTIC_SOURCES = [
    ("中国新闻网", ["http://www.chinanews.com.cn/rss/scroll-news.xml"]),
    ("央视网", ["http://www.cctv.com/program/rss/02/01/index.xml"]),
    ("央视网-新闻联播", hub("/cctv/xwlb")),
    ("央视网-新闻", hub("/cctv/news")),
    ("澎湃新闻-精选", hub("/thepaper/featured")),
    ("澎湃新闻-头条", hub("/thepaper/news")),
    ("人民日报-文字版", hub("/people/paper/rmrb")),
    ("环球网-国内", hub("/huanqiu/news/china")),
    ("环球网-国际", hub("/huanqiu/news/world")),
    ("环球网-军事", hub("/huanqiu/news/mil")),
    ("中国政府网-最新政策", hub("/gov/zhengce/zuixin")),
    ("工信部", hub("/gov/miit/xwfb")),
    ("国家发改委", hub("/gov/ndrc/xwzx")),
    ("教育部", hub("/gov/moe/xwfb")),
    ("人民银行", hub("/gov/pbc/goutongjiaoliu")),
    ("国资委", hub("/gov/sasac/xwfb")),
    ("商务部", hub("/gov/mofcom/xwfb")),
    ("参考消息", hub("/cankaoxiaoxi")),
    ("新华社", hub("/xinhua/news")),
    ("江苏省政府网", hub("/gov/jiangsu")),
    ("浙江省政府网", hub("/gov/zhejiang")),
    ("湖南省政府网", hub("/gov/hunan")),
    ("四川省政府网", hub("/gov/sichuan")),
    ("北京市政府网", hub("/gov/beijing")),
    ("中国日报", ["http://www.chinadaily.com.cn/rss/china_rss.xml"]),
    ("中国日报-国际", ["http://www.chinadaily.com.cn/rss/world_rss.xml"]),
    ("CGTN", ["https://www.cgtn.com/subscribe/rss/section/china.xml"]),
    ("CGTN-国际", ["https://www.cgtn.com/subscribe/rss/section/world.xml"]),
]

# ---------------- 国际新闻信源（10+ 家国际主流媒体） ----------------
INTERNATIONAL_SOURCES = [
    ("BBC News", ["https://feeds.bbci.co.uk/news/world/rss.xml"]),
    ("The Guardian", ["https://www.theguardian.com/world/rss"]),
    ("The Guardian AI", ["https://www.theguardian.com/technology/artificialintelligenceai/rss"]),
    ("Al Jazeera", ["https://www.aljazeera.com/xml/rss/all.xml"]),
    ("NPR", ["https://feeds.npr.org/1004/rss.xml"]),
    ("France 24", ["https://www.france24.com/en/rss"]),
    ("RT", ["https://www.rt.com/rss/news/"]),
    ("TASS", ["https://tass.com/rss/v2.xml"]),
    ("DW", ["https://rss.dw.com/rdf/rss-en-world"]),
    ("Sky News", ["https://feeds.skynews.com/feeds/rss/world.xml"]),
    ("ABC News (AU)", ["https://www.abc.net.au/news/feed/2942460/rss.xml"]),
    ("SCMP", ["https://www.scmp.com/rss/91/feed"]),
]

# ---------------- 城市与天气 ----------------
CITIES = [
    ("南京", 32.06, 118.80),
    ("武汉", 30.59, 114.31),
    ("南宁", 22.82, 108.32),
]

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

# ---------------- 内容筛选规则 ----------------
DOMESTIC_EXCLUDE = ["娱乐", "明星", "八卦", "绯闻", "综艺", "演唱会", "电竞", "球星"]

DOMESTIC_CATEGORIES = {
    "科技": ["人工智能", "AI", "大模型", "芯片", "半导体", "量子", "算力", "航天",
             "卫星", "火箭", "发射", "空间站", "探月", "北斗", "机器人", "无人机",
             "新能源", "光伏", "储能", "电动车", "自动驾驶", "5G", "6G", "华为",
             "软件", "互联网", "数字化", "科技创新", "生物医药", "科学", "院士", "专利"],
    "国防": ["国防", "军队", "军事", "演习", "军演", "战备", "航母", "战机", "导弹",
             "火箭军", "解放军", "海军", "空军", "陆军", "国防部", "军工", "装备",
             "边境", "南海", "台海", "练兵", "阅兵"],
    "政治": ["习近平", "中共中央", "国务院", "全国人大", "全国政协", "常委会", "会议",
             "部署", "政策", "规划", "纲要", "外交", "会见", "磋商", "谈判", "立法",
             "改革", "开放", "高质量发展", "一带一路", "自贸区", "新时代", "治理",
             "中央", "部委", "发布会", "报告", "意见", "条例", "规定"],
    "经济": ["经济", "增长", "GDP", "投资", "外贸", "进出口", "贸易", "关税", "金融",
             "银行", "央行", "汇率", "人民币", "股市", "财政", "税收", "制造业", "工业",
             "企业", "民营经济", "消费", "物价", "产业", "项目", "出口", "进口",
             "产能", "供应链", "订单"],
}

INTL_EXCLUDE_RE = re.compile(
    r"(?i)\b(protest(ers?|s)?|crash(es|ed|ing)?|celebrity|entertainment|"
    r"actress|singer|gossip|scandal|football|soccer|tennis|boxing|movie|concert|"
    r"meme|viral)\b"
)

INTL_TOPIC_RE = re.compile(
    r"(?i)\b(?:president|election|summit|diplomat|sanction|government|minister|"
    r"parliament|senate|defense|military|trade|tariff|energy|economy|bank|"
    r"technology|cyber|satellite|space|semiconductor|chips?|ai|"
    r"artificial intelligence|robotics|nuclear)\b"
)

AI_RE = re.compile(
    r"(?i)\b(?:artificial intelligence|openai|anthropic|chatgpt|deepmind|nvidia|"
    r"machine learning|llm|gpt|robotics|generative ai|large language model|ai)\b"
)


# ---------------- 基础工具 ----------------
def fetch_bytes(url, timeout=8):
    req = urllib.request.Request(url, headers=HTTP_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


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


def parse_feed(content):
    m = re.search(rb'encoding=["\']?([\w-]+)', content[:200])
    enc = m.group(1).decode("ascii", "ignore") if m else "utf-8"
    try:
        text = content.decode(enc, errors="replace")
    except LookupError:
        text = content.decode("utf-8", errors="replace")
    return ET.fromstring(text)


def parse_rss(source, content):
    root = parse_feed(content)
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


def fetch_source(name, urls):
    for url in urls:
        try:
            return parse_rss(name, fetch_bytes(url))
        except Exception as exc:
            print(f"[news] {name} 抓取失败：{exc}", file=sys.stderr)
    return []


def collect_news(sources):
    all_items = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for items in pool.map(lambda s: fetch_source(*s), sources):
            all_items.extend(items)
    return all_items


def dedupe(items):
    seen = set()
    unique = []
    for it in items:
        key = re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", it["title"].lower())
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(it)
    unique.sort(
        key=lambda it: pub_dt(it),
        reverse=True,
    )
    return unique


def is_live_blog(title):
    return bool(re.search(r"(?i)(news live|politics live|\blive$)", title))


def text_of(item):
    return item["title"] + " " + item["summary"]


def pub_dt(item):
    """发布时间；缺省（如人民网等无 pubDate 的源）按当前时间处理。"""
    return item["published"] or datetime.now(TZ)


def pick_domestic(items, limit=5):
    items = filter_recent(items)
    scored = []
    for it in items:
        if is_live_blog(it["title"]):
            continue
        text = text_of(it)
        if any(k in text for k in DOMESTIC_EXCLUDE):
            continue
        score = sum(
            1 for words in DOMESTIC_CATEGORIES.values() if any(w in text for w in words)
        )
        scored.append({"item": it, "score": score})
    scored.sort(
        key=lambda x: (x["score"], pub_dt(x["item"])),
        reverse=True,
    )
    picked = [x for x in scored if x["score"] > 0][:limit]
    if len(picked) < limit:
        for x in scored:
            if len(picked) >= limit:
                break
            if x not in picked:
                picked.append(x)
    return picked


def pick_international(items, limit=5):
    items = filter_recent(items)
    pool = []
    for it in items:
        if is_live_blog(it["title"]):
            continue
        text = text_of(it).lower()
        if INTL_EXCLUDE_RE.search(text):
            continue
        score = len(INTL_TOPIC_RE.findall(text))
        ai = bool(AI_RE.search(text))
        pool.append({"item": it, "score": score, "ai": ai})
    pool.sort(
        key=lambda x: (x["score"], pub_dt(x["item"])),
        reverse=True,
    )
    preferred = [x for x in pool if x["score"] > 0]
    rest = [x for x in pool if x["score"] == 0]
    picked = []
    ai_items = [x for x in preferred if x["ai"]]
    if ai_items:
        picked.append(max(ai_items, key=lambda x: pub_dt(x["item"])))
    for x in preferred:
        if len(picked) >= limit:
            break
        if x not in picked:
            picked.append(x)
    for x in rest:
        if len(picked) >= limit:
            break
        if x not in picked:
            picked.append(x)
    return picked


def filter_recent(items, hours=24):
    """只保留有明确发布时间、且在最近 hours 小时内的新闻；若不足，放宽到 48 小时。

    没有发布时间的源（如人民网旧 RSS）一律不采用，保证时效性。
    """
    cutoff = datetime.now(TZ) - timedelta(hours=hours)
    recent = [it for it in items if it["published"] and it["published"] >= cutoff]
    if len(recent) < 5 and hours < 48:
        return filter_recent(items, hours=48)
    return recent


def to_news_list(picked):
    result = []
    for rank, entry in enumerate(picked, start=1):
        it = entry["item"]
        pub = it["published"].astimezone(TZ) if it["published"] else None
        result.append({
            "rank": rank,
            "title": it["title"],
            "source": it["source"],
            "link": it["link"],
            "published": pub.strftime("%Y-%m-%d %H:%M") if pub else "时间未知",
            "summary": it["summary"],
            "ai": bool(entry.get("ai")),
        })
    return result


# ---------------- 天气 ----------------
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
        data = None
        for attempt in range(2):
            try:
                data = json.loads(fetch_bytes(url).decode("utf-8"))
                break
            except Exception as exc:
                print(f"[weather] {city} 第 {attempt + 1} 次获取失败：{exc}", file=sys.stderr)
        if data:
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
        else:
            result.append({
                "city": city,
                "current": None,
                "min": None,
                "max": None,
                "condition": "暂不可用",
                "icon": "🌡️",
            })
    return result


# ---------------- 问候语 ----------------
def pick_greeting():
    lang = random.choice(list(GREETINGS))
    text = random.choice(GREETINGS[lang])
    count = len(text.split()) if lang != "中文" else len(re.sub(r"\s", "", text))
    if count > 30:
        raise ValueError(f"问候语超过 30 词：{lang}: {text}")
    return {"text": text, "language": lang, "words": count}


# ---------------- 主流程 ----------------
def main():
    now = datetime.now(TZ)
    domestic = to_news_list(pick_domestic(dedupe(collect_news(DOMESTIC_SOURCES))))
    international = to_news_list(pick_international(dedupe(collect_news(INTERNATIONAL_SOURCES))))
    data = {
        "date": now.strftime("%Y-%m-%d"),
        "updated_at": now.strftime("%Y-%m-%d %H:%M"),
        "timezone": "Asia/Shanghai（北京时间）",
        "greeting": pick_greeting(),
        "news": {
            "domestic": domestic,
            "international": international,
        },
        "weather": fetch_weather(),
    }
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    tmp = DATA_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_PATH)
    print(
        f"[generate] 已更新：国内 {len(domestic)} 条 / 国际 {len(international)} 条 "
        f"/ 天气 {len(data['weather'])} 城 / 问候语：{data['greeting']['language']}",
        flush=True,
    )
    return data


if __name__ == "__main__":
    main()
