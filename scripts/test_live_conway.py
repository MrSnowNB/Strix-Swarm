#!/usr/bin/env python3
"""
Test live Conway implementation - same as server uses
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.conway_grid import ConwayGrid

def test_isolated_cells_stuck():
    """Test if isolated cells stay alive (they shouldn't)"""
    grid = ConwayGrid(size=8)

    # Create a simple pattern with some isolated cells
    # Place cells at (4,6) and (5,7) as the user reported
    grid.grid[6, 4] = 1  # Note: grid[y][x] indexing
    grid.grid[7, 5] = 1

    print("Initial grid:")
    for y in range(8):
        for x in range(8):
            if grid.grid[y, x] == 1:
                print(f"({x},{y}) = live, neighbors = {grid.get_neighbors(x, y)}")

    # Check neighbors for the problematic cells
    neighbors_46 = grid.get_neighbors(4, 6)
    neighbors_57 = grid.get_neighbors(5, 7)

    print(f"\nNeighbors for (4,6): {neighbors_46}")
    print(f"Neighbors for (5,7): {neighbors_57}")

    # Step
    deltas = grid.step()

    print(f"\nAfter step - {len(deltas)} deltas:")
    for delta in deltas:
        print(f"  ({delta['y']},{delta['x']}) changed to {'alive' if delta['alive'] else 'dead'}")

    # Check if cells died
    cell_46_alive = bool(grid.grid[6, 4])  # y=6, x=4
    cell_57_alive = bool(grid.grid[7, 5])  # y=7, x=5

    print(f"Cell (4,6) {'alive' if cell_46_alive else 'dead'}")
    print(f"Cell (5,7) {'alive' if cell_57_alive else 'dead'}")

    if not (cell_46_alive or cell_57_alive):
        print("✅ PASS: Isolated cells died correctly")
        return True
    else:
        print("❌ FAIL: Isolated cells stayed alive")
        return False

if __name__ == "__main__":
    test_isolated_cells_stuck()
