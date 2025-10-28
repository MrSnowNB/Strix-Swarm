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
