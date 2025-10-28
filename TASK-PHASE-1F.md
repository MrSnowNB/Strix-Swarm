---
title: "Phase 1F: Conway Correctness Fix + Interactive Teaching Layer"
phase: "1F"
objective: "Fix Conway rule bugs, add interactive web controls, complete Phase 1 as teaching tool"
assigned_to: "coding_agent"
status: "ready_for_execution"
hardware: "128GB Strix Halo HP ZBook, Windows 11"
dependencies: ["Phase 1A-1E foundation", "Strix-Swarm repository"]
estimated_duration: "0.5 days"
validation_gates: ["unit", "lint", "type", "conway_correctness", "interactive_layer"]
priority: "P0 - BLOCKER"
blocker_issue: "Cells not dying per Conway rules in dashboard"
---

# Phase 1F: Conway Correctness Fix + Interactive Teaching Layer

## Critical Issue

**Blocker**: Dashboard shows cells remaining alive that should die based on Conway rules (B3/S23).

**User Report**: "I noticed cells being left alive that should die based on Conway [in the web dashboard]"

**Impact**: 
- ❌ Conway rules not working correctly
- ❌ Cannot trust any Phase 1 validation
- ❌ Demo is incorrect/misleading
- ❌ Must fix before adding interactive layer

---

## Objective

1. **Fix Conway correctness** - Ensure B3/S23 rules execute perfectly
2. **Add interactive controls** - Allow dashboard to send commands to backend
3. **Complete Phase 1** - Verify all components working correctly
4. **Enable teaching mode** - Demo becomes interactive educational tool

---

## Root Cause Analysis

### Likely Bugs (Ranked by Probability)

**A. Neighbor Counting Error** (90% likely)
```python
# WRONG - includes center cell
neighbors = 0
for dx in [-1, 0, 1]:
    for dy in [-1, 0, 1]:
        neighbors += grid[y+dy, x+dx]

# RIGHT - excludes center cell
neighbors = 0
for dx in [-1, 0, 1]:
    for dy in [-1, 0, 1]:
        if dx == 0 and dy == 0:
            continue
        neighbors += grid[y+dy, x+dx]
```

**B. In-Place Update Error** (80% likely)
```python
# WRONG - reading and writing same array
for y in range(8):
    for x in range(8):
        neighbors = count_neighbors(x, y)
        if neighbors == 3:
            self.grid[y, x] = 1  # MODIFIES GRID WHILE READING

# RIGHT - separate arrays
new_grid = np.zeros_like(self.grid)
for y in range(8):
    for x in range(8):
        neighbors = count_neighbors(x, y)
        if neighbors == 3:
            new_grid[y, x] = 1
self.grid = new_grid
```

**C. Index Swap Error** (60% likely)
```python
# WRONG - x/y swapped
def get_neighbors(self, x, y):
    count = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx = (x + dx) % self.size
            ny = (y + dy) % self.size
            count += self.grid[nx, ny]  # WRONG: should be [ny, nx]
```

**D. Wraparound Error** (40% likely)
```python
# WRONG - no modulo
nx = x + dx
ny = y + dy
if 0 <= nx < 8 and 0 <= ny < 8:
    count += grid[ny, nx]
# MISSING: cells at edges

# RIGHT - toroidal wrap
nx = (x + dx) % self.size
ny = (y + dy) % self.size
count += grid[ny, nx]
```

**E. Frontend Delta Application Error** (30% likely)
- Deltas applied out of order
- Stale state not re-synced
- Multiple conflicting updates

---

## Task Breakdown

### Task 1F-1: Diagnose Conway Bug

**File**: `scripts/diagnose_conway.py` (new)

**Requirements**:
- Run deterministic test patterns
- Compare with known correct outcomes
- Log neighbor counts per cell
- Identify exact failure mode

