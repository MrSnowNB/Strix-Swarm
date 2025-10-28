---
title: "Phase 1D: Data Validation & Correctness Testing"
phase: "1D"
objective: "Validate algorithmic correctness, mathematical accuracy, and data integrity across all Phase 1 components"
assigned_to: "coding_agent"
status: "ready_for_execution"
hardware: "128GB Strix Halo HP ZBook, Windows 11"
dependencies: ["Phase 1A complete", "Phase 1B complete", "Phase 1C complete", "Visual demo exists"]
estimated_duration: "0.5 days"
validation_gates: ["unit", "lint", "type", "mathematical_proof"]
priority: "P0 - CRITICAL"
---

# Phase 1D: Data Validation & Correctness Testing

## Objective

Validate that Phase 1 implementation is **mathematically correct** and **algorithmically sound**, not just visually appealing. Prove that Conway's Game of Life rules are correctly implemented, glider pattern is canonical, delta messages are accurate, and data flows correctly through the entire stack.

## Critical Context

**Why This Phase Exists**:
- Visual demo video exists (Phase 1C) ✅
- BUT we skipped validation of **data correctness** ❌
- Pretty pixels ≠ correct computation
- Need to prove: algorithm correctness, mathematical accuracy, data integrity

**What We're Validating**:
- Conway rules (B3/S23) implemented correctly
- Glider pattern is canonical and behaves mathematically
- Wraparound (toroidal topology) works at algorithm level
- Delta messages match actual state changes
- Frontend displays correct data from backend

---

## Task Breakdown

### Task 1D-1: Conway Rule Correctness Tests

**File**: `tests/phase_1d/test_conway_rules.py`

**Requirements**:
- Test birth rule (B3): dead cell with exactly 3 neighbors becomes alive
- Test survival rules (S23): live cell with 2 or 3 neighbors survives
- Test death by underpopulation: live cell with <2 neighbors dies
- Test death by overpopulation: live cell with >3 neighbors dies
- Test all rules in isolation (no side effects)

