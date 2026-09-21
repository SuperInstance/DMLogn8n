# 🚀 DMLog - Next Phases Development Guide

**Complete roadmap for completing Phase 7 and beyond.**

---

## 📊 CURRENT STATUS

**Phase 7 Progress: 4 of 19 tasks complete (20%)**

✅ **Week 1 Complete:** Data Foundation
- Task 7.1.1: Decision Logger
- Task 7.1.2: Outcome Tracker  
- Task 7.1.3: Session Manager

🟡 **Week 2 In Progress:** Reflection & Curation
- Task 7.2.1: Reflection Pipeline (framework done)
- Task 7.2.2: Data Curation ← **YOU ARE HERE**
- Task 7.2.3: Character Dashboard

⬜ **Week 3 Not Started:** Training Engine  
⬜ **Week 4 Not Started:** Quality & Integration

---

## 🎯 IMMEDIATE NEXT TASKS

### **Task 7.2.2: Data Curation Pipeline** ⭐ START HERE

**Time Estimate:** 2-3 days  
**Priority:** HIGH  
**Difficulty:** Medium

**What it does:**
Creates a pipeline to filter, balance, and prepare training data from logged decisions.

**Requirements:**
1. **Quality Filtering**
   - Remove low-confidence decisions
   - Filter out duplicate/near-duplicate decisions
   - Keep only training-eligible decisions
   - Apply minimum quality thresholds

2. **Balance Checking**
   - Ensure good mix of success/failure examples
   - Balance across decision types (combat, social, exploration)
   - Prevent over-representation of any single pattern
   - Target: 60-70% success, 30-40% failure

3. **Data Augmentation** (optional but recommended)
   - Paraphrase similar decisions
   - Generate synthetic teaching moments
   - Expand underrepresented categories

4. **Training Set Generation**
   - Split into train/validation/test (80/10/10)
   - Export in format for LoRA training
   - Generate metadata file

**Files to create:**
```
backend/data_curator.py          # Main curation pipeline
backend/test_data_curator.py     # Unit tests
backend/data_augmentation.py     # Augmentation utilities (optional)
```

**Code structure:**
```python
class DataCurator:
    def __init__(self, training_data_collector):
        self.collector = training_data_collector
        self.filters = []
        self.stats = {}
    
    def add_filter(self, filter_fn):
        """Add quality filter"""
        pass
    
    def filter_decisions(self, decisions):
        """Apply all filters"""
        pass
    
    def check_balance(self, decisions):
        """Check if dataset is balanced"""
        pass
    
    def balance_dataset(self, decisions, target_ratios):
        """Undersample/oversample to achieve balance"""
        pass
    
    def create_training_set(self, character_id, output_path):
        """Generate training set for character"""
        pass
    
    def export_for_training(self, decisions, output_path):
        """Export in LoRA training format"""
        pass
```

**Success criteria:**
- [ ] Can filter decisions by quality threshold
- [ ] Detects and removes duplicates
- [ ] Balances success/failure ratios
- [ ] Exports to JSON in correct format
- [ ] Generates train/val/test splits
- [ ] All tests passing
- [ ] Performance: <1 second for 1000 decisions

**Integration points:**
- Reads from `TrainingDataCollector`
- Feeds into Task 7.3.1 (LoRA Training)

---

### **Task 7.2.3: Character Dashboard**

**Time Estimate:** 1-2 days  
**Priority:** MEDIUM  
**Difficulty:** Medium  
**Can be done in parallel with 7.2.2**

**What it does:**
Web-based UI for monitoring character learning progress and reviewing decisions.

**Requirements:**
1. **Dashboard Views**
   - Character overview (growth score, success rate, sessions)
   - Recent decisions list with filters
   - Session timeline
   - Training progress (when Task 7.3 is done)

2. **Decision Review Interface**
   - View individual decisions with full context
   - See reward signals breakdown
   - Review LLM reflection (if available)
   - Mark as good/bad training example

3. **Analytics**
   - Success rate over time
   - Reward signals by domain (charts)
   - Teaching moments identified
   - Training opportunities

4. **Session Management**
   - Start/end sessions from UI
   - View session summaries
   - Export session data