**Implementation**:
```python
import numpy as np
from src.core.conway_grid import ConwayGrid

def test_isolated_cell_dies():
    """Single cell should die (no neighbors)"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1  # Single alive cell
    
    print("Before:", np.sum(grid.grid), "alive")
    grid.step()
    print("After:", np.sum(grid.grid), "alive")
    
    if grid.grid[3, 3] == 1:
        print("❌ FAIL: Isolated cell did NOT die")
        return False
    else:
        print("✅ PASS: Isolated cell died")
        return True

def test_block_stable():
    """2x2 block should remain stable"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[4, 3] = 1
    grid.grid[4, 4] = 1
    
    before = grid.grid.copy()
    grid.step()
    
    if np.array_equal(before, grid.grid):
        print("✅ PASS: Block stable")
        return True
    else:
        print("❌ FAIL: Block changed")
        print("Before:\n", before[2:6, 2:6])
        print("After:\n", grid.grid[2:6, 2:6])
        return False

def test_blinker_period_2():
    """Blinker should oscillate with period 2"""
    grid = ConwayGrid(size=8)
    # Horizontal blinker
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[3, 5] = 1
    
    state0 = grid.grid.copy()
    grid.step()
    state1 = grid.grid.copy()
    grid.step()
    state2 = grid.grid.copy()
    
    if np.array_equal(state0, state2) and not np.array_equal(state0, state1):
        print("✅ PASS: Blinker oscillates")
        return True
    else:
        print("❌ FAIL: Blinker behavior incorrect")
        return False

def diagnose_neighbor_counting():
    """Check neighbor counting logic"""
    grid = ConwayGrid(size=8)
    
    # Place specific pattern
    grid.grid[3, 3] = 1  # Center
    grid.grid[2, 3] = 1  # North
    grid.grid[4, 3] = 1  # South
    grid.grid[3, 2] = 1  # West
    
    # Center cell should have 3 neighbors
    neighbors = grid.get_neighbors(3, 3)
    print(f"Center cell (3,3) neighbors: {neighbors} (expected: 3)")
    
    if neighbors == 3:
        print("✅ Neighbor counting correct for test case")
    else:
        print(f"❌ Neighbor counting WRONG: got {neighbors}, expected 3")

if __name__ == "__main__":
    print("=== Conway Correctness Diagnosis ===\n")
    
    tests = [
        test_isolated_cell_dies,
        test_block_stable,
        test_blinker_period_2
    ]
    
    results = [test() for test in tests]
    
    print("\n--- Neighbor Counting Check ---")
    diagnose_neighbor_counting()
    
    print(f"\n=== Results: {sum(results)}/{len(results)} passed ===")
    
    if all(results):
        print("✅ Conway implementation appears correct")
    else:
        print("❌ Conway implementation has bugs")
        print("\nNext steps:")
        print("1. Review conway_grid.py step() method")
        print("2. Check neighbor counting logic")
        print("3. Verify new_grid is separate from self.grid")
        print("4. Test wraparound at edges")
```

**Execution**:
```bash
python scripts/diagnose_conway.py > logs/conway_diagnosis.txt
```

**Expected Output**:
- Clear identification of which test fails
- Specific error mode (neighbor count, update logic, etc.)

---

### Task 1F-2: Fix Conway Implementation

**File**: `src/core/conway_grid.py` (update)

**Requirements**:
- Fix identified bugs
- Use separate new_grid for updates
- Correct neighbor counting (exclude center)
- Proper toroidal wraparound
- Optional: use scipy.signal.convolve2d for correctness

