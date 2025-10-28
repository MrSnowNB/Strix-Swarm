import numpy as np
from numpy.typing import NDArray
from scipy.signal import convolve2d
from typing import List
from dataclasses import dataclass

@dataclass
class CellDelta:
    x: int
    y: int
    alive: bool

class ConwayGrid:
    def __init__(self, size: int = 8):
        self.size = size
        self.grid = np.zeros((size, size), dtype=np.uint8)
        self.tick_count = 0
    
    def get_neighbors(self, x: int, y: int) -> int:
        """Count Moore neighborhood (8 neighbors) with wraparound"""
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Don't count center
                nx = (x + dx) % self.size
                ny = (y + dy) % self.size
                count += self.grid[ny, nx]  # Note: [y, x] indexing
        return count
    
    def step(self) -> List[CellDelta]:
        """
        Execute one Conway step using convolution (foolproof).
        Returns list of cell changes.
        """
        # Kernel for neighbor counting (excludes center)
        kernel = np.ones((3, 3), dtype=np.uint8)
        kernel[1, 1] = 0
        
        # Count neighbors with wraparound
        neighbors = convolve2d(self.grid, kernel, mode='same', boundary='wrap')
        
        # Apply Conway rules (B3/S23)
        new_grid = np.zeros_like(self.grid)
        
        # Birth: dead cell with exactly 3 neighbors
        new_grid[(self.grid == 0) & (neighbors == 3)] = 1
        
        # Survival: live cell with 2 or 3 neighbors
        new_grid[(self.grid == 1) & ((neighbors == 2) | (neighbors == 3))] = 1
        
        # Compute deltas
        deltas = []
        changed = np.argwhere(new_grid != self.grid)
        for y, x in changed:
            deltas.append(CellDelta(
                x=int(x),
                y=int(y),
                alive=bool(new_grid[y, x])
            ))
        
        # Update state
        self.grid = new_grid
        self.tick_count += 1
        
        return deltas
    
    def seed_glider(self, x: int, y: int) -> None:
        """Seed canonical glider at (x, y)"""
        # Glider pattern:
        #   .X.
        #   ..X
        #   XXX
        self.grid[y, x+1] = 1      # Top middle
        self.grid[y+1, x+2] = 1    # Middle right
        self.grid[y+2, x] = 1      # Bottom left
        self.grid[y+2, x+1] = 1    # Bottom middle
        self.grid[y+2, x+2] = 1    # Bottom right
    
    def get_state(self) -> NDArray[np.uint8]:
        """Return copy of current grid state"""
        return self.grid.copy()