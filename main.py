import os

from generator import Generator
from models import Cell
from visualizer import draw_grid
from serializer import save_puzzle, load_puzzle

# ===== CONFIGURATION =====
COUNT = 10
ROWS = 10
COLS = 10
MIN_GROUP_SIZE = 2
MAX_GROUP_SIZE = 6
DIFF = 2
REM_PERCENT = 0.5
SEED = None
VERBOSE = False
DIR = f"output"
# =========================

#Average removal without constraint: 
# - 75%     For     6x6     2-5
# - 50%     For     15x15   3-8

def main():
    gen = Generator()
    
    print("Generating puzzle...")
    puzzle = gen.generate(ROWS, COLS,
                         difficulty=DIFF, 
                         max_group_size=MAX_GROUP_SIZE,
                         min_group_size=MIN_GROUP_SIZE,
                         seed=SEED,
                         removal_percentage=REM_PERCENT,
                         verbose=VERBOSE)
    
    if puzzle is None:
        print("Failed to generate puzzle")
        return
    
    save_puzzle(puzzle, "test.json")

    loaded_puzzle = load_puzzle("test.json")
    print(f"Loaded {loaded_puzzle.rows}x{loaded_puzzle.cols} puzzle")

    clues = sum(1 for r in range(loaded_puzzle.rows) for c in range(loaded_puzzle.cols) 
                if loaded_puzzle.cells[r][c].value is not None)
    total = loaded_puzzle.rows * loaded_puzzle.cols
    
    print(f"Success! Generated puzzle with {clues}/{total} clues")
    
    # Now generate the solution by filling the puzzle completely
    from solver import Solver
    solver = Solver()
    result = solver.solve(loaded_puzzle)

    if result.solved:
        draw_grid(loaded_puzzle, solution=result.grid)
        pass
    else:
        print("Warning: generated puzzle couldn't be solved!")
        draw_grid(loaded_puzzle)


def batch_generate():
    """Generate multiple puzzles and save to JSON files."""
    gen = Generator()

    os.makedirs(DIR, exist_ok=True)
    successes = 0
    
    for i in range(COUNT):
        print(f"\n=== Generating puzzle {i+1}/{COUNT} ===")
        
        grid = gen.generate(ROWS, COLS,
                            difficulty=DIFF, 
                            max_group_size=MAX_GROUP_SIZE,
                            min_group_size=MIN_GROUP_SIZE,
                            seed=SEED,
                            removal_percentage=REM_PERCENT,
                            verbose=VERBOSE)
        
        if grid is not None:
            # Save to numbered file
            filepath = os.path.join(DIR, f"puzzle_{i+1:03d}.json")
            save_puzzle(grid, filepath)
            print(f"  Saved to {filepath}")
            successes += 1
        else:
            print(f"  Failed to generate")
    
    print(f"\n=== Complete: {successes}/{COUNT} puzzles generated ===")

if __name__ == "__main__":
    batch_generate()