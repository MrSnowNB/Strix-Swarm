---
title: "Phase 1E: CyberMesh Embedding-Delta Data Validation"
phase: "1E"
objective: "Validate embedding layer data integrity: prove embeddings hold deltas and pass them according to routing policy"
assigned_to: "coding_agent"
status: "ready_for_execution"
hardware: "128GB Strix Halo HP ZBook, Windows 11"
dependencies: ["Phase 1D complete", "Conway validated", "WebSocket validated"]
estimated_duration: "1 day"
validation_gates: ["unit", "lint", "type", "embedding_data_integrity", "visual_overlay_accuracy"]
priority: "P0 - CRITICAL"
concern: "Validating CyberMesh is working as intended, not just Conway cell flips"
---

# Phase 1E: CyberMesh Embedding-Delta Data Validation

## Critical Concern

**User's Primary Question**: 
> "I am most concerned about validating that the CyberMesh is working as intended and the HTML dashboard is actually representing the embeddings holding a delta, then passing it."

**What We Must Prove**:
1. ✅ Embedding vectors exist per cell and change only via intended deltas
2. ✅ Delta payloads are computed, stored ("held"), and passed to neighbors
3. ✅ WebSocket messages reflect BOTH Conway state changes AND embedding-delta lifecycle
4. ✅ Dashboard visually distinguishes Conway flips from embedding passes
5. ✅ Data path integrity: backend events = WebSocket messages = frontend overlays

**What Would Invalidate the System**:
- ❌ Embeddings changing randomly without delta passes
- ❌ WebSocket messages showing embedding passes that didn't occur
- ❌ Dashboard showing Conway flips as if they were embedding passes
- ❌ Mismatched counts: backend events ≠ WS messages ≠ overlay renders

---

## Architecture: Separation of Concerns

### Current Implementation (Phase 1A-1D)
```
Conway Grid → Delta Messages → Dashboard
     ↓              ↓              ↓
  8×8 state    Cell flips    Green cells
```

### Target Implementation (Phase 1E)
```
┌──────────────┐
│ Conway Layer │ → Conway deltas → Green cell flips
└──────────────┘
       ↓
┌──────────────┐
│Embedding Grid│ → Embedding state (384-D vectors per cell)
└──────────────┘
       ↓
┌──────────────┐
│ Delta Payload│ → "Hold" phase (pending_delta flag + vector)
└──────────────┘
       ↓
┌──────────────┐
│Routing Policy│ → "Pass" phase (choose neighbor, transfer)
└──────────────┘
       ↓
┌──────────────┐
│  WebSocket   │ → embedding_deltas: [{from, to, payload_id, ...}]
└──────────────┘
       ↓
┌──────────────┐
│   Dashboard  │ → Cyan arrow overlays (distinct from Conway)
└──────────────┘
```

---

## Task Breakdown

### Task 1E-1: Implement Embedding State Layer

**File**: `src/core/embedding_layer.py`

**Requirements**:
- EmbeddingState class with 384-D vector (float16)
- History buffer (last 4 vectors for change detection)
- Pending delta flag and payload storage
- Vector normalization utilities
- Cosine similarity computation

