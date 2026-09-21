# Working with Claude Opus: Session Structure & Strategies

Once you've given Opus the initialization prompt, use this guide to get maximum value from their deep thinking.

---

## Session Structure (The Pattern)

Each deep-dive session follows this structure:

### Step 1: Present the Puzzle (2-3 messages)

```
You: "Let's work on Puzzle #1: Authentic Learning vs. Apparent Learning.

This is high-impact because players need to feel characters genuinely learn,
not that they're being rewritten by the system.

Here's the relevant context: [share 1-2 relevant .md files from documentation/]

I want you to:
1. Map what makes learning feel authentic vs. fake
2. Identify architectural approaches
3. Spot new unknowns that emerge
4. Propose a solution with clear trade-offs

Ready to dive in?"
```

### Step 2: Opus Explores (1-3 responses)

Opus will:
- Ask clarifying questions
- Explore multiple perspectives
- Identify assumptions
- Map dependencies
- Consider stakeholder viewpoints

Let them explore fully. Don't interrupt with "just give me the answer."

### Step 3: Opus Proposes (1-2 responses)

Opus synthesizes into:
- Clear problem statement
- 3-5 architectural approaches
- Recommendation with reasoning
- Trade-offs and implications
- New sub-puzzles that emerged

### Step 4: You Refine (Your input)

Either:
- Accept and move to next puzzle
- Push back: "Why not approach X?"
- Dig deeper: "What about this edge case?"
- Challenge assumption: "Does that really matter?"

### Step 5: Document (Your action)

Save Opus's output to:
- `strategic_decisions/puzzle_1_authentic_learning.md`
- Update your master architecture document
- Note dependencies to other puzzles

---

## How to Frame Deep-Dives Effectively

### Good Deep-Dive Prompts

✅ **Specific and bounded:**
"Let's solve Puzzle #8: Detecting Biased Training Data. How would we identify when the system is learning from biased data? What mechanisms could detect this?"

✅ **Stakeholder-aware:**
"From the DM perspective, player perspective, and system perspective: what makes multi-character learning work well? What breaks?"

✅ **Architecturally-focused:**
"Should escalation thresholds be adaptive? Map out: what would change? what stays the same? what new problems emerge?"

✅ **Trade-off explicit:**
"Cost vs. quality trade-off: should we use Mistral (cheaper) or GPT-4 (better) as the base model? What are we sacrificing either way?"

### Weak Deep-Dive Prompts

❌ "What should we do about personality preservation?"
→ Too vague. Too many directions.

❌ "I'm stuck on the learning problem. Help."
→ Not specific enough. Opus can't think clearly.

❌ "Just tell me the right way to do this."
→ Missing the exploration. Opus thrives on thinking through options.

---

## Best Deep-Dive Puzzles to Start With

**Session 1: Foundation**
- Puzzle #1: Authentic Learning vs. Apparent Learning
- **Why:** Foundational. Affects all other decisions.
- **Time:** 45-60 min
- **Output:** Understanding of what "good learning" looks like

**Session 2: Data Quality**
- Puzzle #8: Detecting Biased Training Data
- **Why:** Critical for system reliability
- **Time:** 45-60 min
- **Output:** Data quality assurance strategy

**Session 3: Architecture Decision**
- Decision #1: Base Model for LoRA (Llama? Mistral? GPT-4?)
- **Why:** This choice affects everything downstream
- **Time:** 45-60 min
- **Output:** Decision matrix with recommendation

**Session 4: Scaling**
- Puzzle #15: Storage Growth & Scaling Limits
- **Why:** Defines practical limits of the system
- **Time:** 30-45 min
- **Output:** Scaling strategy and breaking points

**Session 5: Future Phases**
- Puzzle #37: Multi-Character Party Learning
- **Why:** Affects Phase 8 design
- **Time:** 45-60 min
- **Output:** Multi-character learning architecture

**Session 6: Synthesis**
- "Map all decisions we've made. How do they interact? Any contradictions? What new puzzles emerged?"
- **Why:** Integration and coherence
- **Time:** 60-90 min
- **Output:** Master architecture document

---

## How to Share Context Efficiently

### Format 1: Sending Documentation

When you need Opus to understand a component:

