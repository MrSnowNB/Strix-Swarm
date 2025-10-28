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
