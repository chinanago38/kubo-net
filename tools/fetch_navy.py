#!/usr/bin/env python3
"""navy.mil 公式RSSから空母関連のニュースだけを取り出して data/navy_news.json に保存する。
保存するのはタイトル・日付・リンク・短い説明のみ（米政府の公開情報）。"""
import json, os, re, sys, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FEEDS = {
    "news": "https://www.navy.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1067&max=100",
}
CARRIERS = {
    "CVN 68": "Nimitz", "CVN 69": "Dwight D. Eisenhower", "CVN 70": "Carl Vinson",
    "CVN 71": "Theodore Roosevelt", "CVN 72": "Abraham Lincoln", "CVN 73": "George Washington",
    "CVN 74": "John C. Stennis", "CVN 75": "Harry S. Truman", "CVN 76": "Ronald Reagan",
    "CVN 77": "George H.W. Bush", "CVN 78": "Gerald R. Ford", "CVN 79": "John F. Kennedy",
}
KEYWORDS = [r"aircraft carrier", r"\bCVN[- ]?\d{2}\b", r"carrier strike group", r"\bCSG ?\d+\b"] + \
           [re.escape(n) for n in CARRIERS.values()]
PAT = re.compile("|".join(KEYWORDS), re.I)
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "navy_news.json")

def clean(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", s).strip()

def ships_in(text):
    found = []
    for hull, name in CARRIERS.items():
        n = hull.split()[1]
        if re.search(r"\bUSS " + re.escape(name) + r"\b(?!-class)", text, re.I) or \
           re.search(r"\b" + re.escape(name) + r" (Carrier Strike Group|CSG)", text, re.I) or \
           re.search(r"\bCVN[- ]?" + n + r"\b", text, re.I):
            found.append(hull)
    return found

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (kubo-net news fetcher)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()

MEDIA_NS = "{http://search.yahoo.com/mrss/}"
def image_in(it):
    # RSSの添付画像（enclosure / media:content / media:thumbnail）
    for e in it.findall("enclosure"):
        if (e.get("type") or "").startswith("image") or re.search(r"\.(jpe?g|png)$", e.get("url") or "", re.I):
            return e.get("url")
    for tag in ("content", "thumbnail"):
        for e in it.iter(MEDIA_NS + tag):
            if e.get("url"): return e.get("url")
    m = re.search(r'<img[^>]+src="([^"]+)"', it.findtext("description") or "")
    return m.group(1) if m else ""

def og_image(link):
    # RSSに画像がないときは記事ページの og:image（米海軍の公開写真）を使う
    try:
        page = fetch(link).decode("utf-8", "ignore")
    except Exception:
        return ""
    m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', page) or \
        re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', page)
    return m.group(1) if m else ""

def ok_img(u):
    return bool(u) and u.startswith("https://") and bool(re.search(r"(navy\.mil|defense\.gov|dvidshub\.net)/", u))

def main():
    try:
        old = {i["link"]: i for i in json.load(open(OUT, encoding="utf-8"))["items"]}
    except Exception:
        old = {}
    ok = 0
    for kind, url in FEEDS.items():
        try:
            root = ET.fromstring(fetch(url))
            ok += 1
        except Exception as e:
            print(f"[warn] {kind}: {e}", file=sys.stderr)
            continue
        for it in root.iter("item"):
            title = clean(it.findtext("title"))
            desc = clean(it.findtext("description"))[:300]
            link = (it.findtext("link") or "").strip()
            if not link.startswith("https://www.navy.mil/") or not PAT.search(title + " " + desc):
                continue
            try:
                date = parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                date = ""
            img = image_in(it)
            if not ok_img(img):
                img = old.get(link, {}).get("image", "")
            if not ok_img(img):
                img = og_image(link)
            old[link] = {"date": date, "title": title, "summary": desc, "link": link,
                         "kind": kind, "ships": ships_in(title + " " + desc),
                         "image": img if ok_img(img) else ""}
    if ok == 0:
        print("no feed reachable; keeping existing data", file=sys.stderr)
        sys.exit(1)
    # 以前に取り込んだ記事で画像がまだないものも補う
    for it in old.values():
        if it.get("ships") and not it.get("image"):
            img = og_image(it["link"])
            it["image"] = img if ok_img(img) else ""
    items = sorted(old.values(), key=lambda x: x["date"], reverse=True)[:300]
    data = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "source": "U.S. Navy (navy.mil) official RSS", "items": items}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)
    print(f"{len(items)} carrier items")

if __name__ == "__main__":
    main()
