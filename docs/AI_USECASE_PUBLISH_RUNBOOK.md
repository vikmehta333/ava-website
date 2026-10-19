# AI Use-Case Publish Runbook

How a harvested use case becomes a live page, who does which step, and the checks that stop it failing **silently**. Companion to [AI_USECASE_PIPELINE_SPEC.md](AI_USECASE_PIPELINE_SPEC.md) (the gates) and [AI_USECASE_HARVEST.md](AI_USECASE_HARVEST.md) (the sources).

## The pipeline, end to end

```
 NIGHTLY (cloud routine, 2:00 AM America/Chicago)        PUBLISH (credentialed)
 ────────────────────────────────────────────────        ──────────────────────
 harvest → score → verify → QA gates                     read queue/*.json
   ↓                                                       ↓
 data/usecases/queue/<date>.json   (passing items)       create /ai-use-cases/<slug>/
 data/usecases/digest/<date>.md    (what passed/failed)    ↓
   ↓                                                     add card to hub (24305)
 commit + push to origin/main                              ↓
                                                         update library.json
                                                           ↓
                                                         purge + verify each page
```

- **The routine cannot publish.** It runs in Anthropic's cloud from a **public** repo, so it has no WordPress credential. It only queues.
- **Publishing is a separate, credentialed step.** It now runs **automatically in GCP**:

| | |
|---|---|
| Cloud Function | `ava-usecase-publisher` (gen2, python311, us-central1) |
| Scheduler job | `ava-usecase-publish-daily` — **3:00 AM America/Chicago**, one hour after the harvest |
| Credential | WordPress app password in **Secret Manager** as `ava-wp-app-password` (never in the repo) |
| Project | `plasma-crossbar-486516-r8` · billing account `01B35E-F90F08-FA6046` |
| Source | versioned at `cloud-functions/ava-usecase-publisher/` |

It needs **no GitHub write access**: it reads the queue from the public repo, and decides what's "already published" by querying WordPress for the hub's child pages. The nightly routine refreshes `library.json` from the live site (its STEP 0b), so the dedup index stays accurate without the publisher committing anything.

Manual run / redeploy:
```bash
gcloud functions call ava-usecase-publisher --project=plasma-crossbar-486516-r8 --region=us-central1
cd cloud-functions/ava-usecase-publisher && gcloud functions deploy ava-usecase-publisher \
  --project=plasma-crossbar-486516-r8 --region=us-central1 --gen2 --runtime=python311 \
  --source=. --entry-point=publish_usecases --trigger-http --no-allow-unauthenticated \
  --set-env-vars=WP_USER=vikmehta
```
The local `scripts/publish_usecases.py` below remains the manual fallback.

## State files (source of truth)
| File | Purpose |
|---|---|
| `data/usecases/library.json` | Every **published** use case. The dedup index the routine reads. |
| `data/usecases/queue/<date>.json` | Items that passed every QA gate, `status: "queued"`. Flipped to `published` after publishing. |
| `data/usecases/digest/<date>.md` | Human-readable nightly report: counts, what passed, what failed and why. |

## How to publish
```bash
export WP_USER=vikmehta
export WP_APP_PASSWORD='<app password>'     # from your password manager — NEVER commit it
cd ~/ava-website && git pull --rebase origin main

python3 scripts/publish_usecases.py          # dry run: lists what would publish
python3 scripts/publish_usecases.py --go     # publish
```
The script creates each detail page as a child of the hub (so the URL is `/ai-use-cases/<slug>/`), sets `template=elementor_canvas`, clears Elementor meta, writes Yoast title/description, rebuilds the hub cards and the sidebar counts, updates `library.json`, marks the queue entries published, purges caches, and verifies every new page. Afterwards **commit the changed `library.json` and queue files.**

## ⚠️ Failure modes — and the checks that catch them

### 1. The queue file is silently dropped by `.gitignore` *(this bit us 2026-10-15 → 10-18)*
The repo blanket-ignores `*.json` as a credential guard. The exception `!data/usecases/*.json` did **not** cover subfolders, so four nights of `queue/<date>.json` were discarded by git while the `.md` digests committed normally — it looked like it was working.
- **Fixed:** `.gitignore` now also has `!data/usecases/**/*.json`.
- **Check (the routine must run this before it finishes):**
  ```bash
  git ls-files --error-unmatch data/usecases/queue/<date>.json   # non-zero = it was ignored
  git add -f data/usecases/queue/<date>.json                     # force-add if so
  ```
- **Reconcile:** every item under "Passed (queued)" in a digest must exist in that night's queue file. If a digest lists passes but the queue file is missing, the drop happened again.

### 2. Nothing new appears on the site
Expected. The routine only queues — **publishing is a separate step.** Check `data/usecases/queue/` for `status: "queued"` items and run the publisher.

### 3. A new page renders as theme chrome / wrong content
A recycled post ID carrying another page's `_elementor_data`, or a non-canvas template. The publisher already sets `template=elementor_canvas` and clears Elementor meta on every write. See the gotchas in [AVA_SITE_PLAYBOOK.md](AVA_SITE_PLAYBOOK.md) §4a.

### 4. Template content leaks into a new page
The publisher clones an existing detail page and swaps the fields. It aborts an item if template-specific wording survives the swap. If you change `TEMPLATE_SLUG`, update that guard.

### 5. "The JS is missing from the page"
Don't diagnose this with `curl` — LiteSpeed serves a different variant to non-browsers, so inline `<script>` can appear absent. **Verify behaviour in a real browser** (Playwright), not by grepping HTML.

## Weekly check (2 minutes)
1. `git pull` and skim the newest `data/usecases/digest/*.md`.
2. Confirm each digest has a matching `queue/<date>.json` (failure mode 1).
3. Run the publisher dry run, then `--go`.
4. Commit `library.json` + queue files.
