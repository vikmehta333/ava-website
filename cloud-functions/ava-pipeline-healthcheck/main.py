"""
Cloud Function: Ava Digital — AI Use-Case Pipeline Health Check.

Verifies the END-TO-END invariant every morning and emails only when something
is wrong (plus a short weekly all-clear). Exists because the pipeline has failed
silently twice: queue files dropped by .gitignore, and a publish that never ran.

Checks:
  C1  Harvest ran last night        -> a digest file exists for today
  C2  Queue file committed          -> queue/<today>.json exists (the .gitignore trap)
  C3  Digest/queue reconcile        -> every "passed" item is in the queue file
  C4  Everything queued is live     -> no item queued in the last 3 days is missing
  C5  Hub is healthy                -> /ai-use-cases/ renders, card count >= live pages

Triggered by Cloud Scheduler ~7:00 AM America/Chicago (after harvest + publish).
"""
import base64, datetime, json, os, re
import requests
import functions_framework
from google.cloud import secretmanager
from email.mime.text import MIMEText

PROJECT_ID = "plasma-crossbar-486516-r8"
WP_URL = "https://avadigitalagency.com"
WP_API = f"{WP_URL}/wp-json/wp/v2"
HUB_ID = 24305
REPO = "vikmehta333/ava-website"
ALERT_TO = os.environ.get("ALERT_TO", "vik@velocitylogicgroup.com")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def get_secret(sid):
    c = secretmanager.SecretManagerServiceClient()
    return c.access_secret_version(
        request={"name": f"projects/{PROJECT_ID}/secrets/{sid}/versions/latest"}
    ).payload.data.decode("UTF-8")


def gh_file(path):
    r = requests.get(f"https://raw.githubusercontent.com/{REPO}/main/{path}",
                     headers={"User-Agent": UA}, timeout=45)
    return r.text if r.status_code == 200 else None


def live_slugs():
    tok = base64.b64encode(
        f"{os.environ.get('WP_USER','vikmehta')}:{get_secret('ava-wp-app-password').replace(' ','')}".encode()).decode()
    h = {"Authorization": f"Basic {tok}", "User-Agent": UA, "Accept": "application/json"}
    slugs, page = set(), 1
    while page < 5:
        r = requests.get(f"{WP_API}/pages?parent={HUB_ID}&per_page=100&page={page}"
                         f"&status=publish&_fields=slug", headers=h, timeout=60)
        if r.status_code != 200:
            break
        b = r.json()
        if not b:
            break
        slugs |= {p["slug"] for p in b}
        if len(b) < 100:
            break
        page += 1
    return slugs


def send_email(subject, body):
    """Send via Gmail API using the same secrets the daily-briefing function uses."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    tok = json.loads(get_secret("gmail-token"))
    # gmail-token holds only the token/refresh_token; the OAuth client id+secret
    # live in gmail-credentials. Credentials.from_authorized_user_info needs both.
    if not tok.get("client_id") or not tok.get("client_secret"):
        cred = json.loads(get_secret("gmail-credentials"))
        inst = cred.get("installed") or cred.get("web") or cred
        tok["client_id"] = tok.get("client_id") or inst.get("client_id")
        tok["client_secret"] = tok.get("client_secret") or inst.get("client_secret")
        tok.setdefault("token_uri", inst.get("token_uri", "https://oauth2.googleapis.com/token"))
    creds = Credentials.from_authorized_user_info(tok, ["https://www.googleapis.com/auth/gmail.send"])
    svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
    msg = MIMEText(body, "plain")
    msg["to"], msg["from"], msg["subject"] = ALERT_TO, ALERT_TO, subject
    svc.users().messages().send(
        userId="me", body={"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}).execute()


@functions_framework.http
def healthcheck(request):
    today = datetime.date.today()
    problems, notes = [], []

    digest = gh_file(f"data/usecases/digest/{today}.md")
    if not digest:
        problems.append(f"C1 HARVEST DID NOT RUN — no digest for {today}.")
    else:
        notes.append(f"harvest ran ({today} digest present)")

    queue_raw = gh_file(f"data/usecases/queue/{today}.json")
    passed = re.findall(r'^- \*\*([a-z0-9-]+)\*\*', digest or "", re.M)
    if passed and not queue_raw:
        problems.append(
            f"C2 QUEUE FILE MISSING — digest lists {len(passed)} passing item(s) but "
            f"queue/{today}.json is absent (the .gitignore trap). Work was lost.")
    elif queue_raw:
        try:
            qslugs = {i["slug"] for i in json.loads(queue_raw)}
            missing = [p for p in passed if p not in qslugs]
            if missing:
                problems.append(f"C3 DIGEST/QUEUE MISMATCH — in digest but not queued: {', '.join(missing)}")
            notes.append(f"{len(qslugs)} item(s) queued today")
        except Exception as e:
            problems.append(f"C3 queue file unreadable: {e}")
    elif not passed:
        notes.append("nothing passed the gates last night (valid outcome)")

    try:
        live = live_slugs()
        notes.append(f"{len(live)} use cases live")
        unpublished = []
        for d in range(0, 3):
            day = today - datetime.timedelta(days=d)
            raw = gh_file(f"data/usecases/queue/{day}.json")
            if not raw:
                continue
            for it in json.loads(raw):
                if it.get("slug") and it["slug"] not in live:
                    unpublished.append(f"{it['slug']} (queued {day})")
        if unpublished:
            problems.append("C4 QUEUED BUT NOT PUBLISHED — the publisher did not pick these up:\n    - "
                            + "\n    - ".join(unpublished))
    except Exception as e:
        problems.append(f"C4 could not verify published state: {e}")

    try:
        hub = requests.get(f"{WP_URL}/ai-use-cases/", headers={"User-Agent": UA}, timeout=60).text
        cards = len(re.findall(r'class="uc(?: ucf)?"', hub))
        if cards == 0:
            problems.append("C5 HUB BROKEN — /ai-use-cases/ rendered 0 cards.")
        else:
            notes.append(f"{cards} cards on the hub")
    except Exception as e:
        problems.append(f"C5 hub unreachable: {e}")

    ok = not problems
    status = "OK" if ok else "NEEDS ATTENTION"
    body = (f"AI Use-Case pipeline — {status} ({today})\n\n"
            + ("PROBLEMS:\n" + "\n".join(f"  ! {p}" for p in problems) + "\n\n" if problems else "")
            + "Checks:\n" + "\n".join(f"  - {n}" for n in notes)
            + f"\n\nHub: {WP_URL}/ai-use-cases/\nDigest: https://github.com/{REPO}/blob/main/data/usecases/digest/{today}.md\n")

    # email on any problem; otherwise only a Monday all-clear.
    # ?test=1 forces a send so the alert path itself can be verified on demand
    # (untested alerting is how silent failures survive).
    forced = bool(request.args.get("test"))
    should_email = bool(problems) or today.weekday() == 0 or forced
    if forced:
        subject_prefix = "[TEST] "
    else:
        subject_prefix = ""
    if should_email:
        try:
            send_email(f"{subject_prefix}[Ava pipeline] {status} — {today}", body)
            notes.append("alert emailed")
        except Exception as e:
            notes.append(f"EMAIL FAILED: {e}")

    return (json.dumps({"status": status, "problems": problems, "notes": notes,
                        "emailed": should_email}, indent=1), 200 if ok else 500,
            {"Content-Type": "application/json"})
