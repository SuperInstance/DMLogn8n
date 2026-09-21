# 05: Known Unknowns & Research Questions (The Puzzle List)

This document lists 50+ unresolved questions across the system. These are genuine unknowns, not implementation details. Each represents a design puzzle worth solving.

## Character Agency & Authenticity (7 Puzzles)

**The Core Question:** Do characters feel like they genuinely learn, or does learning feel scripted/artificial?

### Puzzle 1: Authentic Learning vs. Apparent Learning
**The Problem:**
- When character behavior changes after training, does it *feel* learned to the player?
- Or does it feel like the character was rewritten?
- Can we measure this difference?

**What We Don't Know:**
- What makes learning feel authentic vs. fake?
- Is it about transparency (player sees learning) or invisibility?
- Do different learning types feel different? (Tactical improvement vs. personality change)
- Can we validate authenticity objectively or only subjectively?

**Why It Matters:**
- If learning feels fake, the whole system fails emotionally
- Players invest in characters; fake learning betrays that investment

### Puzzle 2: Personality Preservation During Training
**The Problem:**
- Training might change character behavior in unexpected ways
- Example: Character becomes more aggressive after combat-heavy session
- Is this learning or personality drift?
- How do we prevent it?

**What We Don't Know:**
- How to measure personality drift objectively
- Should we freeze certain decisions during training?
- Can we validate personality stayed consistent post-training?
- What's acceptable amount of personality change?

**Why It Matters:**
- If characters change personality, players feel betrayed
- But some personality change might be learning
- Need to distinguish between healthy growth and corruption

### Puzzle 3: Decision-Making Transparency
**The Problem:**
- When character makes decision, should player understand why?
- Too much transparency breaks immersion
- Too little transparency makes learning feel random

**What We Don't Know:**
- How much explanation helps vs. hurts immersion?
- Should explanation come from character RP or system?
- Do different decision tiers need different explanations? (Bot vs. Brain decisions)
- Can we show learning influence without spoiling magic?

**Why It Matters:**
- Player engagement depends on understanding character actions
- But explaining learning system might break story

### Puzzle 4: Intentional Bad Decisions for Growth
**The Problem:**
- Humans sometimes make intentionally bad decisions to learn
- "Let me try the stupid approach and see what happens"
- Can characters do this? Should they?

**What We Don't Know:**
- Should characters explore decision space deliberately?
- How do we distinguish intentional experimentation from mistakes?
- How much "wasting" turns is acceptable for learning?
- Can we reward good failures more than bad successes?

**Why It Matters:**
- Might accelerate learning significantly
- But could be annoying (watching character deliberately fail)

### Puzzle 5: Consistency Across Sessions
**The Problem:**
- Character should behave similarly in similar situations
- But might use different LLM provider (different responses)
- How much variation is acceptable?

**What We Don't Know:**
- Should character responses be deterministic?
- Is variation good (exploration) or bad (inconsistency)?
- How to balance learning variation vs. personality consistency?

**Why It Matters:**
- Inconsistency makes characters unpredictable (bad)
- But too much consistency makes learning invisible

### Puzzle 6: Learning Curves and Plateaus
**The Problem:**
- Real learning has plateaus (no improvement for a while)
- Should DMLog characters plateau too?
- Or continuously improve?

**What We Don't Know:**
- Should we artificially create plateaus for realism?
- How long should plateaus last?
- What causes plateaus in training? (Data distribution? Hyperparameters?)
- How to communicate plateau to player?

**Why It Matters:**
- Continuous improvement feels unrealistic
- Plateaus might be frustrating to player
- But plateaus create narrative opportunities

### Puzzle 7: Learning Over Years vs. Sessions
**The Problem:**
- If campaign runs for 100 sessions, how much should character improve?
- Should they become superhuman?
- Or should learning rate decay?

**What We Don't Know:**
- Should learning rate decrease over time?
- Is there an asymptotic limit to improvement?
- How to prevent characters becoming too good?
- Should learning reset for new campaigns?

**Why It Matters:**
- Long campaigns risk characters becoming OP
- But continuous growth feels right narratively
- Need balance between challenge and reward

---

## Data Quality & Bias (7 Puzzles)

