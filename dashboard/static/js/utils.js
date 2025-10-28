// Dashboard Utility Functions
// Connection status, metrics, and UI updates

// Connection status management
function updateConnectionStatus(connected) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');

    if (statusDot && statusText) {
        if (connected) {
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'Connected';
        } else {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = 'Disconnected';
        }
    }
    console.log(`Connection status updated: ${connected ? 'connected' : 'disconnected'}`);
}

// Tick count management
function updateTickCount(tick) {
    const tickElement = document.getElementById('tick-count');
    if (tickElement) {
        tickElement.textContent = tick;
    }
}

// Metrics tracking
const metricsTracker = {
    tickCount: 0,
    latencySamples: [],

    recordUpdate() {
        this.tickCount++;
        // Could add more metrics here
    },

    getTicksPerSecond() {
        // Simple calculation for demo
        return Math.round(this.tickCount / (Date.now() / 1000));
    }
};

// Latency tracking
function updateLatency(latency) {
    const latencyElement = document.getElementById('latency');
    if (latencyElement) {
        latencyElement.textContent = `${latency}ms`;
    }
}

// Update rate display
function updateUpdateRate() {
    const rateElement = document.getElementById('update-rate');
    if (rateElement) {
        // For demo, show approximate rate
        rateElement.textContent = '2.0'; // 2 per second (500ms intervals)
    }
}
