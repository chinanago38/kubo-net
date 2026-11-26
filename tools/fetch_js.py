#!/usr/bin/env python3
"""防衛省・統合幕僚監部の報道発表資料一覧から「中国海軍艦艇の動向について」のPDFを取り、
空母（遼寧・山東・福建）が出てくる発表だけを data/js_china.json に保存する（GitHub Actions で実行）。
保存するのは日付・題名・PDFのURL・出てくる空母・本文の最初の段落（政府の公表資料、出典を表示して利用）。"""
import json, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "js_china.json")
INDEX = "https://www.mod.go.jp/js/press/index.html"
UA = {"User-Agent": "Mozilla/5.0 (kubo-net press fetcher; https://xn--3owz62a.net/)"}
CARRIERS = ["遼寧", "山東", "福建"]

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()

def pdf_text(data):
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(data); f.flush()
        return subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True).stdout

def norm(s):
    # 全角数字・空白を整える
    s = s.translate(str.maketrans("０１２３４５６７８９ｋｍ", "0123456789km"))
    return re.sub(r"[ 　]+", "", s)

def first_paragraph(text):
    t = norm(text)
    m = re.search(r"(令和\d+年\d+月\d+日（.）.*?確認(?:した|された)。)", t.replace("\n", ""))
    if not m:
        m = re.search(r"(海上自衛隊は.*?確認(?:した|された)。)", t.replace("\n", ""))
    return m.group(1)[:300] if m else ""

def main():
    try:
        data = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        data = {"items": [], "checked": []}
    checked = set(data.get("checked", []))
    items = {i["url"]: i for i in data.get("items", [])}
    try:
        page = get(INDEX).decode("utf-8", "ignore")
    except Exception as e:
        print("index error:", e, file=sys.stderr); sys.exit(1)
    links = re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', page, re.S)
    print("pdf links:", len(links))
    n = 0
    for href, title in links:
        title = re.sub(r"<[^>]+>|\s+", "", title)
        if "中国海軍艦艇" not in title: continue
        url = urllib.parse.urljoin(INDEX, href)
        if url in checked: continue
        try:
            text = pdf_text(get(url))
        except Exception as e:
            print("pdf error:", url, e, file=sys.stderr); continue
        checked.add(url); n += 1
        found = [c for c in CARRIERS if c in text]
        if not found and "空母" not in text: continue
        m = re.search(r"p(\d{4})(\d{2})(\d{2})_", url)
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
        items[url] = {"date": date, "title": title, "url": url, "carriers": found, "summary": first_paragraph(text)}
        print("carrier:", date, found, title)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
           "source": "防衛省・統合幕僚監部 報道発表資料", "items": sorted(items.values(), key=lambda x: x["date"], reverse=True)[:200],
           "checked": sorted(checked)[-1000:]}
    tmp = OUT + ".tmp"
    json.dump(out, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)
    print("checked new:", n, "carrier items:", len(out["items"]))

if __name__ == "__main__":
    main()