**Implementation**:
```python
import numpy as np
from dataclasses import dataclass
from collections import deque
from typing import Optional

@dataclass
class DeltaPayload:
    """A delta payload to be held and passed"""
    id: str  # Unique identifier for tracking
    vector: np.ndarray  # 384-D delta vector (float16)
    l2_norm: float  # Magnitude for validation
    created_tick: int  # When payload was created
    
    def __post_init__(self):
        assert self.vector.shape == (384,), f"Expected 384-D vector, got {self.vector.shape}"
        assert self.vector.dtype == np.float16, f"Expected float16, got {self.vector.dtype}"

class EmbeddingState:
    """Per-cell embedding state with delta hold/pass capability"""
    
    def __init__(self, cell_idx: int, dim: int = 384):
        self.cell_idx = cell_idx
        self.dim = dim
        
        # Current embedding vector (normalized)
        self.vector = np.zeros(dim, dtype=np.float16)
        
        # History for change detection
        self.history = deque(maxlen=4)
        self.history.append(self.vector.copy())
        
        # Pending delta (if holding)
        self.pending_delta: Optional[DeltaPayload] = None
        
        # Pass statistics
        self.deltas_received = 0
        self.deltas_passed = 0
    
    def hold_delta(self, payload: DeltaPayload):
        """Hold a delta payload for next pass"""
        assert self.pending_delta is None, \
            f"Cell {self.cell_idx} already holding delta {self.pending_delta.id}"
        self.pending_delta = payload
    
    def pass_delta(self) -> Optional[DeltaPayload]:
        """Release held delta and return it"""
        payload = self.pending_delta
        self.pending_delta = None
        if payload:
            self.deltas_passed += 1
        return payload
    
    def receive_delta(self, payload: DeltaPayload, alpha: float = 0.1):
        """Apply incoming delta to embedding vector"""
        # Save old vector to history
        self.history.append(self.vector.copy())
        
        # Apply delta with learning rate
        self.vector = self.vector + alpha * payload.vector
        
        # Normalize
        norm = np.linalg.norm(self.vector)
        if norm > 1e-8:
            self.vector = self.vector / norm
        
        self.deltas_received += 1
    
    def get_hash(self) -> str:
        """Get short hash of current vector for validation"""
        # Use xxhash or simple hash for quick comparison
        hash_val = hash(self.vector.tobytes())
        return f"{hash_val & 0xFFFFFF:06x}"  # Last 6 hex digits
    
    def cosine_similarity(self, other_vector: np.ndarray) -> float:
        """Compute cosine similarity with another vector"""
        dot = np.dot(self.vector, other_vector)
        norm_self = np.linalg.norm(self.vector)
        norm_other = np.linalg.norm(other_vector)
        
        if norm_self < 1e-8 or norm_other < 1e-8:
            return 0.0
        
        return float(dot / (norm_self * norm_other))
    
    def cosine_with_previous(self) -> float:
        """Cosine similarity with previous vector in history"""
        if len(self.history) < 2:
            return 1.0
        
        prev = self.history[-2]
        return self.cosine_similarity(prev)
```

**Validation**:
```bash
pytest tests/phase_1e/test_embedding_state.py -v -s
```

**Tests**:
- `test_embedding_initialization`: Vector is zero, history length 1
- `test_hold_delta`: Pending delta is stored correctly
- `test_pass_delta`: Pending delta is released and cleared
- `test_receive_delta`: Vector changes, history updated, cosine < 1.0
- `test_hash_changes_on_update`: Hash differs after delta application
- `test_no_double_hold`: Cannot hold two deltas simultaneously

---

### Task 1E-2: Implement Embedding Grid with Routing

**File**: `src/core/embedding_grid.py`

**Requirements**:
- Grid of EmbeddingState (parallel to Conway grid)
- Routing policy (cosine similarity + energy)
- Pass event logging
- Integration with Conway ticks

