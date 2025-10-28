#!/usr/bin/env python3
"""
Conway Correctness Diagnosis Script
Phase 1F: Diagnose Conway rule bugs

Identifies exact failure mode: neighbor counting, in-place updates, etc.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.conway_grid import ConwayGrid


def test_isolated_cell_dies():
    """Single cell should die (no neighbors)"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1  # Single alive cell

    print("Before:", np.sum(grid.grid), "alive")
    grid.step()
    print("After:", np.sum(grid.grid), "alive")

    if grid.grid[3, 3] == 1:
        print("❌ FAIL: Isolated cell did NOT die")
        print("   Expected: 0 (dead)")
        print("   Got:", grid.grid[3, 3], "(alive)")
        return False
    else:
        print("✅ PASS: Isolated cell died")
        return True


def test_block_stable():
    """2x2 block should remain stable"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1  # Block pattern
    grid.grid[3, 4] = 1
    grid.grid[4, 3] = 1
    grid.grid[4, 4] = 1

    before_sum = np.sum(grid.grid)
    before = grid.grid.copy()
    grid.step()
    after_sum = np.sum(grid.grid)

    print(f"Block stability: {before_sum} → {after_sum} live cells")

    if np.array_equal(before, grid.grid):
        print("✅ PASS: Block stable")
        return True
    else:
        print("❌ FAIL: Block changed")
        print("Before:\n", before[2:6, 2:6])
        print("After:\n", grid.grid[2:6, 2:6])
        return False


def test_blinker_period_2():
    """Blinker should oscillate with period 2"""
    grid = ConwayGrid(size=8)
    # Horizontal blinker
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[3, 5] = 1

    state0 = grid.grid.copy()
    grid.step()
    state1 = grid.grid.copy()
    grid.step()
    state2 = grid.grid.copy()

    # Check horizontal blinker pattern
    horizontal = state0[3, 3:6].sum() == 3 and state0[2:5, 4].sum() == 1
    vertical = state1[2:5, 4].sum() == 3 and state1[3, 2:6].sum() == 1

    if np.array_equal(state0, state2) and not np.array_equal(state0, state1):
        print("✅ PASS: Blinker oscillates with period 2")
        return True
    else:
        print("❌ FAIL: Blinker behavior incorrect")
        print(f"   State 0 shape: {[state0[y, x] for y in range(2, 5) for x in range(2, 6)]}")
        print(f"   State 1 shape: {[state1[y, x] for y in range(2, 5) for x in range(2, 6)]}")
        print(f"   State 2 shape: {[state2[y, x] for y in range(2, 5) for x in range(2, 6)]}")
        return False


def diagnose_neighbor_counting():
    """Check neighbor counting logic"""
    grid = ConwayGrid(size=8)

    # Place specific test pattern
    grid.grid[3, 3] = 1  # Center
    grid.grid[2, 3] = 1  # North
    grid.grid[4, 3] = 1  # South
    grid.grid[3, 2] = 1  # West

    print("Test pattern:")
    print(grid.grid[2:5, 2:5])

    # Center cell should have 3 neighbors
    neighbors = grid.get_neighbors(3, 3)
    print(f"Center cell (3,3) neighbors: {neighbors} (expected: 3)")

    if neighbors == 3:
        print("✅ Neighbor counting correct for test case")
        return True
    else:
        print(f"❌ Neighbor counting WRONG: got {neighbors}, expected 3")

        # Detailed diagnosis
        print("Diagnosing neighbor count issues:")
        expected_coords = [(2,3), (4,3), (3,2)]  # North, South, West
        actual_neighbors = []

        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                ny = (3 + dy) % 8
                nx = (3 + dx) % 8
                value = grid.grid[ny, nx]
                if value == 1:
                    actual_neighbors.append((nx, ny))
                print(f"  Neighbor ({dx},{dy}) → ({nx},{ny}) = {value}")

        print(f"Expected neighbors at: {expected_coords}")
        print(f"Found live neighbors at: {actual_neighbors}")

        return False


def test_death_by_isolation():
    """Test multiple isolation cases"""
    print("\n--- Death by Isolation Tests ---")

    # Test corner isolation
    grid = ConwayGrid(size=8)
    grid.grid[0, 0] = 1
    initial_sum = np.sum(grid.grid)

    grid.step()
    final_sum = np.sum(grid.grid)

    if final_sum < initial_sum:
        print("✅ Corner cell dies correctly")
        corner_ok = True
    else:
        print("❌ Corner cell did not die")
        corner_ok = False

    # Test edge isolation
    grid = ConwayGrid(size=8)
    grid.grid[0, 4] = 1  # Top middle
    initial_sum = np.sum(grid.grid)

    grid.step()
    final_sum = np.sum(grid.grid)

    if final_sum < initial_sum:
        print("✅ Edge cell dies correctly")
        edge_ok = True
    else:
        print("❌ Edge cell did not die")
        edge_ok = False

    return corner_ok and edge_ok


if __name__ == "__main__":
    print("=== Conway Correctness Diagnosis ===\n")

    tests = [
        test_isolated_cell_dies,
        test_block_stable,
        test_blinker_period_2,
        diagnose_neighbor_counting,
        test_death_by_isolation
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}\n")
            results.append(False)

    passed = sum(1 for r in results if r)
    total = len(results)

    print(f"=== Results: {passed}/{total} passed ===")

    if all(results):
        print("✅ Conway implementation appears correct")
        exit_code = 0
    else:
        print("❌ Conway implementation has bugs")
        print("\nMost likely issues (ranked):")
        print("1. Neighbor counting includes center cell (+1)")
        print("2. In-place updates modify grid while reading")
        print("3. Index swapping (x,y) vs (y,x)")
        print("4. Wraparound not applied correctly")
        print("\nNext steps:")
        print("1. Review conway_grid.py step() method")
        print("2. Check neighbor counting logic")
        print("3. Verify new_grid is separate from self.grid")
        print("4. Test wraparound at edges")
        exit_code = 1

    exit(exit_code)
