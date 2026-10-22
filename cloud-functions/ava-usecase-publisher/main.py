"""
Cloud Function: Ava Digital — AI Use-Case Publisher.

Reads queued use cases from the public ava-website repo, publishes any that
aren't live yet to avadigitalagency.com, and verifies each page.

Deliberately needs NO GitHub write access: "already published" is determined by
querying WordPress for the hub's child pages, not by a repo index. The nightly
harvest routine refreshes data/usecases/library.json from the live site.

Triggered by Cloud Scheduler (~3 AM America/Chicago, after the 2 AM harvest).
"""
import base64, datetime, html, json, os, re
import requests
import functions_framework
from google.cloud import secretmanager

PROJECT_ID = "plasma-crossbar-486516-r8"
WP_URL = "https://avadigitalagency.com"
WP_API = f"{WP_URL}/wp-json/wp/v2"
WP_USER = os.environ.get("WP_USER", "vikmehta")
HUB_ID = 24305
TEMPLATE_SLUG = "turn-voicemails-into-tasks"      # existing no-video detail page
REPO = "vikmehta333/ava-website"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
CATLABEL = {"lead":"Lead Response","marketing":"Marketing","content":"Content","sales":"Sales",
            "ops":"Operations","seo":"Local SEO","cs":"Customer Service"}
ELCLEAR = {"_elementor_edit_mode":"", "_elementor_data":"", "_elementor_template_type":""}


def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    return client.access_secret_version(request={"name": name}).payload.data.decode("UTF-8")


def wp_headers(pw):
    tok = base64.b64encode(f"{WP_USER}:{pw.replace(' ','')}".encode()).decode()
    return {"Authorization": f"Basic {tok}", "User-Agent": UA,
            "Accept": "application/json, */*", "Content-Type": "application/json"}


def esc(t): return html.escape(t, quote=False)


def fetch_queued(days_back=10):
    """
    status=queued items from data/usecases/queue/<date>.json on the public repo.

    Deliberately uses raw.githubusercontent.com by DATE rather than the GitHub
    contents API: the API is rate-limited to 60 req/hour for unauthenticated
    callers on a shared Cloud Run egress IP, which produced a silent HTTP 500
    on 2026-10-22. Raw URLs have no such limit.
    """
    items, checked, found = [], 0, []
    today = datetime.date.today()
    for d in range(days_back):
        day = today - datetime.timedelta(days=d)
        url = f"https://raw.githubusercontent.com/{REPO}/main/data/usecases/queue/{day}.json"
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=45)
        except Exception as e:
            print(f"fetch_queued: {day} request failed: {e}")
            continue
        checked += 1
        if r.status_code == 404:
            continue
        if r.status_code != 200:
            print(f"fetch_queued: {day} HTTP {r.status_code}")
            continue
        try:
            data = r.json()
        except Exception as e:
            print(f"fetch_queued: {day} bad JSON: {e}")
            continue
        found.append(str(day))
        for it in (data if isinstance(data, list) else [data]):
            if it.get("status") == "queued":
                items.append(it)
    print(f"fetch_queued: checked {checked} day(s), queue files found: {found or 'none'}, "
          f"queued items: {len(items)}")
    return items, None


def live_slugs(h):
    """Slugs already published under the hub."""
    slugs, page = set(), 1
    while page < 5:
        r = requests.get(f"{WP_API}/pages?parent={HUB_ID}&per_page=100&page={page}"
                         f"&status=publish&_fields=slug", headers=h, timeout=60)
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        slugs |= {p["slug"] for p in batch}
        if len(batch) < 100:
            break
        page += 1
    return slugs


