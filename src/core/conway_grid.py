import numpy as np


class ConwayGrid:
    def __init__(self, size=8):
        self.size = size
        self.grid = np.zeros((size, size), dtype=int)
        self.delta = []

    def get_neighbors(self, r, c):
        """Calculate number of live neighbors for cell at (r,c) with toroidal wraparound."""
        neighbors = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr = (r + dr) % self.size
                nc = (c + dc) % self.size
                neighbors += self.grid[nr, nc]
        return neighbors

    def step(self):
        """Evolve the grid by one step according to Conway's rules B3/S23, returning delta of changed cells."""
        new_grid = np.zeros_like(self.grid)
        delta = []

        for r in range(self.size):
            for c in range(self.size):
                live_neighbors = self.get_neighbors(r, c)
                current = self.grid[r, c]

                # Apply Conway rules
                if current == 1:
                    # Survive if 2 or 3 neighbors
                    if live_neighbors == 2 or live_neighbors == 3:
                        new_grid[r, c] = 1
                    # else dies
                else:
                    # Born if exactly 3 neighbors
                    if live_neighbors == 3:
                        new_grid[r, c] = 1

                # Track changes for delta
                if new_grid[r, c] != current:
                    delta.append({'x': c, 'y': r, 'alive': int(new_grid[r, c])})

        self.grid = new_grid
        self.delta = delta
        return delta

    def seed_glider(self, r_offset=0, c_offset=0):
        """Seed the glider pattern at given offset with toroidal wraparound."""
        # Standard glider pattern positions
        glider_positions = [
            (0, 1),  # Row 0, Col 1
            (1, 2),  # Row 1, Col 2
            (2, 0),  # Row 2, Col 0
            (2, 1),  # Row 2, Col 1
            (2, 2),  # Row 2, Col 2
        ]

        self.grid = np.zeros_like(self.grid)
        self.delta = []

        for r, c in glider_positions:
            rr = (r + r_offset) % self.size
            cc = (c + c_offset) % self.size
            self.grid[rr, cc] = 1

    def get_state(self):
        """Return a copy of the current grid state."""
        return self.grid.copy()