**Files to create:**
```
backend/dashboard_api.py         # FastAPI routes for dashboard
frontend/dashboard.html          # Single-page dashboard
frontend/static/dashboard.js     # Dashboard logic
frontend/static/dashboard.css    # Styling
```

**Tech stack:**
- Backend: FastAPI (extend existing `api_server.py`)
- Frontend: Vanilla JS + Chart.js for graphs
- No React/Vue needed - keep it simple!

**API endpoints to add:**
```python
# Dashboard API
GET  /api/characters/{character_id}/dashboard
GET  /api/characters/{character_id}/decisions?page=1&limit=20
GET  /api/characters/{character_id}/stats
GET  /api/sessions/{session_id}/summary
POST /api/sessions/start
POST /api/sessions/end
```

**Success criteria:**
- [ ] Dashboard loads and displays character stats
- [ ] Can view list of decisions with pagination
- [ ] Shows graphs of success rate over time
- [ ] Displays reward signals breakdown
- [ ] Can start/end sessions from UI
- [ ] Responsive design (works on mobile)

**Integration points:**
- Uses `TrainingDataCollector` API
- Uses `SessionManager` for stats
- Uses `OutcomeTracker` for rewards

---

## 🏗️ WEEK 3: TRAINING ENGINE

### **Task 7.3.1: QLoRA Training Infrastructure** 🔥 CRITICAL

**Time Estimate:** 5-7 days  
**Priority:** CRITICAL  
**Difficulty:** HARD

**What it does:**
Implements 4-bit quantized LoRA training optimized for RTX 4050 (6GB VRAM).

**Requirements:**

1. **Model Setup**
   - Load base model in 4-bit (bitsandbytes)
   - Configure LoRA adapters (rank, alpha, target modules)
   - Prepare for character-specific training

2. **Training Pipeline**
   - Data loading from curated dataset
   - Training loop with gradient accumulation
   - Validation every N steps
   - Loss calculation and monitoring

3. **Memory Optimization**
   - 4-bit quantization (QLoRA)
   - Gradient checkpointing
   - Optimal batch size for 6GB VRAM
   - Mixed precision training

4. **Checkpoint Management**
   - Save best model based on validation loss
   - Resume from checkpoint
   - Export trained adapters
   - Merge adapters with base model (optional)

5. **Integration**
   - Load trained models in `character_brain.py`
   - A/B testing (original vs trained)
   - Performance comparison

**Files to create:**
```
backend/lora_trainer.py          # Main training logic
backend/training_config.py       # Hyperparameters
backend/model_utils.py           # Model loading utilities
backend/training_dataset.py      # Custom dataset class
backend/test_lora_trainer.py     # Unit tests
```

**Code structure:**
```python
class LoRATrainer:
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.train_dataset = None
        self.val_dataset = None
    
    def load_base_model(self, model_name):
        """Load base model in 4-bit"""
        # Use bitsandbytes for quantization
        pass
    
    def prepare_lora(self, lora_config):
        """Configure LoRA adapters"""
        # Use PEFT library
        pass
    
    def load_training_data(self, data_path):
        """Load curated training data"""
        pass
    
    def train(self, num_epochs, output_dir):
        """Main training loop"""
        pass
    
    def evaluate(self):
        """Run validation"""
        pass
    
    def save_checkpoint(self, path):
        """Save model checkpoint"""
        pass
    
    def merge_and_save(self, output_path):
        """Merge LoRA adapters with base model"""
        pass
```

**Hyperparameters to tune:**
```python
@dataclass
class TrainingConfig:
    # Model
    base_model: str = "meta-llama/Llama-2-7b-hf"  # Or smaller if needed
    load_in_4bit: bool = True
    
    # LoRA
    lora_r: int = 8              # Rank
    lora_alpha: int = 32         # Scaling
    lora_dropout: float = 0.05
    target_modules: List[str] = ["q_proj", "v_proj"]
    
    # Training
    learning_rate: float = 2e-4
    batch_size: int = 1          # Small for 6GB VRAM
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    warmup_steps: int = 100
    
    # Optimization
    gradient_checkpointing: bool = True
    fp16: bool = False           # Use bf16 if supported
    bf16: bool = True
```

