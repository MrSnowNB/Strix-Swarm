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