import random
from typing import List
from models import Grid, Cell, Group
from group_generator import GroupGenerator
from solver import Solver
from difficulty import rate

class FillTimeout(Exception):
    """Raised when fill_grid takes too long or hits too many failures."""
    pass

class Generator:
    """Full puzzle generator: groups -> fill -> remove clues -> rate.
    
    Combines GroupGenerator and Solver to produce valid Suguru puzzles
    with unique solutions at the requested difficulty level.
    """

    def __init__(self):
        """Create a Generator with a default GroupGenerator."""
        self.group_generator = GroupGenerator()

    def generate(self, rows, cols, difficulty=2, removal_percentage=1.0, max_group_size=5, min_group_size=2, seed=None, verbose=False):
        """Generate a complete Suguru puzzle.

        Full pipeline (for now just steps 1-2, more added in steps 6-7):
            1. Generate group layout
            2. Fill with valid solution
            3. (Later) Remove clues while maintaining unique solvability
            4. (Later) Rate and adjust difficulty

        Args:
            rows: number of rows
            cols: number of columns
            difficulty: target difficulty level (1-4) [not used yet]
            max_group_size: largest allowed group size
            min_group_size: smallest allowed group size
            seed: random seed for reproducibility (None = random)
        Returns:
            Grid with all cells filled (a complete valid solution),
            or None if generation failed after retries
        """

        if seed is not None:
            random.seed(seed)
        
        self.group_generator.min_size = min_group_size
        self.group_generator.max_size = max_group_size
        self.verbose = verbose
        
        MAX_ATTEMPTS = 25
        
        for attempt in range(MAX_ATTEMPTS):
            if verbose:
                print(f"\n=== Attempt {attempt + 1}/{MAX_ATTEMPTS} ===")
        
            # Step 1: Generate group layout
            if verbose:
                print("Step 1: Generating groups...")
            layout = self.group_generator.generate(rows, cols, )
            
            if layout is None:
                if verbose:
                    print("  Failed: group layout generation")
                continue
            if verbose:
                print("  Success: groups generated")
            
            # Step 2: Build and fill grid
            if verbose:
                print("Step 2: Building grid...")
            grid = Grid(rows, cols)
            grid.build_cells(layout)
            if verbose:
                print("  Grid built")

            if verbose:
                print("Step 3: Filling grid with backtracking...")
            if not self._fill_grid(grid):
                if verbose:
                    print("  Failed: couldn't fill grid (unsolvable layout)")
                continue
            if verbose:
                print("  Success: grid filled")
            
            # Step 4: Remove clues
            if verbose:
                print("Step 4: Removing clues...")
            solution = grid.clone()
            grid.solution = grid.clone()
            self._remove_clues(grid, solution, difficulty, removal_percentage)
            
            # Step 5: Difficulty Rating
            if verbose:
                print("Step 5: Difficulty Rating...")

            actual_difficulty = rate(grid)
            if  actual_difficulty == difficulty:
                if verbose:
                    print(f"  Generated difficulty {actual_difficulty} puzzle")
                return grid
            else:
                if verbose:
                    print(f"  ✗ Mismatch, retrying...")
                continue  # Try again
            
        
        return None

    def _fill_grid(self, grid):
        """Fill every cell with a valid value using backtracking.

        Uses MRV (Minimum Remaining Values) heuristic: always picks
        the empty cell with fewest possible values to try next.
        Values are tried in random order for puzzle variety.

        Args:
            grid: Grid with groups assigned but cells empty
        Returns:
            True if successfully filled, False if unsolvable layout
        """
        import time
        self.fill_call_count = 0
        self.fill_start_time = time.time()
        self.early_failures = 0  # count how many times we hit dead ends early
        
        try: 
            result = self._fill_grid_recursive(grid, depth=0)
            elapsed = time.time() - self.fill_start_time
            # print(f"    Backtracking: {elapsed:.2f}s, {self.fill_call_count} calls, {self.early_failures} early failures")
            return result
        except FillTimeout:
            elapsed = time.time() - self.fill_start_time
            # print(f"    Aborted: {elapsed:.2f}s, {self.fill_call_count} calls, {self.early_failures} failures")
            return False

    def _fill_grid_recursive(self, grid, depth=0):
        """Recursive backtracking with depth limit."""
        
        # Progress indicator every 100 calls
        # if depth % 50 == 0 and depth > 0:
        #     print(f"    Backtracking depth: {depth}")
        
        # Safety limit - if we go this deep, the layout is probably unsolvable
        self.fill_call_count += 1
    
        # Print progress every 500 calls
        # if self.fill_call_count % 500 == 0:
        #     print(f"      [{self.fill_call_count} calls, depth {depth}]")
        
        cell = grid.find_best_empty_cell()
        if cell is None:
            return True

        candidates = grid.get_candidates_for_cell(cell)
        
        # Track patterns
        if not candidates:
            self.early_failures += 1
            if self.early_failures > 100:
                if self.verbose:
                    print(f"      Aborting: 100 early failures")
                raise FillTimeout(f"100+ early failures")
                # return False
            return False
        
        # NEW: Print when we're at specific depths with info
        if depth >55:
            num_empty = sum(1 for r in range(grid.rows) for c in range(grid.cols) 
                        if grid.cells[r][c].value is None)
            # print(f"      Depth {depth}: {num_empty} cells remaining, trying {len(candidates)} candidates at ({cell.row},{cell.col})")
        
        candidates_list = list(candidates)
        random.shuffle(candidates_list)

        for value in candidates_list:
            cell.value = value
            
            if self._fill_grid_recursive(grid, depth + 1):
                return True
            
            cell.value = None
        
        return False
    
    def _remove_clues(self, grid: Grid, solution, target_difficulty, removal_percentage=1.0):
        """Remove clues one by one while preserving unique solvability.

        Shuffles all filled cells, then for each: tentatively removes
        its value, checks if the solver can still find a unique solution
        at target_difficulty. Keeps it removed if yes, restores if no.
        
        This is the bottleneck — each removal tests uniqueness which
        requires running the solver with backtracking.

        Args:
            grid: the filled solution grid (will be mutated)
            solution: untouched copy of the solution for reference
            target_difficulty: solver max level for uniqueness check (not used yet)
            removal_percentage: 
                0.0-1.0, what fraction of clues to try removing
                1.0 = remove as many as possible
                0.5 = stop after removing 50% of total cells
        Returns:
            the same grid with as many clues removed as possible
        """

        solver = Solver()
        filled_cells = []
        
        for r in range(grid.rows):
            for c in range(grid.cols):
                if grid.cells[r][c].value is not None:
                    filled_cells.append(grid.cells[r][c])
        
        random.shuffle(filled_cells)
        
        total_cells = len(filled_cells)
        max_removals = int(total_cells * removal_percentage)  # ← New limit
        removed_count = 0
        for i, cell in enumerate(filled_cells):
            if removed_count >= max_removals:  # ← Early stop
                if self.verbose:
                    print(f"  Reached removal limit ({max_removals}), stopping")
                break
            if (i + 1) % 5 == 0:
                if self.verbose:
                    print(f"  Checking clue {i+1}/{total_cells} (removed so far: {removed_count})")
            
            val = cell.value
            cell.value = None

            # Check both: solvable at difficulty AND unique
            result = solver.solve(grid.clone(), max_difficulty=target_difficulty)
            
            if result.solved and solver.has_unique_solution(grid):
                removed_count += 1  # keep removed
            else:
                cell.value = val  # restore
                
        # print(f"  Finished: removed {removed_count}/{total_cells} clues")
        return grid