import matplotlib.pyplot as plt
import matplotlib.patches as patches


GROUP_COLORS = [
    "#63A8D6", "#6DDA98", "#F5D969", "#F1BC8C", "#D8A8EB",
    "#EB7B6E", "#7FE4CF", "#F5C373", "#7EF5F5", "#89F0F0",
    "#87C1EB", "#ACF8CD", "#F5DC81", "#F7928B", "#9CD6F8",
]

THIN_BORDER  = 0.5
THICK_BORDER = 3.0
CELL_SIZE    = 1.0


def _draw_static_grid(grid, ax, fig, title):
        """Draw a non-interactive grid (for showing solution)."""
        rows = grid.rows
        cols = grid.cols
        
        dpi = fig.dpi
        cell_pixels = CELL_SIZE * dpi
        fontsize = cell_pixels * 0.35
        
        ax.set_xlim(0, cols)
        ax.set_ylim(0, rows)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=16, pad=10)
        
        # Draw cells
        for r in range(rows):
            for c in range(cols):
                cell = grid.cells[r][c]
                color = GROUP_COLORS[cell.group_id % len(GROUP_COLORS)]
                
                rect = patches.Rectangle(
                    (c, rows - r - 1),
                    CELL_SIZE, CELL_SIZE,
                    linewidth=0,
                    facecolor=color
                )
                ax.add_patch(rect)
                
                value_text = str(cell.value) if cell.value is not None else ""
                ax.text(
                    c + CELL_SIZE / 2,
                    rows - r - 1 + CELL_SIZE / 2,
                    value_text,
                    ha="center", va="center",
                    fontsize=fontsize, fontweight="bold"
                )
        
        # Draw borders (same as before)
        for r in range(1, rows):
            for c in range(cols):
                above = grid.cells[r - 1][c].group_id
                below = grid.cells[r][c].group_id
                width = THICK_BORDER if above != below else THIN_BORDER
                y = rows - r
                ax.plot([c, c + 1], [y, y], color="black", linewidth=width)
        
        for r in range(rows):
            for c in range(1, cols):
                left  = grid.cells[r][c - 1].group_id
                right = grid.cells[r][c].group_id
                width = THICK_BORDER if left != right else THIN_BORDER
                y = rows - r - 1
                ax.plot([c, c], [y, y + 1], color="black", linewidth=width)
        
        outer = patches.Rectangle(
            (0, 0), cols, rows,
            linewidth=THICK_BORDER,
            edgecolor="black",
            facecolor="none"
        )
        ax.add_patch(outer)

def draw_grid(grid, solution=None):
    """Render the grid with interactive number input.
    
    Click a cell to select it, then press 1-9 to fill it.
    Press 0 or Delete to clear a cell.
    Press Escape to close.
    """
    rows = grid.rows
    cols = grid.cols
    
    if solution is not None:
        fig_sol, ax_sol = plt.subplots(figsize=(cols * CELL_SIZE + 1, rows * CELL_SIZE + 1))
        _draw_static_grid(solution, ax_sol, fig_sol, "Solution")

    selected_cell = [None]
    
    fig, ax = plt.subplots(figsize=(cols * CELL_SIZE + 1, rows * CELL_SIZE + 1))
    fig.canvas.manager.set_window_title("Puzzle (interactive)")
    
    dpi = fig.dpi
    cell_pixels = CELL_SIZE * dpi
    fontsize = cell_pixels * 0.35
    
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect("equal")
    ax.axis("off")
    
    def check_completion():
        """Check if puzzle is complete and valid."""

        is_complete = grid.is_complete()
        is_valid = grid.is_valid()
        # print(f"DEBUG: complete={is_complete}, valid={is_valid}")  # ← Add this
        if not grid.is_complete():
            return None
        
        if grid.is_valid():
            return "CORRECT! ✓"
        else:
            return "WRONG - conflicts exist ✗"
    
    def redraw():
        """Redraw the grid with current values."""
        ax.clear()
        ax.set_xlim(0, cols)
        ax.set_ylim(0, rows)
        ax.set_aspect("equal")
        ax.axis("off")
        
        # Check completion status - set on FIGURE not axes
        status = check_completion()
        if status:
            color = "green" if "CORRECT" in status else "red"
            fig.suptitle(status, fontsize=20, color=color, weight='bold')  # ← fig.suptitle
        else:
            fig.suptitle("")  # ← Clear title when not complete
        
        # Draw cells
        for r in range(rows):
            for c in range(cols):
                cell = grid.cells[r][c]
                color = GROUP_COLORS[cell.group_id % len(GROUP_COLORS)]
                
                rect = patches.Rectangle(
                    (c, rows - r - 1),
                    CELL_SIZE, CELL_SIZE,
                    linewidth=0,
                    facecolor=color
                )
                ax.add_patch(rect)
                
                value_text = str(cell.value) if cell.value is not None else ""
                ax.text(
                    c + CELL_SIZE / 2,
                    rows - r - 1 + CELL_SIZE / 2,
                    value_text,
                    ha="center", va="center",
                    fontsize=fontsize, fontweight="bold"
                )
        
        # Draw selected cell highlight
        if selected_cell[0] is not None:
            r, c = selected_cell[0]
            highlight = patches.Rectangle(
                (c, rows - r - 1),
                CELL_SIZE, CELL_SIZE,
                linewidth=3,
                edgecolor="red",
                facecolor="none"
            )
            ax.add_patch(highlight)
        
        # Draw borders
        for r in range(1, rows):
            for c in range(cols):
                above = grid.cells[r - 1][c].group_id
                below = grid.cells[r][c].group_id
                width = THICK_BORDER if above != below else THIN_BORDER
                y = rows - r
                ax.plot([c, c + 1], [y, y], color="black", linewidth=width)
        
        for r in range(rows):
            for c in range(1, cols):
                left  = grid.cells[r][c - 1].group_id
                right = grid.cells[r][c].group_id
                width = THICK_BORDER if left != right else THIN_BORDER
                y = rows - r - 1
                ax.plot([c, c], [y, y + 1], color="black", linewidth=width)
        
        outer = patches.Rectangle(
            (0, 0), cols, rows,
            linewidth=THICK_BORDER,
            edgecolor="black",
            facecolor="none"
        )
        ax.add_patch(outer)
        
        fig.canvas.draw()
    
    def on_click(event):
        """Handle mouse clicks to select cells."""
        if event.inaxes != ax:
            return
        
        col = int(event.xdata)
        row = rows - 1 - int(event.ydata)
        
        if 0 <= row < rows and 0 <= col < cols:
            selected_cell[0] = (row, col)
            redraw()
    
    def on_key(event):
        """Handle keyboard input to fill cells."""
        # Escape to close
        if event.key == 'escape':
            plt.close('all')
            return
        
        if selected_cell[0] is None:
            return
        
        r, c = selected_cell[0]
        cell = grid.cells[r][c]
        
        if event.key in '123456789':
            cell.value = int(event.key)
            redraw()
        elif event.key in ('0', 'delete', 'backspace'):
            cell.value = None
            redraw()
    
    fig.canvas.mpl_connect('button_press_event', on_click)
    fig.canvas.mpl_connect('key_press_event', on_key)
    
    redraw()
    
    plt.tight_layout()
    plt.show()