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
            const wasAlive = this.cells[delta.x][delta.y].classList.contains('alive');
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
