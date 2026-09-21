# STATUS — DMLog / DMLogn8n

## What this is

DMLog (sometimes DMLogn8n in the files) was our ambitious D&D campaign
management platform: FastAPI + PostgreSQL + Redis + Docker, with an n8n
workflow layer for AI-powered character automation and a parallel-development
template for spinning up four cooperating Claude Code agents on the same
project.

This is the **design phase**, not a finished product. Most of what you'll
find here is a giant pile of phase briefs, architecture diagrams, system
specs, and deployment scripts — the whole project's worth of thinking out
loud before any code landed. The actual source under `source_code/` is
sparse by comparison.

## What it was good at

- **Layered architecture doc.** `01_SYSTEM_OVERVIEW.md` →
  `02_LAYERS_FOUNDATION_TO_CONSOLIDATION.md` walks from base infrastructure
  to the consolidated application. Many projects skip this step entirely.
- **A planning arc you can copy.** Phase 1 → Phase 10 briefs each with
  tasks, deliverables, and known-unknowns. This is a *template* for
  bootstrapping a complex project, not just a project.
- **n8n integration research.** DMLog was a real attempt to bolt an n8n
  workflow graph onto an RPG system. The `n8n-api-client.py` and
  `Coden8nWalk.txt` capture what we learned trying to make a workflow
  engine drive character automation.
- **Parallel AI agent workflow.** Four cooperating Claude Code sessions
  per spec, divided by concern. The dispatch files (`OPUS_*`,
  `PARALLEL_*`) are a creative answer to "how do you develop one project
  in parallel with AI agents that don't step on each other?"

## Why we moved on

Two reasons: (1) the surface area ballooned — AI DM, voice chat, mobile
app, VR/AR, metaverse integration, blockchain — and no part of it ever
landed in a fully playable form. (2) The D&D community moved toward
Foundry VTT, Roll20, D&D Beyond; competing with platform incumbents on
"where do you actually play the game" wasn't the right fight.

The salvageable pieces are *below* the campaign/AI layer: the dev
templates, the n8n walkthrough, the parallel-agent workflow.

## Salvageable pieces (what to steal)

- **`OPUS_INITIALIZATION_PROMPT.md`** + `PARALLEL_AI_AGENT_WORKFLOW.md`
  + `PARALLEL_IMPLEMENTATION_TEMPLATES.md` — together these are a
  working scaffold for spinning up parallel Claude Code (or any
  agent) sessions against a single repo. The dispatch language is
  reusable.
- **`AI_DM_MASTER_ARCHITECTURE.md`** — even if you never build the AI
  DM, the schema for "characters have memories with importance
  scoring" is a clean template for any NPC-driven simulation.
- **`n8n-api-client.py`** + `GLM4_API_SETUP_GUIDE.md` — a small,
  focused client for n8n's public API and a note on GLM-4 setup. Not
  plug-and-play but illustrative.
- **`source_code/`** — the early FastAPI/Postgres/Redis skeleton is
  conventional but battle-tested; useful as a starting point for a
  Python+Postgres+Redis project of any kind.

## What was redacted before push

- `.mcp.json` contained a real `N8N_API_KEY` JWT (issued for a private
  n8n instance during development). It was replaced with
  `REDACTED-EXAMPLE-JWT-PLACEHOLDER`. The token was an old dev token
  with TTL since expired.
- All other secrets in the tree were already placeholders
  (`.env.example` files with empty values, `secrets.yaml` k8s
  manifests with `your_*_here` base64 placeholders). No further
  redactions needed.

## What's here vs. upstream

| Aspect | This repo | Notes |
|--------|-----------|-------|
| Size on disk | ~41 MB | Mostly markdown; ~3284 untracked files at the time of push (now committed) |
| Source files | Small subset under `source_code/` and a few root-level `*.py` | Most of the volume is design docs |
| Secrets | None live (only `*.example` and placeholders, plus redacted `.mcp.json`) | |
| License | MIT (added at publication) | Original repo had none |
| Branch | `main` (new — repo had 0 commits at archive time) | First commit created during this push |

## Reading order

1. `README.md` — the original D&D-pitch README (kept verbatim)
2. `README_START_HERE.md` — the developer's entry point at the time
3. `00_OPUS_OPENING_BRIEF.md` — the parallel-agent dispatch brief
4. `01_SYSTEM_OVERVIEW.md` through `10_WEEK_DEVELOPMENT_ROADMAP.md` —
   the layered design and rollout plan
5. `MULTI_AGENT_COMMUNICATION_SYSTEM_GUIDE.md` — inter-agent wiring
6. `n8n-api-client.py` + `Coden8nWalk.txt` — the n8n walkthrough
7. `STATUS.md` (this file) — slice-of-life notes

## How to use it

Most of the code is a scaffold, not a runnable system. The path to a
runnable thing:

1. Pick a smaller subset (e.g., `source_code/backend/` only) to actually
   develop on.
2. Use `OPUS_*` / `PARALLEL_*` dispatch templates if you're curious
   about running parallel Claude Code sessions against a project.
3. The `.env.example` files tell you what env vars the project would
   need if you finished it.

## How to get the big pieces

This repo deliberately does **not** bundle model weights. The `AI DM`
section assumes access to API-based LLMs; set those keys in your own
`.env` (never committed).

## Provenance

Archived from
`~/wslbackup/TECH_EXTRACTIONS/game-dev/DMLogn8n` on a local workstation.
Curated and pushed to `SuperInstance/DMLogn8n` on 2026-09 as part of the
SuperInstance slice-of-life archive.

Take this, fork it, evolve it. No attribution required. We'd love to
hear what you build, but you owe us nothing.
