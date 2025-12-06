import pygame

class Grid:
    def __init__(self, pixel_width, pixel_height, cell_size):
        
        # Initialize cells
        self.cell_size = cell_size
        self.cols = pixel_width // cell_size
        self.rows = pixel_height // cell_size

        # Core arrays
        self.pheromone_to_food = [[0.0] * self.cols for _ in range(self.rows)]
        self.pheromone_to_nest = [[0.0] * self.cols for _ in range(self.rows)]
        self.foods = [[None] * self.cols for _ in range(self.rows)]
        self.obstacles = [[False] * self.cols for _ in range(self.rows)]
        self.heuristics = [[0.0] * self.cols for _ in range(self.rows)]

    # COORDINATE CONVERSION METHODS
    def world_to_grid(self, x, y):
        """Convert PIXEL coordinates to GRID coordinates."""
        return (int(x // self.cell_size), 
                int(y // self.cell_size))
    
    def grid_to_world_center(self, grid_col, grid_row):
        """Convert GRID coordinates to PIXEL coordinates of cell CENTER."""
        return ((grid_col * self.cell_size) + (self.cell_size // 2),
                (grid_row * self.cell_size) + (self.cell_size // 2))
    
    def grid_to_world(self, grid_col, grid_row):
        """Convert GRID coordinates to PIXEL coordinates of cell TOP-LEFT (for drawing)."""
        return (grid_col * self.cell_size,
                grid_row * self.cell_size)
    
    # NEIGHBOUR METHODS
    # All 8 neighbor offsets
    NEIGHBOR_OFFSETS = [(-1, -1), (0, -1), (1, -1),
                        (-1,  0),          (1,  0),
                        (-1,  1), (0,  1), (1,  1)]

    def get_neighbors_8(self, col, row):
        """Get coordinates of all 8 neighboring cells (diagonals included)."""
        neighbors = []
        for dc, dr in self.NEIGHBOR_OFFSETS:
            nc, nr = col + dc, row + dr
            if 0 <= nc < self.cols and 0 <= nr < self.rows:
                neighbors.append((nc, nr))
        return neighbors
    
    # INDIVIDUAL ACCESS METHODS
    
    # Pheromone Methods
    def get_pheromone_to_food(self, grid_col, grid_row):
        """Get food pheromone strength at grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            return self.pheromone_to_food[grid_row][grid_col]
        return 0.0
    
    def get_pheromone_to_nest(self, grid_col, grid_row):
        """Get nest pheromone strength at grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            return self.pheromone_to_nest[grid_row][grid_col]
        return 0.0
    
    def add_pheromone(self, grid_col, grid_row, p_type, strength):
        """Add pheromone to a specific cell."""
        if not self._in_bounds(grid_col, grid_row):
            return False
            
        if p_type == "to_food":
            self.pheromone_to_food[grid_row][grid_col] += strength
        elif p_type == "to_nest":
            self.pheromone_to_nest[grid_row][grid_col] += strength
        return True
    
    def set_pheromone(self, grid_col, grid_row, p_type, strength):
        """Set pheromone to a specific value."""
        if not self._in_bounds(grid_col, grid_row):
            return False
            
        if p_type == "to_food":
            self.pheromone_to_food[grid_row][grid_col] = strength
        elif p_type == "to_nest":
            self.pheromone_to_nest[grid_row][grid_col] = strength
        return True

    # Food Methods
    def get_food(self, grid_col, grid_row):
        """Get food object at grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            return self.foods[grid_row][grid_col]
        return None
    
    def set_food(self, grid_col, grid_row, food_object):
        """Place food object at grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            self.foods[grid_row][grid_col] = food_object
            return True
        return False
    
    def remove_food(self, grid_col, grid_row):
        """Remove food from grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            self.foods[grid_row][grid_col] = None
            return True
        return False
    
    def has_food(self, grid_col, grid_row):
        """Check if cell has food."""
        return self.get_food(grid_col, grid_row) is not None

    # Obstacle Methods
    def is_obstacle(self, grid_col, grid_row):
        """Check if cell is an obstacle."""
        if self._in_bounds(grid_col, grid_row):
            return self.obstacles[grid_row][grid_col]
        return True  # Treat out-of-bounds as obstacles
    
    def set_obstacle(self, grid_col, grid_row, is_obstacle=True):
        """Set or clear obstacle at grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            self.obstacles[grid_row][grid_col] = is_obstacle
            return True
        return False

    # Heuristic Methods
    def get_heuristic(self, grid_col, grid_row):
        """Get heuristic value at grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            return self.heuristics[grid_row][grid_col]
        return 0.0
    
    def set_heuristic(self, grid_col, grid_row, value):
        """Set heuristic value at grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            self.heuristics[grid_row][grid_col] = value
            return True
        return False
    
    
    # WORLD MAINTENANCE METHODS
    def update_heuristics(self, target_col, target_row):
        """
        Update heuristic values using Euclidean distance with diagonal cost.
        More accurate than pure Manhattan for 8-direction movement.
        """
        for row in range(self.rows):
            for col in range(self.cols):
                if self.obstacles[row][col]:
                    self.heuristics[row][col] = 0.0
                    continue
                
                # Calculate diagonal-aware distance
                dx = abs(col - target_col)
                dy = abs(row - target_row)
                
                # For 8-direction movement with diagonals:
                # Distance = min(dx, dy)*√2 + |dx - dy|
                diagonal_moves = min(dx, dy)
                straight_moves = abs(dx - dy)
                distance = (diagonal_moves * 1.414) + straight_moves
                
                # ACO heuristic: η = 1/(1+distance)
                self.heuristics[row][col] = 1.0 / (1.0 + distance)





    # Utility Method (Private)
    def _in_bounds(self, grid_col, grid_row):
        """Check if grid coordinates are within bounds."""
        return (0 <= grid_row < self.rows and 0 <= grid_col < self.cols)

    
