# 07: Critical Decision Points (Where Your Strategic Thinking Matters)

This document lists the 10-15 most important architectural decisions that still need to be made. These are NOT implementation questions—they're design choices that ripple through the entire system.

## Tier 1: Must Decide Before Implementation Continues

### Decision 1: Base Model for LoRA Training
**Question:** What neural network should we fine-tune adapters on?

**Options:**
1. **Llama 2 7B** (open-source, good quality, community support)
   - Pros: Well-tested, lots of documentation, active community
   - Cons: No native instruction following
   - Cost: 7GB loaded, 700MB with QLoRA

2. **Mistral 7B** (newer, better performance)
   - Pros: Better quality, good instruction following
   - Cons: Smaller community, less documentation
   - Cost: 7GB loaded, 700MB with QLoRA

3. **Llama 2 13B** (larger, better quality)
   - Pros: Better quality than 7B
   - Cons: Might not fit in RTX 4050 with QLoRA (needs testing)
   - Cost: 13GB loaded, 1.3GB with QLoRA

4. **Local GPT-2 Small** (simplest)
   - Pros: Fits easily, fast, proven
   - Cons: Lower quality, less sophisticated
   - Cost: 300MB unquantized

5. **Cloud LLM (GPT-4, Claude)** (best quality)
   - Pros: Excellent quality, no local hardware needed
   - Cons: Expensive ($10-20/month per character), slow, relies on APIs
   - Cost: Variable, high

**Implications:**
- **Development Speed:** GPT-4 fastest to implement, local models slower
- **Cost:** Local models cheap long-term, cloud expensive
- **Quality:** GPT-4 best quality, Mistral good, Llama acceptable
- **User Hardware:** Local models require GPU, cloud no hardware needed
- **Determinism:** Local models deterministic, cloud models variable
- **Offline Play:** Cloud requires internet, local works offline
- **Character Uniqueness:** Local per-character adapters, cloud might share models

**Strategic Question:** Do you optimize for quality (GPT-4), cost (local open-source), or accessibility (cloud-optional)?

**Recommendation Path:**
- Start with Mistral 7B (balance of quality and compatibility)
- Support multiple models (pluggable architecture)
- Let users choose based on their hardware

---

### Decision 2: LoRA Configuration (Rank and Alpha)
**Question:** How big should character adapters be?

**LoRA Rank Options:**
- **r=8** (smallest, 5-10MB adapters)
  - Minimal adaptation, might not capture learning
- **r=16** (small-medium, 10-20MB adapters)
  - Good balance, should capture most learning
- **r=32** (medium, 20-40MB adapters)
  - Better fidelity, more learning capacity
- **r=64** (large, 40-100MB adapters)
  - Maximum fidelity, close to full fine-tuning

**LoRA Alpha Options:**
- Standard guidance: alpha = r (e.g., r=16, alpha=16)
- Can tune higher for more LLM influence
- Can tune lower for more base model stability

**Implications:**
- **Training Time:** Higher rank = longer training
- **Model Size:** Rank directly affects adapter size
- **Learning Capacity:** Higher rank learns more
- **Personality Preservation:** Lower rank preserves base model better
- **Computational Cost:** Higher rank = more memory during training

**Strategic Question:** Prioritize character individuality (high rank) or model stability (low rank)?

**Recommendation Path:**
- Start with r=16 (proven in similar systems)
- Test r=8 and r=32 to find optimal
- Allow experimentation, document results

---

### Decision 3: Training Data Requirements (Minimum and Threshold)
**Question:** How many decisions needed before training makes sense?

**Threshold Options:**
- **50 decisions:** Train early, might be noisy
- **100 decisions:** Current default, good compromise
- **200 decisions:** Wait longer, better learning
- **250 decisions:** Ensure statistical significance
- **"Whenever player wants":** Player controls training

**Additional Thresholds:**
- Minimum teaching moments for training: 5? 10? 20?
- Time-based trigger: Train weekly regardless of decisions?
- Manual override: Always allow player to request training?