**The Core Question:** How do we prevent corrupted learning if training data is biased/wrong?

### Puzzle 8: Detecting Biased Training Data
**The Problem:**
- Player might have decision-making style that's suboptimal
- Character learns and amplifies that style
- Is this player preference or corruption?

**What We Don't Know:**
- How to detect bias in decision logs?
- What biases matter? (Combat-heavy? Risk-averse? Trusting?)
- Should we auto-correct bias or let it happen?
- What's acceptable level of bias?

**Why It Matters:**
- Garbage in, garbage out
- Bad training data creates bad learning
- But some "bias" might be intentional style

### Puzzle 9: Imbalanced Decision Domains
**The Problem:**
- Session might have 80% combat, 20% social
- Character learns combat-heavy
- But next session is mostly social
- Character unprepared

**What We Don't Know:**
- Should we reweight domains to match session type?
- Can we predict what decisions will be needed next session?
- Should training account for underrepresented domains?
- How much domain imbalance is acceptable?

**Why It Matters:**
- Specialization might be good or bad depending on context
- Don't want characters overspecialized
- But domain-specific expertise also valuable

### Puzzle 10: Synthetic Data Augmentation
**The Problem:**
- Some decision types rare (convincing dragon to ally)
- Character never learns this decision
- Could we generate synthetic training examples?

**What We Don't Know:**
- How to generate realistic synthetic decisions?
- Will synthetic data help or hurt learning?
- How much synthetic data is safe to use?
- What domains benefit most from augmentation?

**Why It Matters:**
- Could dramatically improve learning for rare situations
- But synthetic data might introduce new biases
- Need validation that synthetic examples are realistic

### Puzzle 11: Corrupted or Invalid Decisions
**The Problem:**
- What if decision logging has bugs?
- What if DM entered wrong outcome?
- What if decision is impossible/cheating?

**What We Don't Know:**
- How to detect invalid decisions automatically?
- Should we allow manual correction of training data?
- How to recover from corrupted data?
- What validation rules should we have?

**Why It Matters:**
- Corrupted data breaks learning
- But manual correction is tedious
- Need automated detection

### Puzzle 12: Conflicting Training Examples
**The Problem:**
- Character trained: "Diplomacy works with nobles"
- Also trained: "Diplomacy fails with nobles"
- Contradictory examples

**What We Don't Know:**
- How does model handle contradictions?
- Should we detect and remove contradictory examples?
- Or learn nuance (context matters)?
- How to validate resolution is correct?

**Why It Matters:**
- Could lead to inconsistent behavior
- Or sophisticated conditional learning (best outcome)
- Need to understand trade-off

### Puzzle 13: Outcome Reward Accuracy
**The Problem:**
- How do we know outcome reward values are correct?
- What if DM got reward values wrong?
- What if delayed effects not captured?

**What We Don't Know:**
- How to validate reward values post-hoc?
- Should players be able to override reward values?
- How to handle delayed effects (poison)?
- What accuracy level is required?

**Why It Matters:**
- Wrong reward values teach wrong lessons
- But perfect accuracy impossible
- Need "good enough" standard

### Puzzle 14: Teaching Moment Detection
**The Problem:**
- System tries to identify high-value failures
- What if identification is wrong?
- What if real teaching moment missed?

**What We Don't Know:**
- How to validate teaching moment detection?
- Should players be able to mark teaching moments?
- Are teaching moments obvious or subtle?
- How to weight teaching moment importance?

**Why It Matters:**
- Teaching moments drive learning
- Incorrect detection wastes training capacity
- Players might see things system misses

---

## Computational Limits & Scaling (8 Puzzles)

**The Core Question:** Where does this system break at scale?

### Puzzle 15: Storage Growth
**The Problem:**
- ~10MB per 1000 decisions
- 4 sessions/month = ~400 decisions/month
- Per character: ~40MB/month = ~480MB/year

**What We Don't Know:**
- How many characters will system handle?
- When does SQLite performance degrade?
- Should we archive old decisions?
- What retention policy is appropriate?

**Why It Matters:**
- 10-year campaign = 5GB per character
- 10 characters = 50GB
- Need to plan for growth

