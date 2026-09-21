# DMLogn8n

> A slice-of-life artifact from the SuperInstance era: a sprawling
> D&D campaign management design workspace — FastAPI + Postgres + Redis +
> n8n + parallel Claude Code agent dispatch — captured in design-doc form.

**What this is:** A frozen snapshot of one team's ambitious attempt to
build a D&D platform with AI-assisted DM tools and a four-agent parallel
development workflow. Most of the value here is in the *thinking* — phase
briefs, layered architecture, parallel-agent dispatch templates,
n8n-integration walkthroughs — not the executable code.

**What it isn't:** A runnable product. This is a design workspace that
nearly became a product and then didn't. See `STATUS.md` for the why.

## Reading order

1. `STATUS.md` — slice-of-life context, what was good, what's
   salvageable
2. `README.md` — original D&D pitch README (kept verbatim)
3. `00_OPUS_OPENING_BRIEF.md` — parallel-agent dispatch brief
4. `01_SYSTEM_OVERVIEW.md` → `10_WEEK_DEVELOPMENT_ROADMAP.md` —
   architecture and rollout
5. `MULTI_AGENT_COMMUNICATION_SYSTEM_GUIDE.md` — inter-agent wiring
6. `n8n-api-client.py` — n8n workflow-engine integration example

## Quick start (only the `source_code/` subset)

```bash
cd source_code
cp backend/.env.example backend/.env
# fill in keys
docker compose up -d
```

## How to get the big pieces

This repo deliberately does **not** bundle model weights. The AI DM and
agent-dispatch sections assume access to API-based LLMs (`OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, etc. in your own `.env`).

## Notable primitives (in `STATUS.md`)

- The four-agent parallel-development dispatch template
- Character memory with importance scoring (NPC simulation primitive)
- n8n workflow-engine integration pattern
- A layered Phase 1 → Phase 10 planning arc

## License

MIT. See `LICENSE`.

Take this, fork it, evolve it. No attribution required. We'd love to
hear what you build, but you owe us nothing.
