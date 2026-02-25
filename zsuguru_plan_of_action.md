# Suguru Python Solver & Generator — Implementation Plan

## Context

Build a Suguru (Tectonics) puzzle solver and generator in Python. The solver will later be ported to Kotlin for an Android app's hint system. The generator stays Python-only (server-side puzzle creation). Design prioritizes clean OOP and easy Kotlin portability.

**Suguru rules recap:**
- NxM grid divided into irregular groups of connected cells
- A group of size N contains exactly the numbers 1..N
- No two identical numbers may be adjacent (including diagonally — 8 neighbors)

---

## File Structure

```
suguru/
├── models.py          # Data structures: Cell, Group, Grid
├── solver.py          # Constraint-propagation solver with technique tracking
├── group_generator.py # Random irregular region/shape generation
├── generator.py       # Full puzzle generation (fill + remove clues)
├── difficulty.py      # Difficulty rating based on solver techniques
├── serializer.py      # Puzzle I/O (load/save/export)
└── main.py            # CLI entry point for testing & batch generation
```

---

## 1. models.py — Data Structures

Portable OOP. No Python-specific magic. These map 1:1 to Kotlin data classes.

### `Cell`
```
Fields:
    row: int
    col: int
    value: int | None          # None = empty, 1..N = filled
    candidates: set[int]       # remaining possible values (for solver)
    group_id: int              # which group this cell belongs to
```

### `Group`
```
Fields:
    id: int
    cells: list[Cell]          # the cells in this group
    size: int                  # len(cells), determines range 1..size
```

### `Grid`
```
Fields:
    rows: int
    cols: int
    cells: list[list[Cell]]    # 2D array [row][col]
    groups: list[Group]

Methods:
    get_cell(row, col) -> Cell
    get_neighbors(cell) -> list[Cell]
        # Returns up to 8 adjacent cells (orthogonal + diagonal)
    get_group(cell) -> Group
    get_group_peers(cell) -> list[Cell]
        # Other cells in the same group (excludes self)
    is_complete() -> bool
        # All cells have a value
    is_valid() -> bool
        # No rule violations
    clone() -> Grid
        # Deep copy (for generator backtracking)
```

---

## 2. solver.py — Constraint Propagation Solver

Inspired by Simon Tatham's approach: layered techniques from simplest to hardest. The solver tracks WHICH techniques it used — this feeds into difficulty rating.

### `SolveResult`
```
Fields:
    solved: bool               # True if puzzle fully solved
    grid: Grid                 # The (partially) solved grid
    techniques_used: set[str]  # Names of techniques applied
    difficulty: int            # Max difficulty level reached (1-4)
    is_unique: bool            # True if exactly one solution (when checked)
```

### `Solver`
```
Fields:
    grid: Grid
    techniques_used: set[str]

Methods:
    solve(grid, max_difficulty=4) -> SolveResult
        # Main entry point. Applies techniques up to max_difficulty.
        # Loop: apply techniques in order until none makes progress, then stop.

    --- TECHNIQUE LEVEL 1 (Naked singles / trivial) ---

    _init_candidates(grid) -> None
        # For each empty cell, set candidates = {1..group_size}
        # Then eliminate: remove values already placed in the group
        # Then eliminate: remove values present in any neighbor

    _naked_single() -> bool
        # Scan all cells. If any cell has exactly 1 candidate, place it.
        # Propagate: remove that value from neighbors' candidates
        #            and from group peers' candidates.
        # Returns True if progress was made.

    _hidden_single() -> bool
        # For each group, for each value 1..N:
        #   if only one cell in the group can hold that value, place it.
        # Returns True if progress was made.

    --- TECHNIQUE LEVEL 2 (Neighbor constraints) ---

    _neighbor_elimination() -> bool
        # For each cell C with candidates, for each candidate V:
        #   look at all neighbors of C that are in the SAME group as C
        #   if placing V in C would leave a group-peer-neighbor with no
        #   valid place for some required value, eliminate V from C.
        # Returns True if any candidate was eliminated.

    _group_pair_exclusion() -> bool
        # Within a group, if two cells share the exact same 2 candidates
        # (naked pair), remove those values from candidates of all
        # cells that are neighbors of BOTH cells AND in the same group.
        # Returns True if progress made.

    --- TECHNIQUE LEVEL 3 (Cross-group reasoning) ---

    _cross_group_elimination() -> bool
        # If a value V in group A can only go in cells that are ALL
        # neighbors of a single cell C in group B, then V is eliminated
        # from C's candidates (since wherever V goes in A, it blocks C).
        # Returns True if progress made.

    --- TECHNIQUE LEVEL 4 (Trial / bifurcation — last resort) ---

    _trial_and_error() -> bool
        # Pick the empty cell with fewest candidates.
        # Try each candidate: clone grid, run solve() recursively
        #   with max_difficulty=3 (no nested trials).
        # If a candidate leads to contradiction, eliminate it.
        # If exactly one candidate survives, place it.
        # Returns True if progress made.

    --- HELPERS ---

    _place_value(cell, value) -> None
        # Set cell.value = value, clear cell.candidates.
        # Remove value from candidates of all neighbors.
        # Remove value from candidates of all group peers.
        # If any cell reaches 0 candidates -> raise Contradiction.

    _check_contradiction() -> bool
        # Any empty cell with 0 candidates?
        # Any group missing a required value with no cell able to hold it?

    has_unique_solution(grid) -> bool
        # Solve with backtracking, count solutions. Stop at 2.
        # Returns True if exactly 1 solution exists.
```

