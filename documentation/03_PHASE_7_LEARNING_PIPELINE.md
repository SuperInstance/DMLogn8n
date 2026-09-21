# 03: Phase 7 - The Learning Pipeline (20% Complete)

## What Phase 7 Does

Phase 7 closes the loop. Layers 1-3 create characters that can play D&D intelligently. Phase 7 makes those characters actually learn and improve from their gameplay.

The mechanism: **Dream Cycles** between sessions where characters reflect on decisions and fine-tune their neural network adapters.

## The Dream Cycle: How Learning Works

### States and Transitions

A character goes through states during the learning process:

```
ACTIVE
  ↓ (100+ decisions accumulated)
DREAMING (preparing to train, final data collection)
  ↓
TRAINING (model fine-tuning, 15-30 minutes)
  ↓
AWAKENING (loading new model weights)
  ↓
ACTIVE (character returns, improved)
```

### What Happens in Each State

**ACTIVE:**
- Normal gameplay
- Decisions logged to database
- Outcomes tracked with multi-domain rewards
- Reflection analysis performed (optional, LLM)

**DREAMING:**
- Session ends
- Character collected final decisions
- System determines if training threshold met
- Triggers: 100+ decisions OR 10+ teaching moments

**TRAINING:**
- Decision data curated (filtered, deduplicated, balanced)
- Training dataset generated (80/10/10 train/val/test split)
- LoRA adapter fine-tuned on RTX 4050
- Takes 15-30 minutes
- Character unavailable during this time

**AWAKENING:**
- New model weights loaded
- System validates training succeeded
- Character ready for next session

**ACTIVE (Improved):**
- Same character, but with updated decision-making
- Next session, character makes better decisions
- Process repeats

## Completed Phase 7 Tasks (Tasks 7.1.1-7.1.3)

### Task 7.1.1: Decision Logger ✅

**Purpose:** Capture every gameplay decision with full context.

**What Gets Stored:**
```json
{
  "decision_id": "uuid",
  "character_id": "uuid",
  "session_id": "uuid",
  "timestamp": "ISO 8601",
  
  "situation_context": {
    "game_state": {
      "location": "tavern",
      "time": "evening",
      "enemies_nearby": false,
      "npcs_present": ["bartender", "mysterious_stranger"]
    },
    "character_state": {
      "hp": 42,
      "max_hp": 50,
      "status_effects": [],
      "resources": {"spell_slots": 2, "gold": 150}
    },
    "perception_data": {
      "heard": "mysterious_stranger whispering about danger",
      "saw": "stranger nervously looking around",
      "inferred": "stranger wants help with something"
    }
  },
  
  "decision": {
    "action": "approach_stranger",
    "reasoning": "Could be a quest hook or valuable information",
    "confidence": 0.72,
    "source": "brain",  # bot/brain/human
    "latency_ms": 2340
  },
  
  "outcome": {
    "success": true,
    "immediate_result": "Stranger revealed vampire plot",
    "side_effects": ["made_enemy_of_local_gang"],
    "reward_signals": {
      "combat": 0,          # No combat yet
      "social": 0.8,        # Great information gathering
      "exploration": 0.5,   # New quest discovered
      "resource": 0,        # No resources gained
      "strategic": 0.9      # Major quest opportunity
    },
    "aggregate_reward": 0.64,
    "quality_score": 0.85
  },
  
  "reflection": {
    "quality_label": "excellent",
    "teaching_value": 0.3,
    "strengths": ["Good information gathering", "Took social approach"],
    "weaknesses": "Could have been more cautious",
    "improvements": ["Gather more information before committing"],
    "teaching_moment": false
  }
}
```

