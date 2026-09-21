# 💬 DMLog - Conversation Highlights & Design Decisions

**Key decisions, context, and rationale from development discussions.**

---

## 🎯 PROJECT VISION

**Goal:** Create AI D&D characters that learn from gameplay without manual training data creation.

**Core Philosophy:**
- Characters improve through experience (like humans)
- Learning happens during "dream cycles" (between sessions)
- No hand-crafted training data required
- Privacy-respecting (opt-in/opt-out per character)
- Cost-effective (optimized for consumer hardware)

---

## 🏗️ ARCHITECTURE DECISIONS

### **Why Three-Layer Architecture?**

**Layer 1 (Foundation):** Game mechanics, character system, basic memory
- **Rationale:** Needed solid foundation before adding intelligence

**Layer 2 (Intelligence):** Decision-making, bot types, escalation
- **Rationale:** Multiple complexity levels allow cost/quality trade-offs

**Layer 3 (Consolidation):** Memory consolidation, pattern recognition
- **Rationale:** Long-term learning requires sophisticated memory

**Phase 7 (Learning Pipeline):** Training from gameplay
- **Rationale:** Closes the loop - characters improve over time

### **Why Escalation Engine?**

**Problem:** Every decision with full LLM reasoning is expensive and slow.

**Solution:** Three-tier system:
1. **Bot:** Fast, cheap, good-enough for simple decisions
2. **Brain:** Full reasoning for complex decisions
3. **Human:** Escalate to player for critical choices

**Key Insight:** Most decisions (60-70%) can use bots, saving massive costs while maintaining quality.

### **Why LoRA Instead of Full Fine-Tuning?**

**Constraints:**
- Consumer hardware (RTX 4050, 6GB VRAM)
- Limited budget
- Need character-specific adaptations
- Fast training times

**Solution:** QLoRA (4-bit quantized LoRA)
- Uses 1/10th the memory of full fine-tuning
- Trains in minutes instead of hours
- Character-specific adapters (tiny files)
- Maintains base model quality

**Trade-off:** Slightly less powerful than full fine-tuning, but practical and affordable.

---

## 📊 PHASE 7 DESIGN DECISIONS

### **Why Log Every Decision?**

**Question:** Should we only log important decisions?

**Decision:** Log everything, filter later.

**Rationale:**
- Don't know what's important upfront
- Storage is cheap
- Can always filter/aggregate
- More data = better training
- Edge cases are valuable

**Privacy:** Per-character opt-in/opt-out controls.

### **Why Multi-Domain Reward Signals?**

**Problem:** Single reward signal loses nuance.

**Example:** "Attack misses but positions party well"
- Combat reward: Negative (missed)
- Strategic reward: Positive (positioning)
- Overall: Mixed outcome with learning value

**Solution:** 5 reward domains:
1. **Combat:** Damage, tactics, victories
2. **Social:** Relationships, persuasion, information
3. **Exploration:** Discoveries, secrets, progress
4. **Resource:** XP, gold, items
5. **Strategic:** Long-term positioning, opportunities

**Rationale:** Characters learn different types of decision-making, not just "win/lose."

### **Why Teaching Moments?**

**Insight:** Failures with high learning value > successes with low learning value.

**Example Teaching Moments:**
- "Tried diplomacy with hostile enemy" → Learn when not to negotiate
- "Used fireball in enclosed space" → Learn environmental awareness
- "Trusted suspicious NPC" → Learn character judgment

**Implementation:**
- LLM labels decisions as "teaching_moment"
- Higher training weight (2-3x)
- Prioritized in training data

**Rationale:** Learn more from mistakes than successes (if reflected on properly).

### **Why DeepSeek Over GPT-4?**

**Cost Comparison (per 1000 decisions):**
- DeepSeek: $0.40
- Claude 3.5: $5
- GPT-4: $15

**Decision:** Recommend DeepSeek, support all three.

**Rationale:**
- 40x cheaper than GPT-4
- Quality sufficient for reflection
- Allows more experimentation
- Users can upgrade if needed

### **Why Automated Fallback?**

**Problem:** What if no API key configured?

**Solution:** Automated reward calculation without LLM.

**Rationale:**
- System works without API keys
- Good for testing/development
- Cheaper for early development
- Can always add LLM reflection later

---

## 🎮 GAMEPLAY INTEGRATION DECISIONS

### **When Does Training Happen?**

**Options Considered:**
1. During gameplay (rejected - too slow)
2. After every session (rejected - too frequent)
3. When enough data collected (CHOSEN)