**Implementation**:
```python
import pytest
import numpy as np
from src.core.conway_grid import ConwayGrid

def test_birth_rule_exactly_three_neighbors():
    """
    Conway Rule: Dead cell with exactly 3 live neighbors becomes alive
    
    Setup:
      . X .
      X . X
      . . .
    
    Center cell (1,1) has 3 neighbors, should become alive
    """
    grid = ConwayGrid(size=5)
    
    # Dead center with 3 neighbors
    grid.grid[0, 1] = 1  # North
    grid.grid[1, 0] = 1  # West
    grid.grid[1, 2] = 1  # East
    grid.grid[1, 1] = 0  # Center (dead)
    
    # Step
    grid.step()
    
    # Center should now be alive
    assert grid.grid[1, 1] == 1, \
        "Birth rule failed: dead cell with 3 neighbors should become alive"

def test_birth_rule_not_two_neighbors():
    """Dead cell with 2 neighbors should stay dead"""
    grid = ConwayGrid(size=5)
    
    # Dead center with 2 neighbors
    grid.grid[0, 1] = 1  # North
    grid.grid[1, 0] = 1  # West
    grid.grid[1, 1] = 0  # Center (dead)
    
    grid.step()
    
    # Center should stay dead
    assert grid.grid[1, 1] == 0, \
        "Cell with 2 neighbors should not be born"

def test_survival_rule_two_neighbors():
    """Live cell with 2 neighbors survives"""
    grid = ConwayGrid(size=5)
    
    # Live center with 2 neighbors
    grid.grid[1, 1] = 1  # Center (alive)
    grid.grid[0, 1] = 1  # North
    grid.grid[1, 0] = 1  # West
    
    grid.step()
    
    # Center should survive
    assert grid.grid[1, 1] == 1, \
        "Survival rule failed: live cell with 2 neighbors should survive"

def test_survival_rule_three_neighbors():
    """Live cell with 3 neighbors survives"""
    grid = ConwayGrid(size=5)
    
    # Live center with 3 neighbors
    grid.grid[1, 1] = 1  # Center (alive)
    grid.grid[0, 1] = 1  # North
    grid.grid[1, 0] = 1  # West
    grid.grid[1, 2] = 1  # East
    
    grid.step()
    
    # Center should survive
    assert grid.grid[1, 1] == 1, \
        "Survival rule failed: live cell with 3 neighbors should survive"

def test_death_underpopulation_zero_neighbors():
    """Live cell with 0 neighbors dies (underpopulation)"""
    grid = ConwayGrid(size=5)
    
    # Single live cell, isolated
    grid.grid[2, 2] = 1
    
    grid.step()
    
    # Should die
    assert grid.grid[2, 2] == 0, \
        "Death rule failed: isolated cell should die from underpopulation"

def test_death_underpopulation_one_neighbor():
    """Live cell with 1 neighbor dies (underpopulation)"""
    grid = ConwayGrid(size=5)
    
    # Live cell with 1 neighbor
    grid.grid[2, 2] = 1  # Center
    grid.grid[2, 3] = 1  # One neighbor
    
    grid.step()
    
    # Both should die (each has only 1 neighbor)
    assert grid.grid[2, 2] == 0, \
        "Death rule failed: cell with 1 neighbor should die"
    assert grid.grid[2, 3] == 0, \
        "Death rule failed: cell with 1 neighbor should die"

def test_death_overpopulation_four_neighbors():
    """Live cell with 4 neighbors dies (overpopulation)"""
    grid = ConwayGrid(size=5)
    
    # Center with 4 neighbors
    grid.grid[2, 2] = 1  # Center
    grid.grid[1, 2] = 1  # North
    grid.grid[3, 2] = 1  # South
    grid.grid[2, 1] = 1  # West
    grid.grid[2, 3] = 1  # East
    
    grid.step()
    
    # Center should die from overpopulation
    assert grid.grid[2, 2] == 0, \
        "Death rule failed: cell with 4 neighbors should die from overpopulation"

def test_death_overpopulation_eight_neighbors():
    """Live cell with 8 neighbors (surrounded) dies"""
    grid = ConwayGrid(size=5)
    
    # Center surrounded by 8 neighbors
    grid.grid[2, 2] = 1
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            grid.grid[2+dy, 2+dx] = 1
    
    grid.step()
    
    # Center should die
    assert grid.grid[2, 2] == 0, \
        "Death rule failed: cell with 8 neighbors should die"

def test_stable_block_pattern():
    """
    Block pattern (2x2) should be stable (still life)
    
    XX
    XX
    
    Each cell has 3 neighbors, all survive
    """
    grid = ConwayGrid(size=5)
    
    # Create block at center
    grid.grid[2, 2] = 1
    grid.grid[2, 3] = 1
    grid.grid[3, 2] = 1
    grid.grid[3, 3] = 1
    
    initial = grid.grid.copy()
    
    # Step multiple times
    for _ in range(5):
        grid.step()
    
    # Block should be unchanged
    assert np.array_equal(grid.grid, initial), \
        "Block pattern should be stable (still life), but changed"
```

**Validation**:
```bash
pytest tests/phase_1d/test_conway_rules.py -v -s
# All 11 tests must pass
```

**Physical Evidence**:
- Test output showing all rules pass
- Screenshot of pytest results

---

### Task 1D-2: Glider Pattern Validation

**File**: `tests/phase_1d/test_glider_correctness.py`

**Requirements**:
- Verify glider is canonical Conway glider shape
- Test glider period-4 property (returns to same shape after 4 steps)
- Verify glider moves diagonally (+1,+1 per 4 steps)
- Test glider survives multiple cycles without dying
- Validate glider maintains 5 cells throughout

