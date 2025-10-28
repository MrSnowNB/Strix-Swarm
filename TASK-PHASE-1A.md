---
title: "Phase 1A: Conway Grid Implementation - Execution Plan"
phase: "1A"
objective: "Implement 8×8 Conway grid with glider pattern and physical hardware validation"
assigned_to: "coding_agent"
status: "ready_for_execution"
hardware: "128GB Strix Halo HP ZBook, Windows 11"
dependencies: ["Phase 0 complete", "Python 3.12+", "numpy installed"]
estimated_duration: "2 days"
validation_gates: ["unit", "lint", "type", "physical_hardware"]
---

# Phase 1A: Conway Grid Implementation

## Objective

Implement an 8×8 Conway's Game of Life grid with glider pattern seeding, Pac-Man wraparound, and physical hardware validation on 128GB Strix Halo HP ZBook running Windows 11.

## Task Breakdown

### Task 1A-1: Implement ConwayGrid Core Class

**File**: `src/core/conway_grid.py`

**Requirements**:
- 8×8 grid with numpy array backend
- Conway's Game of Life rules (B3/S23)
- Toroidal (Pac-Man) wraparound for neighbors
- Delta tracking (changed cells only)
- Glider pattern seeding at arbitrary position

**Acceptance Criteria**:
- Grid initializes with correct shape (8, 8)
- `step()` method applies Conway rules correctly
- `get_neighbors()` handles wraparound with modulo
- `seed_glider()` places 5-cell glider pattern
- Returns list of `CellDelta` objects on each step

**Validation**:
```bash
pytest tests/phase_1a/test_conway_core.py::test_grid_initialization -v
pytest tests/phase_1a/test_conway_core.py::test_conway_rules -v
pytest tests/phase_1a/test_conway_core.py::test_wraparound -v
pytest tests/phase_1a/test_conway_core.py::test_glider_seeding -v
```

**Physical Verification**:
- Run script that creates grid and monitors memory:
  ```powershell
  python scripts/measure_memory.py --test=conway_grid
  ```
- Verify in Task Manager: Process RSS <10MB
- Screenshot evidence required

---

### Task 1A-2: Implement Glider Pattern Tests

**File**: `tests/phase_1a/test_glider_physics.py`

**Requirements**:
- Test glider seeding at (1,1) produces exactly 5 live cells
- Test glider evolution over 4 steps (one cycle)
- Test glider wraparound at grid edges
- Test glider continuous loop over 200 steps
- All tests must verify **actual cell states**, not mathematical simulation

**Physical Tests**:
```python
def test_glider_physical_memory():
    """Physical test: Measure actual memory usage"""
    import psutil
    process = psutil.Process()
    
    baseline_mem = process.memory_info().rss / 1024 / 1024  # MB
    
    grid = ConwayGrid(size=8)
    grid.seed_glider(1, 1)
    
    after_mem = process.memory_info().rss / 1024 / 1024  # MB
    delta = after_mem - baseline_mem
    
    assert delta < 10, f"Grid uses {delta:.2f}MB, should be <10MB"

def test_glider_physical_performance():
    """Physical test: Actual step timing"""
    import time
    
    grid = ConwayGrid(size=8)
    grid.seed_glider(1, 1)
    
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        grid.step()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    avg_time_ms = (sum(times) / len(times)) * 1000
    assert avg_time_ms < 1.0, f"Average step time {avg_time_ms:.3f}ms, should be <1ms"
```

**Validation**:
```bash
pytest tests/phase_1a/test_glider_physics.py -v -s
ruff check tests/phase_1a/
mypy tests/phase_1a/ --strict
```

**Physical Evidence Required**:
- Screenshot of pytest output showing times
- Task Manager screenshot showing memory usage
- Performance log file: `logs/phase_1a_performance.txt`

---

### Task 1A-3: Physical Hardware Validation Scripts

**File**: `scripts/validate_phase_1a.py`

