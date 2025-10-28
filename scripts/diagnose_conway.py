import numpy as np
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
        return False
    else:
        print("✅ PASS: Isolated cell died")
        return True

def test_block_stable():
    """2x2 block should remain stable"""
    grid = ConwayGrid(size=8)
    grid.grid[3, 3] = 1
    grid.grid[3, 4] = 1
    grid.grid[4, 3] = 1
    grid.grid[4, 4] = 1
    
    before = grid.grid.copy()
    grid.step()
    
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
    
    if np.array_equal(state0, state2) and not np.array_equal(state0, state1):
        print("✅ PASS: Blinker oscillates")
        return True
    else:
        print("❌ FAIL: Blinker behavior incorrect")
        return False

def diagnose_neighbor_counting():
    """Check neighbor counting logic"""
    grid = ConwayGrid(size=8)
    
    # Place specific pattern
    grid.grid[3, 3] = 1  # Center
    grid.grid[2, 3] = 1  # North
    grid.grid[4, 3] = 1  # South
    grid.grid[3, 2] = 1  # West
    
    # Center cell should have 3 neighbors
    neighbors = grid.get_neighbors(3, 3)
    print(f"Center cell (3,3) neighbors: {neighbors} (expected: 3)")
    
    if neighbors == 3:
        print("✅ Neighbor counting correct for test case")
    else:
        print(f"❌ Neighbor counting WRONG: got {neighbors}, expected 3")

if __name__ == "__main__":
    print("=== Conway Correctness Diagnosis ===\n")
    
    tests = [
        test_isolated_cell_dies,
        test_block_stable,
        test_blinker_period_2
    ]
    
    results = [test() for test in tests]
    
    print("\n--- Neighbor Counting Check ---")
    diagnose_neighbor_counting()
    
    print(f"\n=== Results: {sum(results)}/{len(results)} passed ===")
    
    if all(results):
        print("✅ Conway implementation appears correct")
    else:
        print("❌ Conway implementation has bugs")
        print("\nNext steps:")
        print("1. Review conway_grid.py step() method")
        print("2. Check neighbor counting logic")
        print("3. Verify new_grid is separate from self.grid")
        print("4. Test wraparound at edges")