**Implementation**:
```python
def test_glider_canonical_shape():
    """
    Verify glider matches canonical Conway glider:
      .X.
      ..X
      XXX
    
    At position (1,1), this means cells at:
    (2,1), (3,2), (1,3), (2,3), (3,3)
    """
    grid = ConwayGrid(size=8)
    grid.seed_glider(x=1, y=1)
    
    # Expected live cells (x, y coordinates)
    expected = {
        (2, 1),  # Top middle
        (3, 2),  # Middle right
        (1, 3),  # Bottom left
        (2, 3),  # Bottom middle
        (3, 3),  # Bottom right
    }
    
    # Get actual live cells
    actual = set()
    for y in range(8):
        for x in range(8):
            if grid.grid[y, x] == 1:
                actual.add((x, y))
    
    assert actual == expected, \
        f"Glider shape incorrect.\nExpected: {expected}\nActual: {actual}"

def test_glider_has_five_cells():
    """Glider should always have exactly 5 cells"""
    grid = ConwayGrid(size=8)
    grid.seed_glider(x=2, y=2)
    
    live_count = np.sum(grid.grid)
    assert live_count == 5, \
        f"Glider should have 5 cells, has {live_count}"

def test_glider_period_four():
    """
    Glider returns to same shape after 4 steps (period-4)
    but shifted by (+1, +1)
    """
    grid = ConwayGrid(size=16)  # Larger grid to prevent edge effects
    grid.seed_glider(x=4, y=4)
    
    # Get initial live cells (relative positions)
    initial_cells = set()
    for y in range(16):
        for x in range(16):
            if grid.grid[y, x] == 1:
                initial_cells.add((x, y))
    
    # Calculate center of mass
    initial_cx = np.mean([c[0] for c in initial_cells])
    initial_cy = np.mean([c[1] for c in initial_cells])
    
    # Run 4 steps
    for _ in range(4):
        grid.step()
    
    # Get cells after 4 steps
    final_cells = set()
    for y in range(16):
        for x in range(16):
            if grid.grid[y, x] == 1:
                final_cells.add((x, y))
    
    # Calculate new center of mass
    final_cx = np.mean([c[0] for c in final_cells])
    final_cy = np.mean([c[1] for c in final_cells])
    
    # Should have moved by approximately (+1, +1)
    dx = final_cx - initial_cx
    dy = final_cy - initial_cy
    
    assert 0.8 < dx < 1.2, f"Glider should move +1 in x after 4 steps, moved {dx}"
    assert 0.8 < dy < 1.2, f"Glider should move +1 in y after 4 steps, moved {dy}"
    
    # Should still have 5 cells
    assert len(final_cells) == 5, \
        f"Glider should maintain 5 cells, has {len(final_cells)}"

def test_glider_trajectory_diagonal():
    """Glider should move diagonally (down-right)"""
    grid = ConwayGrid(size=16)
    grid.seed_glider(x=2, y=2)
    
    # Track center of mass over 20 steps
    positions = []
    for i in range(20):
        live_cells = np.argwhere(grid.grid == 1)
        if len(live_cells) > 0:
            cx = np.mean(live_cells[:, 1])  # x coordinate
            cy = np.mean(live_cells[:, 0])  # y coordinate
            positions.append((cx, cy))
        grid.step()
    
    # Verify consistent diagonal movement
    initial = positions[0]
    final = positions[-1]
    
    dx = final[0] - initial[0]
    dy = final[1] - initial[1]
    
    # Should move diagonally: dx ≈ dy and both positive
    assert dx > 2, f"Glider should move right, dx={dx}"
    assert dy > 2, f"Glider should move down, dy={dy}"
    assert 0.8 < dx/dy < 1.2, \
        f"Glider should move diagonally (dx≈dy), but dx={dx}, dy={dy}"

def test_glider_survives_50_generations():
    """Glider should survive at least 50 generations without dying"""
    grid = ConwayGrid(size=16)
    grid.seed_glider(x=4, y=4)
    
    for i in range(50):
        live_count = np.sum(grid.grid)
        assert live_count > 0, \
            f"Glider died at generation {i}"
        grid.step()
    
    # Final check
    final_count = np.sum(grid.grid)
    assert final_count == 5, \
        f"Glider should have 5 cells after 50 steps, has {final_count}"

def test_glider_never_exceeds_five_cells():
    """During evolution, glider should never have more than 5 cells"""
    grid = ConwayGrid(size=16)
    grid.seed_glider(x=4, y=4)
    
    for i in range(100):
        live_count = np.sum(grid.grid)
        assert live_count <= 5, \
            f"Glider has {live_count} cells at step {i}, should never exceed 5"
        grid.step()
```