**Decision:** "Dream Cycle" when threshold reached.

**Thresholds:**
- Minimum 100 decisions
- Or 10 teaching moments
- Or player manually triggers

**Rationale:**
- Doesn't interrupt gameplay
- Enough data for meaningful training
- Player has control

### **How to Handle Multiple Characters?**

**Challenge:** 4 characters in a party, each learning independently.

**Solution:** Character-specific training.

**Each character:**
- Has own training data
- Own growth score
- Own LoRA adapter
- Own decision history

**Shared:**
- Base model
- Memory system
- Game state

**Rationale:** Characters develop unique personalities and skills.

### **What Happens During Training?**

**"Dream Cycle" States:**
1. **ACTIVE:** Normal gameplay
2. **DREAMING:** Collecting final data, preparing
3. **TRAINING:** Model training in progress
4. **AWAKENING:** Loading new model
5. **ACTIVE:** Resume with improved model

**During TRAINING:**
- Character unavailable for 5-30 minutes
- Show progress UI
- Can cancel and revert
- Other characters continue playing

**Rationale:** Clear state transitions, transparent process.

---

## 💾 DATA & PRIVACY DECISIONS

### **What Gets Stored?**

**For Each Decision:**
```json
{
  "situation_context": {
    "game_state": {...},
    "character_state": {...},
    "perception_data": {...}
  },
  "decision": {
    "action": "attack",
    "reasoning": "Enemy is low HP",
    "confidence": 0.85,
    "source": "bot"
  },
  "outcome": {
    "success": true,
    "immediate": "Hit for 15 damage",
    "reward_signals": [...],
    "quality_score": 0.75
  },
  "reflection": {
    "quality_label": "good",
    "improvements": [...]
  }
}
```

**Not Stored:**
- Player personal information
- Chat logs (unless explicitly enabled)
- Other players' data

### **Privacy Controls**

**Per-Character Settings:**
- `log_bot_decisions` (default: true)
- `log_brain_decisions` (default: true)
- `log_human_decisions` (default: false)
- `training_eligible` (default: true)

**Rationale:**
- Some players want privacy
- Some want to exclude human decisions
- Flexible opt-in/opt-out

### **Data Export**

**Format:** JSON (standard, portable)

**Can Export:**
- All decisions for character
- Specific sessions
- Training datasets
- Statistics

**Rationale:** Player owns their data.

---

## 🧪 TESTING DECISIONS

### **Why 100% Test Coverage?**

**Decision:** Every new module must have tests.

**Rationale:**
- ML systems are complex
- Easy to break accidentally
- Tests document expected behavior
- Confidence in changes

**Types:**
- Unit tests (70%)
- Integration tests (10%)  
- E2E tests (20%)

### **Why Integration Tests?**

**Rationale:**
- Components work alone ≠ work together
- Catch interface mismatches
- Verify data flow
- Real-world scenarios

**Example:** Decision logging → Outcome tracking → Session management
- Each works alone
- Integration test verifies full flow

---

## 🚀 PERFORMANCE DECISIONS

### **Performance Requirements**

**Why These Numbers?**
- Decision logging <1ms: Doesn't slow gameplay
- Outcome tracking <5ms: Imperceptible delay
- Query <100ms: Fast enough for UI

**Trade-offs:**
- Could be faster with caching
- Simplicity > micro-optimization
- "Fast enough" is good enough

### **Why SQLite?**

**Alternatives Considered:**
- PostgreSQL (too heavy)
- MongoDB (overkill)
- JSON files (too slow)

**Decision:** SQLite

**Rationale:**
- No server setup
- Fast enough
- Single file
- Portable
- Battle-tested

---

## 💰 COST DECISIONS

### **Target: <$5/month Per Character**

**Breakdown:**
- Gameplay LLM calls: ~$2-3
- Reflection analysis: ~$0.40 (DeepSeek)
- Training compute: ~$1 (local GPU)
- Total: ~$3.40-4.40

**Achieved By:**
- Escalation engine (bot > brain > human)
- QLoRA instead of full training
- DeepSeek for reflection
- Local GPU for training
- Efficient caching

### **Why Local Training?**

**Cloud Training Costs:**
- RunPod GPU: $0.50/hour
- Training time: 30-60 minutes
- Cost per training: $0.25-0.50
- Frequent training: $10-30/month

**Local GPU (RTX 4050):**
- One-time cost: Already owned
- Training time: 15-30 minutes
- Cost per training: Electricity (~$0.01)
- Unlimited training