### Solver loop pseudocode:
```
def solve(grid, max_difficulty=4):
    init_candidates(grid)
    techniques_used = set()

    changed = True
    while changed:
        changed = False

        # Level 1
        while _naked_single() or _hidden_single():
            changed = True
            techniques_used.add("naked_single" / "hidden_single")

        if grid.is_complete(): break

        # Level 2 (only if level 1 stalled)
        if max_difficulty >= 2:
            if _neighbor_elimination() or _group_pair_exclusion():
                changed = True
                techniques_used.add(...)
                continue  # restart from level 1

        # Level 3
        if max_difficulty >= 3:
            if _cross_group_elimination():
                changed = True
                techniques_used.add(...)
                continue

        # Level 4
        if max_difficulty >= 4:
            if _trial_and_error():
                changed = True
                techniques_used.add("trial_and_error")
                continue

    return SolveResult(...)
```

---

## 3. group_generator.py — Region Shape Generation

Generates random irregular connected groups that tile the entire grid.

### `GroupGenerator`
```
Methods:
    generate(rows, cols, target_sizes=None) -> list[list[int]]
        # Returns a 2D array of group IDs.
        # target_sizes: optional list of desired group sizes.
        #   If None, aims for groups of size 3-5 (adjustable).
        #
        # Algorithm:
        #   1. Start with each cell as its own group (size 1).
        #   2. Randomly merge adjacent groups until all groups
        #      reach a minimum size (e.g., 2).
        #   3. Continue merging small groups into neighbors,
        #      respecting max size constraints.
        #   4. Shuffle merge order for randomness.
        #   5. Validate: all groups are connected (BFS/DFS check).

    _merge_groups(grid, group_a, group_b) -> None
        # Merge two adjacent groups into one.

    _is_connected(cells) -> bool
        # BFS/DFS to verify a set of cells forms a connected region
        # (orthogonal connectivity only — groups must be contiguous).

    _get_adjacent_groups(group_id, grid) -> set[int]
        # Returns IDs of groups that share an edge with this group.
```

### Algorithm detail:

```
1. Initialize: every cell is group_id = row * cols + col (unique)
2. Build list of all adjacent cell pairs (orthogonal only)
3. Shuffle the pair list
4. For each pair (A, B):
     if A and B in different groups:
       if merged size <= max_group_size:
         merge smaller group into larger
5. Repeat pass if any group is still below min_size:
     merge it into its smallest neighbor
6. Return group_id grid
```

---

## 4. generator.py — Puzzle Generation

Creates a complete Suguru puzzle: groups + filled grid + clue removal.