**Validation**:
```bash
pytest tests/phase_1d/test_glider_correctness.py -v -s
# All 6 tests must pass
```

---

### Task 1D-3: Wraparound (Toroidal) Validation

**File**: `tests/phase_1d/test_wraparound.py`

**Requirements**:
- Test neighbor counting across top/bottom edges
- Test neighbor counting across left/right edges
- Test neighbor counting at corners (wraps both x and y)
- Verify glider survives wraparound events
- Test pattern preservation through wraparound

**Implementation**:
```python
def test_wraparound_top_bottom():
    """Verify neighbor counting wraps from top to bottom"""
    grid = ConwayGrid(size=8)
    
    # Place live cells at top and bottom edges
    grid.grid[0, 3] = 1  # Top edge
    grid.grid[7, 3] = 1  # Bottom edge
    
    # Count neighbors of top cell (should see bottom cell)
    neighbors_top = grid.get_neighbors(3, 0)
    
    # Count neighbors of bottom cell (should see top cell)
    neighbors_bottom = grid.get_neighbors(3, 7)
    
    # Each should see the other as neighbor
    assert neighbors_top >= 1, "Top cell should see bottom cell as neighbor (wraparound)"
    assert neighbors_bottom >= 1, "Bottom cell should see top cell as neighbor (wraparound)"

def test_wraparound_left_right():
    """Verify neighbor counting wraps from left to right"""
    grid = ConwayGrid(size=8)
    
    # Place live cells at left and right edges
    grid.grid[3, 0] = 1  # Left edge
    grid.grid[3, 7] = 1  # Right edge
    
    neighbors_left = grid.get_neighbors(0, 3)
    neighbors_right = grid.get_neighbors(7, 3)
    
    assert neighbors_left >= 1, "Left cell should see right cell (wraparound)"
    assert neighbors_right >= 1, "Right cell should see left cell (wraparound)"

def test_wraparound_corner():
    """Verify corner cell sees opposite corner as neighbor"""
    grid = ConwayGrid(size=8)
    
    # Place live cells at opposite corners
    grid.grid[0, 0] = 1  # Top-left
    grid.grid[7, 7] = 1  # Bottom-right
    
    # Top-left should see bottom-right as diagonal neighbor
    neighbors = grid.get_neighbors(0, 0)
    
    assert neighbors >= 1, \
        "Corner wraparound failed: (0,0) should see (7,7) as diagonal neighbor"

def test_glider_survives_edge_crossing():
    """Glider should survive crossing edges"""
    grid = ConwayGrid(size=8)
    
    # Place glider near right edge
    grid.seed_glider(x=6, y=1)
    
    # Run until glider crosses edge
    for _ in range(20):
        grid.step()
    
    # Glider should still exist
    live_count = np.sum(grid.grid)
    assert live_count >= 5, \
        f"Glider died crossing edge: only {live_count} cells remain"

def test_wraparound_preserves_pattern():
    """Pattern shape should be preserved through wraparound"""
    grid = ConwayGrid(size=8)
    grid.seed_glider(x=6, y=6)  # Near bottom-right corner
    
    # Track cell count through multiple steps
    counts = []
    for _ in range(30):
        counts.append(np.sum(grid.grid))
        grid.step()
    
    # Cell count should remain 5 (allowing brief fluctuations during phase transitions)
    stable_counts = [c for c in counts if c == 5]
    
    assert len(stable_counts) > 20, \
        f"Glider unstable during wraparound: counts were {set(counts)}"
```

**Validation**:
```bash
pytest tests/phase_1d/test_wraparound.py -v -s
# All 5 tests must pass
```