```
I'm going to share documentation about the learning pipeline. 
This is ~15 min of reading. When you're ready, I'll ask the question.

[Paste relevant .md file]

Ready? Here's what I want to explore...
```

### Format 2: Referencing Code

When you want Opus to understand actual behavior:

```
I'm pasting the escalation engine code. 
Key thing: understand HOW decisions get routed through bot/brain/human tiers.

[Paste relevant code snippet]

Given this logic, here's my question...
```

### Format 3: Asking About Trade-offs

When comparing approaches:

```
We have two options for personality preservation:

Option A: Freeze certain decisions (keeps personality rigid)
Option B: Multi-task learning (preserve while learning)

From an architectural perspective:
- What would each look like in practice?
- What's the implementation complexity?
- Which enables future features better?
```

---

## Getting More Value from Responses

### If Opus Gives a Good Answer But You Want Deeper

```
This is good. Let me push deeper:
1. You said approach X has trade-off Y. Can we mitigate Y somehow?
2. What happens if our assumption about [thing] is wrong?
3. How does this affect Phase 8 design?
```

### If Opus Identifies a New Problem You Hadn't Seen

```
This new sub-puzzle emerged: [thing]. 
Is this critical to solve before moving forward, or can we defer?
How does it affect the puzzles we've already decided on?
```

### If You Want to Challenge Opus's Recommendation

```
I hear the recommendation for approach X. But what about approach Z?
- Pros of Z?
- Cons of Z?
- When would Z be better than X?
```

### If You Want to Move Faster

```
You've explored the problem well. Let's accelerate:
What's the minimum viable solution that satisfies 80% of requirements?
What can we defer to Phase 8?
```

---

## Session Patterns That Work Well

### Pattern 1: Deep Single Topic (60 min)
- Pick one puzzle
- Explore thoroughly
- Get comprehensive output
- Document and move to next

### Pattern 2: Rapid Fire (30 min)
- Pick 2-3 related puzzles
- Quick exploration of each
- Identify how they interact
- Good for mapping dependencies

### Pattern 3: Comparison (45 min)
- Three approaches to same problem
- Pros/cons of each
- Recommendation with trade-offs
- When to use each

### Pattern 4: Integration (90 min)
- Review all decisions made so far
- Map interactions
- Identify contradictions or gaps
- Update master architecture

### Pattern 5: Edge Case Hunt (45 min)
- Take one decision
- Systematically find edge cases
- What breaks it?
- How to make it robust?

---

## What to Do with Opus's Output

### Immediately (Same Day)

1. **Document the decision**
   - Create file: `decisions/[puzzle_name].md`
   - Include: problem, approaches, recommendation, trade-offs, implications

2. **Update master architecture**
   - Note: "Puzzle #X decided on approach Y because..."
   - Flag any dependencies to other puzzles

3. **Identify next puzzle**
   - What does this decision unblock?
   - What contradicts this?
   - What emerged as new problem?

### Next Session (Before Starting)

1. **Review previous decision**
   - Could we improve it with what we know now?
   - Do we need to revisit?

2. **Check consistency**
   - Does this decision align with earlier decisions?
   - Any unforeseen conflicts?

3. **Map new dependencies**
   - What puzzles does this enable?
   - What puzzles does this constrain?

### Handoff to Sonnet

Once enough puzzles are solved:

```
Here's the architecture Opus designed:

DECISIONS MADE:
1. Base model: Mistral 7B (local, good quality)
2. LoRA rank: r=16 (balance of capacity and stability)
3. Training trigger: 100 decisions OR 10 teaching moments
4. Personality preservation: Multi-task learning approach

IMPLICATIONS FOR IMPLEMENTATION:
- Sonnet can implement... [list of tasks]
- Complex parts still needing Opus: [list]
- Testing approach: [describe]

Here's where to start: [pointer to simple tasks]
```

---

## Questions to Ask Opus During Sessions

### For Understanding
- "Why does approach X work?"
- "What assumption does this rest on?"
- "What would break this?"

### For Exploration
- "What other approaches are possible?"
- "Who would benefit most from this design?"
- "What's the simplest version that works?"

### For Challenge
- "Is that the only trade-off?"
- "Can we have both benefits?"
- "When would we regret this choice?"

