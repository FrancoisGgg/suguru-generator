import sys
import os

# Add parent directory to path so imports work
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from models import Cell, Group, Grid


def build_test_grid():
    """Build a simple 3x3 grid with 3 groups for testing.

    Group layout:
        0 0 1
        0 2 1
        2 2 1
    """
    grid = Grid(3, 3)

    layout = [
        [0, 0, 1],
        [0, 2, 1],
        [2, 2, 1],
    ]

    # build cells
    for r in range(3):
        row = []
        for c in range(3):
            row.append(Cell(r, c, layout[r][c]))
        grid.cells.append(row)

    # build groups
    group0 = Group(0, 3)
    group1 = Group(1, 3)
    group2 = Group(2, 3)

    for r in range(3):
        for c in range(3):
            cell = grid.cells[r][c]
            if cell.group_id == 0:
                group0.cells.append(cell)
            elif cell.group_id == 1:
                group1.cells.append(cell)
            elif cell.group_id == 2:
                group2.cells.append(cell)

    grid.groups = [group0, group1, group2]
    return grid


def test_get_cell():
    grid = build_test_grid()
    cell = grid.get_cell(1, 2)
    passed = cell.row == 1 and cell.col == 2
    print("test_get_cell:", "PASS" if passed else "FAIL")


def test_get_neighbors_corner():
    """Corner cell (0,0) should have exactly 3 neighbors."""
    grid = build_test_grid()
    cell = grid.get_cell(0, 0)
    neighbors = grid.get_neighbors(cell)
    passed = len(neighbors) == 3
    print("test_get_neighbors_corner:", "PASS" if passed else "FAIL",
          "— got", len(neighbors), "expected 3")


def test_get_neighbors_center():
    """Center cell (1,1) should have exactly 8 neighbors."""
    grid = build_test_grid()
    cell = grid.get_cell(1, 1)
    neighbors = grid.get_neighbors(cell)
    passed = len(neighbors) == 8
    print("test_get_neighbors_center:", "PASS" if passed else "FAIL",
          "— got", len(neighbors), "expected 8")


def test_get_neighbors_edge():
    """Edge cell (0,1) should have exactly 5 neighbors."""
    grid = build_test_grid()
    cell = grid.get_cell(0, 1)
    neighbors = grid.get_neighbors(cell)
    passed = len(neighbors) == 5
    print("test_get_neighbors_edge:", "PASS" if passed else "FAIL",
          "— got", len(neighbors), "expected 5")


def test_get_neighbors_does_not_include_self():
    """A cell should never appear in its own neighbor list."""
    grid = build_test_grid()
    cell = grid.get_cell(1, 1)
    neighbors = grid.get_neighbors(cell)
    passed = cell not in neighbors
    print("test_get_neighbors_does_not_include_self:", "PASS" if passed else "FAIL")


def test_get_group():
    grid = build_test_grid()
    cell = grid.get_cell(0, 2)     # group 1
    group = grid.get_group(cell)
    passed = group.id == 1
    print("test_get_group:", "PASS" if passed else "FAIL")


def test_get_group_peers_count():
    """Group peers should exclude the cell itself."""
    grid = build_test_grid()
    cell = grid.get_cell(0, 0)     # group 0, size 3
    peers = grid.get_group_peers(cell)
    passed = len(peers) == 2
    print("test_get_group_peers_count:", "PASS" if passed else "FAIL",
          "— got", len(peers), "expected 2")


def test_get_group_peers_excludes_self():
    """Cell should not appear in its own peer list."""
    grid = build_test_grid()
    cell = grid.get_cell(0, 0)
    peers = grid.get_group_peers(cell)
    passed = cell not in peers
    print("test_get_group_peers_excludes_self:", "PASS" if passed else "FAIL")


def test_is_complete_false():
    """Empty grid should not be complete."""
    grid = build_test_grid()
    passed = grid.is_complete() == False
    print("test_is_complete_false:", "PASS" if passed else "FAIL")