### Puzzle 16: Training Time Scaling
**The Problem:**
- Currently: ~20 minutes per character on RTX 4050
- With 500 decisions: How long?
- With 2000 decisions: How long?

**What We Don't Know:**
- Does training time scale linearly or worse?
- Is there a decision count limit before scaling breaks?
- Can we split training across GPUs?
- Should we prune old decisions from training?

**Why It Matters:**
- If training takes 3 hours, players won't wait
- If training takes 30 seconds, can do it real-time
- Scaling determines feasibility

### Puzzle 17: Simultaneous Character Training
**The Problem:**
- 4 party members, all dream cycle simultaneously
- RTX 4050 can't train 4 models at once
- Need queuing strategy

**What We Don't Know:**
- Should characters wait turn?
- Or train in parallel on CPU?
- Or reduce training quality?
- What's acceptable wait time?

**Why It Matters:**
- Party experience degradation if one character waits
- Need fair queueing strategy
- Trade-off between speed and quality

### Puzzle 18: Memory Usage Scaling
**The Problem:**
- Loading large character dataset into memory
- Running inference on large model
- Memory pressure increases with decision count

**What We Don't Know:**
- At what decision count does RTX 4050 run out of memory?
- Can we use disk swapping?
- Should we use smaller base models?
- What's memory budget per character?

**Why It Matters:**
- OOM crashes lose player progress
- Need graceful degradation strategy
- Determines practical limits

### Puzzle 19: Query Performance Scaling
**The Problem:**
- SessionManager queries decision history
- DataCurator filters/deduplicates
- With 10,000 decisions: How slow?

**What We Don't Know:**
- What's acceptable query latency?
- When does SQLite performance degrade?
- Should we migrate to PostgreSQL?
- What indexing strategy is optimal?

**Why It Matters:**
- Slow queries block gameplay
- Need sub-100ms latency
- Affects playability at scale

### Puzzle 20: Multi-GPU Training
**The Problem:**
- Single RTX 4050 is bottleneck
- Could split training across GPUs
- How feasible is this?

**What We Don't Know:**
- Can LoRA training be parallelized?
- What setup required?
- Is complexity worth speedup?
- What's minimum viable speedup?

**Why It Matters:**
- Might reduce training time 10x
- But adds operational complexity
- Cost-benefit tradeoff

### Puzzle 21: Cloud Fallback Training
**The Problem:**
- What if player doesn't have GPU?
- Could use cloud training as fallback
- But costs money

**What We Don't Know:**
- Should cloud training be supported?
- What cost is acceptable?
- How to validate cloud training worked?
- Should it be transparent to player?

**Why It Matters:**
- Would support non-GPU machines
- But increases complexity and cost
- Need policy decision

### Puzzle 22: Embedding Computation for Deduplication
**The Problem:**
- Generating embeddings slow (10-30 min for 1000 decisions)
- Deduplication bottleneck
- Is this acceptable?

**What We Don't Know:**
- Can embedding generation be parallelized?
- Should we cache embeddings?
- Is faster embedding model acceptable quality trade-off?
- Can we do incremental deduplication?

**Why It Matters:**
- Deduplication is critical for data quality
- But slow deduplication blocks training
- Need to optimize or accept slowness

---

## Privacy & Control (6 Puzzles)

**The Core Question:** How much control should players have?

### Puzzle 23: Data Export and Ownership
**The Problem:**
- Players own their character data
- Should they be able to export it?
- What format? What details?

**What We Don't Know:**
- Should full decision logs be exportable?
- Should DMs be able to see training data?
- Should players be able to edit training data?
- What format is useful/safe?

**Why It Matters:**
- Data ownership is important for trust
- But might enable cheating
- Need balance

### Puzzle 24: Adapter Transfer Between Players
**The Problem:**
- Player 1 trains amazing fighter
- Player 2 wants to use that adapter
- Should this be allowed?

**What We Don't Know:**
- Should adapters be transferable?
- Would this enable cheating/exploitation?
- How to price/credit transfer?
- What's appropriate policy?

**Why It Matters:**
- Creates interesting economy
- But potential for abuse
- Need clear policy

### Puzzle 25: Sensitive Decision Handling
**The Problem:**
- What if player makes decision they regret?
- Suicide, betrayal, intimate choices
- Should these be logged?

