import pygame
import math

from config import Config

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
        self.nest_cells = []

        self.food_clusters = []
        self.food_dropped = 0
        self.food_dropped_this_frame = 0

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
        
        # Calculate which cells are in nest radius
        self._update_nest_cells()
        
        # Set max pheromone in nest area
        self._set_nest_pheromones()
        
        # Update nest heuristic
        self.update_heuristic_to_nest()
        
        print(f"Grid: Nest position set to ({nest_col}, {nest_row})")
        print(f"Grid: {len(self.nest_cells)} cells in nest radius")
    
    def _update_nest_cells(self):
        """Calculate which cells are within nest radius."""
        if self.nest_position is None:
            self.nest_cells = []
            return
            
        nest_col, nest_row = self.nest_position
        self.nest_cells = []
        
        # Calculate bounding box for efficiency
        min_col = max(0, nest_col - Config.NEST_PHEROMONE_RADIUS)
        max_col = min(self.cols - 1, nest_col + Config.NEST_PHEROMONE_RADIUS)
        min_row = max(0, nest_row - Config.NEST_PHEROMONE_RADIUS)
        max_row = min(self.rows - 1, nest_row + Config.NEST_PHEROMONE_RADIUS)
        
        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                # Calculate distance from nest center
                dx = col - nest_col
                dy = row - nest_row
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= Config.NEST_PHEROMONE_RADIUS:
                    self.nest_cells.append((col, row))
    
    def _set_nest_pheromones(self):
        """Set maximum pheromone values in nest area."""
        if not self.nest_cells:
            return
            
        for col, row in self.nest_cells:
            # Set both types of pheromones to maximum at nest
            self.pheromone_to_food[row][col] = Config.NEST_PHEROMONE_STRENGTH
            self.pheromone_to_nest[row][col] = Config.NEST_PHEROMONE_STRENGTH
    
    def _is_in_nest_radius(self, col, row):
        """Check if a cell is within nest pheromone radius."""
        if self.nest_position is None:
            return False
            
        nest_col, nest_row = self.nest_position
        dx = col - nest_col
        dy = row - nest_row
        distance = math.sqrt(dx*dx + dy*dy)
        
        return distance <= Config.NEST_PHEROMONE_RADIUS
    
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
    
    def evaporate_pheromones(self):
        """Apply evaporation to both pheromone grids."""
        for row in range(self.rows):
            for col in range(self.cols):
                # Evaporate food pheromones
                self.pheromone_to_food[row][col] *= (1 - Config.EVAPORATION_RATE)
                # Evaporate nest pheromones (could use different rate if desired)
                self.pheromone_to_nest[row][col] *= (1 - Config.EVAPORATION_RATE)
                
                # Cap at maximum and floor at minimum
                self.pheromone_to_food[row][col] = min(
                    self.pheromone_to_food[row][col], 
                    Config.PHEROMONE_MAX_STRENGTH
                )
                self.pheromone_to_nest[row][col] = min(
                    self.pheromone_to_nest[row][col], 
                    Config.PHEROMONE_MAX_STRENGTH
                )
                
                # Floor very low values to 0
                if self.pheromone_to_food[row][col] < 0.01:
                    self.pheromone_to_food[row][col] = 0
                if self.pheromone_to_nest[row][col] < 0.01:
                    self.pheromone_to_nest[row][col] = 0
    
    def diffuse_pheromones(self):
        """
        Diffuse pheromones with distance-based weights.
        Closer neighbors get more pheromone than diagonals.
        """
        if Config.DIFFUSION_RATE <= 0:
            return
        
        # Weight matrix: orthogonal neighbors get more than diagonals
        # Orthogonal: weight 2, Diagonal: weight 1
        WEIGHT_MATRIX = {
            (-1, -1): 2, (0, -1): 1, (1, -1): 2,
            (-1,  0): 1,             (1,  0): 1,
            (-1,  1): 2, (0,  1): 1, (1,  1): 2
        }
        
        total_weight = sum(WEIGHT_MATRIX.values())
        
        new_food = [[0.0] * self.cols for _ in range(self.rows)]
        new_nest = [[0.0] * self.cols for _ in range(self.rows)]
        
        for row in range(self.rows):
            for col in range(self.cols):
                if self.obstacles[row][col]:
                    continue
                
                current_food = self.pheromone_to_food[row][col]
                current_nest = self.pheromone_to_nest[row][col]
                
                # Keep some in current cell
                keep = 1 - Config.DIFFUSION_RATE
                new_food[row][col] += current_food * keep
                new_nest[row][col] += current_nest * keep
                
                # Distribute to neighbors by weight
                for (dc, dr), weight in WEIGHT_MATRIX.items():
                    nc = col + dc
                    nr = row + dr
                    
                    if (0 <= nr < self.rows and 0 <= nc < self.cols and 
                        not self.obstacles[nr][nc]):
                        
                        # Calculate amount for this neighbor
                        amount_food = current_food * Config.DIFFUSION_RATE * (weight / total_weight)
                        amount_nest = current_nest * Config.DIFFUSION_RATE * (weight / total_weight)
                        
                        new_food[nr][nc] += amount_food
                        new_nest[nr][nc] += amount_nest
        
        self.pheromone_to_food = new_food
        self.pheromone_to_nest = new_nest

    def _update_pheromones(self, should_evaporate=True, should_diffuse=True):
        """
        Update all pheromone operations in one place.
        
        Args:
            should_evaporate: If True, apply evaporation
            should_diffuse: If True, apply diffusion
        """
        # Apply evaporation if needed
        if should_evaporate:
            self._evaporate_pheromones()  # Rename the old method
        
        # Apply diffusion if needed
        if should_diffuse and Config.DIFFUSION_RATE > 0:
            self._diffuse_pheromones()  # Rename the old method
        
        # Always reset nest pheromones to maximum
        self._set_nest_pheromones()

    
    def draw_pheromones(self, surface):
        """
        Draw both pheromone fields onto the given surface.
        Called from main simulation loop.
        """
        if not Config.SHOW_PHEROMONES:
            return
            
        # Create temporary surfaces for alpha blending
        food_surface = pygame.Surface((self.cols * self.cell_size, 
                                       self.rows * self.cell_size), 
                                      pygame.SRCALPHA)
        nest_surface = pygame.Surface((self.cols * self.cell_size, 
                                       self.rows * self.cell_size), 
                                      pygame.SRCALPHA)
        
        # Draw food pheromones (red) - scale to cell size
        for row in range(self.rows):
            for col in range(self.cols):
                strength = self.pheromone_to_food[row][col]
                if strength > 0:
                    # Normalize to 0-200 alpha (keeps it semi-transparent)
                    alpha = min(int(strength / Config.PHEROMONE_MAX_STRENGTH * 200), 200)
                    color = (*Config.TO_FOOD_PHEROMONE_COLOR, alpha)
                    
                    # Calculate pixel position
                    x = col * self.cell_size
                    y = row * self.cell_size
                    
                    # Draw filled cell
                    cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    pygame.draw.rect(food_surface, color, cell_rect)
        
        # Draw nest pheromones (blue) - scale to cell size  
        for row in range(self.rows):
            for col in range(self.cols):
                strength = self.pheromone_to_nest[row][col]
                if strength > 0:
                    # Normalize to 0-200 alpha
                    alpha = min(int(strength / Config.PHEROMONE_MAX_STRENGTH * 200), 200)
                    color = (*Config.TO_NEST_PHEROMONE_COLOR, alpha)
                    
                    # Calculate pixel position
                    x = col * self.cell_size
                    y = row * self.cell_size
                    
                    # Draw filled cell
                    cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    pygame.draw.rect(nest_surface, color, cell_rect)
        
        # Blend onto main surface (food under nest for visual clarity)
        surface.blit(food_surface, (0, 0))
        surface.blit(nest_surface, (0, 0))

    # Food Methods

    def add_food_cluster(self, food_cluster_object):
        """Add a FoodCluster object to the grid."""
        self.food_clusters.append(food_cluster_object)
        
        # Update food heuristic
        self.update_heuristic_to_food()
        
        print(f"Grid: Added food cluster at ({food_cluster_object.grid_x}, {food_cluster_object.grid_y}) "
            f"radius={food_cluster_object.radius}, food={food_cluster_object.total_food}")
        return len(self.food_clusters) - 1  # Return cluster index
    
    def update_food_clusters(self):
        """Updates food clusters - removes empty clusters and updates heuristics."""
        clusters_to_remove = []
        
        # Find empty clusters
        for cluster in self.food_clusters:
            if not cluster.food_cells:  # checks if empty
                clusters_to_remove.append(cluster)
                print(f"✓ Removing empty food cluster at ({cluster.grid_x}, {cluster.grid_y})")
        
        # Remove empty clusters
        if clusters_to_remove:
            for cluster in clusters_to_remove:
                self.food_clusters.remove(cluster)
            
            # Update all remaining cluster indices
            for i, cluster in enumerate(self.food_clusters):
                cluster.cluster_index = i
            
            # Update heuristics AFTER removing clusters
            self.update_heuristic_to_food()
            print(f"✓ Updated food heuristics after removing {len(clusters_to_remove)} empty clusters")

    def update_food_in_cluster(self, cluster_index, delta_food):
        """Update food amount in a specific cluster."""
        if 0 <= cluster_index < len(self.food_clusters):
            cluster = self.food_clusters[cluster_index]
            cluster.total_food = max(0, cluster.total_food + delta_food)
            
            # Update heuristic if significant change
            '''if abs(delta_food) / (cluster.total_food + 1) > 0.2 or cluster.total_food <= 0:
                self.update_heuristic_to_food()'''


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
    
    def draw_obstacles(self, surface, obstacle_color=(80, 80, 80)):
        """
        Draw all obstacles on the grid.
        
        Args:
            surface: Pygame surface to draw on
            obstacle_color: RGB color for obstacles
        """
        for row in range(self.rows):
            for col in range(self.cols):
                if self.obstacles[row][col]:
                    # Get top-left corner of cell
                    x, y = self.grid_to_world(col, row)
                    
                    # Create rectangle for the cell
                    obstacle_rect = pygame.Rect(
                        int(x), 
                        int(y), 
                        self.cell_size, 
                        self.cell_size
                    )
                    
                    # Draw filled rectangle for obstacle
                    pygame.draw.rect(surface, obstacle_color, obstacle_rect)
                    
                    # Optional: Draw border around obstacle
                    '''pygame.draw.rect(surface, (50, 50, 50), obstacle_rect, 1)'''

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
    def update_heuristic_to_food(self, gradient_softness=0.5):
        """
        Use sigmoid function to keep values between 0 and 1.
        """

        # Clear the heuristic grid
        for r in range(self.rows):
            for c in range(self.cols):
                self.heuristic_to_food[r][c] = 0.0
        
        if not self.food_clusters:
            return
        
        for cluster in self.food_clusters:
            if len(cluster.food_cells) <= 0:
                continue
            
            food_cell_count = len(cluster.food_cells)
            influence_radius = cluster.radius * Config.FOOD_CLUSTER_INFLUENCE_RADIUS_MULT
            
            min_col = max(0, cluster.grid_x - influence_radius)
            max_col = min(self.cols - 1, cluster.grid_x + influence_radius)
            min_row = max(0, cluster.grid_y - influence_radius)
            max_row = min(self.rows - 1, cluster.grid_y + influence_radius)
            
            # FIXED: Use different variable names r2, c2 for inner loops
            for r2 in range(min_row, max_row + 1):
                for c2 in range(min_col, max_col + 1):
                    if self.obstacles[r2][c2]:
                        continue
                    
                    dx = c2 - cluster.grid_x
                    dy = r2 - cluster.grid_y    
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance <= influence_radius:
                        raw_attraction = food_cell_count / (1.0 + distance * gradient_softness)
                        # Sigmoid: 1 / (1 + exp(-x))
                        scaled = raw_attraction * 0.1
                        sigmoid_attraction = 1.0 / (1.0 + math.exp(-scaled))
                        self.heuristic_to_food[r2][c2] = max(
                            self.heuristic_to_food[r2][c2],
                            sigmoid_attraction
                        )


    def update_heuristic_to_nest(self, target_col=None, target_row=None, max_range=100):
        """
        Linear nest heuristic with maximum range.
        Simpler to debug and understand.
        """
        if target_col is None or target_row is None:
            if self.nest_position is None:
                return
            target_col, target_row = self.nest_position
        
        for r in range(self.rows):
            for c in range(self.cols):
                if self.obstacles[r][c]:
                    self.heuristic_to_nest[r][c] = 0.0
                    continue
                
                # Calculate diagonal-aware distance
                dx = abs(c - target_col)
                dy = abs(r - target_row)
                diagonal_moves = min(dx, dy)
                straight_moves = abs(dx - dy)
                distance = (diagonal_moves * 1.414) + straight_moves
                
                if distance <= max_range:
                    # Linear: 1.0 at nest, 0.0 at max_range
                    self.heuristic_to_nest[r][c] = 1.0 - (distance / max_range)
                else:
                    self.heuristic_to_nest[r][c] = 0.0


    # Utility Method (Private)
    def _in_bounds(self, grid_col, grid_row):
        """Check if grid coordinates are within bounds."""
        return (0 <= grid_row < self.rows and 0 <= grid_col < self.cols)

    