**Corrected Implementation** (foolproof approach):
```python
import numpy as np
from scipy.signal import convolve2d
from typing import List
from dataclasses import dataclass

@dataclass
class CellDelta:
    x: int
    y: int
    alive: bool

class ConwayGrid:
    def __init__(self, size: int = 8):
        self.size = size
        self.grid = np.zeros((size, size), dtype=np.uint8)
        self.tick_count = 0
    
    def get_neighbors(self, x: int, y: int) -> int:
        """Count Moore neighborhood (8 neighbors) with wraparound"""
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Don't count center
                nx = (x + dx) % self.size
                ny = (y + dy) % self.size
                count += self.grid[ny, nx]  # Note: [y, x] indexing
        return count
    
    def step(self) -> List[CellDelta]:
        """
        Execute one Conway step using convolution (foolproof).
        Returns list of cell changes.
        """
        # Kernel for neighbor counting (excludes center)
        kernel = np.ones((3, 3), dtype=np.uint8)
        kernel[1, 1] = 0
        
        # Count neighbors with wraparound
        neighbors = convolve2d(self.grid, kernel, mode='same', boundary='wrap')
        
        # Apply Conway rules (B3/S23)
        new_grid = np.zeros_like(self.grid)
        
        # Birth: dead cell with exactly 3 neighbors
        new_grid[(self.grid == 0) & (neighbors == 3)] = 1
        
        # Survival: live cell with 2 or 3 neighbors
        new_grid[(self.grid == 1) & ((neighbors == 2) | (neighbors == 3))] = 1
        
        # Compute deltas
        deltas = []
        changed = np.argwhere(new_grid != self.grid)
        for y, x in changed:
            deltas.append(CellDelta(
                x=int(x),
                y=int(y),
                alive=bool(new_grid[y, x])
            ))
        
        # Update state
        self.grid = new_grid
        self.tick_count += 1
        
        return deltas
    
    def seed_glider(self, x: int, y: int):
        """Seed canonical glider at (x, y)"""
        # Glider pattern:
        #   .X.
        #   ..X
        #   XXX
        self.grid[y, x+1] = 1      # Top middle
        self.grid[y+1, x+2] = 1    # Middle right
        self.grid[y+2, x] = 1      # Bottom left
        self.grid[y+2, x+1] = 1    # Bottom middle
        self.grid[y+2, x+2] = 1    # Bottom right
    
    def get_state(self) -> np.ndarray:
        """Return copy of current grid state"""
        return self.grid.copy()
```

**Validation**:
```bash
# Re-run diagnosis script
python scripts/diagnose_conway.py

# Should now show all tests passing
```

---

### Task 1F-3: Add Conway Correctness Tests

**File**: `tests/phase_1f/test_conway_fixed.py`

**Requirements**:
- Test all Conway rules rigorously
- Test edge cases
- Test wraparound
- Test known patterns (glider, block, blinker)

