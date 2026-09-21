# QUICK REFERENCE: Opus Workflow at a Glance

**TL;DR:** Give Opus one prompt, then systematically work through puzzles. Document everything. Hand off clean architecture to Sonnet.

---

## The Immediate Action Plan

### Step 1: Give Opus the Initialization (COPY & PASTE)

**Open Claude Opus → New Conversation → Paste this:**

```
[COPY ENTIRE CONTENTS OF: OPUS_INITIALIZATION_PROMPT.md]
```

Then wait for Opus to confirm they understand. They'll say something like:
> "I understand. I'm ready to be your strategic architecture partner..."

### Step 2: Give Opus the Strategic Context (SHARE FILES)

**Then say:**

```
Great. Here's the complete package of documentation I mentioned.
I'm uploading the 12 strategic documents now.

These files cover:
- System overview and architecture
- 50+ puzzles organized by category
- Critical decision points
- Future phases
- Complete code reference

Take 30 minutes to skim these. Focus on understanding the structure, 
not memorizing details. I'll use them to reference during our deep-dives.

Ready? Tell me when you've reviewed them.
```

**Upload or paste these files:**
1. `00_OPUS_OPENING_BRIEF.md`
2. `01_SYSTEM_OVERVIEW.md`
3. `02_LAYERS_FOUNDATION_TO_CONSOLIDATION.md`
4. `03_PHASE_7_LEARNING_PIPELINE.md`
5. `05_KNOWN_UNKNOWNS_RESEARCH_QUESTIONS.md`
6. `06_FUTURE_PHASES_8_9_10.md`
7. `07_CRITICAL_DECISION_POINTS.md`
8. `DMLOG_COMPLETE_ARCHITECTURE.md`

### Step 3: Start First Deep-Dive

**Say:**

```
Perfect. Now let's work on our first major puzzle.

I want to start with Puzzle #1: Authentic Learning vs. Apparent Learning

This is foundational because if players don't feel characters genuinely learn, 
the whole system fails emotionally.

Here's my question: What would make character learning feel authentic to players?
What could make it feel fake?

Think from three perspectives:
1. Player perspective (emotional investment)
2. System perspective (what's actually happening)
3. Designer perspective (what constraints do we have?)

Give me your analysis, then propose an architecture that makes learning feel real.
```

**Opus responds:** Deep exploration, multiple angles, proposed solution.

**You review:** Document output, pick next puzzle or refine this one.

---

## The 5-Session Deep-Dive Pattern

### Session Template

```
YOU SETUP (1-2 min):
"Let's tackle Puzzle #X: [NAME]

Context: [Why this matters]

Question: [What are we solving?]

Perspectives to consider: [Multiple angles]

Reference: [Which docs/code to look at]"

OPUS EXPLORATION (5-10 min thinking):
- Asks clarifying questions
- Maps the problem
- Considers multiple approaches
- Identifies unknowns

OPUS PROPOSES (3-5 min):
- Recommends an approach
- Explains trade-offs
- Highlights risks
- Suggests next steps

YOU REVIEW (2-3 min):
- Document the decision
- Note implications
- Pick next puzzle
```

---

## Recommended Deep-Dive Sequence

### Deep-Dive 1: Authentic Learning (60 min)
**Puzzle:** #1  
**Why First:** Foundation. Everything else depends on this.  
**Files to Reference:** 01_SYSTEM_OVERVIEW.md, 02_LAYERS.md

**Say to Opus:**
```
Let's start with the most foundational puzzle: authentic learning.

Players invest emotionally in their characters. If they feel the learning
is real, they'll stay engaged. If it feels like the character is being
rewritten by the system, they'll disengage.

From architectural perspective:
1. What makes learning feel authentic?
2. What would make it feel fake?
3. What system design enables real-feeling learning?
4. What risks could break the illusion?
5. New unknowns that emerge?

Think from player, DM, and system perspectives.
```
**Document as:** `decisions/01_authentic_learning.md`

---

