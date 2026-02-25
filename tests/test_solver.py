import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from models import Grid, Cell, Group
from solver import Solver
from visualizer import draw_grid


def build_easy_puzzle():
    """Build a 4x4 puzzle with known layout and clues.
    
    Group layout:
        0 0 0 0
        1 1 2 2
        1 1 2 2
        3 3 3 3
    
    Groups:
        Group 0: size 4 → {1,2,3,4}
        Group 1: size 4 → {1,2,3,4}
        Group 2: size 4 → {1,2,3,4}
        Group 3: size 4 → {1,2,3,4}
    
    Starting clues:
        2 . 3 .
        . 4 2 .
        . 1 . .
        3 . . .
    """
    grid = Grid(4, 4)
    
    layout = [
        [0, 0, 0, 0],
        [1, 1, 2, 2],
        [1, 1, 2, 2],
        [3, 3, 3, 3],
    ]
    
    clues = [
        [2, None, 3, None],
        [None, 4, 2, None],
        [None, 1, None, None],
        [3, None, None, None],
    ]
    
    grid.build_cells(layout)
    
    # Set the clues
    for r in range(4):
        for c in range(4):
            if clues[r][c] is not None:
                grid.cells[r][c].value = clues[r][c]
    
    return grid


def test_init_candidates():
    """Test that candidates are initialized correctly."""
    grid = build_easy_puzzle()
    solver = Solver()
    solver.grid = grid
    solver._init_candidates()
    
    # Check that empty cells have candidates
    empty_cells_have_candidates = True
    for r in range(4):
        for c in range(4):
            cell = grid.cells[r][c]
            if cell.value is None and len(cell.candidates) == 0:
                empty_cells_have_candidates = False
    
    passed = empty_cells_have_candidates
    print("test_init_candidates:", "PASS" if passed else "FAIL")


def test_naked_single_finds_singles():
    """Test that naked single technique works."""
    grid = build_easy_puzzle()
    solver = Solver()
    solver.grid = grid
    solver._init_candidates()
    
    # Run naked single
    progress = solver._naked_single()
    
    # Should find at least one naked single
    passed = progress == True
    print("test_naked_single_finds_singles:", "PASS" if passed else "FAIL")


def test_solve_easy_puzzle():
    """Test that solver can complete the puzzle."""
    grid = build_easy_puzzle()
    solver = Solver()
    
    result = solver.solve(grid, max_difficulty=1)
    
    passed = result.solved == True
    print("test_solve_easy_puzzle:", "PASS" if passed else "FAIL")
    
    if not passed:
        print("  Grid state (incomplete):")
        for row in result.grid.cells:
            print("  ", [c.value if c.value else '.' for c in row])
    else:
        print("  Solved grid:")
        for row in result.grid.cells:
            print("  ", [c.value for c in row])


def test_solve_uses_techniques():
    """Test that solver tracks which techniques were used."""
    grid = build_easy_puzzle()
    solver = Solver()
    
    result = solver.solve(grid)
    
    passed = len(result.techniques_used) > 0
    print("test_solve_uses_techniques:", "PASS" if passed else "FAIL",
          f"— used {result.techniques_used}")

def test_has_unique_solution_on_complete_grid():
    """A complete filled grid should have exactly one solution (itself)."""
    from generator import Generator
    
    gen = Generator()
    grid = None
    while grid is None:
        grid = gen.generate(4, 4, min_group_size=3, max_group_size=4)
    
    solver = Solver()
    passed = solver.has_unique_solution(grid) == True
    
    print("test_has_unique_solution_on_complete_grid:", "PASS" if passed else "FAIL")


def test_has_unique_solution_on_puzzle():
    """The test puzzle should have a unique solution."""
    grid = build_easy_puzzle()
    solver = Solver()
    
    has_unique = solver.has_unique_solution(grid)
    
    print("test_has_unique_solution_on_puzzle:", "PASS" if has_unique else "FAIL",
          f"— unique={has_unique}")


def test_multiple_solutions_detected():
    """A puzzle with multiple solutions should return False."""
    # Create a nearly empty 3x3 grid with just one clue
    grid = Grid(3, 3)
    layout = [
        [0, 0, 1],
        [0, 2, 1],
        [2, 2, 1],
    ]
    grid.build_cells(layout)
    
    # Only one clue - many solutions possible
    grid.cells[0][0].value = 1
    
    solver = Solver()
    has_unique = solver.has_unique_solution(grid)
    
    passed = has_unique == False  # should NOT be unique
    print("test_multiple_solutions_detected:", "PASS" if passed else "FAIL")

def manual_test_puzzle(layout, clues):

    size = len(layout)
    grid = Grid(size, size)

    grid.build_cells(layout)
    # Set the clues
    for r in range(size):
        for c in range(size):
            if clues[r][c] is not None:
                grid.cells[r][c].value = clues[r][c]

    return grid

def changed_cells(grid1, grid2):

    result = []
    for r in range(grid1.rows):
        for c in range(grid1.cols):
            cell1 = grid1.cells[r][c]
            cell2 = grid2.cells[r][c]
            if cell1.value != cell2.value or cell1.candidates != cell2.candidates:
                result.append(cell2)
    return result

def print_all_candidates(grid):
    for row in grid.cells:
        for cell in row:
            print(cell.candidates)

def test_naked_single():
    solver = Solver()
    layout = [
        [0, 0, 0, 0],
        [1, 1, 2, 2],
        [1, 1, 2, 2],
        [3, 3, 3, 3],
    ]
    
    clues = [
        [None, None, None, None],
        [None, None, None, None],
        [None, None, None, None],
        [4, 1, 2, None],
    ]

    grid = manual_test_puzzle(layout, clues)

    solver.grid = grid
    solver._init_candidates()

    before = grid.clone()
    
    solver._naked_single()

    print("test_naked_singles visually OK")


def test_hidden_single():
    solver = Solver()
    layout = [
        [0, 0, 1, 1, 1],
        [0, 0, 1, 1, 2],
        [3, 3, 5, 2, 2],
        [3, 3, 5, 5, 5],
        [4, 3, 5, 6, 6],
    ]
    
    clues = [
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, 3],
        [None, None, None, None, 4],
        [None, 3, None, None, None],
    ]

    grid = manual_test_puzzle(layout, clues)

    solver.grid = grid
    solver._init_candidates()

    before = grid.clone()
    
    # print_all_candidates(grid)
    # print("=====")
    solver._hidden_single()
    # print_all_candidates(grid)
    # draw_grid(grid)
    print("test_hidden_singles visually OK")

def test_neigh_elim():
    pass

def test_naked_pair():
    pass

def test_hidden_pair():
    pass

if __name__ == "__main__":
    print("=== solver.py tests ===\n")

    manual = True

    if manual:
        test_naked_single()
        test_hidden_single()
        test_neigh_elim()
        test_naked_pair()
        test_hidden_pair()
    else:
        test_init_candidates()
        test_naked_single_finds_singles()
        test_solve_easy_puzzle()
        test_solve_uses_techniques()
        test_has_unique_solution_on_complete_grid()
        test_has_unique_solution_on_puzzle()
        test_multiple_solutions_detected()
    print("\n=== done ===")