**Implications:**
- **Learning Speed:** Lower threshold = faster learning
- **Data Quality:** Higher threshold = more stable learning
- **Player Agency:** Manual control = player choice
- **Computational Load:** Fewer trainings with high threshold
- **Player Frustration:** Long wait might frustrate players

**Strategic Question:** Trust in data quality (high threshold) or quick feedback (low threshold)?

**Recommendation Path:**
- Start with 100 decisions OR 10 teaching moments
- Add manual trigger option
- Monitor and adjust based on results

---

### Decision 4: Training Timing (When Does Learning Happen?)
**Question:** When should the system train characters?

**Options:**
1. **Between Sessions** (current plan)
   - After session ends, training starts
   - Character unavailable 15-30 minutes
   - Players understand delay

2. **Overnight** (asynchronous)
   - Training happens in background after everyone logs off
   - Character ready for next session
   - Requires scheduling

3. **On-Demand** (player controlled)
   - Player explicitly requests training
   - Could train mid-campaign if desired
   - Maximum player agency

4. **During Long Rests** (in-world)
   - Characters train while party rests
   - Immersive, integrated into story
   - Requires careful implementation

5. **Continuous** (passive)
   - Training happens in background continuously
   - Character never unavailable
   - Might not fit narrative

**Implications:**
- **Player Experience:** Between sessions least intrusive
- **Narrative Fit:** Long rests most immersive
- **Player Agency:** On-demand most control
- **Technical Complexity:** Overnight/continuous harder to implement
- **Predictability:** On-demand most predictable

**Strategic Question:** Prioritize immersion (in-world) or simplicity (between sessions)?

**Recommendation Path:**
- Start with between sessions (simplest)
- Add optional in-world narrative (long rests)
- Later: add overnight async training

---

### Decision 5: Hyperparameter Strategy (Per-Character vs. Global)
**Question:** Should each character have custom hyperparameters or use global defaults?

**Options:**
1. **Global Defaults**
   - All characters use same learning rate, batch size, LoRA rank
   - Simplest implementation
   - Might suboptimal for some characters

2. **Character-Type Defaults**
   - Warriors get different hyperparameters than wizards
   - Reflects different learning needs
   - Moderate complexity

3. **Learned Hyperparameters**
   - System determines optimal hyperparameters per character
   - Most sophisticated
   - Requires meta-learning infrastructure

4. **User-Configurable**
   - DMs/players can set hyperparameters
   - Maximum control
   - Needs good UI/docs

5. **Hybrid** (recommended)
   - Defaults for most characters
   - Allow users to override if desired
   - Simple + flexible

**Implications:**
- **Implementation Time:** Global fastest, learned most complex
- **Learning Quality:** Learned best, global acceptable
- **User Control:** User-configurable most agency
- **Maintenance:** Global easiest, learned hardest
- **Debuggability:** Global easiest to debug, learned hardest

**Strategic Question:** Optimize for simplicity or performance?

**Recommendation Path:**
- Start with global defaults
- Add character-type customization if time permits
- Leave room for learned hyperparameters as future phase

---

## Tier 2: Important but Can Be Decided Later

### Decision 6: Personality Preservation Mechanism
**Question:** How do we ensure training preserves character personality?

**Approaches:**
1. **Constitutional AI** - Add constraints about personality to training
2. **Value Alignment** - Enforce core character values
3. **Validation Check** - Test post-training to detect drift
4. **Supervised Fine-Tuning** - Only allow personality-consistent training
5. **Multi-Task Learning** - Learn personality and decision-making jointly

**Impact:** Affects whether characters feel like themselves after training

---

### Decision 7: Multi-Character Party Learning
**Question:** Should characters learn from each other's experiences?

**Approaches:**
1. **Independent Learning** - Each character learns alone
2. **Shared Memory** - Characters remember party experiences
3. **Cross-Adapter Training** - Learn from each other's decisions
4. **Party-Level LoRA** - Shared adapter for party strategies
5. **Heterogeneous Learning** - Different learning rates based on role

