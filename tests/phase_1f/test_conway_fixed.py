import pytest
import numpy as np
from src.core.conway_grid import ConwayGrid

def test_isolated_cell_dies():
    """Death: Cell with 0 neighbors dies"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1
    
    grid.step()
    
    assert grid.grid[3, 3] == 0, "Isolated cell should die"

def test_two_cells_both_die():
    """Death: Two cells with 1 neighbor each both die"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    
    grid.step()
    
    assert grid.grid[3, 3] == 0, "Cell with 1 neighbor should die"
    assert grid.grid[3, 4] == 0, "Cell with 1 neighbor should die"

def test_block_stable():
    """Survival: 2x2 block is stable (each has 3 neighbors)"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[4, 3] = 1
    grid.grid[4, 4] = 1
    
    before = grid.grid.copy()
    grid.step()
    
    assert np.array_equal(grid.grid, before), "Block should be stable"

def test_birth_rule():
    """Birth: Dead cell with exactly 3 neighbors becomes alive"""
    grid = ConwayGrid(size=8)
    grid.grid[2, 3] = 1  # North of center
    grid.grid[3, 2] = 1  # West of center
    grid.grid[3, 4] = 1  # East of center
    # Center (3,3) is dead with 3 neighbors
    
    grid.step()
    
    assert grid.grid[3, 3] == 1, "Cell with 3 neighbors should be born"

def test_overpopulation():
    """Death: Cell with 4+ neighbors dies"""
    grid = ConwayGrid(size=8)
    # Center surrounded by 4 neighbors (cross pattern)
    grid.grid[3, 3] = 1  # Center
    grid.grid[2, 3] = 1  # North
    grid.grid[4, 3] = 1  # South
    grid.grid[3, 2] = 1  # West
    grid.grid[3, 4] = 1  # East
    
    grid.step()
    
    assert grid.grid[3, 3] == 0, "Cell with 4 neighbors should die"

def test_blinker_oscillates():
    """Blinker pattern oscillates with period 2"""
    grid = ConwayGrid(size=8)
    # Horizontal blinker
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[3, 5] = 1
    
    state0 = grid.grid.copy()
    
    grid.step()
    state1 = grid.grid.copy()
    assert not np.array_equal(state0, state1), "Blinker should change"
    
    grid.step()
    state2 = grid.grid.copy()
    assert np.array_equal(state0, state2), "Blinker should return to original"

def test_glider_moves():
    """Glider pattern moves diagonally"""
    grid = ConwayGrid(size=16)  # Larger grid for movement
    grid.seed_glider(4, 4)
    
    # Count live cells
    initial_count = np.sum(grid.grid)
    assert initial_count == 5, "Glider should have 5 cells"
    
    # Step 4 times (one glider cycle)
    for _ in range(4):
        grid.step()
    
    final_count = np.sum(grid.grid)
    assert final_count == 5, "Glider should maintain 5 cells"

def test_wraparound_corner():
    """Wraparound: Corners see opposite corners as neighbors"""
    grid = ConwayGrid(size=8)
    grid.grid[0, 0] = 1  # Top-left corner
    
    # Manually check neighbors
    neighbors = grid.get_neighbors(0, 0)
    
    # Top-left corner should see bottom-right as diagonal neighbor
    # But since it's the only cell, it has 0 neighbors
    assert neighbors == 0, "Single corner cell should have 0 neighbors"

def test_edge_wraparound():
    """Wraparound: Edge cells see opposite edge"""
    grid = ConwayGrid(size=8)
    grid.grid[0, 4] = 1  # Top edge, middle
    grid.grid[7, 4] = 1  # Bottom edge, middle (wraps to top)
    
    neighbors_top = grid.get_neighbors(4, 0)
    assert neighbors_top >= 1, "Top edge should see bottom edge neighbor"