def build_detail(tpl, it):
    h = tpl
    title_tag = f"{it['title']} — AI Use Case | Ava Digital"
    steps = "".join(f"<li>{esc(s)}</li>" for s in it["steps"])
    schema = json.dumps({"@context":"https://schema.org","@type":"HowTo","name":it["title"],
        "description":it["one_liner"],
        "step":[{"@type":"HowToStep","position":n+1,"text":s} for n,s in enumerate(it["steps"])]},
        ensure_ascii=False)
    subs = [
        (r'<title>.*?</title>', f"<title>{esc(title_tag)}</title>"),
        (r'<meta name="description" content=".*?">', f'<meta name="description" content="{html.escape(it["one_liner"])}">'),
        (r'<link rel="canonical" href=".*?">', f'<link rel="canonical" href="{WP_URL}/ai-use-cases/{it["slug"]}/">'),
        (r'<div class="dnum">.*?</div>', f'<div class="dnum">AI Use Case · {esc(CATLABEL.get(it["category"],it["category"]))}</div>'),
        (r'<h1>.*?</h1>', f"<h1>{esc(it['title'])}</h1>"),
        (r'<p class="dq">.*?</p>', f'<p class="dq">{esc(it["one_liner"])}</p>'),
        (r'<div class="dtags">.*?</div>', '<div class="dtags"></div>'),
        (r'<ol class="steps">.*?</ol>', f'<ol class="steps">{steps}</ol>'),
        (r'<div class="guard">.*?</div>', f'<div class="guard">{esc(it["guardrail"])}</div>'),
        (r'<p class="dtools">.*?</p>', f'<p class="dtools"><b>Tools that do this:</b> {esc(it["tools"])}</p>'),
        (r'<script type="application/ld\+json">.*?</script>', f'<script type="application/ld+json">{schema}</script>'),
    ]
    for pat, rep in subs:
        h = re.sub(pat, lambda m, r=rep: r, h, count=1, flags=re.S)
    h = re.sub(r'(<div class="pblock">.*?<pre>).*?(</pre>)',
               lambda m: m.group(1)+esc(it["prompt"])+m.group(2), h, count=1, flags=re.S)
    return h, title_tag


def rebuild_hub(h, new_items):
    r = requests.get(f"{WP_API}/pages/{HUB_ID}?_fields=content&context=edit", headers=h, timeout=60)
    hub = r.json()["content"]["raw"]
    existing = re.findall(
        r'<a class="uc(?: ucf)?" href="/ai-use-cases/([a-z0-9-]+)/" data-cat="([a-z]+)"[^>]*>.*?<h3>(.*?)</h3><p>(.*?)</p>',
        hub, re.S)
    cards = [{"slug":s,"cat":c,"title":t,"one":o,
              "ucf": f'<a class="uc ucf" href="/ai-use-cases/{s}/"' in hub, "new":False}
             for s,c,t,o in existing]
    have = {c["slug"] for c in cards}
    for it in new_items:
        if it["slug"] not in have:
            cards.append({"slug":it["slug"],"cat":it["category"],"title":it["title"],
                          "one":it["one_liner"],"ucf":False,"new":True})

    def card_html(c):
        txt = (c["title"]+" "+c["one"]+" "+CATLABEL.get(c["cat"],c["cat"])).lower().replace('"',"")
        badge = '<span class="newb">New</span>' if c["new"] else ''
        cls = "uc ucf" if c["ucf"] else "uc"
        return (f'<a class="{cls}" href="/ai-use-cases/{c["slug"]}/" data-cat="{c["cat"]}" '
                f'data-text="{html.escape(txt)}"><div class="uct"><span class="tag">'
                f'{CATLABEL.get(c["cat"],c["cat"])}</span>{badge}</div><h3>{esc(c["title"])}</h3>'
                f'<p>{esc(c["one"])}</p><span class="bl">See how it works &rarr;</span></a>')

    cards.sort(key=lambda c: (not c["new"], not c["ucf"]))
    grid = "".join(card_html(c) for c in cards)
    hub = re.sub(r'(<div class="uc-grid2" id="ucgrid">).*?(<div class="uc-empty")',
                 lambda m: m.group(1)+grid+m.group(2), hub, count=1, flags=re.S)
    from collections import Counter
    cnt = Counter(c["cat"] for c in cards); total = len(cards)
    newc = sum(1 for c in cards if c["new"])
    hub = re.sub(r'<button class="snav( on)?" data-cat="([a-z]+)"><span>(.*?)</span><b>\d+</b></button>',
                 lambda m: f'<button class="snav{m.group(1) or ""}" data-cat="{m.group(2)}">'
                           f'<span>{m.group(3)}</span><b>{total if m.group(2)=="all" else cnt.get(m.group(2),0)}</b></button>',
                 hub)
    hub = re.sub(r'<span class="nw">\d+ new this week</span>',
                 lambda m: f'<span class="nw">{newc} new this week</span>', hub, count=1)
    requests.post(f"{WP_API}/pages/{HUB_ID}", headers=h, json={"content":hub}, timeout=90)
    return total, newc