### For Integration
- "How does this affect [other component]?"
- "Does this contradict [earlier decision]?"
- "What new problems does this create?"

### For Clarity
- "Can you explain that more simply?"
- "What's the mental model here?"
- "Can you give a concrete example?"

---

## Red Flags & Course Correction

### If Opus Starts Going in Circles

```
I notice we're exploring the same angle multiple times.
Let's step back: what's the core decision we need to make?
What information would help us decide?
```

### If Opus Goes Too Deep Into Implementation

```
This is getting into implementation details.
Let me refocus: at an architectural level, what's the best approach?
Sonnet can figure out the code later.
```

### If You're Uncertain About Opus's Recommendation

```
I like most of this, but I'm uncertain about [aspect].
Can you steelman the opposing view?
What would convince you to change your recommendation?
```

### If Opus Hasn't Identified a Key Trade-off

```
I think we're missing a trade-off here.
What about: maintainability vs. performance?
Should we value simplicity for Sonnet's implementation?
```

---

## Measuring Success

After an Opus deep-dive, you should have:

✅ **Problem clearly articulated** - You understand what we're solving

✅ **Multiple approaches mapped** - You could explain options to someone else

✅ **Trade-offs explicit** - You know what we're gaining/losing

✅ **Recommendation justified** - You could defend the choice

✅ **New unknowns surfaced** - You know what questions emerged

✅ **Implementation pathway clear** - Sonnet knows what to do

✅ **Risk identified** - You know where things could break

✅ **Next steps obvious** - Clear puzzle to solve next

---

## Multi-Session Workflow Example

### Session 1: Authentic Learning
- **Time:** 60 min
- **Output:** Understanding what makes learning feel real
- **Artifact:** `decisions/01_authentic_learning.md`

### Session 2: Data Quality
- **Time:** 45 min
- **Output:** Strategy for detecting biased data
- **Artifact:** `decisions/02_data_quality.md`

### Session 3: Base Model Selection
- **Time:** 45 min
- **Input:** Reference earlier decisions on learning architecture
- **Output:** Base model recommendation matrix
- **Artifact:** `decisions/03_base_model.md`

### Session 4: LoRA Configuration
- **Time:** 45 min
- **Input:** Reference base model decision
- **Output:** Rank/alpha selection strategy
- **Artifact:** `decisions/04_lora_config.md`

### Session 5: Integration Check
- **Time:** 90 min
- **Input:** All 4 previous decisions
- **Output:** Master architecture document showing all interactions
- **Artifact:** `MASTER_ARCHITECTURE.md`

### Handoff to Sonnet
- **Input:** Master architecture + 5 decision documents
- **Task:** "Here's the plan. Implement the learning pipeline following this architecture."

---

## Pro Tips

1. **Let Opus finish thinking** - Don't interrupt with "just tell me"
2. **Reference earlier decisions** - "Remember when we decided X? Does this contradict?"
3. **Ask about unknowns** - "What don't we know that we should?"
4. **Push on assumptions** - "Why are we assuming that's true?"
5. **Document everything** - Future you will thank you
6. **Check consistency** - Before moving forward, ensure no contradictions
7. **Plan for Sonnet** - Keep thinking: "Can Sonnet implement this easily?"
8. **Celebrate progress** - Each puzzle solved unlocks others

---

## Timeline Estimate

**Full Architecture Phase with Opus:** 4-6 sessions × 45-90 min each = 6-9 hours

This yields:
- 5-8 major decisions made
- 30+ architectural details clarified
- Clear scaffolding for Sonnet
- Identified risks and mitigation
- Ready for implementation

**Then:** Hand off to Sonnet for 3-4 weeks of implementation using the roadmap Opus created.

---

## Final Notes

This process works because:
- **Opus thinks complexly** - Can hold many perspectives at once
- **You direct strategically** - You decide what matters most
- **Documentation captures it** - Future versions can execute cleanly
- **Clear handoff** - Sonnet gets a clear blueprint
- **Efficient use of tokens** - Expensive thinking when it matters most

You're essentially using Opus as your strategic advisor, documenting their advice, then handing off the execution to cheaper versions.

Perfect division of cognitive labor.

**Let's build this right.** 🚀