### Deep-Dive 2: Data Quality (45 min)
**Puzzle:** #8  
**Why:** Critical for system reliability  
**Files to Reference:** 03_PHASE_7.md, 05_KNOWN_UNKNOWNS.md (Data section)

**Say to Opus:**
```
How do we know if our training data is good?

Players have decision-making styles. What if that style is biased?
What if the DM logged outcomes wrong?
What if 90% of decisions are combat?

Architecture question: How do we detect when data is too biased to train from?
What mechanisms could flag problems?
What's our data quality assurance strategy?
```
**Document as:** `decisions/02_data_quality.md`

---

### Deep-Dive 3: Base Model (45 min)
**Puzzle:** Decision #1  
**Why:** Cascading impact on everything  
**Files to Reference:** 03_PHASE_7.md, 07_CRITICAL_DECISION.md

**Say to Opus:**
```
We need to pick a base model for LoRA fine-tuning. Options:

A) Llama 2 7B (local, proven, good community)
B) Mistral 7B (newer, better quality)
C) Local GPT-2 (simple, limited quality)
D) Cloud API (best quality, expensive, no offline)

Architecture thinking:
1. What matters most: quality, cost, accessibility, or reliability?
2. How does each choice affect future Phase 7 tasks?
3. What are we sacrificing with each option?
4. Can we change this decision later?
5. What mitigates the weaknesses of our choice?

Give me a decision matrix with recommendation.
```
**Document as:** `decisions/03_base_model_selection.md`

---

### Deep-Dive 4: LoRA Configuration (45 min)
**Puzzle:** Decision #2  
**Why:** Affects training quality and model size  
**Files to Reference:** 03_PHASE_7.md (LoRA section), 07_CRITICAL_DECISION.md

**Say to Opus:**
```
LoRA rank selection. How big should character adapters be?

Options:
- r=8: Tiny (5-10 MB), minimal learning capacity
- r=16: Small (10-20 MB), good balance
- r=32: Medium (20-40 MB), better fidelity
- r=64: Large (40-100 MB), almost full fine-tuning

This decision interacts with:
- Training time (higher rank = slower)
- Model size (storage/memory)
- Learning capacity (personality preservation)

From architectural perspective:
1. What's the right trade-off?
2. Should it vary by character type?
3. Can we optimize this later?
4. What happens if we choose wrong?
5. Any way to test this assumption?
```
**Document as:** `decisions/04_lora_configuration.md`

---

### Deep-Dive 5: Integration Check (90 min)
**Puzzle:** Synthesis  
**Why:** Ensure coherence  
**Files to Reference:** All previous decisions + 06_FUTURE_PHASES.md

**Say to Opus:**
```
We've made 4 major decisions. Let's integrate them.

Here are our decisions so far:
1. Authentic Learning Strategy: [what you decided]
2. Data Quality Approach: [what you decided]
3. Base Model: [what you decided]
4. LoRA Configuration: [what you decided]

Now:
1. Do these decisions contradict each other?
2. How do they interact?
3. What new unknowns emerged?
4. Are there critical decision gaps?
5. Create a master architecture showing how these fit together
6. What should we prioritize next?

Give me: master architecture diagram (in text), interaction map, and next 3 puzzles to solve.
```
**Document as:** `MASTER_ARCHITECTURE.md` + `NEXT_PRIORITIES.md`

---

## After Each Deep-Dive: What You Do

### Immediately (Same Session)

1. **Copy Opus's output** to decision document
2. **Summarize key insight** in 1 sentence
3. **Note dependencies** - What other puzzles depend on this?
4. **Flag unknowns** - What questions emerged?
5. **Pick next puzzle** - What should we tackle next?

### Before Next Session

1. **Review decision** - Does it still make sense?
2. **Check consistency** - Any conflicts with earlier decisions?
3. **Update master doc** - Add to architecture
4. **Prepare context** - What files should Opus reference?

### When Done with All Puzzles

1. **Create master architecture document**
2. **Identify what Sonnet can implement directly**
3. **Flag where advanced thinking still needed**
4. **Create implementation roadmap**
5. **Handoff to Sonnet with clear blueprint**