**Requirements**:
- Script that runs Conway grid for 30 seconds
- Monitors CPU usage via Windows Performance Monitor
- Monitors memory usage in real-time
- Logs all measurements to file
- Generates summary report

**Implementation**:
```python
import time
import psutil
import subprocess
from src.core.conway_grid import ConwayGrid

def validate_hardware_phase_1a():
    """Physical hardware validation for Phase 1A"""
    
    print("=== Phase 1A Hardware Validation ===\n")
    
    # Get baseline metrics
    process = psutil.Process()
    baseline_mem = process.memory_info().rss / 1024 / 1024
    baseline_cpu = psutil.cpu_percent(interval=1)
    
    print(f"Baseline Memory: {baseline_mem:.2f} MB")
    print(f"Baseline CPU: {baseline_cpu:.1f}%\n")
    
    # Create grid and seed glider
    grid = ConwayGrid(size=8)
    grid.seed_glider(1, 1)
    
    after_init_mem = process.memory_info().rss / 1024 / 1024
    print(f"After Grid Init: {after_init_mem:.2f} MB")
    print(f"Grid Memory Delta: {after_init_mem - baseline_mem:.2f} MB\n")
    
    # Run for 30 seconds
    print("Running Conway for 30 seconds...")
    start_time = time.time()
    step_count = 0
    cpu_samples = []
    mem_samples = []
    
    while (time.time() - start_time) < 30:
        grid.step()
        step_count += 1
        
        # Sample every 10 steps
        if step_count % 10 == 0:
            cpu_samples.append(psutil.cpu_percent(interval=0.1))
            mem_samples.append(process.memory_info().rss / 1024 / 1024)
    
    elapsed = time.time() - start_time
    
    # Generate report
    print(f"\n=== Results ===")
    print(f"Total Steps: {step_count}")
    print(f"Elapsed Time: {elapsed:.2f}s")
    print(f"Steps/Second: {step_count/elapsed:.1f}")
    print(f"Average CPU: {sum(cpu_samples)/len(cpu_samples):.1f}%")
    print(f"Peak CPU: {max(cpu_samples):.1f}%")
    print(f"Average Memory: {sum(mem_samples)/len(mem_samples):.2f} MB")
    print(f"Peak Memory: {max(mem_samples):.2f} MB")
    print(f"Memory Growth: {mem_samples[-1] - mem_samples[0]:.2f} MB")
    
    # Write to log file
    with open("logs/phase_1a_validation.txt", "w") as f:
        f.write(f"Phase 1A Hardware Validation\n")
        f.write(f"{'='*50}\n")
        f.write(f"Hardware: 128GB Strix Halo HP ZBook, Windows 11\n")
        f.write(f"Python: {psutil.__version__}\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"Steps: {step_count}\n")
        f.write(f"Time: {elapsed:.2f}s\n")
        f.write(f"Steps/s: {step_count/elapsed:.1f}\n")
        f.write(f"Avg CPU: {sum(cpu_samples)/len(cpu_samples):.1f}%\n")
        f.write(f"Peak CPU: {max(cpu_samples):.1f}%\n")
        f.write(f"Avg Mem: {sum(mem_samples)/len(mem_samples):.2f} MB\n")
        f.write(f"Peak Mem: {max(mem_samples):.2f} MB\n")
    
    # Validation assertions
    assert step_count/elapsed > 100, "Should achieve >100 steps/second"
    assert max(cpu_samples) < 50, "CPU should stay <50%"
    assert max(mem_samples) < 50, "Memory should stay <50MB"
    assert (mem_samples[-1] - mem_samples[0]) < 5, "Memory leak <5MB"
    
    print("\n✅ Phase 1A Hardware Validation PASSED")

if __name__ == "__main__":
    validate_hardware_phase_1a()
```

**Execution**:
```bash
python scripts/validate_phase_1a.py
```

