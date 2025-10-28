---
title: "Phase 1C: HTML Frontend Visualization"
phase: "1C"
objective: "Interactive HTML/JavaScript dashboard for real-time Conway grid visualization"
assigned_to: "coding_agent"
status: "ready_for_execution"
hardware: "128GB Strix Halo HP ZBook, Windows 11"
dependencies: ["Phase 1B complete", "WebSocket server at port 8000"]
estimated_duration: "1 day"
validation_gates: ["manual_visual", "browser_compatibility", "performance", "docs"]
---

# Phase 1C: HTML Frontend Visualization

## Objective

Build interactive HTML/JavaScript dashboard that connects to Phase 1B WebSocket server, visualizes 8×8 Conway grid in real-time with glider animation, displays live metrics, and provides interactive controls.

## Prerequisites

- ✅ Phase 1B complete (WebSocket server validated at 133 bytes/message, 2.0 msg/sec)
- Chrome or Edge browser on Windows 11
- Phase 1B server running on `ws://localhost:8000/ws`
- Static file serving configured in FastAPI

## Task Breakdown

### Task 1C-1: Create HTML Structure

**File**: `dashboard/index.html`

**Requirements**:
- HTML5 document structure
- 8×8 grid container (CSS Grid or HTML table)
- Metrics display panel (tick count, live cells, FPS)
- Control buttons (reset, pause/resume)
- WebSocket connection status indicator
- Responsive layout for 1920×1080 displays

**Acceptance Criteria**:
- Valid HTML5 markup
- Grid renders with 8 rows × 8 columns
- All UI elements visible without scrolling
- Works in Chrome/Edge on Windows 11

**Implementation**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberMesh Conway Glider Demo - 8×8 Grid</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>CyberMesh Conway Glider Demo</h1>
            <div class="status-badge" id="connection-status">
                <span class="status-dot"></span>
                <span class="status-text">Disconnected</span>
            </div>
        </header>

        <div class="metrics-panel">
            <div class="metric-card">
                <div class="metric-label">Tick</div>
                <div class="metric-value" id="tick-count">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Live Cells</div>
                <div class="metric-value" id="live-cells">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Updates/sec</div>
                <div class="metric-value" id="update-rate">0.0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Latency</div>
                <div class="metric-value" id="latency">0ms</div>
            </div>
        </div>

        <div class="grid-wrapper">
            <div id="conway-grid" class="conway-grid"></div>
        </div>

        <div class="controls">
            <button id="btn-reset" class="btn btn-primary">Reset Glider</button>
            <button id="btn-pause" class="btn btn-secondary">Pause</button>
            <button id="btn-resume" class="btn btn-secondary" style="display:none;">Resume</button>
        </div>

        <div class="info-panel">
            <h3>Instructions</h3>
            <ul>
                <li>Watch the glider pattern move diagonally across the grid</li>
                <li>Observe Pac-Man wraparound at edges (glider reappears on opposite side)</li>
                <li>Updates occur every 500ms (2 per second)</li>
                <li>Click "Reset Glider" to restart the pattern at (1,1)</li>
            </ul>
        </div>
    </div>

    <script src="/static/js/websocket.js"></script>
    <script src="/static/js/grid.js"></script>
    <script src="/static/js/controls.js"></script>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

**Validation**:
- Open `http://localhost:8000` in browser
- Verify all elements render correctly
- Check responsive layout at 1920×1080
- Screenshot for evidence

---

### Task 1C-2: Implement Grid Styling

**File**: `dashboard/static/css/style.css`

**Requirements**:
- Dark theme matching CyberMesh branding
- Grid cells with clear alive/dead visual distinction
- Smooth transitions for cell state changes
- Glider highlighting (optional enhancement)
- Responsive font sizes and spacing

**Acceptance Criteria**:
- Dark background (#0a0a0a)
- Green accent color (#00ff00) for alive cells
- Cell size 60×60px with 2px gap
- Smooth 0.3s transitions on state changes
- High contrast for accessibility

**Implementation**:
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', 'Roboto', system-ui, sans-serif;
    background: #0a0a0a;
    color: #e0e0e0;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
}

.container {
    max-width: 1200px;
    width: 100%;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding: 20px;
    background: #1a1a1a;
    border-radius: 10px;
    border: 1px solid #333;
}

h1 {
    color: #00ff00;
    font-size: 28px;
    font-weight: 600;
}

.status-badge {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 16px;
    background: #111;
    border-radius: 20px;
    border: 1px solid #333;
}

.status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #666;
    transition: background 0.3s ease;
}