---

## Handoff to Sonnet Template

When Opus finishes strategic work, give Sonnet:

```
Here's the complete architecture Opus designed for Phase 7.

STRATEGIC DECISIONS MADE:
[List all decisions with reasoning]

MASTER ARCHITECTURE:
[How everything fits together]

IMPLEMENTATION ROADMAP:
[What to build in what order]

CRITICAL CONSTRAINTS:
[What can't change without rethinking]

YOUR TASKS:
1. Data Curation Pipeline (Task 7.2.2)
2. Character Dashboard UI (Task 7.2.3)
3. QLoRA Training Infrastructure (Task 7.3.1)
[etc]

WHEN YOU GET STUCK:
These decisions are made. But if you discover something that contradicts them,
flag it to me for reconsideration with Opus.

START HERE: [First task pointer]
```

---

## Quick Decision Reference

**High Priority (Do First):**
- Puzzle #1: Authentic Learning
- Decision #1: Base Model
- Decision #2: LoRA Rank
- Puzzle #8: Data Quality

**Medium Priority:**
- Puzzle #2: Personality Preservation
- Puzzle #37: Party Learning
- Decision #3: Training Threshold
- Puzzle #29: Learning Visibility

**Lower Priority (After above):**
- Puzzle #44-50 (Speculative features)
- Puzzle #16-22 (Scaling details)

---

## Expected Timeline

| Time | Activity | Output |
|------|----------|--------|
| 0 min | Send Opus initialization | Opus ready |
| 10 min | Upload documentation | Opus familiarized |
| 60 min | Deep-dive 1 (Authentic Learning) | Decision #1 |
| 60 min | Deep-dive 2 (Data Quality) | Decision #2 |
| 60 min | Deep-dive 3 (Base Model) | Decision #3 |
| 60 min | Deep-dive 4 (LoRA Config) | Decision #4 |
| 90 min | Deep-dive 5 (Integration) | Master Architecture |
| **Total** | **5 sessions** | **Complete architecture** |

**Then:** Hand off to Sonnet for 3-4 weeks of implementation.

---

## Success Checklist

Before handing off to Sonnet, you should have:

- [ ] 5-8 major decisions documented
- [ ] Trade-offs explicit for each
- [ ] Master architecture created
- [ ] New puzzles identified
- [ ] Risks and mitigations mapped
- [ ] Implementation roadmap clear
- [ ] Sonnet knows exactly what to build
- [ ] Fallback plans documented

---

## Emergency: If Opus Goes Off Track

**If Opus starts solving implementation details:**
```
Let me refocus - we're at an architecture level.
Sonnet will figure out the code.
What's the right high-level approach?
```

**If Opus goes in circles:**
```
Let's step back. What's the core decision?
What information would help us decide?
Can we move forward with current understanding?
```

**If you're unsure about Opus's recommendation:**
```
I like this, but I'm uncertain about [aspect].
Can you steelman the opposing view?
What would have to be true for that approach to be better?
```

---

## File Organization Once Done

Create this structure:

```
dmlog-opus-work/
├── OPUS_INITIALIZATION_PROMPT.md          (What you gave Opus)
├── WORKING_WITH_OPUS.md                   (This workflow doc)
├── decisions/
│   ├── 01_authentic_learning.md
│   ├── 02_data_quality.md
│   ├── 03_base_model_selection.md
│   ├── 04_lora_configuration.md
│   └── ...more decisions
├── MASTER_ARCHITECTURE.md                 (Integration of all)
└── HANDOFF_TO_SONNET.md                   (For next phase)
```

---

## The Philosophy

You're using Opus as your **strategic thinking partner**, not your implementation team.

- **Opus:** "Here's how to think about this problem"
- **You:** "This is the direction we should go"
- **Documentation:** "Here's why we made this choice"
- **Sonnet:** "Here's how to implement this"

Efficient. Elegant. Effective.

**Ready to start?** Give Opus the initialization prompt. 🚀