**Implementation**:
```python
import pytest
import numpy as np
from src.core.conway_grid import ConwayGrid

def test_isolated_cell_dies():
    """Death: Cell with 0 neighbors dies"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1
    
    grid.step()
    
    assert grid.grid[3, 3] == 0, "Isolated cell should die"

def test_two_cells_both_die():
    """Death: Two cells with 1 neighbor each both die"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    
    grid.step()
    
    assert grid.grid[3, 3] == 0, "Cell with 1 neighbor should die"
    assert grid.grid[3, 4] == 0, "Cell with 1 neighbor should die"

def test_block_stable():
    """Survival: 2x2 block is stable (each has 3 neighbors)"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[4, 3] = 1
    grid.grid[4, 4] = 1
    
    before = grid.grid.copy()
    grid.step()
    
    assert np.array_equal(grid.grid, before), "Block should be stable"

def test_birth_rule():
    """Birth: Dead cell with exactly 3 neighbors becomes alive"""
    grid = ConwayGrid(size=8)
    grid.grid[2, 3] = 1  # North of center
    grid.grid[3, 2] = 1  # West of center
    grid.grid[3, 4] = 1  # East of center
    # Center (3,3) is dead with 3 neighbors
    
    grid.step()
    
    assert grid.grid[3, 3] == 1, "Cell with 3 neighbors should be born"

def test_overpopulation():
    """Death: Cell with 4+ neighbors dies"""
    grid = ConwayGrid(size=8)
    # Center surrounded by 4 neighbors (cross pattern)
    grid.grid[3, 3] = 1  # Center
    grid.grid[2, 3] = 1  # North
    grid.grid[4, 3] = 1  # South
    grid.grid[3, 2] = 1  # West
    grid.grid[3, 4] = 1  # East
    
    grid.step()
    
    assert grid.grid[3, 3] == 0, "Cell with 4 neighbors should die"

def test_blinker_oscillates():
    """Blinker pattern oscillates with period 2"""
    grid = ConwayGrid(size=8)
    # Horizontal blinker
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[3, 5] = 1
    
    state0 = grid.grid.copy()
    
    grid.step()
    state1 = grid.grid.copy()
    assert not np.array_equal(state0, state1), "Blinker should change"
    
    grid.step()
    state2 = grid.grid.copy()
    assert np.array_equal(state0, state2), "Blinker should return to original"

def test_glider_moves():
    """Glider pattern moves diagonally"""
    grid = ConwayGrid(size=16)  # Larger grid for movement
    grid.seed_glider(4, 4)
    
    # Count live cells
    initial_count = np.sum(grid.grid)
    assert initial_count == 5, "Glider should have 5 cells"
    
    # Step 4 times (one glider cycle)
    for _ in range(4):
        grid.step()
    
    final_count = np.sum(grid.grid)
    assert final_count == 5, "Glider should maintain 5 cells"

def test_wraparound_corner():
    """Wraparound: Corners see opposite corners as neighbors"""
    grid = ConwayGrid(size=8)
    grid.grid[0, 0] = 1  # Top-left corner
    
    # Manually check neighbors
    neighbors = grid.get_neighbors(0, 0)
    
    # Top-left corner should see bottom-right as diagonal neighbor
    # But since it's the only cell, it has 0 neighbors
    assert neighbors == 0, "Single corner cell should have 0 neighbors"

def test_edge_wraparound():
    """Wraparound: Edge cells see opposite edge"""
    grid = ConwayGrid(size=8)
    grid.grid[0, 4] = 1  # Top edge, middle
    grid.grid[7, 4] = 1  # Bottom edge, middle (wraps to top)
    
    neighbors_top = grid.get_neighbors(4, 0)
    assert neighbors_top >= 1, "Top edge should see bottom edge neighbor"
```

**Validation**:
```bash
pytest tests/phase_1f/test_conway_fixed.py -v -s
# All 9 tests must pass
```

---

### Task 1F-4: Add Interactive Web Controls

**File**: `src/api/conway_server.py` (update)

**Requirements**:
- WebSocket command handlers
- Safe atomic updates at tick boundaries
- Full state re-sync after commands
- Command audit logging

