// Interactive Dashboard Controls
// Cell click-to-toggle, mode switches, randomization

function initializeCellClicks() {
    const gridElement = document.getElementById('conway-grid');

    gridElement.addEventListener('click', (e) => {
        // Only handle clicks on cell elements
        if (e.target.classList.contains('cell')) {
            const x = parseInt(e.target.dataset.x);
            const y = parseInt(e.target.dataset.y);

            if (wsClient && wsClient.ws && wsClient.ws.readyState === WebSocket.OPEN) {
                wsClient.send(JSON.stringify({
                    type: "toggle_cell",
                    x: x,
                    y: y
                }));

                // Visual feedback - highlight the clicked cell briefly
                e.target.classList.add('clicked');
                setTimeout(() => e.target.classList.remove('clicked'), 300);
            }
        }
    });
}

function updateModeDisplay() {
    // Called when mode changes are received from server
    console.log('Mode display updated');
}

// Mode toggle handler
document.addEventListener('DOMContentLoaded', () => {
    const toggleCoupled = document.getElementById('toggle-coupled');
    const policySelect = document.getElementById('policy-select');

    if (toggleCoupled) {
        toggleCoupled.addEventListener('change', (e) => {
            const mode = e.target.checked ? "coupled" : "decoupled";
            const policy = policySelect ? policySelect.value : "birth";

            if (wsClient && wsClient.ws && wsClient.ws.readyState === WebSocket.OPEN) {
                wsClient.send(JSON.stringify({
                    type: "set_mode",
                    mesh_mode: mode,
                    policy: policy
                }));
            }
        });
    }

    // Randomize button handler
    const randomizeBtn = document.getElementById('btn-randomize');
    if (randomizeBtn) {
        randomizeBtn.addEventListener('click', () => {
            if (wsClient && wsClient.ws && wsClient.ws.readyState === WebSocket.OPEN) {
                wsClient.send(JSON.stringify({
                    type: "randomize_dead_embeddings"
                }));
            }
        });
    }
});

// Controls initialization function
function initializeControls() {
    // Controls are initialized via DOMContentLoaded event above
    // This function confirms controls are set up
    console.log('Dashboard controls initialization complete');
    return true;
}
