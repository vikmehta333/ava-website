#!/usr/bin/env python3
"""
Publish queued AI use cases to avadigitalagency.com.

Reads data/usecases/queue/*.json (items with status "queued"), creates a detail
page for each at /ai-use-cases/<slug>/, adds a card to the hub, updates
data/usecases/library.json, marks the queue items published, purges caches and
verifies every new page.

Credentials come from the environment and are NEVER stored in this repo:
    export WP_USER=...            # e.g. vikmehta
    export WP_APP_PASSWORD=...    # a WordPress Application Password

Usage:
    python3 scripts/publish_usecases.py          # dry run (default)
    python3 scripts/publish_usecases.py --go     # actually publish
"""
import base64, json, os, re, sys, glob, html, datetime, urllib.request, urllib.error

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://avadigitalagency.com/wp-json/wp/v2"
HUB_ID = 24305
TEMPLATE_SLUG = "turn-voicemails-into-tasks"   # an existing no-video detail page
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
CATLABEL = {"lead":"Lead Response","marketing":"Marketing","content":"Content","sales":"Sales",
            "ops":"Operations","seo":"Local SEO","cs":"Customer Service"}
GO = "--go" in sys.argv

user, pw = os.environ.get("WP_USER"), os.environ.get("WP_APP_PASSWORD")
if not user or not pw:
    sys.exit("ERROR: set WP_USER and WP_APP_PASSWORD in the environment (never commit them).")
AUTH = base64.b64encode(f"{user}:{pw.replace(' ','')}".encode()).decode()

def req(url, data=None, method=None):
    h = {"Authorization": "Basic "+AUTH, "User-Agent": UA, "Accept": "application/json, */*"}
    if data is not None:
        h["Content-Type"] = "application/json"; data = json.dumps(data).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h, method=method), timeout=120))

def purge():
    for t in ("object", "ALL"):
        try:
            urllib.request.urlopen(urllib.request.Request(
                f"https://avadigitalagency.com/?LSCWP_CTRL=PURGE&LSCWP_TYPE={t}",
                headers={"Authorization":"Basic "+AUTH, "User-Agent":UA}), timeout=60).read()
        except Exception as e:
            print("  purge warning:", e)

def esc(t): return html.escape(t, quote=False)

# ---------- load queued items ----------
queue_files = sorted(glob.glob(os.path.join(REPO, "data/usecases/queue/*.json")))
items, origin = [], {}
for qf in queue_files:
    try: data = json.load(open(qf, encoding="utf-8"))
    except Exception as e: print(f"  skip {qf}: {e}"); continue
    for it in (data if isinstance(data, list) else [data]):
        if it.get("status") == "queued":
            items.append(it); origin[it["slug"]] = qf
if not items:
    sys.exit("Nothing queued. (Did the nightly queue file get committed? See docs/AI_USECASE_PUBLISH_RUNBOOK.md)")

library = json.load(open(os.path.join(REPO,"data/usecases/library.json"), encoding="utf-8"))

# Dedup against the LIVE site, not library.json — the index can be stale
# (the cloud publisher doesn't write to this repo). The live hub is authoritative.
def _live_slugs():
    slugs, page = set(), 1
    while page < 5:
        r = req(f"{BASE}/pages?parent={HUB_ID}&per_page=100&page={page}&status=publish&_fields=slug")
        if not r: break
        slugs |= {p["slug"] for p in r}
        if len(r) < 100: break
        page += 1
    return slugs
live_slugs = _live_slugs()
items = [i for i in items if i["slug"] not in live_slugs]
print(f"queued and not yet live: {len(items)}")
for i in items: print("  •", i["slug"], "|", i["category"])
if not GO:
    print("\nDRY RUN — rerun with --go to publish.")

# ---------- build detail page from the live template ----------
tpl_pages = req(f"{BASE}/pages?slug={TEMPLATE_SLUG}&per_page=5&_fields=id,parent")
tpl_id = next((p["id"] for p in tpl_pages if p.get("parent")==HUB_ID), None)
if not tpl_id: sys.exit(f"template page '{TEMPLATE_SLUG}' not found under the hub")
TPL = req(f"{BASE}/pages/{tpl_id}?_fields=content&context=edit")["content"]["raw"]