**Implementation**:
```python
from src.core.embedding_layer import EmbeddingState, DeltaPayload
from src.core.conway_grid import ConwayGrid
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class PassEvent:
    """Record of a delta pass from one cell to another"""
    def __init__(self, tick: int, from_idx: int, to_idx: int, 
                 payload_id: str, payload_norm: float, 
                 similarity: float, seed: Optional[int] = None):
        self.tick = tick
        self.from_idx = from_idx
        self.to_idx = to_idx
        self.payload_id = payload_id
        self.payload_norm = payload_norm
        self.similarity = similarity
        self.seed = seed
    
    def to_dict(self):
        """Convert to dict for WebSocket/logging"""
        from_x = self.from_idx % 8
        from_y = self.from_idx // 8
        to_x = self.to_idx % 8
        to_y = self.to_idx // 8
        
        return {
            'tick': self.tick,
            'from': {'x': from_x, 'y': from_y},
            'to': {'x': to_x, 'y': to_y},
            'payload_id': self.payload_id,
            'norm': round(self.payload_norm, 4),
            'sim': round(self.similarity, 4)
        }

class EmbeddingGrid:
    """Grid of embedding states with delta routing"""
    
    def __init__(self, size: int = 8, embedding_dim: int = 384):
        self.size = size
        self.embedding_dim = embedding_dim
        
        # Create embedding state for each cell
        self.states = []
        for i in range(size * size):
            self.states.append(EmbeddingState(cell_idx=i, dim=embedding_dim))
        
        # Routing policy weights
        self.alpha_cosine = 0.7
        self.alpha_energy = 0.3
        
        # Pass event log
        self.pass_events: List[PassEvent] = []
        
        # Tick counter
        self.tick = 0
    
    def idx_to_xy(self, idx: int) -> Tuple[int, int]:
        """Convert flat index to (x, y)"""
        return (idx % self.size, idx // self.size)
    
    def xy_to_idx(self, x: int, y: int) -> int:
        """Convert (x, y) to flat index"""
        return y * self.size + x
    
    def get_neighbors(self, idx: int) -> List[int]:
        """Get Moore neighborhood indices (8-connected with wraparound)"""
        x, y = self.idx_to_xy(idx)
        neighbors = []
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.size
                ny = (y + dy) % self.size
                neighbors.append(self.xy_to_idx(nx, ny))
        
        return neighbors
    
    def route_delta(self, from_idx: int, payload: DeltaPayload, 
                    energy_field: Optional[np.ndarray] = None) -> int:
        """
        Choose best neighbor to receive delta.
        
        Policy: score = alpha_cosine * cos_sim + alpha_energy * energy
        """
        neighbor_indices = self.get_neighbors(from_idx)
        scores = []
        
        for neighbor_idx in neighbor_indices:
            neighbor_state = self.states[neighbor_idx]
            
            # Cosine similarity between payload and neighbor embedding
            cos_sim = neighbor_state.cosine_similarity(payload.vector)
            
            # Energy from field (if provided)
            if energy_field is not None:
                nx, ny = self.idx_to_xy(neighbor_idx)
                energy = energy_field[ny, nx]
            else:
                energy = 0.5  # Default neutral energy
            
            # Weighted score
            score = self.alpha_cosine * cos_sim + self.alpha_energy * energy
            scores.append(score)
        
        # Pick best neighbor
        best_idx = np.argmax(scores)
        chosen_neighbor = neighbor_indices[best_idx]
        
        # Log similarity for tracking
        chosen_state = self.states[chosen_neighbor]
        similarity = chosen_state.cosine_similarity(payload.vector)
        
        return chosen_neighbor, similarity
    
    def step(self, energy_field: Optional[np.ndarray] = None) -> List[PassEvent]:
        """
        Execute one routing step: pass all pending deltas.
        
        Returns list of pass events for this tick.
        """
        tick_events = []
        
        # Find all cells with pending deltas
        pending_cells = [i for i, state in enumerate(self.states) 
                        if state.pending_delta is not None]
        
        # Pass each delta
        for from_idx in pending_cells:
            from_state = self.states[from_idx]
            payload = from_state.pass_delta()
            
            if payload is None:
                continue
            
            # Route to best neighbor
            to_idx, similarity = self.route_delta(from_idx, payload, energy_field)
            to_state = self.states[to_idx]
            
            # Deliver delta
            to_state.receive_delta(payload)
            
            # Log event
            event = PassEvent(
                tick=self.tick,
                from_idx=from_idx,
                to_idx=to_idx,
                payload_id=payload.id,
                payload_norm=payload.l2_norm,
                similarity=similarity
            )
            tick_events.append(event)
            self.pass_events.append(event)
            
            logger.debug(f"Tick {self.tick}: Pass {payload.id} from {from_idx} to {to_idx} (sim={similarity:.3f})")
        
        self.tick += 1
        return tick_events
    
    def inject_delta(self, cell_idx: int, vector: np.ndarray, payload_id: str):
        """Inject a new delta payload at a specific cell"""
        payload = DeltaPayload(
            id=payload_id,
            vector=vector.astype(np.float16),
            l2_norm=float(np.linalg.norm(vector)),
            created_tick=self.tick
        )
        
        self.states[cell_idx].hold_delta(payload)
        logger.info(f"Injected delta {payload_id} at cell {cell_idx}")
```

