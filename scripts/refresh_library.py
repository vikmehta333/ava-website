#!/usr/bin/env python3
"""
Refresh data/usecases/library.json from the live site, and mark queue items published.

WHY THIS EXISTS
---------------
library.json is the dedup index the nightly harvest agent reads. The agent's sandbox
has no route to avadigitalagency.com, and the 3 AM publisher is a Cloud Function with
no GitHub write access -- so nothing either one does ever updates this file. It drifts
behind the live site until someone runs this. C7 in the health check alerts when the
drift reaches 5 items.

Needs no credentials: the hub's child pages are readable from the public REST API.

    python3 scripts/refresh_library.py          # report drift only
    python3 scripts/refresh_library.py --go     # write library.json + mark queue items
"""
import datetime, glob, json, os, sys, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUB_ID = 24305
BASE = "https://avadigitalagency.com/wp-json/wp/v2"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
GO = "--go" in sys.argv


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=90))


def live_pages():
    pages, page = {}, 1
    while page < 10:
        r = get(f"{BASE}/pages?parent={HUB_ID}&per_page=100&page={page}"
                f"&status=publish&_fields=slug,id,date")
        for p in r:
            pages[p["slug"]] = p
        if len(r) < 100:
            break
        page += 1
    return pages


live = live_pages()
lib_path = os.path.join(REPO, "data/usecases/library.json")
lib = json.load(open(lib_path, encoding="utf-8"))
items = lib["items"] if isinstance(lib, dict) else lib
indexed = {i["slug"] for i in items}

# queue files carry the title/category/source for anything the index is missing
meta = {}
for f in glob.glob(os.path.join(REPO, "data/usecases/queue/*.json")):
    for it in json.load(open(f, encoding="utf-8")):
        meta[it["slug"]] = it

missing = sorted(set(live) - indexed)
stale = sorted(indexed - set(live))

print(f"live: {len(live)}   library.json: {len(indexed)}")
print(f"missing from index: {len(missing)}")
for s in missing:
    print("  +", s)
if stale:
    print(f"in index but NOT live ({len(stale)}) — check these by hand, not auto-removed:")
    for s in stale:
        print("  ?", s)

if not GO:
    print("\nreport only — rerun with --go to write.")
    sys.exit(0)

for s in missing:
    it = meta.get(s, {})
    items.append({
        "slug": s,
        "title": it.get("title", s.replace("-", " ").capitalize()),
        "category": it.get("category", "ops"),
        "page_id": live[s]["id"],
        "published_at": live[s]["date"],
        "source_name": it.get("source_name", ""),
    })
if isinstance(lib, dict):
    lib["count"] = len(items)
    lib["refreshed_from_live_at"] = datetime.datetime.now().isoformat(timespec="seconds")
json.dump(lib, open(lib_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"\n✔ library.json now {len(items)} items")

for f in sorted(glob.glob(os.path.join(REPO, "data/usecases/queue/*.json"))):
    q = json.load(open(f, encoding="utf-8"))
    changed = 0
    for it in q:
        if it.get("status") == "queued" and it["slug"] in live:
            it["status"] = "published"
            it["page_id"] = live[it["slug"]]["id"]
            changed += 1
    if changed:
        json.dump(q, open(f, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"  ✔ marked {changed} published in {os.path.basename(f)}")
