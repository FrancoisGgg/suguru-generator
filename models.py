from random import randint
from typing import List

class Cell:
    def __init__(self, row, col, group_id, value=None):
        """Create a cell at (row, col) belonging to group_id.

        Args:
            row: zero-based row index
            col: zero-based column index
            group_id: ID of the group this cell belongs to
            value: initial value (None if empty)
        """
        self.row = row
        self.col = col
        self.value = value
        self.candidates = set()
        self.group_id = group_id
    
    def __str__(self):
        return "(" + str(self.row) + ", " + str(self.col) + ", " + str(self.value) + ")"
    
    def __repr__(self):
        return self.__str__()
    


class Group:
    def __init__(self, id, size):
        """Create an empty group.

        Args:
            id: unique identifier for this group
            size: number of cells in this group, determines range 1..size
        """
        self.id = id
        self.size = size
        self.cells : List[Cell] = []

    def __str__(self):
        return "g." + str(self.id)


class Grid:
    """The full Suguru board: a 2D array of cells divided into groups.

    This is the central data structure passed between solver, generator,
    and serializer. All coordinates are (row, col), zero-indexed.
    """

    def __init__(self, nrows, mcols):
        """Create an empty grid of given dimensions.

        Cells and groups must be populated after construction.

        Args:
            nrows: number of rows
            mcols: number of columns
        """
        self.rows = nrows
        self.cols = mcols
        self.cells : List[List[Cell]] = []     # 2D list: self.cells[row][col] = Cell
        self.groups : List[Group] = []    # flat list of Group objects
        self.solution : List[List[Cell]] = None

    def __str__(self):
        result = ""
        for row in self.cells:
            for cell in row:
                result += str(cell.value) + " "
            result += "\n"
        return result
    
    def build_cells(self, group_map):
        """Populate self.cells and self.groups from a 2D group ID layout.
        
        Args:
            group_map: 2D list of group IDs, same shape as the grid
        """
        # print("    Building cells...")
    
        # First, count group sizes
        group_sizes = {}
        for row in group_map:
            for gid in row:
                group_sizes[gid] = group_sizes.get(gid, 0) + 1
        
        # print(f"    Found {len(group_sizes)} groups")
        
        # Create Group objects
        groups_dict = {}
        for gid, size in group_sizes.items():
            group = Group(gid, size)
            groups_dict[gid] = group
            self.groups.append(group)
        
        # print("    Creating cells...")
        
        # Create cells and assign to groups
        self.cells = []
        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                gid = group_map[r][c]
                cell = Cell(r, c, gid, value=None)
                groups_dict[gid].cells.append(cell)
                row_cells.append(cell)
            self.cells.append(row_cells)
    
    # print("    Cells built successfully")

    def get_cell(self, row, col):
        """Return the Cell at position (row, col)."""
        return self.cells[row][col]


    def get_neighbors(self, cell) -> list[Cell]:
        """Return all cells adjacent to this cell, including diagonals.

        Checks all 8 directions. Skips out-of-bounds positions.
        A neighbor is any cell that cannot share the same value as this cell
        (the core Suguru adjacency constraint).

        Args:
            cell: the Cell whose neighbors we want
        Returns:
            list of Cell objects (between 3 and 8 depending on position)
        """

        cellx = cell.row
        celly = cell.col
        neig = list(0 for i in range(8))

        index = 0
        oob = 0
        for i in range(-1,2):
            for j in range(-1,2):

                if (cellx+i < 0 or cellx+i >= self.rows or celly+j < 0 or celly+j >= self.cols):
                    oob += 1
                    continue

                if (i or j):
                    neig[index] = self.cells[cellx+i][celly+j]
                    index += 1
        return neig[:8-oob]

        

    def get_group(self, cell) -> Group:
        """Return the Group that this cell belongs to.

        Args:
            cell: any Cell in the grid
        Returns:
            the Group object whose id matches cell.group_id
        """
        for group in self.groups:
            if group.id == cell.group_id:
                return group
        return None  # shouldn't happen if grid is valid

    def get_group_peers(self, cell) -> list[Cell]: 
        """Return all other cells in the same group as this cell.

        Excludes the cell itself. These cells must all have
        different values and collectively cover 1..group.size.

        Args:
            cell: the Cell whose group peers we want
        Returns:
            list of Cell objects in the same group, excluding cell itself
        """
        group = self.get_group(cell)
        others = list(0 for i in range(group.size-1))

        index = 0
        for c in group.cells:
            if c is not cell:
                others[index] = c
                index += 1
        return others



    def is_complete(self):
        """Return True if every cell has a non-None value."""
        return not any(cell.value is None for row in self.cells for cell in row)
        

    def is_valid(self):
        """Return True if no Suguru rule is currently violated.

        Checks two rules:
        1. No two adjacent cells (including diagonal) share the same value.
        2. No group contains a duplicate value.
        Does not check completeness — a partial grid can be valid.
        """
        # Rule 1 — no duplicate values in any group
        for group in self.groups:
            vals = [c.value for c in group.cells if c.value is not None]
            if len(vals) != len(set(vals)):
                return False

        # Rule 2 — no two neighbors share the same value
        for row in self.cells:
            for cell in row:
                if cell.value is not None:
                    neighbor_vals = [n.value for n in self.get_neighbors(cell) 
                                    if n.value is not None]
                    if cell.value in neighbor_vals:
                        return False

        return True

    def clone(self):
        """Return a fully independent deep copy of this grid.

        Used by the generator before backtracking and by the solver
        before trial-and-error, so the original is never mutated.
        """
        new_grid = Grid(self.rows, self.cols)
    
        # Step 1 — copy all cells
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                old_cell = self.cells[r][c]
                new_cell = Cell(old_cell.row, old_cell.col, old_cell.group_id, old_cell.value)
                new_cell.candidates = set(old_cell.candidates)  # copy the set
                row.append(new_cell)
            new_grid.cells.append(row)
        
        # Step 2 — rebuild groups pointing to new cells
        for group in self.groups:
            new_group = Group(group.id, group.size)
            for cell in group.cells:
                new_group.cells.append(new_grid.cells[cell.row][cell.col])
            new_grid.groups.append(new_group)
        
        return new_grid
    
    def get_candidates_for_cell(self, cell):
        """Get valid values for a cell based on current grid state."""
        cell_group = self.get_group(cell)
        candidates = set(range(1, cell_group.size + 1))
        
        for peer in self.get_group_peers(cell):
            candidates.discard(peer.value)
        
        for neigh in self.get_neighbors(cell):
            candidates.discard(neigh.value)
        
        return candidates

    def find_best_empty_cell(self):
        """Find empty cell with fewest candidates (MRV heuristic)."""
        best_cell = None
        min_candidates = float('inf')
        
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[r][c]
                
                if cell.value is not None:
                    continue
                
                candidates = self.get_candidates_for_cell(cell)
                num_candidates = len(candidates)
                
                if num_candidates < min_candidates:
                    min_candidates = num_candidates
                    best_cell = cell
        
        return best_cell








