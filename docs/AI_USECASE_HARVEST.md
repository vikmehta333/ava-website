# AI Use-Case Harvest — Pipeline

**Goal:** keep `/ai-use-cases/` growing with *real, working* AI use cases + prompts sourced from the wild, rewritten as Ava's own, and verified before they ship. Mirrors how agentusecases.ai stays fresh — but filtered to Ava's ICP and in Ava's voice.

## Sources (discover)
- **agentusecases.ai** — a daily feed; filter hard (most entries are consumer finance/tax/trading, not SMB marketing).
- **Reddit** — r/automation, r/AI_Agents, r/Entrepreneur, r/smallbusiness, r/marketing, r/Zapier, r/n8n, r/make, r/msp, and trade subs (r/HVAC, r/plumbing, r/Dentistry…). Search practitioner reports, not vendor blogs.
- **X / threads** from automation builders (Make/n8n/Zapier/AI-agency accounts).
- **Template galleries** — Make, Zapier, n8n public templates (real, buildable workflows).
- **Service-SaaS resource libraries** — Housecall Pro, Signpost, etc. publish genuinely-tested local-business prompts.

## Rank (keep the best)
Keep an item only if it is:
1. **On-ICP** — useful to a local/SMB in marketing, front desk, sales, ops, content, or local SEO.
2. **Buildable** — we could actually implement it (clear trigger → AI step → action).
3. **Specific** — a concrete task, not "use AI to grow." Prefer high-engagement/high-upvote items.
Drop: consumer-only (personal taxes, trading, subscriptions), anything we can't deliver, anything vague.

## Make it ours (the important rule)
Sources are for **discovery, not copy-paste.** For each kept item we write:
- an **original title** (benefit-first, Ava voice),
- our **own "How it works"** (the trigger → AI step → action, in plain English),
- the **real stack** we'd use,
- a **rewritten starter prompt** in our voice.
Never republish another author's write-up verbatim. (Prompts are short/functional and generally not copyrightable, but we rewrite for quality + voice anyway.) Where a source is genuinely notable, an optional "inspired by" credit is fine.

## Verify (before publish)
- **Run each starter prompt** against a model and read the output; only ship prompts that produce a good, safe result.
- Sanity-check the stack (do those tools actually integrate?).
- No fabricated metrics or claims. No customer PII in example prompts.

## Publish
- Add cards to `/ai-use-cases/` via the generator (`scratchpad/build_usecases*.py` — the card model is `(category, title, one-liner, how, stack, prompt)` plus an optional Instagram link).
- Tag the category; keep the search `data-text` in sync.
- Each card stays **teach-to-sell**: How it works + Stack + Starter prompt + "Want us to build it for you? →".
- Optional later: a **"New this week"** counter + per-use-case indexable pages for deeper SEO.
- Pair with Instagram: each harvested use case can become an IG post; the card links to it ("See it on Instagram").

## Cadence
- **Weekly batch** of N new use cases (default 5), **drafted automatically, published after a quick human approval** — not fully autonomous publishing to the live site (quality/brand control).
- Can run as a scheduled cloud agent (see the `schedule` skill / scheduled-tasks) or the `ava-digital-agents` pipeline once verified end-to-end.

## Status
- First manual harvest run 2026-10-12 (proof): agentusecases.ai + web search surfaced real on-ICP patterns (Instagram-content automation, booking→calendar, review-reply, 3-step quote follow-up). The 18 launch cards were Ava-drafted (plausible, unverified) — the harvest replaces/augments them with sourced + verified ones over time.