---

### Task 1D-4: Delta Message Accuracy

**File**: `tests/phase_1d/test_delta_accuracy.py`

**Requirements**:
- Verify deltas exactly match state changes
- Test that no changes are missed
- Test that no false deltas are generated
- Validate delta coordinates are correct
- Verify delta alive/dead values match reality

**Implementation**:
```python
import pytest
from src.core.conway_grid import ConwayGrid

def test_delta_matches_state_change():
    """Every delta should correspond to actual cell state change"""
    grid = ConwayGrid(size=8)
    grid.seed_glider(1, 1)
    
    # Capture before state
    before = grid.grid.copy()
    
    # Step and get deltas
    deltas = grid.step()
    
    # Capture after state
    after = grid.grid
    
    # Verify each delta
    for delta in deltas:
        before_val = before[delta.y, delta.x]
        after_val = after[delta.y, delta.x]
        
        if delta.alive:
            assert before_val == 0 and after_val == 1, \
                f"Delta at ({delta.x},{delta.y}) says alive=True but state: {before_val}→{after_val}"
        else:
            assert before_val == 1 and after_val == 0, \
                f"Delta at ({delta.x},{delta.y}) says alive=False but state: {before_val}→{after_val}"

def test_all_changes_captured_in_deltas():
    """No state changes should be missed by deltas"""
    grid = ConwayGrid(size=8)
    grid.seed_glider(1, 1)
    
    before = grid.grid.copy()
    deltas = grid.step()
    after = grid.grid
    
    # Find all actual changes
    actual_changes = []
    for y in range(8):
        for x in range(8):
            if before[y, x] != after[y, x]:
                actual_changes.append((x, y))
    
    # Verify delta count matches
    assert len(deltas) == len(actual_changes), \
        f"Delta count mismatch: {len(deltas)} deltas but {len(actual_changes)} actual changes"
    
    # Verify all change positions are in deltas
    delta_positions = {(d.x, d.y) for d in deltas}
    actual_positions = set(actual_changes)
    
    assert delta_positions == actual_positions, \
        f"Delta positions don't match changes.\nDeltas: {delta_positions}\nActual: {actual_positions}"

def test_no_false_deltas():
    """Deltas should not report changes for unchanged cells"""
    grid = ConwayGrid(size=8)
    
    # Create stable block pattern
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[4, 3] = 1
    grid.grid[4, 4] = 1
    
    deltas = grid.step()
    
    # Block is stable, should have zero deltas
    assert len(deltas) == 0, \
        f"Stable pattern should have 0 deltas, got {len(deltas)}: {deltas}"

def test_delta_coordinates_valid():
    """All delta coordinates should be within grid bounds"""
    grid = ConwayGrid(size=8)
    grid.seed_glider(1, 1)
    
    for _ in range(10):
        deltas = grid.step()
        for delta in deltas:
            assert 0 <= delta.x < 8, f"Delta x-coordinate out of bounds: {delta.x}"
            assert 0 <= delta.y < 8, f"Delta y-coordinate out of bounds: {delta.y}"
```

**Validation**:
```bash
pytest tests/phase_1d/test_delta_accuracy.py -v -s
# All 4 tests must pass
```

---

### Task 1D-5: Frontend Data Consistency

**File**: `tests/phase_1d/test_frontend_data.py`

**Requirements**:
- Verify WebSocket messages contain valid data
- Test tick counter increases monotonically
- Validate live cell count matches visual grid
- Verify update rate is approximately 2.0/sec
- Test reset button resets tick counter