**What We Don't Know:**
- Should system auto-detect sensitive decisions?
- Should there be opt-out for specific decision types?
- Should sensitive decisions affect learning?
- How to handle ethically?

**Why It Matters:**
- Player comfort is essential
- Some decisions shouldn't be training data
- Need respectful handling

### Puzzle 26: Campaign Privacy
**The Problem:**
- What if player wants campaign private?
- Or only specific sessions private?
- Or only specific characters?

**What We Don't Know:**
- How granular should privacy controls be?
- Should privacy settings be exportable?
- What's default privacy level?
- How to communicate privacy policy?

**Why It Matters:**
- Some campaigns are sensitive
- Need flexibility
- Should be obvious to player

### Puzzle 27: Third-Party Sharing
**The Problem:**
- What if someone wants to study character learning?
- Or create tool using decision data?
- Should this be allowed?

**What We Don't Know:**
- Should data sharing be opt-in or opt-out?
- Should academic use be different from commercial?
- How to anonymize while preserving value?
- What's fair data sharing policy?

**Why It Matters:**
- Data could enable cool research
- But player privacy must be respected
- Need balance

### Puzzle 28: Cross-Campaign Learning
**The Problem:**
- Should character remember previous campaigns?
- Or start fresh each campaign?
- Or selective memory?

**What We Don't Know:**
- Should learning carry over between campaigns?
- Should characters remember NPCs between campaigns?
- What about personality changes?
- Player preferences on this?

**Why It Matters:**
- Continuity vs. fresh start
- Changes character development arc
- Need player agency

---

## Player Experience (7 Puzzles)

**The Core Question:** When should learning be visible vs. invisible?

### Puzzle 29: Learning Visibility
**The Problem:**
- Is learning better obvious or hidden?
- Too obvious: Feels gamey
- Too hidden: Players don't notice

**What We Don't Know:**
- What visibility level feels right?
- Should learning be gradual or sudden?
- Can player control visibility?
- What does "good" feel like?

**Why It Matters:**
- Affects engagement and satisfaction
- Drives whether players feel learning is real
- Core emotional experience

### Puzzle 30: Dashboard vs. Immersion
**The Problem:**
- Dashboard shows training happens
- But breaks immersion
- Where's the balance?

**What We Don't Know:**
- Should characters visibly "rest" during training?
- Should players see training progress?
- Is dashboard RP-friendly or mechanical?
- What's optimal immersion level?

**Why It Matters:**
- Immersion is critical to D&D
- But transparency also important
- Need elegant solution

### Puzzle 31: Failure Feedback
**The Problem:**
- When character makes bad decision and fails
- Should they learn from it?
- Or is failure enough punishment?

**What We Don't Know:**
- How much failure teaching should happen?
- Do failures need to be explained?
- Should failures give special rewards?
- How to avoid rub-in-your-face feel?

**Why It Matters:**
- Balance between challenge and learning
- Failure can be demoralizing
- But failure is valuable teacher

### Puzzle 32: Session Length and Learning
**The Problem:**
- Long session: Many decisions, good training data
- Short session: Few decisions, might not train
- How to handle short sessions?

**What We Don't Know:**
- Should threshold be flexible?
- Should short sessions accumulate toward threshold?
- How to make short sessions feel valuable?
- What's minimum meaningful session length?

**Why It Matters:**
- Some sessions are short
- Don't want players to feel their session wasted
- Need inclusive design

### Puzzle 33: Explaining Character Behavior Changes
**The Problem:**
- Character behavior suddenly different (learned something)
- How to explain this in-world?
- Too much explanation breaks immersion

**What We Don't Know:**
- Should character explain their growth?
- Or should it be mysterious?
- Can we use RP to explain learning?
- What feels natural?

**Why It Matters:**
- Narrative satisfaction
- Player understanding
- Emotional resonance

### Puzzle 34: Challenge Scaling
**The Problem:**
- As character improves, encounters should adapt
- Otherwise character becomes OP and bored
- But how to scale fairly?

**What We Don't Know:**
- Should DM manually increase difficulty?
- Should system suggest difficulty increases?
- How to measure appropriate challenge?
- What if player prefers easy mode?