.status-badge.connected .status-dot {
    background: #00ff00;
    box-shadow: 0 0 10px #00ff00;
}

.status-badge.disconnected .status-dot {
    background: #ff0000;
}

.status-text {
    font-size: 14px;
    font-weight: 500;
}

.metrics-panel {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 30px;
}

.metric-card {
    background: #1a1a1a;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #333;
    text-align: center;
}

.metric-label {
    color: #888;
    font-size: 14px;
    margin-bottom: 8px;
}

.metric-value {
    color: #00ff00;
    font-size: 32px;
    font-weight: 700;
    font-family: 'Courier New', monospace;
}

.grid-wrapper {
    display: flex;
    justify-content: center;
    margin-bottom: 30px;
}

.conway-grid {
    display: grid;
    grid-template-columns: repeat(8, 60px);
    grid-template-rows: repeat(8, 60px);
    gap: 2px;
    background: #1a1a1a;
    padding: 15px;
    border-radius: 10px;
    border: 2px solid #333;
}

.cell {
    width: 60px;
    height: 60px;
    background: #0a0a0a;
    border: 1px solid #222;
    border-radius: 4px;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    color: #444;
    cursor: pointer;
}

.cell.alive {
    background: #00ff00;
    box-shadow: 0 0 15px rgba(0, 255, 0, 0.5);
    border-color: #00ff00;
}

.cell.alive:hover {
    box-shadow: 0 0 25px rgba(0, 255, 0, 0.8);
}

.cell.dead:hover {
    border-color: #444;
}

.controls {
    display: flex;
    justify-content: center;
    gap: 15px;
    margin-bottom: 30px;
}

