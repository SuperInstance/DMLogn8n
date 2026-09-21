# 🚀 DMLog - Developer Onboarding Guide

**Welcome to DMLog!** This is an AI-powered D&D character system with autonomous learning capabilities.

---

## 📋 TABLE OF CONTENTS

1. [Quick Start](#quick-start)
2. [Project Overview](#project-overview)
3. [Architecture](#architecture)
4. [Current Status](#current-status)
5. [Development Setup](#development-setup)
6. [Testing](#testing)
7. [Key Concepts](#key-concepts)
8. [Next Phases](#next-phases)
9. [Contributing](#contributing)

---

## 🎯 QUICK START

```bash
# 1. Clone repository
git clone https://github.com/ctothed/DMLog.git
cd DMLog

# 2. Set up Python environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
cd backend
pip install -r requirements.txt

# 4. Run tests
python test_training_data_collector.py

# 5. Start development server (when ready)
python api_server.py
```

**That's it!** You're ready to explore the codebase.

---

## 📖 PROJECT OVERVIEW

**DMLog** is an AI D&D system where characters learn from gameplay experiences through:
- **Automated decision logging** (every action captured)
- **Multi-domain reward signals** (combat, social, exploration, resource, strategic)
- **Character evolution tracking** (growth scores, learning opportunities)
- **LLM reflection** (GPT-4/Claude/DeepSeek analysis)
- **LoRA fine-tuning** (character-specific model improvements)

**Goal:** Create AI characters that improve through gameplay without manual training data creation.

---

## 🏗️ ARCHITECTURE

### **Layer 1: Foundation** ✅ Complete
- Character system with traits, stats, inventory
- Game mechanics (combat, skills, dice rolling)
- Memory system with episodic/semantic storage

### **Layer 2: Intelligence** ✅ Complete
- Character Brain (decision-making core)
- Bot types: Mechanical, Combat, Social
- Escalation engine (bot → brain → human routing)
- Model routing (local/cloud LLMs)

### **Layer 3: Consolidation** ✅ Complete
- Advanced memory consolidation
- Long-term pattern recognition
- Cross-session learning
- Digital Twin for analysis

### **Phase 7: Learning Pipeline** 🟡 20% Complete
**THIS IS WHERE WE ARE NOW!**

```
Gameplay → Escalation → Training Data → Outcomes → Sessions → Reflection → Training
            Engine       Collector       Tracker     Manager     Pipeline      LoRA
            ✅           ✅              ✅          ✅          ✅ (framework)  ⬜
```

**What's Built:**
- ✅ Decision logging with privacy controls
- ✅ Multi-domain reward calculation
- ✅ Character evolution tracking
- ✅ Session quality scoring
- ✅ LLM reflection framework
- ✅ Unified API client (GPT-4/Claude/DeepSeek)

**What's Next:**
- ⬜ Data curation pipeline
- ⬜ Character dashboard UI
- ⬜ QLoRA training infrastructure
- ⬜ Dream cycle integration

---

## 📊 CURRENT STATUS

**Phase 7 Progress: 4 of 19 tasks (20%)**

### ✅ Completed Tasks:

**Task 7.1.1: Decision Logger** (850 lines)
- SQLite-based decision storage
- Privacy controls per character
- Session tracking
- Export to JSON
- Query performance <100ms

**Task 7.1.2: Outcome Tracker** (700 lines)
- 5 reward domains (combat, social, exploration, resource, strategic)
- Temporal correlation (immediate/short/long-term)
- Causal chain tracking
- Quality analysis with confidence scores
- Performance <5ms per outcome

**Task 7.1.3: Session Manager** (600 lines)
- Character growth scores (0-1)
- Teaching moment detection
- Multi-character coordination
- Training opportunity identification

**Task 7.2.1: Reflection Pipeline** (550 lines + 400 lines API)
- LLM-based decision analysis (framework ready)
- Quality labeling system
- Unified API client for GPT-4/Claude/DeepSeek
- Cost tracking and rate limiting
- Automated fallback analysis

### ⬜ Next Tasks (See [NEXT_PHASES.md](NEXT_PHASES.md)):
- Task 7.2.2: Data Curation (2-3 days)
- Task 7.2.3: Character Dashboard (1-2 days)
- Task 7.3.1: QLoRA Training (5-7 days)

---

## 💻 DEVELOPMENT SETUP

### **Prerequisites:**
- Python 3.10+ (required)
- 8GB+ RAM
- GPU optional but recommended (RTX 4050+ for training)
- Git configured with GitHub

### **Environment Setup:**

```bash
# 1. Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Create .env file (for API keys - optional)
cp ../.env.example .env
# Edit .env with your API keys if using reflection pipeline
```

### **API Keys (Optional - For Reflection):**

Create `.env` file in root directory:

```env
# Choose ONE provider:

# DeepSeek (RECOMMENDED - cheapest!)
DEEPSEEK_API_KEY=your_key_here

# OR OpenAI
OPENAI_API_KEY=your_key_here

# OR Anthropic
ANTHROPIC_API_KEY=your_key_here
```

**Cost estimates (per 1000 decisions):**
- DeepSeek: ~$0.40 ⭐ (RECOMMENDED)
- Claude 3.5: ~$5
- GPT-4: ~$15

### **Database Setup:**

The system automatically creates SQLite databases:
- `data/decisions.db` - Training data storage
- `data/memory.db` - Character memory (if using memory system)

No manual setup needed! Databases are created on first run.

---

## 🧪 TESTING

### **Run All Tests:**

```bash
cd backend

# Individual test suites
python test_training_data_collector.py  # Decision logging (14 tests)
python test_outcome_tracker.py          # Reward signals (16 tests)
python test_session_manager.py          # Session tracking (15 tests)

# Integration tests
python test_integration_training_data.py       # 4 integration tests
python test_integration_outcome_tracker.py     # 6 integration tests

# Quick verification
python test_task_7_1_1.py  # Runs all + creates sample data
```

**Expected output:** All tests passing ✅

### **Test Coverage:**
- 60 unit tests
- 10 integration tests
- 100% coverage of Phase 7 code
- All tests passing

---

## 🔑 KEY CONCEPTS

### **1. Decision Logging**

Every gameplay decision is captured with:
- **Context:** Game state, character state, perception
- **Decision:** Action, reasoning, confidence, source (bot/brain/human)
- **Outcome:** Success/failure, rewards, quality score
- **Reflection:** LLM analysis (optional)

**Example:**
```python
from training_data_collector import TrainingDataCollector

collector = TrainingDataCollector()
session_id = collector.start_session(character_ids=["thorin"])

decision_id = collector.log_decision(
    character_id="thorin",
    situation_context={
        "game_state": {"turn": 5, "location": "Cave"},
        "character_state": {"hp": 35, "max_hp": 50}
    },
    decision={
        "action": "attack",
        "reasoning": "Enemy is low HP",
        "confidence": 0.85,
        "source": "bot"
    }
)

collector.update_outcome(
    decision_id=decision_id,
    outcome={"immediate": "Hit for 15 damage, enemy defeated"},
    success=True
)
```

### **2. Reward Signals**

Each outcome is analyzed across 5 domains:
- **Combat:** Damage, tactics, victories, party safety
- **Social:** Relationships, persuasion, information gathering
- **Exploration:** Discoveries, secrets, progress
- **Resource:** XP, gold, items acquired
- **Strategic:** Positioning, opportunities, long-term goals

**Example:**
```python
# Outcome automatically calculates rewards:
{
  "reward_signals": [
    {"domain": "combat", "value": 0.75, "confidence": 0.8},
    {"domain": "resource", "value": 0.5, "confidence": 0.9}
  ],
  "aggregate_reward": 0.625,
  "quality_analysis": {"quality_score": 0.68}
}
```

### **3. Character Evolution**

Characters track growth through:
- **Growth Score (0-1):** Overall improvement metric
- **Success Rate:** % of successful decisions
- **Learning Opportunities:** Number of teaching moments
- **Domain Performance:** Success by reward domain

**Example:**
```python
# Session summary shows character evolution
summary = collector.end_session()
# {
#   "duration_seconds": 1800,
#   "characters_improved": ["thorin"],
#   "avg_growth_score": 0.72,
#   "teaching_moments": 5
# }
```

### **4. Reflection Pipeline**

LLM analyzes decisions to provide:
- **Quality Labels:** excellent → good → acceptable → poor → bad → teaching_moment
- **What Worked:** Strengths identified
- **What Failed:** Weaknesses identified
- **Improvements:** Actionable suggestions
- **Teaching Value:** Learning potential (0-1)

**Example:**
```python
from reflection_pipeline import ReflectionPipeline
from llm_api_integration import get_config_preset, LLMAPIClient

# Configure LLM
config = get_config_preset("deepseek", os.getenv("DEEPSEEK_API_KEY"))
client = LLMAPIClient(config)
pipeline = ReflectionPipeline(llm_client=client)

# Reflect on decision
reflection = await pipeline.reflect_on_decision(
    decision_data, outcome_data, context
)
# reflection.quality_label = "teaching_moment"
# reflection.teaching_value = 0.85
# reflection.improvement_suggestions = [...]
```

### **5. Escalation Engine**

Routes decisions through complexity levels:
- **Bot:** Fast, cached, mechanical decisions
- **Brain:** Full LLM reasoning for complex situations
- **Human:** Escalate to player for critical choices

**When to escalate:**
- Uncertainty > threshold
- Novel situations
- High stakes
- Moral dilemmas

---

## 📅 NEXT PHASES

See **[NEXT_PHASES.md](NEXT_PHASES.md)** for complete roadmap.

### **Week 2: Reflection & Curation** (Current)

**Task 7.2.2: Data Curation** (2-3 days)
- Quality filtering
- Balance checking (success/failure ratio)
- Duplicate removal
- Data augmentation
- Training set generation

**Task 7.2.3: Character Dashboard** (1-2 days)
- Web UI for monitoring
- Training progress visualization
- Decision review interface
- Session analytics

### **Week 3: Training Engine**

**Task 7.3.1: QLoRA Training Infrastructure** (5-7 days)
- 4-bit quantization (QLoRA)
- RTX 4050 optimization
- Character-specific adapters
- Training loop with validation
- Checkpoint management

**Task 7.3.2: Hyperparameter Optimization** (2-3 days)
- Learning rate tuning
- Batch size optimization
- LoRA rank/alpha tuning
- Early stopping criteria

**Task 7.3.3: Training Automation** (2 days)
- Automatic training triggers
- Batch processing
- Progress monitoring
- Error handling

### **Week 4: Quality & Integration**

**Tasks 7.4-7.6:** Integration, validation, testing

---

## 🤝 CONTRIBUTING

### **Code Style:**
- Python 3.10+ syntax
- Type hints where helpful
- Docstrings for public methods
- Tests for new features

### **Branch Strategy:**
- `main` - Production-ready code
- `dev` - Development branch
- Feature branches: `feature/task-name`

### **Commit Messages:**
```
feat: Add data curation pipeline
fix: Resolve session tracking bug
docs: Update developer guide
test: Add integration tests for reflection
```

### **Pull Requests:**
1. Create feature branch
2. Write code + tests
3. Run all tests
4. Update documentation
5. Submit PR with description

---

## 📚 KEY DOCUMENTATION

**Essential Reading:**
- [README.md](README.md) - Project overview
- [START_HERE.md](START_HERE.md) - Quick intro
- [NEXT_PHASES.md](NEXT_PHASES.md) - Complete roadmap
- [CONVERSATION_HIGHLIGHTS.md](CONVERSATION_HIGHLIGHTS.md) - Key decisions

**Architecture:**
- [LAYER3_ARCHITECTURE.md](LAYER3_ARCHITECTURE.md) - Layer 3 design
- [PHASE_7_ARCHITECTURE_DESIGN.md](docs/PHASE_7_ARCHITECTURE_DESIGN.md) - Phase 7 design

**Phase 7 Completion:**
- [TASK_7_1_1_COMPLETE.md](docs/TASK_7_1_1_COMPLETE.md) - Decision Logger
- [TASK_7_1_2_COMPLETE.md](docs/TASK_7_1_2_COMPLETE.md) - Outcome Tracker
- [TASK_7_1_3_COMPLETE.md](docs/TASK_7_1_3_COMPLETE.md) - Session Manager

**Quick Reference:**
- [QUICK_REFERENCE_7_1_1.md](docs/QUICK_REFERENCE_7_1_1.md) - Essential commands

---

## 🆘 HELP & SUPPORT

**Common Issues:**

**Issue:** Tests fail with "module not found"
**Solution:** 
```bash
pip install -r backend/requirements.txt
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Issue:** Database locked error
**Solution:** Close all Python processes and delete `.db-journal` files

**Issue:** API rate limits exceeded
**Solution:** Increase `max_requests_per_minute` in LLMConfig or add delays

**Issue:** Out of memory during training (future)
**Solution:** Reduce batch size, use 4-bit quantization, or train on smaller subsets

---

## 🎯 YOUR FIRST TASK

**As a new developer, here's what to do first:**

1. **✅ Run tests** - Verify everything works
   ```bash
   cd backend
   python test_task_7_1_1.py
   ```

2. **📖 Read key docs** - Understand the system
   - README.md
   - NEXT_PHASES.md
   - This file (ONBOARDING.md)

3. **🔍 Explore code** - Start with these files:
   - `backend/training_data_collector.py` - Decision logging
   - `backend/outcome_tracker.py` - Reward signals
   - `backend/escalation_engine.py` - Decision routing

4. **🎯 Pick a task** - See NEXT_PHASES.md for:
   - Task 7.2.2 (Data Curation) - Good first task!
   - Task 7.2.3 (Dashboard) - If you prefer UI work
   - Task 7.3.1 (Training) - If you want the challenge

5. **💬 Ask questions** - Review CONVERSATION_HIGHLIGHTS.md for context

---

## 📊 PROJECT STATISTICS

**Current Stats:**
- **Code:** 6,500+ lines (production + tests)
- **Tests:** 70 tests, 100% passing
- **Documentation:** 35,000+ words
- **Modules:** 30+ Python files
- **Phase 7 Progress:** 20% complete

**Performance:**
- Decision logging: <1ms
- Outcome tracking: <5ms
- Query performance: <100ms
- Zero gameplay impact ✅

---

## 🎉 WELCOME ABOARD!

You're joining at an exciting time! The data foundation is complete, and we're ready to build the training engine. Your contributions will directly impact how AI characters learn and improve.

**Questions?** Check [CONVERSATION_HIGHLIGHTS.md](CONVERSATION_HIGHLIGHTS.md) for key design decisions and context.

**Ready to code?** See [NEXT_PHASES.md](NEXT_PHASES.md) for available tasks!

---

*Last updated: October 22, 2025*  
*Phase 7 progress: 20% complete*  
*Next milestone: Data Curation Pipeline*