**Impact:** Determines whether party develops group strategies

---

### Decision 8: Teaching Moment Weighting
**Question:** How much more should teaching moments be weighted than regular decisions?

**Options:** 2x, 3x, 5x, 10x, or learned weighting

**Impact:** Affects how much learning happens from failures vs. successes

---

## Tier 3: Design Flexibility (Multiple Good Answers)

### Decision 9: Escalation Threshold Adaptivity
**Question:** Should characters learn which escalation tier works best?

**Approaches:**
- Fixed thresholds (current)
- Adaptive based on success rate
- Personality-based
- Learned over time

---

### Decision 10: Training Data Curation Strategy
**Question:** How aggressive should data filtering be?

**Options:**
- Minimal: Keep everything
- Moderate: Remove clear duplicates
- Aggressive: Remove all suspicious data
- Collaborative: Let DM curate

---

## Decision Trees for Common Scenarios

### "I want learning to be fast and visible to players"
→ Base Model: GPT-4 (fast)
→ Rank: r=32 (fast learning)
→ Threshold: 50 decisions (early training)
→ Timing: Between sessions (fast feedback)
→ Hyperparameters: Global defaults (simple)

### "I want maximum cost efficiency and offline play"
→ Base Model: Mistral 7B (local)
→ Rank: r=16 (balance)
→ Threshold: 100 decisions (stable)
→ Timing: Between sessions
→ Hyperparameters: Global defaults

### "I want maximum player agency and control"
→ Base Model: User choice (pluggable)
→ Rank: User configurable
→ Threshold: Player-triggered + automatic thresholds
→ Timing: User choice (scheduled training)
→ Hyperparameters: User configurable

### "I want maximum immersion and world-building"
→ Base Model: Mistral 7B (stable)
→ Rank: r=16 (smooth learning)
→ Threshold: Teaching moments (story-driven)
→ Timing: During long rests (in-world)
→ Hyperparameters: Character-type specific

---

## How to Make These Decisions

**For Each Decision:**

1. **Understand the Trade-offs**
   - What are we optimizing for? (Speed? Quality? Cost?)
   - What are we sacrificing?
   - What are acceptable compromises?

2. **Map Implications**
   - How does this decision affect downstream components?
   - What becomes easier/harder?
   - What new decisions does this create?

3. **Find the Pivot Point**
   - What's the minimum viable version?
   - What can we add later?
   - What would be hard to change later?

4. **Document the Decision**
   - Why we chose this option
   - What trade-offs we accepted
   - When we might reconsider
   - What would trigger change

5. **Implement Flexibly**
   - Architecture should allow changing this decision
   - Use configuration, not hard-coded
   - Plan for future alternatives

---

## Master Decision Matrix

This table shows how decisions interact:

| Decision | Affects | Is Affected By |
|----------|---------|----------------|
| Base Model | Training time, quality, cost | Hardware constraints |
| LoRA Rank | Training time, adapter size, learning capacity | Base model size |
| Threshold | Learning speed, stability | Player preferences |
| Training Timing | Player experience, narrative fit | Implementation complexity |
| Hyperparameters | Learning quality, convergence | Base model, rank, data |
| Personality Preservation | Player satisfaction | All other decisions |
| Party Learning | Game dynamics | Parallel learning capabilities |
| Teaching Weights | Learning from failures | Outcome analysis quality |

---

## Recommendation: Decision-Making Process

**Phase 1: Foundational Decisions (Do Now)**
- Base model selection
- LoRA rank
- Threshold policy
- Training timing

**Phase 2: Refinement Decisions (After Phase 1)**
- Personality preservation
- Teaching moment weighting
- Party learning approach
- Hyperparameter strategy

**Phase 3: Advanced Decisions (After Phase 2)**
- Multi-character learning dynamics
- Cross-adapter training
- Escalation adaptivity
- Advanced curation strategies

This phased approach lets you make informed decisions with real data from earlier phases.