**Implementation**:
```python
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConwayRunner:
    def __init__(self, grid_size: int = 8, tick_ms: int = 500):
        self.grid = ConwayGrid(size=grid_size)
        self.embedding_grid = EmbeddingGrid(size=grid_size)
        self.tick_ms = tick_ms
        self.running = False
        self.websockets = set()
        self.tick_count = 0
        
        # Interactive mode
        self.mesh_mode = "coupled"  # or "decoupled"
        self.couple_policy = "birth"  # or "alive"
        
        # Command queue for atomic updates
        self.command_queue = []
    
    async def handle_command(self, websocket: WebSocket, data: dict):
        """Handle interactive commands from dashboard"""
        cmd_type = data.get("type")
        
        if cmd_type == "toggle_cell":
            x = data.get("x")
            y = data.get("y")
            if x is not None and y is not None and 0 <= x < 8 and 0 <= y < 8:
                self.command_queue.append({"type": "toggle", "x": x, "y": y})
                logger.info(f"Queued toggle cell ({x}, {y})")
        
        elif cmd_type == "set_mode":
            self.mesh_mode = data.get("mesh_mode", "coupled")
            self.couple_policy = data.get("policy", "birth")
            logger.info(f"Set mode: {self.mesh_mode}, policy: {self.couple_policy}")
            await websocket.send_json({
                "type": "mode_changed",
                "mesh_mode": self.mesh_mode,
                "policy": self.couple_policy
            })
        
        elif cmd_type == "randomize_dead_embeddings":
            self.command_queue.append({"type": "randomize"})
            logger.info("Queued randomize dead embeddings")
        
        elif cmd_type == "reset":
            self.command_queue.append({"type": "reset"})
            logger.info("Queued reset")
    
    def process_commands(self):
        """Process queued commands at tick boundary"""
        for cmd in self.command_queue:
            if cmd["type"] == "toggle":
                x, y = cmd["x"], cmd["y"]
                self.grid.grid[y, x] = 1 - self.grid.grid[y, x]
                logger.info(f"Toggled cell ({x}, {y})")
            
            elif cmd["type"] == "randomize":
                for i, state in enumerate(self.embedding_grid.states):
                    x, y = i % 8, i // 8
                    if self.grid.grid[y, x] == 0:  # Dead cell
                        rand_vec = np.random.randn(state.dim).astype(np.float16)
                        rand_vec /= np.linalg.norm(rand_vec) + 1e-8
                        state.vector = rand_vec
                logger.info("Randomized dead cell embeddings")
            
            elif cmd["type"] == "reset":
                self.grid.grid.fill(0)
                self.grid.seed_glider(1, 1)
                logger.info("Reset grid with glider")
        
        self.command_queue.clear()
    
    async def run_loop(self):
        """Main loop with command processing"""
        self.running = True
        self.grid.seed_glider(1, 1)
        
        while self.running:
            tick_start = time.perf_counter()
            
            # Process queued commands
            self.process_commands()
            
            # Conway step
            conway_deltas = self.grid.step()
            
            # Embedding step (if mode allows)
            # ... existing embedding logic
            
            self.tick_count += 1
            
            # Broadcast
            await self.broadcast_conway_deltas(conway_deltas)
            # ... other broadcasts
            
            # Maintain tick rate
            elapsed = time.perf_counter() - tick_start
            sleep_time = (self.tick_ms / 1000.0) - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
```