**Decision:** Optimize for local GPU.

**Rationale:** Users likely have gaming PCs, leverage existing hardware.

---

## 🎨 UI/UX DECISIONS

### **Why No React/Vue?**

**Decision:** Vanilla JS + HTML

**Rationale:**
- Simpler to maintain
- No build process
- Faster load times
- Lower barrier to contribution
- Good enough for dashboard

**Future:** Can always add framework later if needed.

### **Dashboard Design Principles**

1. **Information Density:** Show relevant data quickly
2. **Progressive Disclosure:** Details on demand
3. **Actionable:** Can take actions from UI
4. **Responsive:** Works on mobile
5. **Fast:** <1s load time

---

## 🔮 FUTURE DECISIONS

### **What About Multi-Player Learning?**

**Current:** Each character learns independently.

**Future Ideas:**
- Characters learn from each other
- Party-wide strategies
- Shared memory pool
- Collaborative decision-making

**Decision:** Phase 8 or later.

**Rationale:** Solve single character first.

### **What About Transfer Learning?**

**Idea:** New character starts with knowledge from existing characters.

**Challenges:**
- Character personality preservation
- Preventing homogenization
- Balancing fresh start vs. bootstrapping

**Decision:** Phase 9 research topic.

### **What About Real-Time Training?**

**Current:** Training between sessions.

**Alternative:** Continuous training during gameplay.

**Challenges:**
- GPU contention
- Latency
- Stability

**Decision:** Maybe Phase 10 with better hardware.

---

## 🤔 OPEN QUESTIONS

### **Questions We Haven't Solved Yet:**

1. **Optimal Training Frequency**
   - After every session? Every 5 sessions? Player choice?
   - **Current thinking:** Threshold-based (100 decisions or 10 teaching moments)

2. **Character Personality Drift**
   - How to ensure character stays in-character after training?
   - **Approaches:** Constitutional AI, value alignment, periodic checks

3. **Training Data Staleness**
   - Should old decisions count less than recent ones?
   - **Idea:** Time-decay weighting, but needs testing

4. **Multi-Task Learning**
   - Train one model for all characters vs. separate models?
   - **Trade-off:** Efficiency vs. specialization

5. **Validation Metrics**
   - How to quantify "improved character"?
   - **Current:** Success rate, reward signals, player feedback

---

## 💡 KEY INSIGHTS

### **What We Learned:**

1. **Start Simple:** Working system > perfect system
2. **Iterate Fast:** Ship, test, improve
3. **User First:** Optimize for player experience, not technical elegance
4. **Measure Everything:** Can't improve what you don't measure
5. **Document Decisions:** Future you will thank you

### **What Surprised Us:**

1. **Teaching Moments:** More valuable than we expected
2. **Bot Performance:** Better than anticipated, escalates rarely
3. **Memory Usage:** QLoRA fits even better than predicted
4. **Development Speed:** Faster with clear architecture
5. **Test Value:** Caught many bugs early

---

## 🎯 DESIGN PRINCIPLES

**Core Principles That Guide All Decisions:**

1. **Player Agency:** Player always has control
2. **Transparency:** Show what system is doing
3. **Privacy:** Player owns their data
4. **Affordability:** Work on consumer hardware
5. **Reliability:** Fail gracefully, recover automatically
6. **Extensibility:** Easy to add features later
7. **Simplicity:** Simple solutions over clever ones

---

## 📝 DECISION LOG

**Timeline of Major Decisions:**

**October 2024:**
- Project start, basic architecture
- Three-layer design chosen
- Escalation engine concept

**March 2025:**
- Layer 3 consolidation implemented
- Digital twin for analysis
- Memory system refinement

**October 2025:**
- Phase 7 planning
- LoRA decision made
- DeepSeek recommendation
- Multi-domain rewards designed
- Teaching moments concept
- Dream cycle state machine

---

## 🙏 ACKNOWLEDGMENTS

**Concepts Borrowed From:**
- Constitutional AI (Anthropic)
- QLoRA paper (Dettmers et al.)
- RLHF (OpenAI)
- Curriculum learning (Various)
- Active learning (Various)

**Inspiration:**
- Westworld (HBO) - Character consciousness
- Skyrim's Radiant AI
- Dwarf Fortress learning systems
- Chess engines (AlphaZero)

---

**This document captures the "why" behind the "what."**

Use it to understand context when making future decisions!

*Last updated: October 22, 2025*
