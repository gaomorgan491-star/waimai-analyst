#!/usr/bin/env python3
"""抓取 RSS 并更新 index.html 中的 newsData 数组
   排序规则（Python 端完成）：
     priority=3（外卖/美团/餐饮）最前
     priority=1（AI/抖音）最后
     同 priority 按时间倒序（最新在前）
   浏览器端 renderNews() 不做排序，直接按数组顺序渲染
"""
import json
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ── 关键词配置 ──────────────────────────────────────────
KEYWORDS = [
    '外卖', '美团', '饿了么', '抖音', '抖音外卖',
    'AI', '人工智能', '餐饮', '闪购', '美团闪购',
    '即时零售', '本地生活', '配送', '骑手', '商家',
    '外卖平台', '饿了么', '美团外卖', '饿了么外卖',
    '餐厅', '饭店', '奶茶', '咖啡', '快餐', '生鲜',
    '京东外卖', '外卖员', '众包', '专送', '拼好饭',
    '饿了么星选', '达达', '美团买菜', '美团优选',
    '小象超市', '盒马', '叮咚'
]

PRIORITY_HIGH = [
    '外卖', '美团', '饿了么', '餐饮', '餐厅', '饭店', '奶茶', '咖啡',
    '快餐', '生鲜', '闪购', '美团闪购', '即时零售', '本地生活',
    '配送', '骑手', '商家', '外卖平台', '美团外卖', '饿了么外卖',
    '京东外卖', '外卖员', '众包', '专送', '拼好饭', '饿了么',
    '饿了么星选', '抖音外卖', '达达', '美团买菜', '美团优选',
    '小象超市', '盒马', '叮咚'
]
PRIORITY_LOW = ['AI', '人工智能', '抖音']


def get_priority(text):
    for kw in PRIORITY_HIGH:
        if kw in text:
            return 3
    for kw in PRIORITY_LOW:
        if kw in text:
            return 1
    return 2


def is_relevant(text):
    for kw in KEYWORDS:
        if kw in text:
            return True
    return False


def fetch_rss(rss_url, max_items=30):
    """通过 rss2json.com 代理抓取 RSS，返回 item 列表"""
    api = "https://api.rss2json.com/v1/api.json?rss_url=" + urllib.parse.quote(rss_url, safe='')
    try:
        req = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        if data.get("status") != "ok":
            return []
        items = []
        for item in data.get("items", [])[:max_items]:
            title = re.sub(r'<[^>]+>', '', item.get("title", "")).strip()
            desc  = re.sub(r'<[^>]+>', ' ', item.get("description", "")).strip()
            desc  = re.sub(r'\s+', ' ', desc)[:150]
            pub   = item.get("pubDate", "")
            link  = item.get("link", "")
            if not title:
                continue
            items.append({
                "title": title,
                "summary": desc,
                "pubDate": pub,
                "url": link
            })
        return items
    except Exception as e:
        print("    Error: " + str(e))
        return []


# ── RSS 源列表 ──────────────────────────────────────────
sources = [
    # 普通 RSS（作为基础来源）
    {"name": "36氪",   "rss": "https://36kr.com/feed",                    "cls": "source-36kr"},
    {"name": "虎嗅",   "rss": "https://www.huxiu.com/rss/1.xml",       "cls": "source-tmt"},
    {"name": "爱范儿", "rss": "https://www.ifanr.com/feed",               "cls": "source-ifanr"},
    {"name": "IT之家",  "rss": "https://www.ithome.com/rss/",             "cls": "source-ithome"},
    {"name": "钛媒体",  "rss": "https://www.tmtpost.com/rss.xml",         "cls": "source-tmt"},
    # RSSHub 标签路由（能直接拿到带标签的文章，需要 RSSHub 可访问）
    {"name": "36氪-美团",   "rss": "https://rsshub.app/36kr/tag/美团",   "cls": "source-36kr"},
    {"name": "36氪-外卖",   "rss": "https://rsshub.app/36kr/tag/外卖",   "cls": "source-36kr"},
    {"name": "36氪-餐饮",   "rss": "https://rsshub.app/36kr/tag/餐饮",   "cls": "source-36kr"},
]

# ── 抓取 ──────────────────────────────────────────────────
all_news  = []
seen_titles = set()