**Manual Browser Validation Script**:
```javascript
// tests/phase_1d/browser_validation.js
// Run this in browser console while dashboard is active

console.log('=== Phase 1D: Frontend Data Validation ===\n');

// Test 1: Message Reception
const receivedMessages = [];
let messageCount = 0;
const startTime = Date.now();

// Intercept WebSocket messages
const originalHandler = wsClient.ws.onmessage;
wsClient.ws.onmessage = function(event) {
    const msg = JSON.parse(event.data);
    receivedMessages.push({
        time: Date.now() - startTime,
        type: msg.type,
        tick: msg.tick,
        deltaCount: msg.deltas ? msg.deltas.length : 0
    });
    messageCount++;
    originalHandler.call(this, event);
};

// Wait 10 seconds then analyze
setTimeout(() => {
    console.log(`\n=== Results after 10 seconds ===`);
    console.log(`Total messages: ${messageCount}`);
    
    const deltas = receivedMessages.filter(m => m.type === 'delta');
    console.log(`Delta messages: ${deltas.length}`);
    
    // TEST 1: Monotonic tick counter
    let tickErrors = 0;
    for (let i = 1; i < deltas.length; i++) {
        if (deltas[i].tick !== deltas[i-1].tick + 1) {
            console.error(`❌ Tick not monotonic: ${deltas[i-1].tick} → ${deltas[i].tick}`);
            tickErrors++;
        }
    }
    
    if (tickErrors === 0) {
        console.log('✅ TEST 1 PASS: Tick counter monotonic');
    } else {
        console.error(`❌ TEST 1 FAIL: ${tickErrors} tick errors`);
    }
    
    // TEST 2: Live cell count consistent
    const liveCellElement = document.getElementById('live-cells');
    const finalLiveCount = parseInt(liveCellElement.textContent);
    
    // Count actual live cells in DOM
    const aliveCells = document.querySelectorAll('.cell.alive').length;
    
    if (finalLiveCount === aliveCells && finalLiveCount === 5) {
        console.log(`✅ TEST 2 PASS: Live cell count correct (${finalLiveCount} == ${aliveCells} == 5)`);
    } else {
        console.error(`❌ TEST 2 FAIL: Live count mismatch: display=${finalLiveCount}, DOM=${aliveCells}, expected=5`);
    }
    
    // TEST 3: Update rate
    const updateRateElement = document.getElementById('update-rate');
    const updateRate = parseFloat(updateRateElement.textContent);
    
    if (1.8 <= updateRate && updateRate <= 2.2) {
        console.log(`✅ TEST 3 PASS: Update rate correct (${updateRate}/sec ≈ 2.0)`);
    } else {
        console.error(`❌ TEST 3 FAIL: Update rate wrong: ${updateRate}/sec (expected ~2.0)`);
    }
    
    // TEST 4: Delta sizes reasonable
    const avgDeltaSize = deltas.reduce((sum, d) => sum + d.deltaCount, 0) / deltas.length;
    
    if (2 <= avgDeltaSize && avgDeltaSize <= 15) {
        console.log(`✅ TEST 4 PASS: Average delta size reasonable (${avgDeltaSize.toFixed(1)} cells/update)`);
    } else {
        console.warn(`⚠️  TEST 4 WARNING: Average delta size unexpected: ${avgDeltaSize.toFixed(1)}`);
    }
    
    console.log('\n=== Frontend Data Validation Complete ===');
    console.log('Copy these results to docs/validation/frontend_data_results.txt');
    
}, 10000);

console.log('Validation running for 10 seconds...');
```

**Validation**:
- Open dashboard in browser
- Open console (F12)
- Paste script and run
- Wait 10 seconds
- Copy results to file

---

## Validation Gates

### Gate 1: Unit Tests - Conway Rules
```bash
pytest tests/phase_1d/test_conway_rules.py -v -s
# Expected: 11/11 tests pass
# All Conway rules must be mathematically correct
```

### Gate 2: Unit Tests - Glider Correctness
```bash
pytest tests/phase_1d/test_glider_correctness.py -v -s
# Expected: 6/6 tests pass
# Glider must be canonical Conway glider
```

### Gate 3: Unit Tests - Wraparound
```bash
pytest tests/phase_1d/test_wraparound.py -v -s
# Expected: 5/5 tests pass
# Toroidal topology must work correctly
```

### Gate 4: Unit Tests - Delta Accuracy
```bash
pytest tests/phase_1d/test_delta_accuracy.py -v -s
# Expected: 4/4 tests pass
# Delta messages must exactly match state changes
```