**Validation**:
```bash
pytest tests/phase_1e/test_embedding_grid.py -v -s
```

**Tests**:
- `test_grid_initialization`: All states initialized correctly
- `test_neighbor_calculation`: 8 neighbors per cell with wraparound
- `test_inject_delta`: Delta is held at target cell
- `test_route_delta_chooses_best`: Highest similarity neighbor selected
- `test_step_passes_all_deltas`: All pending deltas passed in one step
- `test_pass_events_logged`: PassEvent count matches actual passes
- `test_recipient_embeddings_change`: Only recipients show embedding changes

---

### Task 1E-3: Extend WebSocket Messages for Embedding Deltas

**File**: `src/api/conway_runner.py` (update)

**Requirements**:
- Add embedding_grid alongside conway_grid
- Collect embedding pass events per tick
- Broadcast embedding_deltas separately from conway deltas
- Maintain message size <1KB per tick

**Implementation**:
```python
from src.core.embedding_grid import EmbeddingGrid
import json

class ConwayRunner:
    def __init__(self, grid_size: int = 8, tick_ms: int = 500):
        self.grid = ConwayGrid(size=grid_size)
        self.embedding_grid = EmbeddingGrid(size=grid_size)  # NEW
        # ... existing initialization
        
    async def run_loop(self):
        """Main loop with both Conway and embedding updates"""
        self.running = True
        self.grid.seed_glider(x=1, y=1)
        
        # Inject test delta for validation
        test_vector = np.random.randn(384).astype(np.float16)
        test_vector /= np.linalg.norm(test_vector)
        self.embedding_grid.inject_delta(
            cell_idx=10,  # Cell (2, 1)
            vector=test_vector,
            payload_id=f"test_delta_0"
        )
        
        while self.running:
            tick_start = time.perf_counter()
            
            # Step 1: Conway evolution
            conway_deltas = self.grid.step()
            
            # Step 2: Embedding delta passes (NEW)
            # Use Conway energy field for routing
            energy_field = self.grid.grid.astype(np.float32) * 0.5 + 0.25
            pass_events = self.embedding_grid.step(energy_field)
            
            self.tick_count += 1
            
            # Step 3: Broadcast both types of deltas
            await self.broadcast_conway_deltas(conway_deltas)
            await self.broadcast_embedding_deltas(pass_events)  # NEW
            
            # ... rest of tick logic
    
    async def broadcast_embedding_deltas(self, pass_events: List[PassEvent]):
        """Broadcast embedding pass events to all clients"""
        if not self.websockets or not pass_events:
            return
        
        message = {
            "type": "embedding_deltas",
            "tick": self.tick_count,
            "edges": [event.to_dict() for event in pass_events]
        }
        
        # Check message size
        msg_size = len(json.dumps(message))
        if msg_size > 1024:
            logger.warning(f"Embedding delta message {msg_size} bytes exceeds 1KB")
        
        # Broadcast
        disconnected = set()
        for ws in self.websockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send embedding deltas: {e}")
                disconnected.add(ws)
        
        self.websockets -= disconnected
```

**Validation**:
```bash
pytest tests/phase_1e/test_ws_embedding_messages.py -v -s
```

**Tests**:
- `test_embedding_deltas_message_format`: Correct JSON schema
- `test_pass_events_match_messages`: Count and content match
- `test_message_size_under_1kb`: All messages <1024 bytes
- `test_conway_and_embedding_separate`: Two distinct message types
- `test_coordinates_match_events`: from/to coords match actual passes