for src in sources:
    name = src["name"]
    rss  = src["rss"]
    cls  = src["cls"]
    print("Fetching " + name + " ...")
    items = fetch_rss(rss)
    print("  Got " + str(len(items)) + " items")
    count = 0
    for item in items:
        t = item["title"]
        s = item["summary"]
        if t in seen_titles:
            continue
        combined = t + " " + s
        if is_relevant(combined):
            pri = get_priority(combined)
            all_news.append({
                "title":       t,
                "summary":     s,
                "pubDate":     item["pubDate"],
                "url":         item["url"],
                "source":      name,
                "sourceClass": cls,
                "priority":    pri
            })
            seen_titles.add(t)
            count += 1
            print("    [p=" + str(pri) + "] " + t[:55])
    print("  Added " + str(count) + " relevant items\n")

print("Total before sort: " + str(len(all_news)))

# ── 排序（Python 端完成）──────────────────────────────────
# 先按时间倒序，再按 priority 倒序（稳定排序 = 高优先级在前）
all_news.sort(key=lambda x: x.get("pubDate", ""), reverse=True)
all_news.sort(key=lambda x: x.get("priority", 2), reverse=True)
all_news = all_news[:25]

print("\n=== 排序后（共 " + str(len(all_news)) + " 条）===")
for i, n in enumerate(all_news):
    print("  " + str(i+1) + ". [p=" + str(n["priority"]) + "] " + n["title"][:60])

# ── 更新 index.html ────────────────────────────────────────
with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

def format_time(pub_date):
    try:
        d    = datetime.strptime(pub_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        diff = (datetime.now(timezone.utc) - d).total_seconds()
        if   diff < 60:   return '刚刚'
        elif diff < 3600:  return str(int(diff // 60)) + '分钟前'
        elif diff < 86400: return str(int(diff // 3600)) + '小时前'
        else:               return str(int(diff // 86400)) + '天前'
    except Exception:
        return '近期'

def extract_tags(text):
    keywords = ['外卖','美团','饿了么','抖音','AI','人工智能','餐饮',
                '闪购','美团闪购','即时零售','本地生活','配送','骑手','商家',
                '京东外卖','饿了么外卖','奶茶','咖啡','生鲜','饿了么']
    tags = []
    for kw in keywords:
        if kw in text and len(tags) < 2:
            tags.append(kw)
    if not tags:
        tags.append('行业资讯')
    return tags

def je(s):
    """JS 字符串安全转义"""
    return (s.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", " ")
            .replace("\r", " ")
            .replace("\t", " "))

# ── 构建 newsData 数组文本 ─────────────────────────────────
news_lines = []
for item in all_news:
    time_str  = format_time(item["pubDate"])
    tags      = extract_tags(item["title"] + " " + item["summary"])
    tags_json = json.dumps(tags, ensure_ascii=False)
    line = ("  {\n"
             "    source: '" + je(item["source"]) + "',\n"
             "    sourceClass: '" + je(item["sourceClass"]) + "',\n"
             "    time: '" + je(time_str) + "',\n"
             "    title: '" + je(item["title"]) + "',\n"
             "    summary: '" + je(item["summary"]) + "',\n"
             "    url: '" + je(item["url"]) + "',\n"
             "    tags: " + tags_json + ",\n"
             "    priority: " + str(item["priority"]) + "\n"
             "  }")
    news_lines.append(line)

news_array = ",\n".join(news_lines)

# ── 替换 index.html 中的 newsData 数组 ─────────────────────
# 找到 "const newsData = [" 的位置
nd_start = content.find("\nconst newsData = [\n")
if nd_start == -1:
    print("\nERROR: 找不到 newsData 数组起始位置")
    sys.exit(1)

# 找到对应的 "];" 位置
nd_end = content.find("\n];\n", nd_start)
if nd_end == -1:
    print("\nERROR: 找不到 newsData 数组结束位置")
    sys.exit(1)

nd_end = nd_end + 4  # 包含 ];\n

new_block = "\nconst newsData = [\n" + news_array + "\n];\n"
content = content[:nd_start] + new_block + content[nd_end:]

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("\nDone! index.html updated with " + str(len(all_news)) + " items.")
print("Array is already sorted: priority 3 (外卖/餐饮) items come FIRST.")
