import pygame
import math

class Grid:
    def __init__(self, pixel_width, pixel_height, cell_size):
        
        # Initialize cells
        self.cell_size = cell_size
        self.cols = pixel_width // cell_size
        self.rows = pixel_height // cell_size

        # Core arrays
        self.pheromone_to_food = [[0.0] * self.cols for _ in range(self.rows)]
        self.pheromone_to_nest = [[0.0] * self.cols for _ in range(self.rows)]
        self.heuristic_to_food = [[0.0] * self.cols for _ in range(self.rows)]
        self.heuristic_to_nest = [[0.0] * self.cols for _ in range(self.rows)]
        self.foods = [[None] * self.cols for _ in range(self.rows)]
        self.obstacles = [[False] * self.cols for _ in range(self.rows)]

        self.nest_position = None
        self.food_clusters = []

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
    
    # NEST
    def set_nest_position(self, nest_col, nest_row):
        """Set nest position and update nest heuristic."""
        self.nest_position = (nest_col, nest_row)
        self.update_heuristic_to_nest()
        print(f"Grid: Nest position set to ({nest_col}, {nest_row})")
    
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

    def add_food_cluster(self, food_cluster_object):
        """Add a FoodCluster object to the grid."""
        self.food_clusters.append(food_cluster_object)
        
        # Update food heuristic
        self.update_heuristic_to_food()
        
        print(f"Grid: Added food cluster at ({food_cluster_object.grid_x}, {food_cluster_object.grid_y}) "
            f"radius={food_cluster_object.radius}, food={food_cluster_object.total_food}")
        return len(self.food_clusters) - 1  # Return cluster index

    def update_food_in_cluster(self, cluster_index, delta_food):
        """Update food amount in a specific cluster."""
        if 0 <= cluster_index < len(self.food_clusters):
            cluster = self.food_clusters[cluster_index]
            cluster.total_food = max(0, cluster.total_food + delta_food)
            
            # Update heuristic if significant change
            if abs(delta_food) / (cluster.total_food + 1) > 0.2:
                self.update_heuristic_to_food()

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

    # Heuristic Methods - updated for dual heuristics
    def get_heuristic_to_food(self, grid_col, grid_row):
        """Get food heuristic value at grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            return self.heuristic_to_food[grid_row][grid_col]
        return 0.0
    
    def get_heuristic_to_nest(self, grid_col, grid_row):
        """Get nest heuristic value at grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            return self.heuristic_to_nest[grid_row][grid_col]
        return 0.0
    
    def set_heuristic_to_food(self, grid_col, grid_row, value):
        """Set food heuristic value at grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            self.heuristic_to_food[grid_row][grid_col] = value
            return True
        return False
    
    def set_heuristic_to_nest(self, grid_col, grid_row, value):
        """Set nest heuristic value at grid coordinates."""
        if self._in_bounds(grid_col, grid_row):
            self.heuristic_to_nest[grid_row][grid_col] = value
            return True
        return False
    
    def get_heuristic(self, grid_col, grid_row, has_food=False):
        """Get appropriate heuristic based on ant state (backward compatible)."""
        if has_food:
            return self.get_heuristic_to_nest(grid_col, grid_row)
        else:
            return self.get_heuristic_to_food(grid_col, grid_row)
        
    # HEURISTIC UPDATE METHODS - UPDATED
    def update_heuristic_to_food(self, gradient_softness=0.1):
        """
        Update food heuristic grid based on all food clusters.
        Uses sum of attractions from all food sources.
        """
        # Clear the heuristic grid
        for row in range(self.rows):
            for col in range(self.cols):
                self.heuristic_to_food[row][col] = 0.0
        
        # If no food clusters, return
        if not self.food_clusters:
            return
        
        # Calculate attraction from each cluster
        for row in range(self.rows):
            for col in range(self.cols):
                if self.obstacles[row][col]:
                    continue
                
                total_attraction = 0.0
                for cluster in self.food_clusters:  # Now cluster is an object
                    # Skip empty clusters
                    if cluster.total_food <= 0:
                        continue
                    
                    # Calculate Euclidean distance to cluster center
                    dx = col - cluster.grid_x
                    dy = row - cluster.grid_y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    # Only consider clusters within influence range (3x radius)
                    influence_radius = cluster.radius * 3
                    if distance <= influence_radius:
                        # Calculate attraction: cluster density / (1 + distance * gradient_softness)
                        cluster_density = cluster.total_food / (cluster.radius * cluster.radius)
                        attraction = cluster_density / (1.0 + distance * gradient_softness)
                        total_attraction += attraction
                
                self.heuristic_to_food[row][col] = total_attraction

    
    def update_heuristic_to_nest(self, target_col=None, target_row=None, gradient_softness=0.25):
        """
        Update nest heuristic grid based on nest position.
        If target is provided, use it; otherwise use self.nest_position.
        """
        # Use provided target or stored nest position
        if target_col is None or target_row is None:
            if self.nest_position is None:
                return  # No nest position set
            target_col, target_row = self.nest_position
        
        for row in range(self.rows):
            for col in range(self.cols):
                if self.obstacles[row][col]:
                    self.heuristic_to_nest[row][col] = 0.0
                    continue
                
                # Calculate diagonal-aware distance (same as original method)
                dx = abs(col - target_col)
                dy = abs(row - target_row)
                
                # For 8-direction movement with diagonals:
                # Distance = min(dx, dy)*√2 + |dx - dy|
                diagonal_moves = min(dx, dy)
                straight_moves = abs(dx - dy)
                distance = (diagonal_moves * 1.414) + straight_moves
                
                # ACO heuristic: η = 1/(1+distance*gradient_softness)
                self.heuristic_to_nest[row][col] = 1.0 / (1.0 + distance * gradient_softness)


    # Utility Method (Private)
    def _in_bounds(self, grid_col, grid_row):
        """Check if grid coordinates are within bounds."""
        return (0 <= grid_row < self.rows and 0 <= grid_col < self.cols)

    