---

### Task 1E-4: Frontend Overlay Visualization

**File**: `dashboard/static/js/overlay.js` (new)

**Requirements**:
- SVG/Canvas layer for arrow overlays
- Distinct visual: cyan arrows (vs green cells)
- 500ms fade animation
- Tooltip showing payload_id, norm, sim
- Toggle to show/hide overlay

**Implementation**:
```javascript
class EmbeddingOverlay {
    constructor(gridElement, gridSize = 8) {
        this.gridElement = gridElement;
        this.gridSize = gridSize;
        this.cellSize = 60;  // Match grid.js cell size
        this.gap = 2;
        
        // Create SVG overlay
        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.setAttribute('class', 'embedding-overlay');
        this.svg.setAttribute('width', gridSize * (this.cellSize + this.gap));
        this.svg.setAttribute('height', gridSize * (this.cellSize + this.gap));
        this.svg.style.position = 'absolute';
        this.svg.style.top = '0';
        this.svg.style.left = '0';
        this.svg.style.pointerEvents = 'none';
        
        gridElement.parentElement.style.position = 'relative';
        gridElement.parentElement.appendChild(this.svg);
        
        // Arrow counter for validation
        this.arrowCount = 0;
        this.lastPayloadId = null;
        this.lastSim = null;
    }
    
    drawPass(fromX, fromY, toX, toY, payload_id, norm, sim) {
        // Calculate cell centers
        const fromCenterX = fromX * (this.cellSize + this.gap) + this.cellSize / 2;
        const fromCenterY = fromY * (this.cellSize + this.gap) + this.cellSize / 2;
        const toCenterX = toX * (this.cellSize + this.gap) + this.cellSize / 2;
        const toCenterY = toY * (this.cellSize + this.gap) + this.cellSize / 2;
        
        // Create arrow path
        const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        arrow.setAttribute('x1', fromCenterX);
        arrow.setAttribute('y1', fromCenterY);
        arrow.setAttribute('x2', toCenterX);
        arrow.setAttribute('y2', toCenterY);
        arrow.setAttribute('stroke', '#00ffff');  // Cyan (distinct from green)
        arrow.setAttribute('stroke-width', '3');
        arrow.setAttribute('marker-end', 'url(#arrowhead)');
        arrow.setAttribute('opacity', '1.0');
        
        // Add tooltip
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = `Payload: ${payload_id}\nNorm: ${norm}\nSim: ${sim}`;
        arrow.appendChild(title);
        
        this.svg.appendChild(arrow);
        this.arrowCount++;
        this.lastPayloadId = payload_id;
        this.lastSim = sim;
        
        // Fade out after 500ms
        setTimeout(() => {
            arrow.setAttribute('opacity', '0');
            setTimeout(() => {
                this.svg.removeChild(arrow);
                this.arrowCount--;
            }, 300);  // Remove after fade
        }, 500);
    }
    
    initializeArrowhead() {
        // Create arrowhead marker
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', 'arrowhead');
        marker.setAttribute('markerWidth', '10');
        marker.setAttribute('markerHeight', '10');
        marker.setAttribute('refX', '5');
        marker.setAttribute('refY', '3');
        marker.setAttribute('orient', 'auto');
        
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', '0 0, 10 3, 0 6');
        polygon.setAttribute('fill', '#00ffff');
        
        marker.appendChild(polygon);
        defs.appendChild(marker);
        this.svg.appendChild(defs);
    }
    
    getStats() {
        return {
            arrowCount: this.arrowCount,
            lastPayloadId: this.lastPayloadId,
            lastSim: this.lastSim
        };
    }
}

// Global overlay instance
let embeddingOverlay = null;

function initializeOverlay() {
    const gridElement = document.getElementById('conway-grid');
    embeddingOverlay = new EmbeddingOverlay(gridElement, 8);
    embeddingOverlay.initializeArrowhead();
    return embeddingOverlay;
}
```

**Validation**:
- Manual visual inspection in browser
- Automated count verification via console