**Physical Evidence**:
- `logs/phase_1a_validation.txt` generated
- Task Manager screenshot during execution
- Performance Monitor screenshot (CPU graph)

---

### Task 1A-4: Update Living Documentation

**Files to Update**:

**REPLICATION-NOTES.md**:
```markdown
## Phase 1A: Conway Grid - Replication Notes

### Successful Execution on HP ZBook

**Date**: [YYYY-MM-DD]
**Hardware**: 128GB Strix Halo, Windows 11 Build [number]
**Python**: 3.12.x

### Baseline Performance Achieved

- Grid initialization: <1ms
- Step execution: 0.5ms average (8×8 grid)
- Memory usage: 8MB total (grid + process overhead)
- CPU usage: 15% average during continuous execution
- Steps/second: 150+ sustained

### Known Issues Encountered

- None on initial implementation

### Environment-Specific Notes

- Windows Defender can slow first run (scan on execute)
- AMD GPU not used for this phase (CPU only)
- NUMA effects minimal at this small scale

### Replicable Setup Verified

1. Install numpy via pip
2. Run validation script
3. All tests pass on first attempt
```

**TROUBLESHOOTING.md**:
```markdown
### Conway Grid Initialization Failure

**Context**: Creating ConwayGrid(size=8) raises exception
**Symptom**: `ImportError: numpy not found`
**Error Snippet**:
\`\`\`
ModuleNotFoundError: No module named 'numpy'
\`\`\`
**Probable Cause**: numpy not installed in environment
**Quick Fix**: `pip install numpy`
**Permanent Fix**: Add numpy to requirements.txt
**Prevention**: Run `pip install -e .` during setup
**Tags**: setup, dependency, P2

---

### Step Performance Slower Than Expected

**Context**: Conway steps taking >5ms on 8×8 grid
**Symptom**: Validation script reports low steps/second
**Error Snippet**:
\`\`\`
AssertionError: Should achieve >100 steps/second
\`\`\`
**Probable Cause**: Debug mode enabled or background processes
**Quick Fix**: Close other applications, run in release mode
**Permanent Fix**: Profile with cProfile, optimize hot paths
**Prevention**: Check Task Manager before validation runs
**Tags**: performance, optimization, P3
```

---

## Validation Gates

### Gate 1: Unit Tests
```bash
pytest tests/phase_1a/ -v --tb=short
# All tests must pass, no failures or errors
```

### Gate 2: Linting
```bash
ruff check src/core/conway_grid.py tests/phase_1a/
# Must return exit code 0, no violations
```

### Gate 3: Type Checking
```bash
mypy src/core/conway_grid.py --strict
# Must return exit code 0, no type errors
```

### Gate 4: Physical Hardware Validation
```bash
python scripts/validate_phase_1a.py
# Must complete successfully, generate log file
# Task Manager screenshot must show <50MB memory
# Performance Monitor screenshot must show <50% CPU
```

### Gate 5: Documentation Drift Check
```bash
python scripts/check_docs.py --phase=1a
# Verify README.md, REPLICATION-NOTES.md updated
```

---

## Failure Handling Protocol

If ANY gate fails:

1. **Capture logs**:
   ```powershell
   mkdir logs\failures\phase_1a_$(Get-Date -Format 'yyyyMMdd_HHmmss')
   copy logs\*.txt logs\failures\phase_1a_*\
   copy pytest_output.txt logs\failures\phase_1a_*\
   ```

2. **Update TROUBLESHOOTING.md**:
   - Add new entry with full context
   - Include error snippet
   - Document quick fix and permanent fix

3. **Update REPLICATION-NOTES.md**:
   - Add to "Known Pitfalls"
   - Document environment deltas
   - Record resolution steps

