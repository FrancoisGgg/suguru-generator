
import sys
import os

# Add parent directory to path so imports work
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from generator import Generator


def test_removal_rates():
    """Generate multiple puzzles and track removal statistics."""
    gen = Generator()
    
    results = {
        "diff_1": [],
        "diff_2": [],
        "diff_3": []
    }
    
    for difficulty in [1, 2, 3]:
        print(f"\n=== Testing Difficulty {difficulty} ===")
        
        for i in range(10):  # Generate 10 puzzles per difficulty
            print(f"\nAttempt {i+1}/10:")
            grid = gen.generate(10, 10, difficulty=difficulty, max_group_size=6, min_group_size=2, removal_percentage=1.0)
            
            if grid is not None:
                total = grid.rows * grid.cols
                filled = sum(1 for r in range(grid.rows) for c in range(grid.cols) 
                           if grid.cells[r][c].value is not None)
                removed = total - filled
                removal_rate = removed / total
                
                results[f"diff_{difficulty}"].append(removal_rate)
                print(f"  Removed {removed}/{total} = {removal_rate:.1%}")
    
    # Print summary
    print("\n=== SUMMARY ===")
    for diff, rates in results.items():
        if rates:
            avg = sum(rates) / len(rates)
            min_rate = min(rates)
            max_rate = max(rates)
            print(f"{diff}: avg={avg:.1%}, min={min_rate:.1%}, max={max_rate:.1%}")

if __name__ == "__main__":
    test_removal_rates()
