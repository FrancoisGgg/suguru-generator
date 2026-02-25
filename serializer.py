import json
from models import Grid
from difficulty import rate

def save_puzzle(grid, filepath):
    """Save a puzzle grid to JSON file.
    
    Args:
        grid: Grid object with cells filled (the puzzle state)
        filepath: where to save
    """
def save_puzzle(grid, filepath):
    """Save a puzzle grid to JSON file."""
    
    # Build groups list
    groups_data = []
    for group in grid.groups:
        groups_data.append({
            "id": group.id,
            "size": group.size
        })
    
    # Build layout (2D array of group IDs)
    layout = []
    for r in range(grid.rows):
        row = []
        for c in range(grid.cols):
            row.append(grid.cells[r][c].group_id)
        layout.append(row)
    
    # Build puzzle (current values)
    puzzle = []
    for r in range(grid.rows):
        row = []
        for c in range(grid.cols):
            row.append(grid.cells[r][c].value)
        puzzle.append(row)
    
    # Build solution (if exists)
    solution = None
    if hasattr(grid, 'solution') and grid.solution is not None:
        solution = []
        for row in grid.solution.cells:  # ← Extract from the Grid's cells
            solution.append([cell.value for cell in row])
    
    # Combine into dictionary
    data = {
        "rows": grid.rows,
        "cols": grid.cols,
        "groups": groups_data,
        "layout": layout,
        "puzzle": puzzle,
        "solution": solution
    }

    data["difficulty"] = rate(grid)
    
    # Custom formatting: write manually for readable grids
    with open(filepath, 'w') as f:
        f.write("{\n")
        f.write(f'  "rows": {data["rows"]},\n')
        f.write(f'  "cols": {data["cols"]},\n')
        
        # Groups
        f.write('  "groups": [\n')
        for i, g in enumerate(data["groups"]):
            comma = "," if i < len(data["groups"]) - 1 else ""
            f.write(f'    {json.dumps(g)}{comma}\n')
        f.write('  ],\n')
        
        # Layout - each row on one line
        f.write('  "layout": [\n')
        for i, row in enumerate(data["layout"]):
            comma = "," if i < len(data["layout"]) - 1 else ""
            f.write(f'    {json.dumps(row)}{comma}\n')
        f.write('  ],\n')
        
        # Puzzle - each row on one line
        f.write('  "puzzle": [\n')
        for i, row in enumerate(data["puzzle"]):
            comma = "," if i < len(data["puzzle"]) - 1 else ""
            f.write(f'    {json.dumps(row)}{comma}\n')
        f.write('  ],\n')
        
        # Solution - each row on one line
        f.write('  "solution": ')
        if data["solution"] is None:
            f.write('null\n')
        else:
            f.write('[\n')
            for i, row in enumerate(data["solution"]):
                comma = "," if i < len(data["solution"]) - 1 else ""
                f.write(f'    {json.dumps(row)}{comma}\n')
            f.write('  ]\n')
        
        f.write("}\n")

def load_puzzle(filepath):
    """Load a puzzle from JSON file.
    
    Args:
        filepath: path to JSON file
    Returns:
        Grid object with puzzle loaded
    """
    # Step 1: Read the JSON file
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Step 2: Create empty grid
    grid = Grid(data["rows"], data["cols"])
    
    # Step 3: Build cells from layout
    grid.build_cells(data["layout"])
    
    # Step 4: Set the puzzle values
    for r in range(grid.rows):
        for c in range(grid.cols):
            grid.cells[r][c].value = data["puzzle"][r][c]
    
    # Step 5: Optionally store the solution
    if data["solution"] is not None:
        solution = Grid(data["rows"], data["cols"])
        solution.build_cells(data["layout"])
        for r in range(solution.rows):
            for c in range(solution.cols):
                solution.cells[r][c].value = data["solution"][r][c]
        grid.solution = solution
    
    return grid