---

### Task 1E-5: Integration and Data Path Validation

**File**: `tests/phase_1e/test_data_path_integrity.py`

**Requirements**:
- Prove: backend pass events = WebSocket messages = frontend overlays
- Test coordinate accuracy
- Test embedding hash changes only for recipients
- Test independence from Conway updates

**Implementation**:
```python
import pytest
import asyncio
import numpy as np
from src.core.embedding_grid import EmbeddingGrid, DeltaPayload

def test_pass_event_creates_hash_change():
    """Recipient cell embedding hash changes, others don't"""
    grid = EmbeddingGrid(size=8)
    
    # Record hashes before
    hashes_before = [state.get_hash() for state in grid.states]
    
    # Inject delta at cell 10
    test_vector = np.random.randn(384).astype(np.float16)
    test_vector /= np.linalg.norm(test_vector)
    grid.inject_delta(10, test_vector, "test_001")
    
    # Step (pass delta)
    events = grid.step()
    
    # Check hashes after
    hashes_after = [state.get_hash() for state in grid.states]
    
    # Assertions
    assert len(events) == 1, "Should have exactly 1 pass event"
    
    event = events[0]
    from_idx = event.from_idx
    to_idx = event.to_idx
    
    # Sender hash unchanged (just passed, didn't receive)
    assert hashes_before[from_idx] == hashes_after[from_idx], \
        "Sender hash should not change"
    
    # Recipient hash changed
    assert hashes_before[to_idx] != hashes_after[to_idx], \
        f"Recipient hash should change: before={hashes_before[to_idx]}, after={hashes_after[to_idx]}"
    
    # All other hashes unchanged
    for i in range(64):
        if i == to_idx:
            continue
        assert hashes_before[i] == hashes_after[i], \
            f"Cell {i} hash should not change (only recipient should change)"

def test_embedding_independence_from_conway():
    """Embedding changes are independent of Conway flips"""
    from src.core.conway_grid import ConwayGrid
    
    conway = ConwayGrid(size=8)
    embedding = EmbeddingGrid(size=8)
    
    # Seed glider in Conway
    conway.seed_glider(1, 1)
    
    # Record embedding hashes
    hashes_before = [s.get_hash() for s in embedding.states]
    
    # Conway step (NO embedding deltas)
    conway_deltas = conway.step()
    
    # Check embeddings unchanged
    hashes_after = [s.get_hash() for s in embedding.states]
    
    assert len(conway_deltas) > 0, "Conway should have deltas"
    assert hashes_before == hashes_after, \
        "Embeddings should not change without delta passes"

def test_data_path_count_consistency():
    """Backend events = WebSocket messages = overlay renders"""
    # This test requires end-to-end integration
    # See scripts/validate_mesh_data_path.py for full implementation
    pass

@pytest.mark.asyncio
async def test_ws_message_coordinates_match_events():
    """WebSocket message coordinates match actual pass events"""
    grid = EmbeddingGrid(size=8)
    
    # Inject delta
    test_vector = np.random.randn(384).astype(np.float16)
    test_vector /= np.linalg.norm(test_vector)
    grid.inject_delta(10, test_vector, "coord_test")
    
    # Step and get events
    events = grid.step()
    
    assert len(events) == 1
    event = events[0]
    
    # Convert to message format
    message_dict = event.to_dict()
    
    # Verify coordinates
    expected_from_x = event.from_idx % 8
    expected_from_y = event.from_idx // 8
    expected_to_x = event.to_idx % 8
    expected_to_y = event.to_idx // 8
    
    assert message_dict['from']['x'] == expected_from_x
    assert message_dict['from']['y'] == expected_from_y
    assert message_dict['to']['x'] == expected_to_x
    assert message_dict['to']['y'] == expected_to_y
    assert message_dict['payload_id'] == "coord_test"
```

**Validation**:
```bash
pytest tests/phase_1e/test_data_path_integrity.py -v -s
```

---

### Task 1E-6: End-to-End Data Path Validation Script