**Why It Matters:**
- Dynamic difficulty keeps games fun
- But removing player agency is bad
- Need collaborative approach

### Puzzle 35: Celebrating Growth
**The Problem:**
- When character achieves growth, should it be celebrated?
- How without being saccharine?

**What We Don't Know:**
- Should session end with "character learned X"?
- Should character RP their new insight?
- What triggers celebration?
- How to avoid feeling forced?

**Why It Matters:**
- Acknowledging growth reinforces it
- Players want to feel achievement
- Satisfying narrative closure

---

## System Architecture Puzzles (10+ Advanced)

### Puzzle 36: Escalation Threshold Adaptation
**The Problem:**
- Should escalation thresholds adapt over time?
- Conservative character becomes confident over time?
- Or stay consistent?

**Research Questions:**
- Q: Should success rate affect escalation threshold?
- Q: Should character learn which tier works best?
- Q: Should aggressive/conservative personalities escalate differently?
- Q: Can we prevent escalation threshold from drifting?

### Puzzle 37: Multi-Character Party Learning
**The Problem:**
- Characters in party learn separately
- But they're part of same experiences
- Should party learning emerge?

**Research Questions:**
- Q: How should party-level strategies work?
- Q: Should characters learn from each others' decisions?
- Q: What constitutes party success vs. individual?
- Q: How to prevent homogenization of party?

### Puzzle 38: Personality-Based Learning Rates
**The Problem:**
- Should different personality types learn at different rates?
- Genius learns faster than average?
- Stubborn character resists learning?

**Research Questions:**
- Q: Should personality affect learning rate?
- Q: Can we make personality learnable trait?
- Q: How to validate personality-based learning?
- Q: What's realistic personality-learning relationship?

### Puzzle 39: Cross-Campaign Transfer Learning
**The Problem:**
- Can knowledge transfer between campaigns?
- Should it?
- What about character personality?

**Research Questions:**
- Q: Should new character inherit knowledge from old?
- Q: What percentage of knowledge transfers?
- Q: Can players control transfer level?
- Q: What prevents transfer learning from breaking flavor?

### Puzzle 40: Emotional State Persistence
**The Problem:**
- Should emotional state affect learning?
- Traumatized character learns differently?
- Overconfident character learns poorly?

**Research Questions:**
- Q: Should we track character emotional state?
- Q: How should emotional state affect training?
- Q: Can character recover from trauma?
- Q: Is this realistic or overwrought?

---

## Remaining Puzzles (Quick List)

- **41:** Should characters sometimes deliberately make mistakes to test boundaries?
- **42:** How do we validate that neural network adapters work correctly?
- **43:** Should there be character skill caps? (Max effectiveness)
- **44:** Can characters learn meta-game strategies? (Exploit system)
- **45:** Should we detect and prevent "adversarial learning" between characters?
- **46:** How to handle DM mistakes in logging? (Wrong outcome recorded)
- **47:** Should character learning be reversible? (Forgetting/retraining)
- **48:** Can characters learn when playing different class? (Ranger learns rogue skills)
- **49:** Should learning rate accelerate with more data? (Faster learning as character grows)
- **50:** What happens if base LLM changes? (Model updates)

---

## How to Use This Document

**For Strategic Thinking:**
- Pick a puzzle that resonates with your vision
- Explore it deeply across multiple angles
- Document trade-offs and implications
- Propose solution architecture (not code)

**For Dependency Analysis:**
- Some puzzles block others
  - Puzzle 29 (visibility) affects Puzzle 30 (dashboard)
  - Puzzle 38 (personality learning) affects Puzzle 35 (celebration)
- Map dependencies before solving

**For Priority Setting:**
- **High Impact, Low Cost:** Puzzles 1, 8, 15, 29
- **High Impact, High Cost:** Puzzles 37, 38, 45
- **Medium Impact:** Everything else
- **Lower Priority:** Puzzles 44, 48, 50

**For Collaborative Problem-Solving:**
- Each puzzle worth 2-4 hour deep-dive session with Opus
- Document decision and reasoning for future reference
- Build architecture as you solve puzzles

---

**Next Steps:** Pick one puzzle from each category and dive deep. Start with high-impact puzzles you find most interesting.