def build_detail(it):
    h = TPL
    title_tag = f"{it['title']} — AI Use Case | Ava Digital"
    steps = "".join(f"<li>{esc(s)}</li>" for s in it["steps"])
    h = re.sub(r'<title>.*?</title>', lambda m: f"<title>{esc(title_tag)}</title>", h, count=1, flags=re.S)
    h = re.sub(r'<meta name="description" content=".*?">',
               lambda m: f'<meta name="description" content="{html.escape(it["one_liner"])}">', h, count=1, flags=re.S)
    h = re.sub(r'<link rel="canonical" href=".*?">',
               lambda m: f'<link rel="canonical" href="https://avadigitalagency.com/ai-use-cases/{it["slug"]}/">', h, count=1, flags=re.S)
    h = re.sub(r'<div class="dnum">.*?</div>',
               lambda m: f'<div class="dnum">AI Use Case · {esc(CATLABEL.get(it["category"],it["category"]))}</div>', h, count=1, flags=re.S)
    h = re.sub(r'<h1>.*?</h1>', lambda m: f"<h1>{esc(it['title'])}</h1>", h, count=1, flags=re.S)
    h = re.sub(r'<p class="dq">.*?</p>', lambda m: f'<p class="dq">{esc(it["one_liner"])}</p>', h, count=1, flags=re.S)
    h = re.sub(r'<div class="dtags">.*?</div>', lambda m: '<div class="dtags"></div>', h, count=1, flags=re.S)
    h = re.sub(r'<ol class="steps">.*?</ol>', lambda m: f'<ol class="steps">{steps}</ol>', h, count=1, flags=re.S)
    h = re.sub(r'<div class="guard">.*?</div>', lambda m: f'<div class="guard">{esc(it["guardrail"])}</div>', h, count=1, flags=re.S)
    h = re.sub(r'<p class="dtools">.*?</p>',
               lambda m: f'<p class="dtools"><b>Tools that do this:</b> {esc(it["tools"])}</p>', h, count=1, flags=re.S)
    h = re.sub(r'(<div class="pblock">.*?<pre>).*?(</pre>)',
               lambda m: m.group(1)+esc(it["prompt"])+m.group(2), h, count=1, flags=re.S)
    schema = json.dumps({"@context":"https://schema.org","@type":"HowTo","name":it["title"],
        "description":it["one_liner"],
        "step":[{"@type":"HowToStep","position":n+1,"text":s} for n,s in enumerate(it["steps"])]}, ensure_ascii=False)
    h = re.sub(r'<script type="application/ld\+json">.*?</script>',
               lambda m: f'<script type="application/ld+json">{schema}</script>', h, count=1, flags=re.S)
    return h, title_tag

ELCLEAR = {"_elementor_edit_mode":"", "_elementor_data":"", "_elementor_template_type":""}
published = []
for it in items:
    h, title_tag = build_detail(it)
    # safety: the template must not leak into the new page
    if "voicemail" in h.lower() and "voicemail" not in json.dumps(it).lower():
        print(f"  !! {it['slug']}: template content leaked, skipping"); continue
    if not GO:
        print(f"  would publish {it['slug']} ({len(h)} bytes)"); continue
    ex = req(f"{BASE}/pages?slug={it['slug']}&per_page=5&_fields=id,parent")
    pid = next((p["id"] for p in ex if p.get("parent")==HUB_ID), None)
    meta = {"_yoast_wpseo_title":title_tag, "_yoast_wpseo_metadesc":it["one_liner"], **ELCLEAR}
    body = {"content":h, "status":"publish", "template":"elementor_canvas", "parent":HUB_ID, "meta":meta}
    if pid: req(f"{BASE}/pages/{pid}", body, "POST")
    else:
        body.update({"title":it["title"], "slug":it["slug"]})
        pid = req(f"{BASE}/pages", body, "POST")["id"]
    published.append((it, pid)); print(f"  ✔ published {it['slug']} -> {pid}")

if not GO: sys.exit(0)

# ---------- rebuild hub cards + counts ----------
hub = req(f"{BASE}/pages/{HUB_ID}?_fields=content&context=edit")["content"]["raw"]
existing = re.findall(r'<a class="uc(?: ucf)?" href="/ai-use-cases/([a-z0-9-]+)/" data-cat="([a-z]+)"[^>]*>.*?<h3>(.*?)</h3><p>(.*?)</p>', hub, re.S)
cards = [{"slug":s,"cat":c,"title":t,"one":o,"ucf":f'/ai-use-cases/{s}/" data-cat' in hub and f'<a class="uc ucf" href="/ai-use-cases/{s}/"' in hub,"new":False} for s,c,t,o in existing]
for it,_ in published:
    cards.append({"slug":it["slug"],"cat":it["category"],"title":it["title"],"one":it["one_liner"],"ucf":False,"new":True})