**Update WebSocket handler**:
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await runner.add_client(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle commands
            await runner.handle_command(websocket, message)
            
    except WebSocketDisconnect:
        runner.remove_client(websocket)
```

---

### Task 1F-5: Add Interactive Dashboard Controls

**File**: `dashboard/index.html` (update)

**Requirements**:
- Click-to-toggle cells
- Mode toggle (Coupled/Decoupled)
- Randomize button
- Visual feedback

**HTML additions**:
```html
<div class="controls">
    <button id="btn-reset" class="btn btn-primary">Reset Glider</button>
    
    <div class="mode-toggle">
        <label class="toggle-label">
            <input type="checkbox" id="toggle-coupled" checked>
            <span>Coupled (Conway-driven)</span>
        </label>
        <select id="policy-select">
            <option value="birth">Birth</option>
            <option value="alive">Alive</option>
        </select>
    </div>
    
    <button id="btn-randomize" class="btn btn-secondary">Randomize Embeddings</button>
</div>

<div class="info-panel">
    <h3>Interactive Controls</h3>
    <ul>
        <li><strong>Click cells</strong> to toggle alive/dead</li>
        <li><strong>Coupled mode</strong>: Deltas pass only on Conway births</li>
        <li><strong>Decoupled mode</strong>: Deltas pass by policy</li>
        <li><strong>Randomize</strong>: Reset dead cell embeddings</li>
    </ul>
</div>
```

**JS handlers** (`dashboard/static/js/controls.js`):
```javascript
// Cell click handler
function initializeCellClicks() {
    document.getElementById('conway-grid').addEventListener('click', (e) => {
        if (e.target.classList.contains('cell')) {
            const x = parseInt(e.target.dataset.x);
            const y = parseInt(e.target.dataset.y);
            
            if (wsClient && wsClient.ws && wsClient.ws.readyState === WebSocket.OPEN) {
                wsClient.send(JSON.stringify({
                    type: "toggle_cell",
                    x: x,
                    y: y
                }));
                
                // Visual feedback
                e.target.classList.add('clicked');
                setTimeout(() => e.target.classList.remove('clicked'), 300);
            }
        }
    });
}

// Mode toggle
document.getElementById('toggle-coupled').addEventListener('change', (e) => {
    const mode = e.target.checked ? "coupled" : "decoupled";
    const policy = document.getElementById('policy-select').value;
    
    wsClient.send(JSON.stringify({
        type: "set_mode",
        mesh_mode: mode,
        policy: policy
    }));
});

// Randomize button
document.getElementById('btn-randomize').addEventListener('click', () => {
    wsClient.send(JSON.stringify({
        type: "randomize_dead_embeddings"
    }));
});
```

---

## Validation Gates

### Gate 1: Conway Diagnosis
```bash
python scripts/diagnose_conway.py
# All 3 diagnostic tests must pass
```

### Gate 2: Conway Unit Tests
```bash
pytest tests/phase_1f/test_conway_fixed.py -v -s
# All 9 tests must pass
```

### Gate 3: Interactive Controls Test
```bash
# Manual browser test:
# 1. Start server
# 2. Open http://localhost:8000
# 3. Click cells → should toggle
# 4. Toggle mode → should update
# 5. Randomize → should affect dead cells
```

### Gate 4: End-to-End Validation
```bash
# 30-second observation:
# - Conway rules correct (glider moves properly)
# - Cell clicks work
# - Mode toggle affects behavior
# - No console errors
```

### Gate 5: Linting & Type Checking
```bash
ruff check src/core/conway_grid.py src/api/conway_server.py
mypy src/core/conway_grid.py --strict
```

---

## Success Criteria

Phase 1F (and Phase 1 overall) is complete when:

- [ ] Conway rules execute correctly (all 9 tests pass)
- [ ] No cells incorrectly stay alive or die
- [ ] Glider moves properly without corruption
- [ ] Cell click-to-toggle works
- [ ] Mode toggle (coupled/decoupled) works
- [ ] Randomize embeddings works
- [ ] Dashboard shows clear legend
- [ ] No console errors
- [ ] All validation gates pass
- [ ] Living docs updated

---

## Deliverables

1. **Fixed Implementation**:
   - `src/core/conway_grid.py` (corrected)
   - `src/api/conway_server.py` (commands)

2. **Tests**:
   - `scripts/diagnose_conway.py`
   - `tests/phase_1f/test_conway_fixed.py` (9 tests)

3. **Interactive Layer**:
   - `dashboard/index.html` (controls)
   - `dashboard/static/js/controls.js` (handlers)

4. **Documentation**:
   - REPLICATION-NOTES.md updated
   - TROUBLESHOOTING.md updated
   - logs/conway_diagnosis.txt

---

## Failure Handling

If Conway diagnosis fails:

1. **Capture detailed state**:
   ```bash
   python scripts/diagnose_conway.py > logs/failure_conway.txt
   # Save grid states, neighbor counts, delta
   ```

2. **Update TROUBLESHOOTING.md**:
   ```markdown
   ### Conway Cells Not Dying
   **Context**: Phase 1F diagnosis, test_isolated_cell_dies
   **Symptom**: Cell (3,3) alive after step, should be dead
   **Error Snippet**: "Isolated cell did NOT die"
   **Probable Cause**: In-place update or neighbor counting includes center
   **Quick Fix**: Use separate new_grid array, exclude center in neighbor count
   **Permanent Fix**: Use scipy.signal.convolve2d with boundary='wrap'
   **Prevention**: Add test_isolated_cell_dies to CI
   **Tags**: conway, correctness, P0
   ```

3. **Create ISSUE.md** and halt

---

## Timeline

- Task 1F-1 (Diagnosis): 30 min
- Task 1F-2 (Fix): 1 hour
- Task 1F-3 (Tests): 1 hour
- Task 1F-4 (Backend): 1 hour
- Task 1F-5 (Frontend): 1 hour
- **Total: 4.5 hours**

---

This task is **ready for execution** and is **CRITICAL** for Phase 1 completion.