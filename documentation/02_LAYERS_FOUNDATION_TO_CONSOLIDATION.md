# 02: Layers 1-3 - Foundation, Intelligence, and Consolidation

## Layer 1: Foundation - The Game Rules Engine

### What Layer 1 Does

Layer 1 implements D&D mechanics and creates playable characters. By the end of Layer 1, you have fully functional NPC characters who can participate in combat, negotiate, explore, and remember things.

**What Layer 1 Is NOT:**
- Smart (characters don't make strategic decisions)
- Learning (characters don't improve from experience)
- Adaptive (characters don't change behavior)

**What Layer 1 IS:**
- A complete implementation of D&D 5e rules
- A character system with stats, skills, inventory
- An NPC lifecycle and relationship system
- A memory system for recalling past events

### Components

| Component | Purpose | Status |
|-----------|---------|--------|
| `game_mechanics.py` | D&D 5e rules, dice rolling, calculations | Complete |
| `character_brain.py` | Character definition, traits, personality | Complete |
| `npc_manager.py` | NPC creation, relationships, lifecycle | Complete |
| `chat_system.py` | Communication system | Complete |
| `memory_system.py` | Episodic memory (remembering events) | Complete |

### The Memory Problem It Solves

Without memory, NPCs can't reference the past. They don't remember who the party is, what happened last session, or what they promised to do. Layer 1's memory system allows:

- Characters remember party members across sessions
- Characters recall past events relevant to current situation
- Relationships evolve based on history
- NPCs can reference prior conversations

But memory is simple: episodic (specific events) and semantic (facts). It doesn't learn patterns or adapt behavior.

### Layer 1 Refinements: What Could Be Better

**Memory Management:**
- When should old memories be pruned? (Currently unlimited)
- Should traumatic events be remembered better? (Emotional weighting)
- Should memories degrade or fade? (Forgetting mechanism)
- Should characters misremember based on personality? (Bias in recall)

**Character Consistency:**
- How well should characters stay in-character? (Need validation metrics)
- Should personality affect available actions? (Lawful characters can't betray)
- Can characters have conflicting personality traits? (Complexity vs. consistency)

**NPC Relationships:**
- Should relationships decay if not maintained? (Currently static)
- How do group relationships differ from individual? (Party vs. character)
- Can relationships be severed permanently? (Burned bridges)
- Should reputation precede characters? (Rumor spreading)

### Layer 1 Research Questions

These are genuine unknowns that could affect design:

1. **Q: Should memory be lossy?**
   - Perfect memory feels inhuman
   - But selective memory needs rules
   - How do we decide what to forget?

2. **Q: Can characters have inconsistent memories of the same event?**
   - Different perspectives on what happened
   - Creates narrative depth but breaks logic
   - How do we validate memory?

3. **Q: Should personality constrain decision availability?**
   - Lawful character shouldn't have "betray party" option
   - But this reduces player agency if NPC refuses
   - What level of constraint is healthy?

4. **Q: How do we measure character consistency?**
   - Can we score how well NPC stays in-character?
   - Should this be observable to player?
   - Is consistency even the goal?

5. **Q: Should relationships have momentum?**
   - If party is rude, should NPC relationship drop quickly or stick?
   - Should characters give second chances?
   - How many negative interactions until permanent damage?

### Known Issues in Layer 1

- No memory decay implemented (characters remember everything forever)
- Relationship weighting is hardcoded (all relationships weighted equally)
- No personality-driven action constraints (any character can attempt anything)
- Limited NPC lifecycle (NPCs don't evolve much)

---

## Layer 2: Intelligence - The Escalation Engine

### What Layer 2 Does

Layer 2 gives characters the ability to make intelligent decisions. This is where NPCs stop being puppets and start being agents.

**The Problem Layer 2 Solves:**
How do you make responsive, intelligent decisions for AI characters without:
- Slowing down gameplay
- Breaking the budget
- Requiring human intervention every turn

**The Solution:**
The Escalation Engine: route decisions through three tiers based on complexity.

### The Three Tiers Explained

**Tier 1: Bot** (60-70% of decisions)
- Rule-based, hardcoded decision-making
- Examples:
  - "Low HP? Drink healing potion"
  - "Enemy attacking? Defend position"
  - "Treasure visible? Move toward it"
- Latency: <50ms
- Cost: ~$0.00001
- When used: Routine, predictable situations

**Tier 2: Brain** (20-30% of decisions)
- Full LLM reasoning with context
- Examples:
  - "Should I trust this NPC?"
  - "What's the diplomatic approach?"
  - "Is this trap worth the risk?"
- Latency: 1-5 seconds
- Cost: ~$0.0001
- When used: Novel, complex, uncertain situations

**Tier 3: Human** (1-5% of decisions)
- Escalate to player for final decision
- Examples:
  - "Betray the party?"
  - "Attack the king?"
  - "Abandon the mission?"
- Latency: Manual (player decides)
- Cost: Player attention
- When used: Critical choices, moral dilemmas, high stakes

### The Escalation Decision

What determines which tier?

**Complexity Factors:**
- Novel situation? (Never encountered before)
- High stakes? (Someone could die)
- High uncertainty? (Multiple valid options)
- Time pressure? (Need quick decision)
- Moral dimension? (Right vs. wrong)

**Decision Logic:**
```
If complexity < 0.3: Use Bot (safe, routine)
If complexity 0.3-0.7: Use Brain (needs reasoning)
If complexity > 0.7: Use Human (too important)
```

### Cost Efficiency

The magic is in the distribution:

- 70% decisions × 0.001 seconds = 0.7 seconds
- 25% decisions × 3 seconds = 75 seconds
- 5% decisions × manual = variable

**Total per 100 decisions:** ~75-80 seconds + manual time

**Cost per 100 decisions:**
- Bots: $0.000007 (negligible)
- Brains: $0.0025 (LLM API calls)
- Humans: $0 (player time)
- **Total: ~$0.0025**

**Without escalation (all LLM):**
- 100 decisions × 3 seconds = 300 seconds
- 100 decisions × $0.001 = $0.10
- **40x more expensive**

This is why the system works on consumer budgets.

### Components

| Component | Purpose |
|-----------|---------|
| `escalation_engine.py` | Routing logic, complexity evaluation |
| `mechanical_bot.py` | Rule-based decisions |
| `combat_bots.py` | Combat tactics |
| `social_bots.py` | Dialogue and negotiation |
| `model_routing.py` | LLM provider selection |
| `local_llm_engine.py` | Local inference support |
| `llm_api_integration.py` | API client (GPT-4, Claude, DeepSeek) |

### Layer 2 Refinements: What Could Be Better

**Adaptive Escalation:**
- Currently: Thresholds are hardcoded
- Better: Thresholds adapt based on character success/failure
- Example: If character's "Brain" decisions fail consistently, lower Brain threshold?

**Model Selection Learning:**
- Currently: Randomly routes between LLM providers
- Better: Track which LLM works best for this character
- Example: Warrior characters might do better with a tactical model

**Context Window Management:**
- Currently: Each decision gets fixed context
- Better: Adaptive context based on situation complexity
- Example: Combat decisions need more tactical context than social decisions

**Cost Optimization:**
- Currently: All LLM calls cost equally
- Better: Cache decisions, reuse similar outcomes
- Example: Same tactical situation, similar solution

**Fallback Strategies:**
- Currently: If API down, system breaks
- Better: Automatic fallback to more expensive local LLM or simpler heuristics
- Example: DeepSeek down? Use local model. Local down? Use deterministic rules.

### Layer 2 Research Questions

1. **Q: Should escalation thresholds be personality-based?**
   - Aggressive warriors might escalate less (act before thinking)
   - Careful wizards might escalate more (analyze before acting)
   - How do we prevent personalities from being strategies to exploit?

2. **Q: Can we predict escalation success before calling LLMs?**
   - Train a lightweight classifier on past decisions
   - Predict "This will fail" before expensive API call
   - Would save 30% of LLM calls?

3. **Q: Should characters remember past escalation failures?**
   - "Last time I trusted my instincts, I died"
   - Dynamically lower escalation threshold?
   - Could this create learning without Phase 7?

4. **Q: How do we keep decisions consistent across sessions?**
   - Same situation, but different LLM provider
   - Character behavior changes unexpectedly
   - Need deterministic handling?

5. **Q: Should escalation thresholds decay during long sessions?**
   - Characters get "tired" after many decisions
   - Start using more bots, fewer brains
   - Mimics human fatigue?

6. **Q: Can characters learn which escalation tier works best?**
   - Some characters better at improvisation (lower escalation threshold)
   - Others better at planning (higher threshold)
   - Does this constitute learning without Phase 7?

### Known Issues in Layer 2

- Escalation thresholds hardcoded (all characters use same thresholds)
- No mechanism to prevent characters getting stuck in Bot-only mode
- No learning about which LLM providers work best
- LLM API calls not cached (same decision called multiple times)
- No degraded fallback if APIs are down

---

## Layer 3: Consolidation - Memory and Pattern Recognition

### What Layer 3 Does

Layer 3 extracts patterns from decisions and consolidates experiences into insights. Characters don't just remember individual events—they understand trends and patterns.

**The Problem Layer 3 Solves:**
Humans don't just remember individual experiences. We extract patterns:
- "Wizards always open with fireball"
- "Betrayals always backfire"
- "Careful planning usually succeeds"

Layer 3 gives NPCs similar capability.

### How It Works

**Episodic → Semantic Transition:**
- Episodic: "Session 5, the party killed the bandits"
- Semantic: "This party defeats enemies efficiently"

**Pattern Extraction:**
- Look for repeated situations
- Identify successful vs. unsuccessful outcomes
- Extract decision rules
- Create generalizable knowledge

**Digital Twin Analysis:**
- Create copy of character for analysis
- Test strategies without affecting real character
- Simulate situations to prepare
- Learn from counterfactuals

### Components

| Component | Purpose |
|-----------|---------|
| `vector_memory.py` | Semantic search using embeddings |
| `advanced_consolidation.py` | Pattern extraction and consolidation |
| `digital_twin.py` | Analysis instance for simulation |
| `pathology_detection.py` | Monitor for unhealthy patterns |

### Memory Consolidation Process

**Stage 1: Collection**
- All decisions from session gathered
- Episodic memories created

**Stage 2: Analysis**
- Digital twin analyzes decisions
- Patterns detected
- Quality assessed

**Stage 3: Consolidation**
- Similar memories grouped
- Common themes extracted
- Semantic knowledge created

**Stage 4: Integration**
- New knowledge integrated into character
- Old contradictory knowledge pruned
- Decision-making updated

### Layer 3 Refinements: What Could Be Better

**Consolidation Timing:**
- Currently: One consolidation per session
- Better: Adaptive consolidation based on decision count
- Example: After 50 decisions, consolidate. After 100, consolidate again.

**Interference Management:**
- Currently: New memories might overwrite important old ones
- Better: Protect high-confidence memories from interference
- Example: Core personality memories shouldn't change from one session

**Personality Preservation:**
- Currently: Consolidation doesn't explicitly preserve personality
- Better: Ensure consolidation reinforces core personality
- Example: Honest character shouldn't learn dishonesty from one event

**Pattern Validation:**
- Currently: No validation that extracted patterns are meaningful
- Better: Only extract patterns with minimum support
- Example: Need 5 similar decisions before extracting pattern

**Pathology Detection:**
- Currently: Rule-based detection of bad patterns
- Better: Learn what healthy learning looks like
- Example: Detect when character repeatedly makes same mistake

### Layer 3 Research Questions

1. **Q: How many examples needed to extract a valid pattern?**
   - Too few: Extract noise
   - Too many: Miss learning
   - Should this vary by decision type?

2. **Q: Should characters unlearn old patterns?**
   - Character learned "run from combat"
   - Through 10 victories, learns "stand and fight"
   - Should old pattern be deleted?

3. **Q: Can we use attention mechanisms to understand what matters?**
   - Show which memories character attends to
   - Validate that consolidation captured important parts
   - Help debug bad learning

4. **Q: How do we detect personality drift?**
   - Character improving in combat but becoming aggressive
   - Is this growth or corruption?
   - When should we intervene?

5. **Q: Should old memories decay or permanently influence behavior?**
   - Fresh trauma should matter most (recency)
   - But foundational memories should persist (importance)
   - How to balance?

6. **Q: Can characters have multi-faceted motivations?**
   - "Wants to be rich AND wants to help people"
   - These sometimes conflict
   - How do we preserve both?

7. **Q: Should party-level strategies emerge from individual learning?**
   - Characters learn individually
   - Do collective patterns form naturally?
   - Or require explicit multi-character learning?

### Known Issues in Layer 3

- Memory consolidation is manual, not automatic
- Consolidation doesn't explicitly preserve personality
- Pattern extraction has no minimum support threshold
- Pathology detection is rule-based, not learned
- No mechanism for characters to unlearn outdated patterns
- No multi-character pattern extraction
- No ability to validate that consolidation was successful

---

## Integration Across Layers

### The Complete Flow

```
Layer 1: Character makes decision
  ↓
Layer 2: Escalation Engine routes decision intelligently
  ↓
Layer 1: Decision executed, outcome recorded
  ↓
Layer 1: Memory stores the event
  ↓
Layer 3: Patterns extracted from memories
  ↓
Layer 2: Escalation Engine uses extracted patterns for future decisions
  ↓
Back to Layer 1: Repeat
```

### Key Insights

**No Learning Yet:**
Layers 1-3 create intelligent characters but they don't improve. A character that wins 5 combats doesn't fight better on the 6th.

**Solid Foundation:**
Every capability needed for Phase 7 exists in Layers 1-3. Phase 7 just adds the mechanism to improve the escalation layer's decision weights.

**Modular Design:**
Each layer can be understood independently but serves a clear function in the whole. Layer 1 without 2 is static. Layer 2 without 1 has no rules to follow. Layer 3 without 2 has nothing to consolidate.

---

## The Challenges We Haven't Solved

Layers 1-3 are complete but leave major questions:

**In Layer 1:**
- Should relationships decay?
- Can characters have inconsistent memories?
- What determines character consistency?

**In Layer 2:**
- Should escalation thresholds be adaptive?
- Can we predict when LLM calls will fail?
- What about when APIs are down?

**In Layer 3:**
- How do we validate consolidation worked?
- Can characters unlearn?
- When does learning become personality drift?

**Across Layers:**
- How do characters stay themselves while using learned patterns?
- Should Layer 3 learning feed back to Layer 2's escalation thresholds?
- Can characters learn which escalation strategy works best for them?

These are the architectural puzzles worth solving at the Opus level.