### Gate 5: Browser Data Validation
```bash
# Manual execution in browser console
# Expected: 4/4 tests pass
# Frontend must display correct data
```

### Gate 6: Linting
```bash
ruff check tests/phase_1d/
# Must be clean
```

### Gate 7: Type Checking
```bash
mypy tests/phase_1d/ --strict
# Must pass
```

---

## Success Criteria

Phase 1D is complete when:

- [ ] All 26 unit tests pass (11+6+5+4)
- [ ] All 4 browser validation tests pass
- [ ] Linting clean
- [ ] Type checking clean
- [ ] Conway rules proven mathematically correct
- [ ] Glider proven to be canonical Conway glider
- [ ] Wraparound proven to work correctly
- [ ] Deltas proven to match state changes exactly
- [ ] Frontend proven to display correct data
- [ ] Documentation updated with validation results

---

## Deliverables

1. **Test Files**:
   - `tests/phase_1d/test_conway_rules.py` (11 tests)
   - `tests/phase_1d/test_glider_correctness.py` (6 tests)
   - `tests/phase_1d/test_wraparound.py` (5 tests)
   - `tests/phase_1d/test_delta_accuracy.py` (4 tests)
   - `tests/phase_1d/browser_validation.js` (4 tests)

2. **Validation Report**:
   - `docs/validation/phase_1d_report.md`
   - Test results for all 30 tests
   - Screenshots of pytest output
   - Browser console validation results

3. **Documentation Updates**:
   - REPLICATION-NOTES.md with validation results
   - README.md updated with "Data Validated" badge

---

## Failure Handling

If ANY test fails:

1. **Document the failure**:
   ```markdown
   ### Test Failure: [TEST-ID]
   **Test**: test_conway_rules.py::test_birth_rule_exactly_three_neighbors
   **Expected**: Cell with 3 neighbors becomes alive
   **Actual**: Cell remained dead
   **Root Cause**: [Investigation required]
   ```

2. **Update TROUBLESHOOTING.md**:
   ```markdown
   ### Conway Birth Rule Incorrect
   **Context**: Running Phase 1D validation tests
   **Symptom**: test_birth_rule_exactly_three_neighbors fails
   **Probable Cause**: Bug in neighbor counting or rule application
   **Investigation**: Check get_neighbors() and step() implementations
   **Tags**: phase_1d, conway_rules, P0
   ```

3. **Create ISSUE.md**:
   ```markdown
   ---
   title: "[CRITICAL] Phase 1D Test Failure - Conway Rules Incorrect"
   date: "2025-10-27"
   severity: "P0"
   assigned_to: "coding_agent"
   status: "open"
   ---
   
   ## Test Failure
   **Phase**: 1D Data Validation
   **Test**: test_conway_rules.py
   **Status**: FAILED
   
   ## Impact
   If Conway rules are incorrect, entire Phase 1 is invalid.
   Demo may look correct but be mathematically wrong.
   
   ## Required Actions
   - [ ] Fix Conway rule implementation
   - [ ] Re-run all Phase 1D tests
   - [ ] Verify fix doesn't break Phase 1A/1B/1C
   ```

4. **Halt execution** until human reviews

---

## Notes for Coding Agent

- **This is critical validation** - do not skip any tests
- **Mathematical correctness required** - pretty demo is not enough
- **All 30 tests must pass** - zero tolerance for failures
- **If any test fails**, the entire Phase 1 is suspect
- **Document everything** - this validates months of work

---

## Expected Timeline

- Task 1D-1: 2 hours (Conway rule tests)
- Task 1D-2: 1.5 hours (Glider correctness)
- Task 1D-3: 1 hour (Wraparound validation)
- Task 1D-4: 1 hour (Delta accuracy)
- Task 1D-5: 0.5 hours (Browser validation)
- **Total: 6 hours (0.5 days)**

---

This task is **ready for execution** and is **CRITICAL** for Phase 1 validation.