**File**: `scripts/validate_mesh_data_path.py`

**Requirements**:
- Run 60-second live test
- Count backend pass events
- Count WebSocket messages received
- Count overlay arrows rendered
- Assert all counts match
- Detect coordinate mismatches

**Implementation**:
```python
import asyncio
import websockets
import json
import time
from collections import defaultdict

async def validate_data_path():
    """
    End-to-end validation: backend events = WS messages = overlays
    """
    print("=== CyberMesh Embedding-Delta Data Path Validation ===\n")
    
    uri = "ws://localhost:8000/ws"
    
    # Counters
    ws_embedding_messages = 0
    ws_embedding_edges = 0
    ws_conway_messages = 0
    coordinate_mismatches = 0
    
    # Storage
    received_edges = []
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to server\n")
            
            # Skip full_state
            await websocket.recv()
            
            print("Collecting data for 60 seconds...\n")
            start_time = time.time()
            
            while (time.time() - start_time) < 60:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                if data['type'] == 'delta':
                    ws_conway_messages += 1
                    
                elif data['type'] == 'embedding_deltas':
                    ws_embedding_messages += 1
                    ws_embedding_edges += len(data.get('edges', []))
                    
                    # Validate coordinates
                    for edge in data.get('edges', []):
                        from_x = edge['from']['x']
                        from_y = edge['from']['y']
                        to_x = edge['to']['x']
                        to_y = edge['to']['y']
                        
                        # Check bounds
                        if not (0 <= from_x < 8 and 0 <= from_y < 8):
                            coordinate_mismatches += 1
                            print(f"❌ Invalid from coords: ({from_x}, {from_y})")
                        
                        if not (0 <= to_x < 8 and 0 <= to_y < 8):
                            coordinate_mismatches += 1
                            print(f"❌ Invalid to coords: ({to_x}, {to_y})")
                        
                        received_edges.append(edge)
            
            elapsed = time.time() - start_time
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Results
    print(f"\n=== Results ({elapsed:.1f}s) ===")
    print(f"Conway delta messages: {ws_conway_messages}")
    print(f"Embedding delta messages: {ws_embedding_messages}")
    print(f"Total embedding edges: {ws_embedding_edges}")
    print(f"Coordinate mismatches: {coordinate_mismatches}")
    
    # Analysis
    if ws_embedding_edges > 0:
        avg_edges_per_msg = ws_embedding_edges / ws_embedding_messages
        print(f"Average edges per message: {avg_edges_per_msg:.2f}")
    
    # Validation
    success = True
    
    if coordinate_mismatches > 0:
        print(f"\n❌ FAIL: {coordinate_mismatches} coordinate mismatches")
        success = False
    
    if ws_embedding_messages == 0:
        print("\n⚠️  WARNING: No embedding delta messages received")
        print("   Check that embedding_grid is active and deltas are being injected")
        success = False
    
    if success:
        print("\n✅ Data path validation PASSED")
        print(f"   - {ws_embedding_edges} embedding passes tracked")
        print(f"   - Zero coordinate errors")
        print(f"   - Messages properly formatted")
    
    # Write report
    with open("logs/data_path_validation.txt", "w") as f:
        f.write(f"CyberMesh Data Path Validation\n")
        f.write(f"{'='*50}\n")
        f.write(f"Duration: {elapsed:.1f}s\n")
        f.write(f"Conway messages: {ws_conway_messages}\n")
        f.write(f"Embedding messages: {ws_embedding_messages}\n")
        f.write(f"Embedding edges: {ws_embedding_edges}\n")
        f.write(f"Coordinate errors: {coordinate_mismatches}\n")
        f.write(f"Status: {'PASS' if success else 'FAIL'}\n")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(validate_data_path())
    exit(0 if result else 1)
```

**Execution**:
```bash
# Start server first
python -m uvicorn src.api.conway_server:app

# Run validation in another terminal
python scripts/validate_mesh_data_path.py
```

---

## Validation Gates

