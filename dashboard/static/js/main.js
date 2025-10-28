// Main application entry point
window.addEventListener('DOMContentLoaded', () => {
    console.log('CyberMesh Conway Dashboard initializing...');

    // Initialize grid
    const grid = initializeGrid();
    console.log('Grid initialized');

    // Initialize controls
    initializeControls();
    console.log('Controls initialized');

    // Initialize embedding overlay
    const overlay = initializeOverlay();
    console.log('Embedding overlay initialized');

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

    // NEW: Handle embedding deltas
    ws.onEmbeddingDeltas = (message) => {
        console.log(`Received embedding_deltas: tick=${message.tick}, ${message.edges.length} passes`);
        for (const edge of message.edges) {
            overlay.drawPass(
                edge.from.x, edge.from.y,
                edge.to.x, edge.to.y,
                edge.payload_id, edge.norm, edge.sim
            );
        }
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
