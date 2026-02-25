from models import *


def init_test_grid():
    grid = Grid(6, 6)

    # Group layout
    group_map = [
        [0, 0, 0, 1, 2, 2],
        [3, 3, 1, 1, 2, 2],
        [3, 3, 1, 7, 7, 2],
        [3, 4, 1, 7, 7, 6],
        [4, 4, 5, 5, 7, 6],
        [4, 5, 5, 5, 6, 6],
    ]

    # solution = [
    #     [2, 3, 1, 4, None, 2],
    #     [1, 4, 5, 3, None, 3],
    #     [2, 3, 2, 4, None, 2],
    #     [5, 4, 1, 3, 1, 3],
    #     [1, 3, 5, 2, 5, 2],
    #     [2, 4, 1, 3, 4, 1],
    # ]

    solution = [
        [2, 3, 1, 4, 1, 2],
        [1, 4, 5, 3, 5, 3],
        [2, 3, 2, 4, 2, 4],
        [5, 4, 1, 3, 1, 3],
        [1, 3, 5, 2, 5, 2],
        [2, 4, 1, 3, 4, 1],
    ]

    # Create groups with correct sizes
    group_sizes = {}
    for row in group_map:
        for gid in row:
            group_sizes[gid] = group_sizes.get(gid, 0) + 1

    # Create Group objects
    groups = {}
    for gid, size in group_sizes.items():
        group = Group(gid, size)
        groups[gid] = group
        grid.groups.append(group)

    # Create cells and assign to groups
    grid.cells = []
    for r in range(grid.rows):
        row_cells = []
        for c in range(grid.cols):
            gid = group_map[r][c]
            cell = Cell(r, c, gid, solution[r][c])

            # Add cell to group
            groups[gid].cells.append(cell)

            row_cells.append(cell)
        grid.cells.append(row_cells)
    # grid.cells[1][1].value = None

    return grid



def print_grid(grid):
    rows = grid.rows
    cols = grid.cols

    def cell_value(cell):
        return str(cell.value) if cell.value is not None else "."

    for r in range(rows):

        # --- Print horizontal group boundaries ---
        if r == 0:
            # Top border
            # print("+" + "---+" * cols)
            pass
        else:
            line = ""
            for c in range(cols):
                # If group differs from cell above, draw thick border
                if grid.cells[r][c].group_id != grid.cells[r-1][c].group_id:
                    line += " ---"
                else:
                    line += "    "
            print(line)

        # --- Print row content with vertical borders ---
        row_line = ""
        for c in range(cols):

            # Left border
            if c == 0:
                row_line += " "
                pass

            else:
                # If group differs from left cell, draw thick border
                if grid.cells[r][c].group_id != grid.cells[r][c-1].group_id:
                    row_line += "|"
                else:
                    row_line += " "

            row_line += f" {cell_value(grid.cells[r][c])} "

        # row_line += "|"
        print(row_line)

    # Bottom border
    # print("+" + "---+" * cols)
