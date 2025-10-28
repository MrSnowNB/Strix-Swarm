#!/usr/bin/env python3
"""
Test diagonal Conway case - cells [1,3] and [2,4] should die
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.conway_grid import ConwayGrid

def test_diagonal_cells():
    """Test diagonal case [1,3] and [2,4] - should both die"""
    grid = ConwayGrid(size=8)

    # Set cells [1,3] and [2,4] as alive (diagonal pattern)
    grid.grid[1, 3] = 1  # [y,x]
    grid.grid[2, 4] = 1

    print("Initial diagonal pattern:")
    for y in range(8):
        row = ""
        for x in range(8):
            if grid.grid[y, x] == 1:
                row += f"[{y},{x}] "
        if row.strip():
            print(row.strip())

    # Check neighbors for each cell
    n13 = grid.get_neighbors(1, 3)  # cell (1,3) - y=1, x=3
    n24 = grid.get_neighbors(2, 4)  # cell (2,4) - y=2, x=4

    print(f"\nNeighbors for (1,3): {n13} (expected: 1)")
    print(f"Neighbors for (2,4): {n24} (expected: 1)")

    # Manual neighbor counting for (1,3)
    print("\nManual_neighbor_count for (1,3):")
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            ny = (1 + dy) % 8
            nx = (3 + dx) % 8
            if grid.grid[ny, nx] == 1:
                print(f"  Lives at ({ny},{nx}) - neighbor offset ({dy},{dx})")

    # Step
    deltas = grid.step()

    print(f"\nAfter step - {len(deltas)} deltas:")
    for delta in deltas:
        status = "alive" if delta['alive'] else "dead"
        print(f"  ({delta['y']},{delta['x']}) changed to {status}")

    # Check final state
    final_13 = bool(grid.grid[1, 3])
    final_24 = bool(grid.grid[2, 4])

    print("\nFinal state:")
    print(f"Cell (1,3) {'alive' if final_13 else 'dead'}")
    print(f"Cell (2,4) {'alive' if final_24 else 'dead'}")

    # Both should die due to underpopulation (1 < 2 neighbors)
    if not (final_13 or final_24):
        print("\n✅ PASS: Diagonal cells correctly died from underpopulation")
        return True
    else:
        print("\n❌ FAIL: Diagonal cells stayed alive (Conway rule violation)")
        return False

if __name__ == "__main__":
    test_diagonal_cells()
