# difficulty.py

from solver import Solver

def rate(grid):
    """Rate puzzle difficulty by trying solver at each level.
    
    Args:
        grid: the puzzle to rate
    Returns:
        int: difficulty level (1-4)
    """
    solver = Solver()
    
    for level in [1, 2, 3, 4]:
        result = solver.solve(grid.clone(), max_difficulty=level)
        if result.solved:
            return level
    
    return 4  # Expert if not solvable with our techniques