// Embedding Overlay Visualization
// Cyan arrows showing embedding delta passes (distinct from Conway green cells)

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
