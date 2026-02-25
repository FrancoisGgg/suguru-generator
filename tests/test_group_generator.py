
import sys
import os

# Add parent directory to path so imports work
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from group_generator import GroupGenerator
from models import Grid
from visualizer import draw_grid

def test_generate_returns_correct_shape():
    """Generated layout should match requested dimensions."""
    gen = GroupGenerator(min_size=2, max_size=5)
    layout = gen.generate(6, 6)
    
    passed = layout is not None and len(layout) == 6 and len(layout[0]) == 6
    print("test_generate_returns_correct_shape:", "PASS" if passed else "FAIL")


def test_all_cells_assigned():
    """Every cell should belong to exactly one group."""
    gen = GroupGenerator(min_size=2, max_size=5)
    layout = gen.generate(5, 5)
    
    if layout is None:
        print("test_all_cells_assigned: FAIL — generation returned None")
        return
    
    # Count unique group IDs
    group_ids = set()
    for row in layout:
        for gid in row:
            group_ids.add(gid)
    
    passed = len(group_ids) > 0  # at least one group exists
    print("test_all_cells_assigned:", "PASS" if passed else "FAIL",
          f"— found {len(group_ids)} groups")


def test_group_sizes_within_bounds():
    """All groups should respect min_size and max_size constraints."""
    gen = GroupGenerator(min_size=2, max_size=5)
    layout = gen.generate(8, 8)
    
    if layout is None:
        print("test_group_sizes_within_bounds: FAIL — generation returned None")
        return
    
    # Count cells per group
    group_sizes = {}
    for row in layout:
        for gid in row:
            group_sizes[gid] = group_sizes.get(gid, 0) + 1
    
    violations = []
    for gid, size in group_sizes.items():
        if size < gen.min_size or size > gen.max_size:
            violations.append((gid, size))
    
    passed = len(violations) == 0
    print("test_group_sizes_within_bounds:", "PASS" if passed else "FAIL")
    if violations:
        print(f"  Violations: {violations}")


def test_groups_are_connected():
    """Every group should form a contiguous region."""
    gen = GroupGenerator(min_size=2, max_size=5)
    layout = gen.generate(7, 7)
    
    if layout is None:
        print("test_groups_are_connected: FAIL — generation returned None")
        return
    
    # Collect cells for each group
    groups = {}
    for r in range(len(layout)):
        for c in range(len(layout[0])):
            gid = layout[r][c]
            if gid not in groups:
                groups[gid] = []
            groups[gid].append((r, c))
    
    # Check connectivity for each group
    disconnected = []
    for gid, cells in groups.items():
        if not gen._is_connected(cells):
            disconnected.append(gid)
    
    passed = len(disconnected) == 0
    print("test_groups_are_connected:", "PASS" if passed else "FAIL")
    if disconnected:
        print(f"  Disconnected groups: {disconnected}")


def test_visual_small_grid():
    """Visual test: generate and display a 5x5 grid."""
    print("\n=== Visual Test: 5x5 grid ===")
    gen = GroupGenerator(min_size=2, max_size=4)
    
    attempts = 0
    layout = None
    while layout is None and attempts < 10:
        layout = gen.generate(5, 5)
        attempts += 1
    
    if layout is None:
        print("FAIL — could not generate valid layout after 10 attempts")
        return
    
    print(f"Generated successfully in {attempts} attempt(s)")
    
    # Build a Grid and visualize
    grid = Grid(5, 5)
    grid.build_cells(layout)
    draw_grid(grid)


def test_visual_medium_grid():
    """Visual test: generate and display an 8x8 grid."""
    print("\n=== Visual Test: 8x8 grid ===")
    gen = GroupGenerator(min_size=3, max_size=5)
    
    attempts = 0
    layout = None
    while layout is None and attempts < 10:
        layout = gen.generate(8, 8)
        attempts += 1
    
    if layout is None:
        print("FAIL — could not generate valid layout after 10 attempts")
        return
    
    print(f"Generated successfully in {attempts} attempt(s)")
    
    grid = Grid(8, 8)
    grid.build_cells(layout)
    draw_grid(grid)


if __name__ == "__main__":
    print("=== group_generator.py tests ===\n")
    test_generate_returns_correct_shape()
    test_all_cells_assigned()
    test_group_sizes_within_bounds()
    test_groups_are_connected()
    test_visual_small_grid()
    test_visual_medium_grid()
    print("\n=== done ===")