def card_html(c):
    txt = (c["title"]+" "+c["one"]+" "+CATLABEL.get(c["cat"],c["cat"])).lower().replace('"',"")
    badge = '<span class="newb">New</span>' if c["new"] else ''
    cls = "uc ucf" if c["ucf"] else "uc"
    return (f'<a class="{cls}" href="/ai-use-cases/{c["slug"]}/" data-cat="{c["cat"]}" data-text="{html.escape(txt)}">'
            f'<div class="uct"><span class="tag">{CATLABEL.get(c["cat"],c["cat"])}</span>{badge}</div>'
            f'<h3>{esc(c["title"])}</h3><p>{esc(c["one"])}</p>'
            f'<span class="bl">See how it works &rarr;</span></a>')
cards.sort(key=lambda c: (not c["new"], not c["ucf"]))
grid = "".join(card_html(c) for c in cards)
hub = re.sub(r'(<div class="uc-grid2" id="ucgrid">).*?(<div class="uc-empty")', lambda m: m.group(1)+grid+m.group(2), hub, count=1, flags=re.S)
from collections import Counter
cnt = Counter(c["cat"] for c in cards); total=len(cards); newc=sum(1 for c in cards if c["new"])
def snav_sub(m):
    cat = m.group(1)
    return f'<button class="snav{m.group(2)}" data-cat="{cat}"><span>{m.group(3)}</span><b>{total if cat=="all" else cnt.get(cat,0)}</b></button>'
hub = re.sub(r'<button class="snav( on)?" data-cat="([a-z]+)"><span>(.*?)</span><b>\d+</b></button>',
             lambda m: f'<button class="snav{m.group(1) or ""}" data-cat="{m.group(2)}"><span>{m.group(3)}</span><b>{total if m.group(2)=="all" else cnt.get(m.group(2),0)}</b></button>', hub)
hub = re.sub(r'<span class="nw">\d+ new this week</span>', lambda m: f'<span class="nw">{newc} new this week</span>', hub, count=1)
req(f"{BASE}/pages/{HUB_ID}", {"content":hub}, "POST")
print(f"  ✔ hub updated: {total} cards, {newc} new")

purge(); print("  ✔ caches purged")

# ---------- update library + mark queue published ----------
today = datetime.date.today().isoformat()
for it,pid in published:
    library["items"].append({"id":pid,"slug":it["slug"],"title":it["title"],"one_liner":it["one_liner"],
        "category":CATLABEL.get(it["category"],it["category"]),"has_reel":False,
        "url":f"https://avadigitalagency.com/ai-use-cases/{it['slug']}/","status":"published","published_at":today})
library["items"].sort(key=lambda x:x["slug"]); library["count"]=len(library["items"]); library["generated_at"]=today
json.dump(library, open(os.path.join(REPO,"data/usecases/library.json"),"w"), indent=1, ensure_ascii=False)
touched=set()
for it,_ in published:
    qf=origin[it["slug"]]; d=json.load(open(qf,encoding="utf-8"))
    for row in (d if isinstance(d,list) else [d]):
        if row.get("slug")==it["slug"]: row["status"]="published"; row["published_at"]=today
    json.dump(d, open(qf,"w"), indent=1, ensure_ascii=False); touched.add(qf)
print(f"  ✔ library.json now {library['count']} items; marked published in {len(touched)} queue file(s)")

# ---------- verify ----------
print("\nverifying live pages:")
for it,_ in published:
    url=f"https://avadigitalagency.com/ai-use-cases/{it['slug']}/?v={today}"
    try:
        page=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=60).read().decode("utf-8","ignore")
        ok = ("--bg:#f7f8fc" in page and "Hanken Grotesk" in page and "<p><!DOCTYPE" not in page
              and 'class="nav-cta"' in page and "<footer>" in page)
        print(f"  {'PASS' if ok else 'FAIL'}  {it['slug']}")
    except Exception as e:
        print(f"  FAIL  {it['slug']}: {e}")