**Success criteria:**
- [ ] Loads model in 4-bit successfully
- [ ] Fits in 6GB VRAM (RTX 4050)
- [ ] Completes training on 100 decisions in <30 min
- [ ] Validation loss decreases over epochs
- [ ] Can save and load checkpoints
- [ ] Trained model integrates with `character_brain.py`
- [ ] Shows improvement on validation set

**Key libraries:**
```bash
pip install transformers>=4.35.0
pip install peft>=0.7.0
pip install bitsandbytes>=0.41.0
pip install accelerate>=0.24.0
pip install datasets>=2.15.0
```

**Resources:**
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [Efficient Training Guide](https://huggingface.co/docs/transformers/perf_train_gpu_one)

---

### **Task 7.3.2: Hyperparameter Optimization**

**Time Estimate:** 2-3 days  
**Priority:** MEDIUM  
**Difficulty:** MEDIUM

**What it does:**
Automates finding optimal hyperparameters for training.

**Requirements:**
1. Parameter search space definition
2. Automatic training runs with different configs
3. Validation metric tracking
4. Best config selection

**Files to create:**
```
backend/hyperparam_search.py     # Search logic
backend/search_configs.py        # Config definitions
```

**Success criteria:**
- [ ] Can run automated hyperparameter search
- [ ] Tracks validation metrics for each config
- [ ] Selects best configuration automatically
- [ ] Saves search results to JSON

---

### **Task 7.3.3: Training Automation**

**Time Estimate:** 2 days  
**Priority:** LOW  
**Difficulty:** EASY

**What it does:**
Automates training triggers and batch processing.

**Requirements:**
1. Automatic training when enough data collected
2. Batch training for multiple characters
3. Progress monitoring
4. Error handling and retries

**Files to create:**
```
backend/training_scheduler.py    # Automation logic
backend/training_monitor.py      # Progress tracking
```

**Success criteria:**
- [ ] Automatically triggers training when threshold reached
- [ ] Handles training failures gracefully
- [ ] Monitors training progress
- [ ] Sends notifications on completion

---

## 🎨 WEEK 4: QUALITY & INTEGRATION

### **Task 7.4.1: Dream Cycle State Machine**

**Time Estimate:** 2 days  
**Priority:** HIGH  
**Difficulty:** MEDIUM

**What it does:**
Implements "dream cycle" - the transition from active play to training.

**Requirements:**
1. State machine for character lifecycle
2. Transition triggers (session end, data threshold)
3. Training initiation
4. Model loading after training

**States:**
```
ACTIVE → DREAMING → TRAINING → AWAKENING → ACTIVE
  ↑                                          |
  └──────────────────────────────────────────┘
```

**Files to create:**
```
backend/dream_cycle.py           # State machine
backend/test_dream_cycle.py      # Tests
```

**Success criteria:**
- [ ] Character transitions through states correctly
- [ ] Training triggers automatically
- [ ] Model updates after training
- [ ] Maintains game state during transition

---

### **Task 7.4.2: Intermission UI**

**Time Estimate:** 1 day  
**Priority:** LOW  
**Difficulty:** EASY

**What it does:**
Shows UI during character "dreaming" (training).

**Requirements:**
1. Training progress display
2. Character reflection visualization
3. Estimated time remaining
4. Cancel/resume options

**Success criteria:**
- [ ] Shows training progress bar
- [ ] Displays reflection insights
- [ ] Estimates completion time
- [ ] Allows cancellation

---

### **Task 7.5.1: Validation System**

**Time Estimate:** 2 days  
**Priority:** HIGH  
**Difficulty:** MEDIUM

**What it does:**
Validates that trained models are actually better.

**Requirements:**
1. Performance metrics (accuracy, coherence, etc.)
2. A/B testing framework
3. Automatic rollback if worse
4. Validation dataset management

**Files to create:**
```
backend/model_validator.py       # Validation logic
backend/ab_testing.py            # A/B test framework
backend/test_model_validator.py  # Tests
```

**Success criteria:**
- [ ] Compares trained vs baseline models
- [ ] Calculates improvement metrics
- [ ] Automatically rolls back if worse
- [ ] Tracks validation history

---

### **Task 7.5.2: Constitutional AI Integration**

**Time Estimate:** 2 days  
**Priority:** MEDIUM  
**Difficulty:** MEDIUM

**What it does:**
Ensures trained models stay aligned with character values.

**Requirements:**
1. Value alignment checking
2. Red-line detection (harmful outputs)
3. Automatic filtering
4. Alignment fine-tuning

**Success criteria:**
- [ ] Detects value misalignment
- [ ] Prevents harmful outputs
- [ ] Maintains character personality
- [ ] Logs alignment issues

---

### **Task 7.5.3: Rollback Mechanism**

**Time Estimate:** 1 day  
**Priority:** HIGH  
**Difficulty:** EASY

**What it does:**
Allows reverting to previous model version.

**Requirements:**
1. Model versioning
2. One-click rollback
3. Version comparison
4. Automatic fallback on errors

**Success criteria:**
- [ ] Stores multiple model versions
- [ ] Can rollback instantly
- [ ] Preserves training history
- [ ] Auto-reverts on validation failure

---

### **Task 7.6.1: Full Integration Testing**

**Time Estimate:** 2 days  
**Priority:** CRITICAL  
**Difficulty:** MEDIUM

**What it does:**
End-to-end testing of complete pipeline.

**Requirements:**
1. Full gameplay → training → improvement flow
2. Multi-character scenarios
3. Performance testing
4. Edge case handling

**Files to create:**
```
backend/test_e2e_training.py     # End-to-end tests
backend/test_performance.py      # Performance tests
```

**Success criteria:**
- [ ] Complete flow works end-to-end
- [ ] Multiple characters train simultaneously
- [ ] Performance meets requirements
- [ ] All edge cases handled

---

### **Task 7.6.2: Documentation & Examples**

**Time Estimate:** 1 day  
**Priority:** MEDIUM  
**Difficulty:** EASY

**What it does:**
Complete documentation for Phase 7.

**Requirements:**
1. API documentation
2. Usage examples
3. Tutorial notebook
4. Troubleshooting guide

**Files to create:**
```
docs/API_REFERENCE.md            # Complete API docs
docs/TUTORIAL.ipynb              # Jupyter tutorial
docs/TROUBLESHOOTING.md          # Common issues
```

**Success criteria:**
- [ ] All APIs documented
- [ ] Working examples provided
- [ ] Tutorial runs successfully
- [ ] Troubleshooting covers common issues

---

### **Task 7.6.3: Performance Optimization**

**Time Estimate:** 2 days  
**Priority:** LOW  
**Difficulty:** HARD

**What it does:**
Optimizes performance of complete system.

**Requirements:**
1. Profiling and bottleneck identification
2. Database query optimization
3. Caching strategies
4. Memory optimization

**Success criteria:**
- [ ] Decision logging <1ms
- [ ] Outcome tracking <5ms
- [ ] Training completes in reasonable time
- [ ] Memory usage optimized

---

## 📋 TASK DEPENDENCIES

```
Week 1 (✅ Complete)
├── 7.1.1 Decision Logger
├── 7.1.2 Outcome Tracker
└── 7.1.3 Session Manager

Week 2 (🟡 In Progress)
├── 7.2.1 Reflection Pipeline (✅ Framework)
├── 7.2.2 Data Curation ← START HERE
│   └── Depends on: 7.1.1, 7.1.2
└── 7.2.3 Character Dashboard
    └── Depends on: 7.1.1, 7.1.2, 7.1.3

Week 3 (⬜ Not Started)
├── 7.3.1 LoRA Training ← CRITICAL PATH
│   └── Depends on: 7.2.2
├── 7.3.2 Hyperparameter Optimization
│   └── Depends on: 7.3.1
└── 7.3.3 Training Automation
    └── Depends on: 7.3.1

Week 4 (⬜ Not Started)
├── 7.4.1 Dream Cycle
│   └── Depends on: 7.3.1
├── 7.4.2 Intermission UI
│   └── Depends on: 7.4.1
├── 7.5.1 Validation System
│   └── Depends on: 7.3.1
├── 7.5.2 Constitutional AI
│   └── Depends on: 7.5.1
├── 7.5.3 Rollback Mechanism
│   └── Depends on: 7.5.1
├── 7.6.1 Integration Testing
│   └── Depends on: ALL previous
├── 7.6.2 Documentation
│   └── Depends on: ALL previous
└── 7.6.3 Performance Optimization
    └── Depends on: ALL previous
```

---

## 🎯 RECOMMENDED WORK ORDER

**For a single developer:**

1. **Task 7.2.2** - Data Curation (2-3 days)
2. **Task 7.3.1** - LoRA Training (5-7 days) ⭐ MOST IMPORTANT
3. **Task 7.4.1** - Dream Cycle (2 days)
4. **Task 7.5.1** - Validation System (2 days)
5. **Task 7.5.3** - Rollback Mechanism (1 day)
6. **Task 7.2.3** - Character Dashboard (1-2 days)
7. **Task 7.3.2** - Hyperparameter Optimization (2-3 days)
8. **Task 7.6.1** - Integration Testing (2 days)
9. Remaining tasks as needed

**For multiple developers:**

**Developer 1 (ML focus):**
- 7.3.1 LoRA Training
- 7.3.2 Hyperparameter Optimization
- 7.5.1 Validation System
- 7.5.2 Constitutional AI

**Developer 2 (Backend focus):**
- 7.2.2 Data Curation
- 7.4.1 Dream Cycle
- 7.5.3 Rollback Mechanism
- 7.3.3 Training Automation

**Developer 3 (Frontend focus):**
- 7.2.3 Character Dashboard
- 7.4.2 Intermission UI
- 7.6.2 Documentation
- UI polish

---

## 💡 TIPS & BEST PRACTICES

### **Development Tips:**

1. **Start Small:** Test with 100 decisions before scaling to thousands
2. **GPU Management:** Use `torch.cuda.empty_cache()` liberally
3. **Save Often:** Checkpoint frequently during training
4. **Monitor Memory:** Watch VRAM usage, stop before OOM
5. **Version Models:** Always version trained models

### **Testing Strategy:**

1. **Unit Tests First:** Write tests before implementation
2. **Integration Tests:** Test components together
3. **E2E Tests:** Full pipeline testing
4. **Performance Tests:** Ensure speed requirements met

### **Documentation:**

1. **Docstrings:** Every public method
2. **Type Hints:** Use Python type hints
3. **Examples:** Provide usage examples
4. **Comments:** Explain complex logic

### **Git Workflow:**

1. **Feature Branches:** One branch per task
2. **Small Commits:** Commit often with clear messages
3. **Pull Requests:** Review before merge
4. **CI/CD:** Run tests on every push

---

## 📚 LEARNING RESOURCES

### **LoRA & QLoRA:**
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [PEFT Library Docs](https://huggingface.co/docs/peft)
- [Efficient Finetuning Guide](https://www.philschmid.de/fine-tune-llms-in-2024-with-trl)

### **Transformers:**
- [Hugging Face Course](https://huggingface.co/learn/nlp-course)
- [Transformers Docs](https://huggingface.co/docs/transformers)

### **FastAPI:**
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)

### **Testing:**
- [pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)

---

## 🎉 COMPLETION CHECKLIST

Phase 7 is complete when:

- [ ] All 19 tasks implemented
- [ ] 100+ unit tests passing
- [ ] 20+ integration tests passing
- [ ] E2E test passes
- [ ] Documentation complete
- [ ] Performance requirements met
- [ ] Can train character with 100 decisions
- [ ] Trained model shows improvement
- [ ] Dashboard functional
- [ ] Dream cycle works
- [ ] Validation system prevents regressions
- [ ] Ready for Phase 8

---

## 🚀 BEYOND PHASE 7

**Phase 8: Scaling & Production**
- Multi-character training batches
- Distributed training
- Production deployment
- Monitoring & alerting

**Phase 9: Advanced Features**
- Transfer learning between characters
- Meta-learning
- Curriculum learning
- Active learning

**Phase 10: Research**
- New architectures
- Novel training methods
- Publication-quality experiments

---

**Ready to build?** Start with Task 7.2.2 (Data Curation)!

*Last updated: October 22, 2025*  
*Phase 7 progress: 20% complete*