4. **Create ISSUE.md**:
   ```markdown
   ---
   title: "[FAILURE] Phase 1A Gate X Failed"
   date: "YYYY-MM-DD HH:MM:SS"
   severity: "P0|P1|P2|P3"
   assigned_to: "human"
   status: "open"
   ---
   
   ## Failure Summary
   **Phase**: Phase 1A
   **Gate Failed**: [unit|lint|type|physical_hardware|docs]
   **Task**: [Task number]
   
   ## Error Details
   \`\`\`
   [Full error output]
   \`\`\`
   
   ## Logs Collected
   - pytest output: logs/failures/phase_1a_*/pytest_output.txt
   - validation log: logs/failures/phase_1a_*/phase_1a_validation.txt
   
   ## Next Steps Required
   - [ ] Human investigation needed
   ```

5. **Halt execution**:
   ```python
   print("❌ Gate X failed - halting execution")
   print("See ISSUE-[timestamp].md for details")
   sys.exit(1)
   ```

---

## Success Criteria

Phase 1A is complete when:

- [ ] All unit tests pass (gate 1)
- [ ] Linting clean (gate 2)
- [ ] Type checking clean (gate 3)
- [ ] Physical hardware validation passes (gate 4)
- [ ] Documentation updated (gate 5)
- [ ] REPLICATION-NOTES.md has Phase 1A entry
- [ ] No ISSUE.md files in open status
- [ ] Task Manager screenshots archived in `docs/evidence/phase_1a/`
- [ ] Performance log exists at `logs/phase_1a_validation.txt`

---

## Deliverables

1. **Code**:
   - `src/core/conway_grid.py` (fully tested)
   - `tests/phase_1a/test_conway_core.py`
   - `tests/phase_1a/test_glider_physics.py`
   - `scripts/validate_phase_1a.py`

2. **Documentation**:
   - REPLICATION-NOTES.md updated
   - TROUBLESHOOTING.md updated (if issues encountered)
   - Performance log: `logs/phase_1a_validation.txt`

3. **Evidence**:
   - Task Manager screenshot showing <50MB memory
   - Performance Monitor screenshot showing <50% CPU
   - pytest output showing all tests passed
   - Video recording of glider evolution (optional but recommended)

---

## Execution Command for Agent

```bash
# Agent should execute this sequence atomically

# Step 1: Implement core
# (agent writes src/core/conway_grid.py)

# Step 2: Implement tests
# (agent writes tests/phase_1a/*.py)

# Step 3: Run validation gates
pytest tests/phase_1a/ -v --tb=short || {
  echo "Unit tests failed - halting"
  # agent updates TROUBLESHOOTING.md, creates ISSUE.md, exits
}

ruff check src/core/conway_grid.py tests/phase_1a/ || {
  echo "Linting failed - halting"
  # agent updates TROUBLESHOOTING.md, creates ISSUE.md, exits
}

mypy src/core/conway_grid.py --strict || {
  echo "Type checking failed - halting"
  # agent updates TROUBLESHOOTING.md, creates ISSUE.md, exits
}

# Step 4: Physical validation
python scripts/validate_phase_1a.py || {
  echo "Physical validation failed - halting"
  # agent updates TROUBLESHOOTING.md, creates ISSUE.md, exits
}

# Step 5: Update docs
# (agent updates REPLICATION-NOTES.md with results)

# Step 6: Verify all deliverables present
python scripts/check_deliverables.py --phase=1a || {
  echo "Missing deliverables - halting"
  # agent creates ISSUE.md, exits
}

echo "✅ Phase 1A complete - ready for human review"
```

---

## Notes for Coding Agent

- **Do not proceed to Phase 1B** until Phase 1A is marked complete by human
- **Stop immediately** on any gate failure and wait for human input
- **Take screenshots** during physical validation (use `pyautogui` if needed)
- **Verify hardware** matches spec: 128GB RAM, Windows 11, AMD Strix Halo
- **Run on actual hardware**, not simulation or Docker container
- **Measure real metrics**, not theoretical or estimated values

This task is **ready for execution** by a coding agent following the Policy lifecycle.