def test_is_complete_true():
    """Fully filled grid should be complete."""
    grid = build_test_grid()
    values = [
        [1, 2, 1],
        [3, 3, 2],
        [1, 2, 3],
    ]
    for r in range(3):
        for c in range(3):
            grid.cells[r][c].value = values[r][c]
    passed = grid.is_complete() == True
    print("test_is_complete_true:", "PASS" if passed else "FAIL")


def test_is_valid_empty():
    """Empty grid should be valid."""
    grid = build_test_grid()
    passed = grid.is_valid() == True
    print("test_is_valid_empty:", "PASS" if passed else "FAIL")


def test_is_valid_no_conflicts():
    """A correctly filled grid should be valid."""
    grid = build_test_grid()
    # manually place non-conflicting values
    grid.cells[0][0].value = 1
    grid.cells[0][1].value = 3
    grid.cells[1][0].value = 2
    passed = grid.is_valid() == True
    print("test_is_valid_no_conflicts:", "PASS" if passed else "FAIL")


def test_is_valid_neighbor_conflict():
    """Two adjacent cells with same value should fail."""
    grid = build_test_grid()
    grid.cells[0][0].value = 1
    grid.cells[0][1].value = 1     # adjacent to (0,0)
    passed = grid.is_valid() == False
    print("test_is_valid_neighbor_conflict:", "PASS" if passed else "FAIL")


def test_is_valid_diagonal_conflict():
    """Two diagonally adjacent cells with same value should fail."""
    grid = build_test_grid()
    grid.cells[0][0].value = 1
    grid.cells[1][1].value = 1     # diagonal neighbor of (0,0)
    passed = grid.is_valid() == False
    print("test_is_valid_diagonal_conflict:", "PASS" if passed else "FAIL")


def test_is_valid_group_conflict():
    """Two cells in the same group with same value should fail."""
    grid = build_test_grid()
    grid.cells[0][2].value = 2     # group 1
    grid.cells[1][2].value = 2     # group 1 — duplicate
    passed = grid.is_valid() == False
    print("test_is_valid_group_conflict:", "PASS" if passed else "FAIL")


def test_clone_independence():
    """Modifying clone should not affect original."""
    grid = build_test_grid()
    grid.cells[0][0].value = 1
    clone = grid.clone()
    clone.cells[0][0].value = 99
    passed = grid.cells[0][0].value == 1
    print("test_clone_independence:", "PASS" if passed else "FAIL")


def test_clone_candidates_independence():
    """Modifying clone candidates should not affect original."""
    grid = build_test_grid()
    grid.cells[0][0].candidates = {1, 2, 3}
    clone = grid.clone()
    clone.cells[0][0].candidates.add(99)
    passed = 99 not in grid.cells[0][0].candidates
    print("test_clone_candidates_independence:", "PASS" if passed else "FAIL")


def test_clone_groups_point_to_new_cells():
    """Groups in the clone should reference clone cells, not original cells."""
    grid = build_test_grid()
    clone = grid.clone()
    original_cell = grid.cells[0][0]
    clone_group_cells = clone.groups[0].cells
    passed = original_cell not in clone_group_cells
    print("test_clone_groups_point_to_new_cells:", "PASS" if passed else "FAIL")


if __name__ == "__main__":
    print("=== models.py tests ===\n")
    test_get_cell()
    test_get_neighbors_corner()
    test_get_neighbors_center()
    test_get_neighbors_edge()
    test_get_neighbors_does_not_include_self()
    test_get_group()
    test_get_group_peers_count()
    test_get_group_peers_excludes_self()
    test_is_complete_false()
    test_is_complete_true()
    test_is_valid_empty()
    test_is_valid_no_conflicts()
    test_is_valid_neighbor_conflict()
    test_is_valid_diagonal_conflict()
    test_is_valid_group_conflict()
    test_clone_independence()
    test_clone_candidates_independence()
    test_clone_groups_point_to_new_cells()
    print("\n=== done ===")