def purge(h):
    for t in ("object", "ALL"):
        try:
            requests.get(f"{WP_URL}/?LSCWP_CTRL=PURGE&LSCWP_TYPE={t}", headers=h, timeout=60)
        except Exception:
            pass


@functions_framework.http
def publish_usecases(request):
    result = {"published": [], "skipped": [], "errors": [], "verified": []}
    try:
        pw = get_secret("ava-wp-app-password")
        h = wp_headers(pw)

        queued, err = fetch_queued()
        if err:
            result["errors"].append(err)
            return (json.dumps(result), 500, {"Content-Type":"application/json"})

        live = live_slugs(h)
        todo, seen = [], set()
        for it in queued:
            s = it.get("slug")
            if not s or s in seen:
                continue
            seen.add(s)
            if s in live:
                result["skipped"].append(s)
            else:
                todo.append(it)

        print(f"live slugs: {len(live)}; queued: {len(queued)}; to publish: {len(todo)}")
        if not todo:
            result["message"] = "nothing new to publish"
            return (json.dumps(result), 200, {"Content-Type":"application/json"})

        tp = requests.get(f"{WP_API}/pages?slug={TEMPLATE_SLUG}&per_page=5&_fields=id,parent",
                          headers=h, timeout=60).json()
        tpl_id = next((p["id"] for p in tp if p.get("parent") == HUB_ID), None)
        if not tpl_id:
            result["errors"].append("template page not found")
            return (json.dumps(result), 500, {"Content-Type":"application/json"})
        tpl = requests.get(f"{WP_API}/pages/{tpl_id}?_fields=content&context=edit",
                           headers=h, timeout=60).json()["content"]["raw"]

        made = []
        for it in todo:
            try:
                page_html, title_tag = build_detail(tpl, it)
                if "voicemail" in page_html.lower() and "voicemail" not in json.dumps(it).lower():
                    result["errors"].append(f"{it['slug']}: template leak, skipped"); continue
                body = {"title": it["title"], "slug": it["slug"], "parent": HUB_ID,
                        "status": "publish", "template": "elementor_canvas", "content": page_html,
                        "meta": {"_yoast_wpseo_title": title_tag,
                                 "_yoast_wpseo_metadesc": it["one_liner"], **ELCLEAR}}
                r = requests.post(f"{WP_API}/pages", headers=h, json=body, timeout=120)
                if r.status_code not in (200, 201):
                    result["errors"].append(f"{it['slug']}: HTTP {r.status_code}"); continue
                made.append(it); result["published"].append(it["slug"])
            except Exception as e:
                result["errors"].append(f"{it['slug']}: {e}")

        if made:
            total, newc = rebuild_hub(h, made)
            result["hub"] = {"cards": total, "new": newc}
            purge(h)
            for it in made:
                try:
                    p = requests.get(f"{WP_URL}/ai-use-cases/{it['slug']}/",
                                     headers={"User-Agent": UA}, timeout=60).text
                    ok = ("--bg:#f7f8fc" in p and "Hanken Grotesk" in p
                          and "<p><!DOCTYPE" not in p and "<footer>" in p)
                    result["verified"].append({it["slug"]: "PASS" if ok else "FAIL"})
                except Exception as e:
                    result["verified"].append({it["slug"]: f"ERROR {e}"})
        return (json.dumps(result), 200, {"Content-Type":"application/json"})
    except Exception as e:
        import traceback
        print("FATAL:", e)
        traceback.print_exc()
        result["errors"].append(str(e))
        return (json.dumps(result), 500, {"Content-Type":"application/json"})