.btn {
    padding: 12px 24px;
    font-size: 16px;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary {
    background: #00ff00;
    color: #0a0a0a;
    border: 2px solid #00ff00;
}

.btn-primary:hover {
    background: #00cc00;
    box-shadow: 0 0 20px rgba(0, 255, 0, 0.5);
}

.btn-secondary {
    background: #1a1a1a;
    color: #00ff00;
    border: 2px solid #00ff00;
}

.btn-secondary:hover {
    background: #00ff00;
    color: #0a0a0a;
}

.info-panel {
    background: #1a1a1a;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #333;
}

.info-panel h3 {
    color: #00ff00;
    margin-bottom: 15px;
}

.info-panel ul {
    list-style: none;
    padding-left: 0;
}

.info-panel li {
    padding: 8px 0;
    padding-left: 20px;
    position: relative;
    color: #ccc;
}

.info-panel li::before {
    content: "▹";
    position: absolute;
    left: 0;
    color: #00ff00;
}

@media (max-width: 768px) {
    .metrics-panel {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .conway-grid {
        grid-template-columns: repeat(8, 50px);
        grid-template-rows: repeat(8, 50px);
    }
    
    .cell {
        width: 50px;
        height: 50px;
    }
}
```

**Validation**:
- Visual inspection in browser
- Test hover effects on cells
- Verify transitions are smooth
- Screenshot before/after cell changes

---

### Task 1C-3: Implement WebSocket Client

**File**: `dashboard/static/js/websocket.js`

**Requirements**:
- Connect to `ws://localhost:8000/ws`
- Handle connection open/close events
- Parse full_state and delta messages
- Automatic reconnection on disconnect
- Error handling and logging

**Implementation**:
```javascript
class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.onStateChange = null;
        this.onDelta = null;
        this.onConnectionChange = null;
        this.lastMessageTime = Date.now();
    }

    connect() {
        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                if (this.onConnectionChange) {
                    this.onConnectionChange(true);
                }
            };

            this.ws.onmessage = (event) => {
                this.lastMessageTime = Date.now();
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                if (this.onConnectionChange) {
                    this.onConnectionChange(false);
                }
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

        } catch (error) {
            console.error('Failed to connect:', error);
            this.attemptReconnect();
        }
    }

    handleMessage(message) {
        if (message.type === 'full_state') {
            if (this.onStateChange) {
                this.onStateChange(message);
            }
        } else if (message.type === 'delta') {
            if (this.onDelta) {
                this.onDelta(message);
            }
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        } else {
            console.warn('WebSocket not connected, cannot send:', data);
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectDelay);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    getLatency() {
        return Date.now() - this.lastMessageTime;
    }
}

// Global WebSocket instance
let wsClient = null;

function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws`;
    
    wsClient = new WebSocketClient(url);
    return wsClient;
}
```

**Validation**:
- Open browser console
- Verify "WebSocket connected" message
- Check for errors
- Test reconnection by stopping/starting server

---

### Task 1C-4: Implement Grid Rendering

**File**: `dashboard/static/js/grid.js`

**Requirements**:
- Create 8×8 cell DOM elements
- Handle full_state initialization
- Apply delta updates incrementally
- Count live cells
- Track cell coordinates

**Implementation**:
```javascript
class ConwayGrid {
    constructor(containerId, size = 8) {
        this.container = document.getElementById(containerId);
        this.size = size;
        this.cells = [];
        this.liveCount = 0;
        this.initializeGrid();
    }

    initializeGrid() {
        this.container.innerHTML = '';
        this.cells = [];

        for (let y = 0; y < this.size; y++) {
            this.cells[y] = [];
            for (let x = 0; x < this.size; x++) {
                const cell = document.createElement('div');
                cell.className = 'cell dead';
                cell.dataset.x = x;
                cell.dataset.y = y;
                cell.title = `(${x}, ${y})`;
                
                this.container.appendChild(cell);
                this.cells[y][x] = cell;
            }
        }
    }

    applyFullState(state) {
        console.log('Applying full state:', state);
        this.liveCount = 0;

        for (let y = 0; y < this.size; y++) {
            for (let x = 0; x < this.size; x++) {
                const isAlive = state[y][x] === 1;
                this.setCellState(x, y, isAlive);
                if (isAlive) this.liveCount++;
            }
        }

        this.updateLiveCount();
    }

    applyDeltas(deltas) {
        deltas.forEach(delta => {
            const wasAlive = this.cells[delta.y][delta.x].classList.contains('alive');
            this.setCellState(delta.x, delta.y, delta.alive);

            // Update live count
            if (delta.alive && !wasAlive) {
                this.liveCount++;
            } else if (!delta.alive && wasAlive) {
                this.liveCount--;
            }
        });

        this.updateLiveCount();
    }

    setCellState(x, y, alive) {
        const cell = this.cells[y][x];
        if (alive) {
            cell.classList.remove('dead');
            cell.classList.add('alive');
        } else {
            cell.classList.remove('alive');
            cell.classList.add('dead');
        }
    }

    updateLiveCount() {
        const countElement = document.getElementById('live-cells');
        if (countElement) {
            countElement.textContent = this.liveCount;
        }
    }

    getLiveCount() {
        return this.liveCount;
    }
}

// Global grid instance
let conwayGrid = null;

function initializeGrid() {
    conwayGrid = new ConwayGrid('conway-grid', 8);
    return conwayGrid;
}
```

**Validation**:
- Visual inspection of grid
- Verify cells update on delta messages
- Check live cell count matches visual
- Test with manual cell toggling (future feature)

---

### Task 1C-5: Implement Controls and Metrics

**File**: `dashboard/static/js/controls.js`

**Requirements**:
- Reset button sends "reset" command
- Pause/Resume toggle (future: controls server)
- Update metrics display (tick, FPS, latency)
- Connection status indicator

**Implementation**:
```javascript
class MetricsTracker {
    constructor() {
        this.updateCount = 0;
        this.lastUpdateTime = Date.now();
        this.updateRate = 0.0;
    }

    recordUpdate() {
        this.updateCount++;
        const now = Date.now();
        const elapsed = (now - this.lastUpdateTime) / 1000;

        if (elapsed >= 1.0) {
            this.updateRate = this.updateCount / elapsed;
            this.updateCount = 0;
            this.lastUpdateTime = now;
            this.displayUpdateRate();
        }
    }

    displayUpdateRate() {
        const element = document.getElementById('update-rate');
        if (element) {
            element.textContent = this.updateRate.toFixed(1);
        }
    }
}

let metricsTracker = null;

function initializeControls() {
    metricsTracker = new MetricsTracker();

    // Reset button
    const btnReset = document.getElementById('btn-reset');
    if (btnReset) {
        btnReset.addEventListener('click', () => {
            if (wsClient) {
                wsClient.send('reset');
                console.log('Sent reset command');
            }
        });
    }

    // Pause button (placeholder for future implementation)
    const btnPause = document.getElementById('btn-pause');
    if (btnPause) {
        btnPause.addEventListener('click', () => {
            console.log('Pause not yet implemented');
            // Future: send "stop" command to server
        });
    }

    // Resume button (placeholder)
    const btnResume = document.getElementById('btn-resume');
    if (btnResume) {
        btnResume.addEventListener('click', () => {
            console.log('Resume not yet implemented');
            // Future: send "start" command to server
        });
    }
}

function updateConnectionStatus(connected) {
    const statusBadge = document.getElementById('connection-status');
    const statusText = statusBadge.querySelector('.status-text');
    
    if (connected) {
        statusBadge.classList.remove('disconnected');
        statusBadge.classList.add('connected');
        statusText.textContent = 'Connected';
    } else {
        statusBadge.classList.remove('connected');
        statusBadge.classList.add('disconnected');
        statusText.textContent = 'Disconnected';
    }
}

function updateTickCount(tick) {
    const element = document.getElementById('tick-count');
    if (element) {
        element.textContent = tick;
    }
}

function updateLatency(latency) {
    const element = document.getElementById('latency');
    if (element) {
        element.textContent = `${latency}ms`;
    }
}
```

**Validation**:
- Click reset button, observe grid reset
- Watch metrics update in real-time
- Verify connection status changes on disconnect/reconnect
- Screenshot of metrics panel

---

### Task 1C-6: Main Application Logic

**File**: `dashboard/static/js/main.js`

**Requirements**:
- Initialize all components on page load
- Wire WebSocket callbacks to grid updates
- Handle full_state and delta messages
- Update metrics continuously

**Implementation**:
```javascript
// Main application entry point
window.addEventListener('DOMContentLoaded', () => {
    console.log('CyberMesh Conway Dashboard initializing...');

    // Initialize grid
    const grid = initializeGrid();
    console.log('Grid initialized');

    // Initialize controls
    initializeControls();
    console.log('Controls initialized');

    // Initialize WebSocket
    const ws = initializeWebSocket();
    console.log('WebSocket connecting...');

    // Set up WebSocket callbacks
    ws.onConnectionChange = (connected) => {
        updateConnectionStatus(connected);
    };

    ws.onStateChange = (message) => {
        console.log('Received full_state:', message);
        grid.applyFullState(message.grid);
        updateTickCount(message.tick);
    };

    ws.onDelta = (message) => {
        console.log(`Received delta: tick=${message.tick}, ${message.deltas.length} changes`);
        grid.applyDeltas(message.deltas);
        updateTickCount(message.tick);
        metricsTracker.recordUpdate();
        
        // Update latency estimate
        const latency = ws.getLatency();
        updateLatency(latency);
    };

    // Connect WebSocket
    ws.connect();

    console.log('CyberMesh Conway Dashboard ready');
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (wsClient) {
        wsClient.disconnect();
    }
});
```

**Validation**:
- Check browser console for initialization messages
- Verify grid updates on WebSocket messages
- Confirm metrics display real-time data
- Test full page reload

---

## Manual Validation Protocol

### Visual Verification Checklist

**Pre-Test Setup**:
1. Start Phase 1B server: `python -m uvicorn src.api.conway_server:app`
2. Open Chrome/Edge browser
3. Navigate to `http://localhost:8000`
4. Open Developer Tools (F12)
5. Go to Network tab, filter by "WS" (WebSocket)

**Visual Tests**:

| Test | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| VIS-001 | Page loads | All UI elements visible | ☐ |
| VIS-002 | WebSocket connects | Status shows "Connected" (green) | ☐ |
| VIS-003 | Initial state | 5 cells alive (glider pattern) | ☐ |
| VIS-004 | Wait 2 seconds | Glider moves diagonally | ☐ |
| VIS-005 | Wait 10 seconds | Glider continues moving | ☐ |
| VIS-006 | Edge wraparound | Glider appears on opposite side | ☐ |
| VIS-007 | Metrics update | Tick count increases every 500ms | ☐ |
| VIS-008 | Live cell count | Shows 5 consistently | ☐ |
| VIS-009 | Update rate | Shows ~2.0 updates/sec | ☐ |
| VIS-010 | Click "Reset" | Glider resets to (1,1) | ☐ |
| VIS-011 | DevTools Network | WebSocket shows Connected | ☐ |
| VIS-012 | DevTools Messages | Delta messages every 500ms | ☐ |

**Screenshot Requirements**:
- Initial page load (full screen)
- Glider at starting position
- Glider mid-movement
- Glider wrapping around edge
- Developer Tools showing WebSocket messages
- Metrics panel with values
- Before/after reset button click

---

## Browser Compatibility Testing

### Required Tests

**Chrome (Windows 11)**:
- [ ] Page loads without errors
- [ ] WebSocket connects successfully
- [ ] Grid renders correctly
- [ ] Animations smooth
- [ ] Controls functional

**Edge (Windows 11)**:
- [ ] Same as Chrome tests
- [ ] No Edge-specific issues

**Console Errors**:
- [ ] No JavaScript errors in console
- [ ] No CSS warnings
- [ ] No 404 errors for resources

---

## Performance Validation

### Performance Metrics

**Target**: 60 FPS rendering, smooth animations

**Measurement**:
1. Open Performance tab in DevTools
2. Click "Record"
3. Let glider run for 10 seconds
4. Stop recording
5. Analyze frame rate

**Success Criteria**:
- FPS ≥ 30 throughout
- No frame drops during delta updates
- Memory usage stable (<100MB)
- CPU usage <20% during idle rendering

---

## Validation Gates

### Gate 1: Manual Visual Validation
```
- Open dashboard in browser
- Complete VIS-001 through VIS-012 checklist
- All items must pass
- Screenshots captured for evidence
```

### Gate 2: Browser Compatibility
```
- Test in Chrome (latest)
- Test in Edge (latest)
- No console errors
- Functionality identical across browsers
```

### Gate 3: Performance Check
```
- Record 10-second performance profile
- Verify FPS ≥ 30
- Verify no memory leaks
- CPU usage <20%
```

### Gate 4: Documentation
```
- Update README with dashboard usage
- Document WebSocket message format
- Add troubleshooting entries
- Include screenshots in docs/evidence/phase_1c/
```

---

## Failure Handling Protocol

If ANY gate fails:

1. **Capture evidence**:
   ```powershell
   mkdir docs\evidence\phase_1c\failures\
   # Save screenshots of failure
   # Save browser console output
   # Save DevTools Network tab
   ```

2. **Update TROUBLESHOOTING.md**:
   ```markdown
   ### WebSocket Connection Fails in Browser
   **Context**: Dashboard loads but doesn't connect to WebSocket
   **Symptom**: Status shows "Disconnected" (red), no grid updates
   **Error Snippet**:
   \`\`\`
   WebSocket connection to 'ws://localhost:8000/ws' failed: Connection refused
   \`\`\`
   **Probable Cause**: Phase 1B server not running
   **Quick Fix**: Start server: `python -m uvicorn src.api.conway_server:app`
   **Permanent Fix**: Add server health check before connecting
   **Prevention**: Document server startup in dashboard instructions
   **Tags**: frontend, websocket, P1
   ```

3. **Update REPLICATION-NOTES.md** with browser-specific issues

4. **Create ISSUE.md** with screenshots

5. **Halt execution** and wait for human

---

## Success Criteria

Phase 1C is complete when:

- [ ] HTML dashboard loads at `http://localhost:8000`
- [ ] WebSocket connects to Phase 1B server
- [ ] 8×8 grid renders with correct styling
- [ ] Glider pattern visible and animates
- [ ] Glider wraps around edges (Pac-Man behavior)
- [ ] Metrics update in real-time (tick, live cells, FPS)
- [ ] Reset button restarts glider at (1,1)
- [ ] Connection status indicator works
- [ ] All visual tests pass (VIS-001 through VIS-012)
- [ ] Works in Chrome and Edge
- [ ] No console errors
- [ ] Performance ≥30 FPS
- [ ] Documentation updated with screenshots

---

## Deliverables

1. **Code**:
   - `dashboard/index.html`
   - `dashboard/static/css/style.css`
   - `dashboard/static/js/websocket.js`
   - `dashboard/static/js/grid.js`
   - `dashboard/static/js/controls.js`
   - `dashboard/static/js/main.js`

2. **Documentation**:
   - README.md updated with dashboard usage
   - REPLICATION-NOTES.md updated with Phase 1C
   - TROUBLESHOOTING.md updated (if issues encountered)

3. **Evidence**:
   - Screenshots (12 required from checklist)
   - Browser console logs
   - DevTools Network tab screenshot
   - Performance profile recording

---

## Notes for Coding Agent

- **Visual validation required** - automated tests cannot verify rendering
- **Human must perform VIS-001 through VIS-012** checklist
- **Screenshots are mandatory** for evidence
- **Test in both Chrome and Edge** on Windows 11
- **No TypeScript** - use vanilla JavaScript for simplicity
- **No frameworks** - vanilla HTML/CSS/JS only
- **Stop on any rendering issues** and document

This task is **ready for execution** by a coding agent following the Policy lifecycle, with final validation requiring human visual confirmation.