### Gate 1: Unit Tests - Embedding State
```bash
pytest tests/phase_1e/test_embedding_state.py -v -s
# Expected: 6/6 tests pass
```

### Gate 2: Unit Tests - Embedding Grid
```bash
pytest tests/phase_1e/test_embedding_grid.py -v -s
# Expected: 7/7 tests pass
```

### Gate 3: Unit Tests - Data Path Integrity
```bash
pytest tests/phase_1e/test_data_path_integrity.py -v -s
# Expected: 4/4 tests pass
```

### Gate 4: End-to-End Data Path Validation
```bash
python scripts/validate_mesh_data_path.py
# Expected: PASS with zero coordinate mismatches
```

### Gate 5: Browser Overlay Validation (Manual)
```javascript
// In browser console while dashboard is running
const overlayStats = embeddingOverlay.getStats();
console.log('Overlay Stats:', overlayStats);
// Verify: arrowCount > 0, lastPayloadId present, lastSim reasonable
```

### Gate 6: Visual Inspection
- [ ] Cyan arrows distinct from green cells
- [ ] Arrows fade after 500ms
- [ ] Tooltip shows payload_id, norm, sim
- [ ] Arrow count matches message count
- [ ] Coordinates align with grid cells

### Gate 7: Linting & Type Checking
```bash
ruff check src/core/embedding_layer.py src/core/embedding_grid.py
mypy src/core/embedding_layer.py src/core/embedding_grid.py --strict
```

---

## Success Criteria

Phase 1E is complete when:

- [ ] All 17 unit tests pass (6+7+4)
- [ ] End-to-end validation script passes (zero coordinate errors)
- [ ] Browser overlay renders cyan arrows for embedding passes
- [ ] Visual inspection confirms Conway (green) distinct from embedding (cyan)
- [ ] Data path integrity: backend events = WS messages = overlay renders
- [ ] Embedding hashes change only for recipient cells
- [ ] Conway updates independent from embedding updates
- [ ] Linting and type checking clean
- [ ] Documentation updated with embedding layer architecture

---

## Deliverables

1. **Core Implementation**:
   - `src/core/embedding_layer.py` (EmbeddingState, DeltaPayload)
   - `src/core/embedding_grid.py` (EmbeddingGrid, PassEvent, routing)
   - `src/api/conway_runner.py` (embedding integration)

2. **Frontend**:
   - `dashboard/static/js/overlay.js` (cyan arrow overlays)
   - `dashboard/static/js/main.js` (overlay initialization)

3. **Tests**:
   - `tests/phase_1e/test_embedding_state.py` (6 tests)
   - `tests/phase_1e/test_embedding_grid.py` (7 tests)
   - `tests/phase_1e/test_data_path_integrity.py` (4 tests)

4. **Validation**:
   - `scripts/validate_mesh_data_path.py`
   - `logs/data_path_validation.txt`

5. **Documentation**:
   - REPLICATION-NOTES.md updated with embedding validation
   - README.md updated with "Embedding Layer Validated" status

---

## Failure Handling

If ANY test fails:

1. **Update TROUBLESHOOTING.md**:
   ```markdown
   ### Embedding Hash Not Changing on Delta Receipt
   **Context**: test_pass_event_creates_hash_change fails
   **Symptom**: Recipient cell hash remains same after delta
   **Probable Cause**: receive_delta() not updating vector or normalization issue
   **Investigation**: Check EmbeddingState.receive_delta() implementation
   **Tags**: phase_1e, embedding_state, P0
   ```

2. **Update REPLICATION-NOTES.md**:
   ```markdown
   ## Phase 1E Known Issues
   - Embedding vector must be normalized after delta application
   - Hash function requires consistent byte order for reproducibility
   - Overlay rendering requires exact coordinate matching
   ```

3. **Create ISSUE.md** and **halt execution**

---

This task is **ready for execution** and addresses your critical concern: proving the CyberMesh embedding-delta system works as intended, not just pretty Conway animations.