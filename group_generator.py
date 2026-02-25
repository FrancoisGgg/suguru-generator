import random


class GroupGenerator:
    """Generates random irregular connected regions that tile the grid.

    The output is a 2D array of group IDs. Every cell gets exactly
    one group ID, groups are contiguous, and sizes stay within bounds.
    
    Algorithm: starts with every cell as its own group, then
    randomly merges adjacent groups respecting size constraints.
    """

    def __init__(self, min_size=2, max_size=5):
        """Create a GroupGenerator with size constraints.

        Args:
            min_size: minimum number of cells per group
            max_size: maximum number of cells per group
        """
        self.min_size = min_size
        self.max_size = max_size

    def generate(self, rows, cols):
        """Generate a valid group layout for a grid of given dimensions.

        Algorithm:
            1. Start with each cell as its own group (unique ID)
            2. Build list of all adjacent orthogonal cell pairs
            3. Shuffle the pair list for randomness
            4. For each pair: merge their groups if merged size <= max
            5. Repeat pass to merge any group still below min size
            6. Return the 2D group ID layout

        Args:
            rows: number of rows
            cols: number of columns
            target_sizes: optional list of desired group sizes.
                If None, aims for groups of size 3-5.
        Returns:
            2D list of group IDs, same shape as the grid, or None if failed
        """
        # print(f"Generating group layout for {rows}x{cols}...")
        
        layout = []
        for r in range(rows):
            row = []
            for c in range(cols):
                group_id = r * cols + c  # unique ID per cell
                row.append(group_id)
            layout.append(row)
        
        pairs = []
        for r in range(rows):
            for c in range(cols - 1):
                pairs.append(((r, c), (r, c + 1)))
        for r in range(rows - 1):
            for c in range(cols):
                pairs.append(((r, c), (r + 1, c)))
        
        random.shuffle(pairs)

        # First we need to track group sizes
        group_sizes = {}
        for r in range(rows):
            for c in range(cols):
                gid = layout[r][c]
                group_sizes[gid] = group_sizes.get(gid, 0) + 1
        
        # Now process pairs
        for (cell_a, cell_b) in pairs:
            r1, c1 = cell_a
            r2, c2 = cell_b
            
            group_a = layout[r1][c1]
            group_b = layout[r2][c2]
            
            if group_a == group_b:
                continue  # already same group
            
            merged_size = group_sizes[group_a] + group_sizes[group_b]
            
            if merged_size <= self.max_size:
                # merge smaller group into larger (or arbitrary if same size)
                if group_sizes[group_a] < group_sizes[group_b]:
                    group_a, group_b = group_b, group_a  # swap so we merge b into a
                
                self._merge_groups(layout, group_a, group_b)
                group_sizes[group_a] += group_sizes[group_b]
                group_sizes[group_b] = 0  # group_b no longer exists

        # Find all groups still below min_size
        MAX_ITERATIONS = rows * cols

        iterations = 0
        while True:
            small_groups = [gid for gid, size in group_sizes.items() 
                            if size > 0 and size < self.min_size]
            
            if not small_groups:
                break  # success
            
            iterations += 1
            if iterations > MAX_ITERATIONS:
                # Generation failed, return None to signal caller to retry
                return None
            
            for small_gid in small_groups:
                neighbors = self._get_adjacent_groups(small_gid, layout, rows, cols)
                
                if not neighbors:
                    continue
                
                smallest_neighbor = min(neighbors, key=lambda gid: group_sizes[gid])
                self._merge_groups(layout, smallest_neighbor, small_gid)
                group_sizes[smallest_neighbor] += group_sizes[small_gid]
                group_sizes[small_gid] = 0

        return layout

    def _merge_groups(self, layout, group_a, group_b):
        """Merge group_b into group_a in the layout.

        Replaces all occurrences of group_b ID with group_a ID
        in the 2D layout array.

        Args:
            layout: 2D list of group IDs (mutated in place)
            group_a: the group ID to merge into (survives)
            group_b: the group ID to merge from (disappears)
        """
        for row in range(len(layout)):
            for col in range(len(layout[0])):
                if layout[row][col] == group_b:
                    layout[row][col] = group_a

    def _is_connected(self, cells):
        """Return True if all cells form a connected region.

        Uses BFS over orthogonal neighbors only — diagonal
        connections do not count for group connectivity.

        Args:
            cells: list of (row, col) tuples
        Returns:
            True if all cells are reachable from the first cell
        """
        if not cells:
            return True
        
        cells_set = set(cells)
        visited = set()
        queue = [cells[0]]
        
        while queue:
            current = queue.pop(0)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            row, col = current
            # check all 4 orthogonal directions
            neighbors = [
                (row - 1, col),  # up
                (row + 1, col),  # down
                (row, col - 1),  # left
                (row, col + 1),  # right
            ]
            
            for neighbor in neighbors:
                if neighbor in cells_set and neighbor not in visited:
                    queue.append(neighbor)
        
        return len(visited) == len(cells)

    def _get_adjacent_groups(self, group_id, layout, rows, cols):
        """Return IDs of all groups that share an edge with this group.

        Scans all cells belonging to group_id, checks their
        orthogonal neighbors, collects any different group IDs found.

        Args:
            group_id: the group whose neighbors we want
            layout: current 2D group ID array
            rows, cols: grid dimensions for bounds checking
        Returns:
            set of group ID integers (excludes group_id itself)
        """
        groups = set()

        for row in range(len(layout)):
            for col in range(len(layout[0])):
                if layout[row][col] == group_id:
                    
                    neighbors = [
                        (row - 1, col),  # up
                        (row + 1, col),  # down
                        (row, col - 1),  # left
                        (row, col + 1),  # right
                    ]
                    
                    for (x, y) in neighbors:
                        # bounds check
                        if 0 <= x < len(layout) and 0 <= y < len(layout[0]):
                            if layout[x][y] != group_id:
                                groups.add(layout[x][y])

        return groups