### `Generator`
```
Methods:
    generate(rows, cols, difficulty=2, max_group_size=5, min_group_size=2) -> Grid
        # Full pipeline:
        #   1. Generate group shapes (group_generator)
        #   2. Fill grid with valid complete solution (backtracking)
        #   3. Remove clues while maintaining unique solution
        #   4. Rate difficulty, adjust if needed
        #   Returns a Grid with some cells empty (the puzzle).

    _fill_grid(grid) -> bool
        # Backtracking fill: pick empty cell with fewest candidates,
        # try values in random order, recurse.
        # Returns True if a valid complete fill was found.

    _remove_clues(grid, solution, target_difficulty) -> Grid
        # 1. List all filled cells, shuffle them.
        # 2. For each cell:
        #      tentatively remove its value
        #      run solver at target_difficulty level
        #      if solver finds unique solution: keep it removed
        #      else: put the value back
        # 3. Return the puzzle grid.
        #
        # This is the bottleneck — each removal tests uniqueness.

    _adjust_difficulty(grid, solution, target) -> Grid
        # If puzzle is too easy: try removing more clues.
        # If puzzle is too hard: add back a strategic clue.
        # Re-rate after each adjustment.
```

### Generation flow:
```
generate(8, 8, difficulty=2)
    │
    ├─ GroupGenerator.generate(8, 8) -> group layout
    │
    ├─ Build Grid from group layout
    │
    ├─ _fill_grid(grid) -> complete valid solution
    │   └─ Backtracking with random value ordering
    │
    ├─ _remove_clues(grid, solution, target_difficulty=2)
    │   └─ For each cell (random order):
    │       ├─ Remove value
    │       ├─ Solver.solve(puzzle, max_difficulty=2)
    │       ├─ Solver.has_unique_solution(puzzle)
    │       └─ Keep removed or restore
    │
    └─ Return puzzle Grid
```

---

## 5. difficulty.py — Difficulty Rating

### `DifficultyRater`
```
Methods:
    rate(grid) -> DifficultyLevel
        # Run solver at increasing difficulty caps.
        # The minimum cap that solves it = the puzzle's difficulty.

    DifficultyLevel (enum):
        EASY = 1       # Only naked singles + hidden singles needed
        MEDIUM = 2     # Needs neighbor elimination or naked pairs
        HARD = 3       # Needs cross-group reasoning
        EXPERT = 4     # Needs trial-and-error / bifurcation
```

### Rating algorithm:
```
def rate(grid):
    for level in [1, 2, 3, 4]:
        result = solver.solve(grid.clone(), max_difficulty=level)
        if result.solved:
            return level
    return EXPERT  # shouldn't happen if puzzle is valid
```

---

## 6. serializer.py — Puzzle I/O

### `Serializer`
```
Methods:
    to_json(grid) -> str
        # JSON format:
        # {
        #   "rows": 8, "cols": 8,
        #   "groups": [[0,0,0,1,1,...], [0,0,1,1,1,...], ...],  # 2D group IDs
        #   "clues": [[null,3,null,...], [1,null,null,...], ...], # 2D values (null=empty)
        #   "solution": [[2,3,1,...], ...]                       # optional full solution
        # }

    from_json(json_str) -> Grid
        # Parse JSON back into Grid object.

    to_string(grid) -> str
        # Human-readable text format for debugging:
        # +---+---+---+
        # | 1   . | 2 |
        # |   +---+   |
        # | .   3 | . |
        # +---+---+---+

    from_string(text) -> Grid
        # Parse text format back into Grid.
```

---

## 7. main.py — Entry Point (edit-and-run style)

No CLI argument parsing. All config is set as variables at the top of main.py that you edit directly before running.

```python
# ===== CONFIGURATION (edit these) =====
ROWS = 8
COLS = 8
DIFFICULTY = 2                  # 1=Easy, 2=Medium, 3=Hard, 4=Expert
MAX_GROUP_SIZE = 5
MIN_GROUP_SIZE = 2
COUNT = 1                       # Number of puzzles to generate
SEED = None                     # Set to int for reproducible generation (None = random)
MODE = "generate"               # "generate" or "solve"
SOLVE_FILE = "puzzle.json"      # Only used when MODE = "solve"
OUTPUT_FORMAT = "both"          # "json", "text", or "both"
# =======================================

def main():
    if MODE == "generate":
        for i in range(COUNT):
            grid = Generator().generate(ROWS, COLS, DIFFICULTY, MAX_GROUP_SIZE, MIN_GROUP_SIZE, SEED)
            if OUTPUT_FORMAT in ("text", "both"):
                print(Serializer.to_string(grid))
            if OUTPUT_FORMAT in ("json", "both"):
                print(Serializer.to_json(grid))
    elif MODE == "solve":
        grid = Serializer.from_json(open(SOLVE_FILE).read())
        result = Solver().solve(grid)
        print(Serializer.to_string(result.grid))
        print(f"Difficulty: {result.difficulty}")
```

