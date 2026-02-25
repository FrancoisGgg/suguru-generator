from models import Grid, Cell, Group


class Contradiction(Exception):
    """Raised when a cell reaches zero candidates.
    
    Signals that the current grid state is unsolvable.
    Used to abort backtracking branches early.
    """
    pass


class SolveResult:
    """The outcome of a solve attempt.
    
    Returned by Solver.solve(). Contains the resulting grid
    and metadata about how it was solved.
    """

    def __init__(self, solved, grid, techniques_used, difficulty):
        """Create a solve result.

        Args:
            solved: True if the puzzle was fully solved
            grid: the (partially) solved grid
            techniques_used: set of technique name strings that were applied
            difficulty: maximum difficulty level reached (1-4)
        """
        self.solved = solved
        self.grid = grid
        self.techniques_used = techniques_used
        self.difficulty = difficulty


class Solver:
    """Constraint-propagation solver for Suguru puzzles.

    Applies techniques in order from simplest to hardest.
    Tracks which techniques were needed — this determines difficulty.
    Designed to be portable to Kotlin for the Android hint system.
    """

    def __init__(self):
        self.grid = None
        self.techniques_used = set()

    def solve(self, grid: Grid, max_difficulty=4):
        """Main entry point. Attempt to solve the given grid.

        Applies techniques in increasing difficulty order.
        Stops when the puzzle is solved or no technique makes progress.
        Works on a clone — never mutates the input grid.

        Args:
            grid: the puzzle to solve (will not be mutated)
            max_difficulty: highest technique level allowed (1-4)
        Returns:
            SolveResult with solved=True if fully solved, False if stuck
        """

        self.grid = grid.clone()
        self.techniques_used = set()
        
        self._init_candidates()
        
        changed = True
        while changed:
            changed = False
            
            # Level 1 - keep applying until no progress
            while self._naked_single() or self._hidden_single():
                changed = True
            
            if self.grid.is_complete():
                break
            
            # Level 2 (if allowed)
            if max_difficulty >= 2:
                if self._neighbor_elimination():
                    changed = True
            
            if self.grid.is_complete():
                break
            
            # Level 3 (if allowed)
            if max_difficulty >= 3:
                if self._naked_subsets_generalized() or self._hidden_pairs():
                    changed = True
            
            if self.grid.is_complete():
                break
        
        return SolveResult(
            solved=self.grid.is_complete(),
            grid=self.grid,
            techniques_used=self.techniques_used,
            difficulty=1  # for now, only level 1 implemented
        )
    
    def has_unique_solution(self, grid):
        """Return True if the puzzle has exactly one solution.

        Uses backtracking to count solutions, stopping as soon as
        a second solution is found. Used by the generator to validate
        puzzles before keeping them.

        Args:
            grid: the puzzle to check
        Returns:
            True if exactly one solution exists, False otherwise
        """
        cloned = grid.clone()
        count = self._count_solutions(cloned, limit=2)
        return count == 1

    def _count_solutions(self, grid, limit=2):
        """Count solutions up to a limit using backtracking."""
        if grid.is_complete():
            return 1
        
        best_cell = grid.find_best_empty_cell()
        
        if best_cell is None:
            return 1
        
        best_candidates = grid.get_candidates_for_cell(best_cell)
        
        # Try each candidate and count solutions
        total_count = 0
        
        for value in best_candidates:
            best_cell.value = value
            count = self._count_solutions(grid, limit)
            total_count += count
            
            if total_count >= limit:
                best_cell.value = None
                return limit
            
            best_cell.value = None
        
        return total_count

    def _init_candidates(self):
        """Initialize candidate sets for all empty cells.

        For each empty cell: start with {1..group_size},
        then remove values already placed in its group,
        then remove values present in any of its neighbors.
        Must be called once at the start before any technique.
        """

        cells = self.grid.cells
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                cell = cells[r][c]
                if cell.value is None:
                    cell_group = self.grid.get_group(cell)
                    # init
                    cell.candidates = set(range(1, cell_group.size + 1))
                    # print(f"Cell ({r},{c}) group {cell.group_id} size {cell_group.size}, initial: {cell.candidates}")
                    
                    # remove group
                    for peer in self.grid.get_group_peers(cell):
                        if peer.value is not None:
                            cell.candidates.discard(peer.value)
                            # print(f"  Removed {peer.value} (from group)")
                    
                    # remove neighbors
                    for neigh in self.grid.get_neighbors(cell):
                        if neigh.value is not None:
                            cell.candidates.discard(neigh.value)
                            # print(f"  Removed {neigh.value} (from neighbor)")
                    
                    # print(f"  Final candidates: {cell.candidates}")


        
    def _naked_single(self): # LEVEL 1
        """Place any cell that has exactly one remaining candidate.

        After placing, propagate: remove the value from all
        neighbors' candidates and all group peers' candidates.
        
        Returns:
            True if at least one cell was placed
        """

        is_placed = False

        cells = self.grid.cells
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                cell = cells[r][c]
                if cell.value is None and len(cell.candidates) == 1:
                    self._place_value(cell, list(cell.candidates)[0])
                    self.techniques_used.add("naked_single")
                    # print(f"Naked sinlge: Placed {cell.value} at ({cell.row}, {cell.col})")
                    is_placed = True
        return is_placed


    def _hidden_single(self): # LEVEL 1
        """Place a value if only one cell in its group can hold it.

        For each group, for each value 1..N: if exactly one cell
        in the group still has that value as a candidate, place it.
        
        Returns:
            True if at least one cell was placed
        """

        is_placed = False

        groups = self.grid.groups

        for group in groups:
            vals = [0] * (group.size + 1)
            for cell in group.cells:
                if cell.value is None:  # only empty cells
                    for cand in cell.candidates:
                        vals[cand] += 1
            to_place = [i for i, v in enumerate(vals) if v == 1] # all the singles
            # After finding which values appear exactly once
            for value in to_place:
                # Find which cell has this value as a candidate
                for cell in group.cells:
                    if cell.value is None and value in cell.candidates:
                        self._place_value(cell, value)
                        self.techniques_used.add("hidden_single")
                        # print(f"Hidden sinlge: Placed {cell.value} at ({cell.row}, {cell.col})")
                        is_placed = True
                        break  # found it, move to next value
        return is_placed

    def _neighbor_elimination(self): # LEVEL 2
        """Level 2: Remove candidates based on neighbor constraints.
        
        If a value in a group can only appear in cells that are
        neighbors of each other, eliminate that value from their
        shared neighbors.
        
        Returns:
            True if any candidates were removed
        """
        progress = False

        for group in self.grid.groups:
            
            # Create dict {value: [cells]}
            common_cands = {}
            for cell in group.cells:
                if cell.value is None:  # Only empty cells
                    for cand in cell.candidates:
                        if cand not in common_cands:
                            common_cands[cand] = []
                        common_cands[cand].append(cell)

            # For each value with multiple cells -> discard from common neighbors
            for val, cells in common_cands.items(): 
                if len(cells) > 1:  # Only if multiple cells in group
                    common_neigh = set(self.grid.get_neighbors(cells[0]))
                    for i in range(1, len(cells)):  # ← Fixed range
                        common_neigh &= set(self.grid.get_neighbors(cells[i]))

                    # Remove candidates for all concerned cells
                    for cell in common_neigh:
                        if cell.value is None and val in cell.candidates:  # ← Check empty and has candidate
                            cell.candidates.discard(val)
                            self.techniques_used.add("neighbor_elimination")
                            progress = True

        return progress
    
    def _naked_pairs(self, max_size=3): # LEVEL 3
        """Level 3: Naked pairs elimination.
        
        If two cells in a group both have exactly the same two candidates
        (e.g., both are {2, 5}), then those two values must go in those
        two cells. Remove those candidates from all other cells in the group.
        
        Also handles naked triples: three cells with the same three candidates.
        
        Returns:
            True if any candidates were removed
        """

        progress = False

        for group in self.grid.groups:

            #Create dict {[candidates]: [cells]}
            pairs_cells = {}
            for cell in group.cells:
                if cell.value is None:  # Only empty cells
                    cands = frozenset(cell.candidates)
                    if 2 <= len(cands) <= max_size:
                        if cands not in pairs_cells:
                            pairs_cells[cands] = []
                        pairs_cells[cands].append(cell)

            #Check pairs and apply
            for pair, cells in pairs_cells.items():
                size_pair = len(pair)
                size_cells = len(cells)
                if size_cells < 2: #nothing to infer
                    continue
                if size_pair < size_cells: #puzzle broken
                    print("Puzzle broken. Shouldnt happen.")
                    continue
                if size_pair > size_cells: #nothing to infer
                    continue
                if size_pair > max_size: #out of limits
                    continue

                #case left: size_pair == size_cells -> naked pair
                cells_to_modif = set(group.cells)
                for cell in cells: 
                    cells_to_modif.discard(cell)
                for cell in cells_to_modif:
                    if cell.value is None:  # Check cell is empty
                        before = len(cell.candidates)
                        cell.candidates -= pair  
                        if len(cell.candidates) < before:
                            progress = True
                            self.techniques_used.add("naked_pairs")

        return progress
    
    #NAKED PAIRS GENERALIZED current version only check EXACT pairs 
    def _naked_subsets_generalized(self, max_size=3):
        """Generalized naked subsets - handles non-uniform candidates."""
        progress = False
        
        for group in self.grid.groups:
            # Get all empty cells
            empty_cells = [c for c in group.cells if c.value is None]
            
            # Try all combinations of 2-3 cells
            from itertools import combinations
            
            for size in range(2, min(max_size + 1, len(empty_cells) + 1)):
                for cell_combo in combinations(empty_cells, size):
                    # Union of all candidates in this combo
                    union = set()
                    for cell in cell_combo:
                        union |= cell.candidates
                    
                    # If N cells contain exactly N values total: naked subset!
                    if len(union) == size:
                        # Remove these values from other cells
                        for cell in group.cells:
                            if cell not in cell_combo and cell.value is None:
                                before = len(cell.candidates)
                                cell.candidates -= union
                                if len(cell.candidates) < before:
                                    progress = True
                                    self.techniques_used.add("naked_subsets")
        
        return progress
    
    def _hidden_pairs(self, max_size=3): # LEVEL 3
        """Level 3: Hidden pairs/triples elimination.
        
        If two values in a group can only appear in the same two cells
        (and nowhere else in the group), then those two cells must contain
        those two values. Remove all other candidates from those cells.
        
        Also handles hidden triples: three values restricted to three cells.
        
        Args:
            max_size: maximum subset size to check (2 for pairs, 3 for triples)
        
        Returns:
            True if any candidates were removed
        """

        progress = False

        for group in self.grid.groups:
            # Create dict {val: [cells]}
            cands_to_cells = {i: [] for i in range(1, group.size + 1)}
            for cell in group.cells:
                if cell.value is None:
                    for cand in cell.candidates:
                        cands_to_cells[cand].append(cell)

            # Find intersections: Create dict {cell_comb: appearances}
            comb_appear = {}
            for key, item in cands_to_cells.items():
                comb = frozenset(item)
                if len(comb) <= max_size:  # Only check subsets up to max_size
                    if comb not in comb_appear:
                        comb_appear[comb] = 0
                    comb_appear[comb] += 1

            # Find hidden pairs/triples
            for key, item in comb_appear.items():
                if item < 2:  # Need at least 2 values
                    continue
                if item != len(key):  # N values in N cells
                    continue

                # Left over case: hidden pair/triple found
                cands_to_remove = set(range(1, group.size + 1))
                for cand, pair in cands_to_cells.items():
                    if key == frozenset(pair):  # ← Fixed
                        cands_to_remove.discard(cand)

                for cell in key:
                    before = len(cell.candidates)
                    for val in cands_to_remove:
                        cell.candidates.discard(val)
                    if len(cell.candidates) < before:
                        progress = True
                        self.techniques_used.add("hidden_pairs")

        return progress


    def _place_value(self, cell: Cell, value):
        """Place a value in a cell and propagate constraints.

        Sets cell.value, clears cell.candidates.
        Removes value from all neighbors' candidates.
        Removes value from all group peers' candidates.
        Raises Contradiction if any cell reaches zero candidates.

        Args:
            cell: the Cell to fill
            value: the integer value to place
        """
        # print(f"Placing {value} at ({cell.row}, {cell.col})")
        cell.value = value
        cell.candidates = set()
        
        for peer in self.grid.get_group_peers(cell):
            peer.candidates.discard(value)
            if peer.value is None and len(peer.candidates) == 0:
                # print(f"  Contradiction: peer at ({peer.row}, {peer.col}) has no candidates left")
                # print(f"  Peer group: {peer.group_id}, current candidates were: {peer.candidates}")
                raise Contradiction()
        
        for neigh in self.grid.get_neighbors(cell):
            neigh.candidates.discard(value)
            if neigh.value is None and len(neigh.candidates) == 0:
                # print(f"  Contradiction: neighbor at ({neigh.row}, {neigh.col}) has no candidates left")
                raise Contradiction()