**Key Features:**
- <1ms latency (logging doesn't slow gameplay)
- SQLite storage with indexes on character_id, session_id, created_at
- Privacy controls: per-character opt-in/opt-out
- Export capabilities: JSON, LoRA training format
- <100ms query performance

**Known Issues:**
- No data retention policy (grows indefinitely)
- No archival strategy for old data
- Reflection not automatically called
- Sensitive decisions (betrayal, suicide, etc.) not specially handled

### Task 7.1.2: Outcome Tracker ✅

**Purpose:** Assign reward signals across 5 domains.

**The Five Domains:**

| Domain | Metrics | Example |
|--------|---------|---------|
| **Combat** | Damage, tactics, victories, party safety | "Flanking maneuver: +0.4 tactical reward" |
| **Social** | Relationships, persuasion, info gained | "Successfully negotiated peace: +0.8" |
| **Exploration** | Discoveries, secrets, progress | "Found secret passage: +0.6" |
| **Resource** | XP, gold, items, buffs | "Gained 500 XP: +0.3" |
| **Strategic** | Positioning, opportunities, long-term | "Positioned for ambush: +0.7" |

**Why Multi-Domain:**
Character learns nuanced decision-making:
- "Attack failed (Combat: -0.3) but revealed enemy position (Strategic: +0.5)"
- "Paid bribe (Resource: -0.4) but gained trust (Social: +0.6)"

Single-domain rewards would make characters learn only "win" vs. "lose". Multi-domain teaches sophistication.

**How Rewards Are Calculated:**
- DM input: "What was the outcome?"
- System analysis: "What domains does this affect?"
- LLM reflection (if enabled): "What was the decision quality?"
- Result: Multi-dimensional reward vector

**Known Issues:**
- Reward domain weights hardcoded (all equal)
- Assumes linear causality (D&D is nonlinear)
- Temporal correlation doesn't handle delayed effects well
- No consensus on correct reward values
- Imbalanced domains (lots of combat, few social decisions)

### Task 7.1.3: Session Manager ✅

**Purpose:** Coordinate learning across multiple party members.

**Growth Score:**
- Range: 0-1 (0 = no learning, 1 = significant improvement)
- Calculation:
  - % of decisions with high quality_score
  - % of teaching moments
  - Comparison to prior session
  - Average across all characters

**Multi-Character Coordination:**
- Each character logs independently
- Party decisions (group attacks) logged for all participants
- Party outcomes recorded for all
- Each character calculates individual growth score

**Training Trigger Decision:**
```
For each character:
  If total_decisions >= 100:
    Trigger dream cycle
  Else if teaching_moments >= 10:
    Trigger dream cycle
  Else if session_duration > 4 hours:
    Trigger dream cycle
```

**Known Issues:**
- No party-level learning (each character learns alone)
- Growth score calculation somewhat arbitrary
- No weighting based on decision importance
- Manual intervention needed to trigger training

## In-Progress Phase 7 Tasks

### Task 7.2.1: Reflection Pipeline (Framework Complete) ⚠️

**Purpose:** Use LLM to analyze decision quality and identify learning opportunities.

**What It Does:**
- Analyzes each decision: "Was this good?"
- Assigns quality label: excellent/good/acceptable/poor/teaching_moment
- Identifies improvements: "Next time try X instead"
- Calculates teaching value: How valuable for learning? (0-1)

**Quality Labels:**
- **excellent**: Perfect decision, couldn't do better
- **good**: Solid decision, reasonable approach
- **acceptable**: Worked but suboptimal alternatives existed
- **poor**: Failed, better alternatives existed
- **teaching_moment**: Failure with high learning value

**LLM Providers Supported:**
- DeepSeek: $0.40/1000 decisions (RECOMMENDED)
- Claude 3.5: $5/1000 decisions
- GPT-4: $15/1000 decisions

**Cost Optimization:**
System chooses cheaper providers by default. Fallback to heuristic analysis if no API key.

**Known Issues:**
- Reflection called manually, not automatically
- No caching of reflection results (same decision analyzed twice?)
- Fallback analysis is too simplistic
- No human validation of LLM quality labels
- Bias possible: LLM might favor certain decision types

## Tasks In Development (Next to Tackle)

### Task 7.2.2: Data Curation Pipeline (2-3 days) 🚧

**Purpose:** Prepare training data for LoRA fine-tuning.

**What It Does:**
1. **Quality Filtering**
   - Remove decisions with confidence < 0.3
   - Remove decisions with quality_score < 0.4
   - Keep teaching_moment decisions regardless

2. **Deduplication**
   - Use sentence-transformer embeddings for similarity
   - Remove near-duplicates (cosine similarity > 0.95)
   - Keep highest-quality version of duplicate set

3. **Dataset Balancing**
   - Current success/failure ratio measured
   - Target: 65% success, 35% failure
   - Stratified random undersampling of majority class
   - Teaching moments always included (weighted 3x)

4. **Train/Validation/Test Splits**
   - 80% training, 10% validation, 10% test
   - Stratified by decision type
   - Ensure diversity in each split

5. **Export Format**
   - JSONL format: `{"context": {...}, "decision": {...}, "outcome": {...}}`
   - Ready for LoRA training

**Implementation Challenges:**
- Embedding generation slow (10-30 min for 1000 decisions)
- Duplicate threshold varies by decision type
- Handling imbalanced domains (combat heavy)
- Ensuring splits representative

**Research Questions:**
- Q: Should similarity threshold vary by decision type?
- Q: Is 65/35 ratio optimal or just a guess?
- Q: Should we weight teaching moments 3x, 5x, 10x?
- Q: Can we augment underrepresented categories synthetically?
- Q: How do we validate splits are representative?

### Task 7.2.3: Character Dashboard UI (1-2 days) 🚧

**Purpose:** Visualize character learning progress.

**What Should It Show:**
- Real-time training progress during dream cycle
- Historical graphs of decision quality
- Character learning curves (improvement over sessions)
- Decision replay: Show specific decision with reasoning
- Training statistics: Decision counts, domain distribution, teaching moments
- Model version history: Which LoRA adapters, when trained

**Major Decision: Web UI or CLI?**
- Web UI: More accessible, better visualizations, requires server
- CLI: Simpler, dev-friendly, less pretty
- Recommendation: Start with CLI, move to web if needed

**Major Decision: What Metrics Matter Most?**
- Learning rate? (Technical, confusing to players)
- Validation loss? (Technical, not intuitive)
- Character behavior change? (What players care about)
- Success rate improvement? (Measurable, meaningful)
- Teaching moment frequency? (Shows system is learning)

---

## Not-Yet-Started Phase 7 Tasks

### Task 7.3.1: QLoRA Training Infrastructure (5-7 days)

**Purpose:** Fine-tune LoRA adapters on RTX 4050.

**What It Needs to Do:**
- Implement 4-bit quantized LoRA training
- Character-specific adapters (10-50MB vs. 7GB full model)
- Auto-trigger when thresholds met
- Progress monitoring and ETA
- Automatic model loading/caching
- Rollback on failure

**Major Constraints:**
- VRAM: 6GB on RTX 4050 (QLoRA reduces 7GB → 700MB)
- Time: Complete in 15-30 minutes
- Stability: Graceful degradation on out-of-memory
- Data: Convert decision logs to training prompts

**Major Unknowns:**
- Base model selection (Llama 2? Mistral? GPT-2 local?)
- LoRA rank (r=8, 16, 32, 64?)
- Character-type specific tuning needed?
- How to handle characters with <50 decisions?

### Task 7.3.2: Hyperparameter Optimization (2-3 days)

**Purpose:** Tune learning parameters per character type.

**Decisions Needed:**
- Learning rate per character (0.0001? 0.001? 0.01?)
- Batch size (8? 16? 32?)
- LoRA rank and alpha (trade-off: quality vs. model size)
- Early stopping criteria (when to stop training?)
- Warmup steps vs. constant learning rate

**Questions:**
- Should warrior and wizard characters have different hyperparameters?
- Should hyperparameters adapt over multiple training cycles?
- Can we use meta-learning to find hyperparameters faster?

### Task 7.3.3: Training Automation (2 days)

**Purpose:** Automatically trigger and monitor training.

**Needs:**
- Auto-trigger logic (100 decisions, 10 teaching moments, manual)
- Queue management (multiple characters training)
- Error handling and recovery
- Status monitoring and reporting

### Task 7.4: Integration & Full Testing (3 days)

**Purpose:** End-to-end validation of complete learning loop.

**Tests Needed:**
- Full gameplay → training → improved decisions
- Performance metrics (latency, memory, training time)
- Failure modes (API down, out of memory, corrupted data)
- Documentation complete

---

## The Complete Data Flow During Dream Cycle

```
Session ends with 150 logged decisions
  ↓
SessionManager calculates growth_score = 0.73
  ↓
Triggers dream cycle (growth_score > threshold AND decisions >= 100)
  ↓
Character state: DREAMING
  ↓
DecisionCollector gathers all 150 decisions from database
  ↓
DataCurator processes:
  - Filters out 15 low-confidence decisions (leaving 135)
  - Detects 8 duplicates, removes them (leaving 127)
  - Balances success/failure (127 × 0.65 success → final set)
  - Splits 80/10/10 (train/val/test)
  ↓
Exports training set to JSONL
  ↓
Character state: TRAINING
  ↓
LoRATrainer.train(character_id=X, training_data=dataset)
  - Loads base model (Llama-2-7B)
  - Loads character's previous LoRA adapter (if exists)
  - Trains for 20 epochs or early stopping
  - Saves new adapter weights
  - Takes ~20 minutes on RTX 4050
  ↓
Character state: AWAKENING
  ↓
ModelLoader loads new adapter weights into character's model
  ↓
Character state: ACTIVE
  ↓
Next gameplay session starts
  ↓
Character makes better decisions based on learned patterns
```

## Key Insights About Phase 7

**Why This Works:**
- Training between sessions doesn't interrupt gameplay
- Automatic logging means no extra work for DM
- Local GPU training is 100x cheaper than cloud
- QLoRA makes training feasible on consumer hardware
- Characters visibly improve session-to-session

**What We're Still Figuring Out:**
- How to preserve character personality during training
- How to detect if training worked (beyond loss metrics)
- What hyperparameters work best
- How much data is needed before learning is meaningful
- What prevents pathological learning (learning wrong lessons)

**The Biggest Unknown:**
Will characters trained this way feel authentic to players? Or will the learning feel fake/scripted?

---

## Success Metrics for Phase 7

**Completion Criteria:**
- ✅ All 19 tasks implemented
- ✅ 100+ tests passing
- ✅ Full learning loop works end-to-end
- ✅ Characters demonstrably improve session-to-session
- ✅ Training completes in <30 minutes on RTX 4050
- ✅ Cost stays under $5/month per character
- ✅ No gameplay lag from learning system

**Quality Criteria:**
- Character learning feels authentic (subject to player testing)
- Personality preserved during training
- Failures handled gracefully (API down, OOM, data corruption)
- Documentation complete and clear

## Timeline Estimate

- **Week 1:** Data Curation + Dashboard (Tasks 7.2.2-7.2.3)
- **Week 2-3:** QLoRA Training Infrastructure (Task 7.3.1)
- **Week 3:** Hyperparameter Optimization (Task 7.3.2)
- **Week 4:** Training Automation + Integration (Tasks 7.3.3-7.4)
- **Total:** ~4 weeks to 100% Phase 7 complete

After Phase 7, Phases 8-10 become possible (multi-character learning, transfer learning, opponent adaptation).