---

## Key Design Decisions (for Kotlin portability)

1. **No Python-specific idioms**: No list comprehensions in logic, no `*args/**kwargs`, no decorators. Use explicit loops and if/else.
2. **Classes over functions**: Everything in classes, easy to map to Kotlin classes.
3. **`set[int]` for candidates**: Maps to `MutableSet<Int>` in Kotlin.
4. **`None` for empty cells**: Maps to `null` / nullable `Int?` in Kotlin.
5. **No numpy/scipy**: Pure Python only, so Kotlin port has no dependency gap.
6. **Exceptions for contradictions**: `class Contradiction(Exception)` — maps to Kotlin exceptions.
7. **Clone via explicit copy methods**: `grid.clone()` not `copy.deepcopy()`.

---

## What ports to Kotlin (and what doesn't)

| Module | Kotlin? | Why |
|---|---|---|
| models.py | YES | Core data structures needed everywhere |
| solver.py | YES | Powers the hint system in the app |
| difficulty.py | YES | Rate puzzles client-side if needed |
| group_generator.py | NO | Puzzles generated server-side |
| generator.py | NO | Puzzles generated server-side |
| serializer.py | PARTIAL | `from_json` only (app receives puzzles as JSON) |

---

## Verification Plan

1. **Unit test the solver**: Create hand-crafted small grids (3x3, 4x4) with known solutions. Verify solver finds them.
2. **Test uniqueness checker**: Create a puzzle with 2 solutions, verify `has_unique_solution` returns False.
3. **Test group generator**: Generate 100 random grids, verify every cell is in a group, all groups connected, sizes within bounds.
4. **Test full pipeline**: Generate a puzzle, solve it, verify solution matches the original fill.
5. **Test difficulty rating**: Generate puzzles at each difficulty, verify easy ones don't need advanced techniques.
6. **Visual test**: Print puzzles with `to_string()`, manually verify they look correct.

---

## Implementation Order (step by step)

### Step 1: models.py
Foundation. Code Cell, Group, Grid with all methods (get_neighbors, get_group_peers, clone, is_valid, is_complete). Everything depends on this.

### Step 2: visualizer.py (early visual feedback)
Simple pygame or matplotlib grid renderer so you can SEE what's happening from step 2 onward.
- `draw_grid(grid)` — renders the grid in a window: group borders (thick lines), cell values, empty cells shown as dots
- `draw_candidates(grid)` — same but shows candidate sets in small text (useful for debugging solver)
- Color-code groups with distinct pastel colors
- Call it from main.py at any point to visualize current state

### Step 3: group_generator.py
Generate random group shapes. Use visualizer to inspect that groups look good (connected, reasonable sizes, organic shapes).

### Step 4: main.py (scaffold)
Wire up steps 1-3: generate a grid with random groups, visualize it. At this point you can run `python main.py` and SEE an empty grouped grid.

### Step 5: generator.py — _fill_grid() only
Backtracking fill that produces a valid complete solution. Visualize the filled grid to confirm it's correct.

### Step 6: solver.py — level 1 only
Naked singles + hidden singles. Test on easy hand-crafted puzzles.

### Step 7: generator.py — _remove_clues()
Remove clues one by one, checking the solver can still solve it. This gives you your first real playable puzzles (easy difficulty). Visualize puzzle vs solution side by side.

### Step 8: serializer.py
JSON save/load so you can persist puzzles and share them.

### Step 9: solver.py — level 2-3 techniques
Neighbor elimination, naked pairs, cross-group reasoning. Test each technique on crafted cases.

### Step 10: difficulty.py
Rate puzzles by which techniques they require. Update generator to target a difficulty level.

### Step 11: solver.py — level 4 (trial and error)
Last resort bifurcation. Enables generating expert-level puzzles.

### Step 12: polish
Tune generation speed, group shape aesthetics, difficulty balance. Batch generate and QA.
