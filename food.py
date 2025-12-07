import random
import math
import pygame

class FoodCluster:
    def __init__(self, grid, grid_x, grid_y, radius, density, food_per_cell=1, 
                 influence_radius_multiplier=3.0, gaussian_std=None):
        """
        Initialize a food cluster with Gaussian distribution.
        
        Args:
            grid: Reference to the grid
            grid_x, grid_y: Center of the cluster
            radius: Maximum radius of the cluster
            density: Overall density of food (0-1)
            food_per_cell: Food amount per cell
            influence_radius_multiplier: For heuristic calculation
            gaussian_std: Standard deviation for Gaussian (None = radius/3)
        """
        self.grid = grid
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.radius = radius
        self.density = density
        self.food_per_cell = food_per_cell
        self.influence_radius_multiplier = influence_radius_multiplier
        self.gaussian_std = gaussian_std if gaussian_std is not None else radius / 3.0
        
        # Generate foods with Gaussian distribution
        self.food_cells = self.generate_foods_gaussian()
        self.total_food = len(self.food_cells) * self.food_per_cell
        
        # Register with grid
        self.cluster_index = self.grid.add_food_cluster(self)
    
    def gaussian_probability(self, distance):
        """
        Calculate Gaussian probability for a given distance from center.
        Returns probability between 0 and 1.
        """
        # Gaussian PDF: (1/(σ√(2π))) * exp(-(x²)/(2σ²))
        # We normalize so probability at center = 1
        exponent = -(distance * distance) / (2.0 * self.gaussian_std * self.gaussian_std)
        return math.exp(exponent)
    
    def generate_foods_gaussian(self):
        """
        Generate food in a circular area with Gaussian distribution.
        Ensures no overlapping food cells.
        """
        food_cells = []
        attempts = 0
        max_attempts = self.radius * self.radius * 100  # Reasonable limit
        
        # Calculate number of potential food cells based on area and density
        circle_area = math.pi * self.radius * self.radius
        target_food_cells = int(circle_area * self.density)
        
        # Generate candidate positions with Gaussian distribution
        candidates = []
        
        # Calculate bounding box
        min_col = max(0, self.grid_x - self.radius)
        max_col = min(self.grid.cols - 1, self.grid_x + self.radius)
        min_row = max(0, self.grid_y - self.radius)
        max_row = min(self.grid.rows - 1, self.grid_y + self.radius)
        
        # First pass: collect all possible positions with their probabilities
        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                dx = col - self.grid_x
                dy = row - self.grid_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= self.radius:
                    # Check if cell is not an obstacle
                    if not self.grid.is_obstacle(col, row):
                        # Calculate Gaussian probability
                        prob = self.gaussian_probability(distance)
                        # Adjust by overall density
                        adjusted_prob = prob * self.density
                        
                        if adjusted_prob > 0.001:  # Skip very low probabilities
                            candidates.append((col, row, adjusted_prob, distance))
        
        # Sort candidates by probability (highest first)
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        # Select food cells ensuring no overlap
        selected_positions = set()
        
        for col, row, prob, distance in candidates:
            if len(food_cells) >= target_food_cells:
                break
                
            attempts += 1
            if attempts > max_attempts:
                break
            
            # Skip if cell already has food (from another cluster or this one)
            if self.grid.has_food(col, row):
                continue
            
            # Check minimum distance from other food cells in this cluster
            too_close = False
            for fc_col, fc_row in selected_positions:
                dist_to_other = math.sqrt((col - fc_col)**2 + (row - fc_row)**2)
                if dist_to_other < 1.0:  # Minimum 1 cell apart (no direct neighbors)
                    too_close = True
                    break
            
            if too_close:
                continue
            
            # Probabilistic placement based on Gaussian probability
            if random.random() <= prob:
                # Place food
                food_obj = Food(col, row, self.food_per_cell)
                self.grid.set_food(col, row, food_obj)
                food_cells.append((col, row))
                selected_positions.add((col, row))
        
        return food_cells
    
    # Alternative: Spiral placement method for guaranteed non-overlap
    def generate_foods_spiral(self):
        """
        Generate food in a spiral pattern from center outward.
        Guarantees no overlap and follows Gaussian density.
        """
        food_cells = []
        selected_positions = set()
        
        # Create spiral coordinates
        spiral_coords = self.generate_spiral_coordinates()
        
        for col, row, distance in spiral_coords:
            if distance > self.radius:
                continue
            
            # Skip obstacles
            if self.grid.is_obstacle(col, row):
                continue
            
            # Skip if cell already has food
            if self.grid.has_food(col, row):
                continue
            
            # Check minimum distance from other selected cells
            too_close = False
            for fc_col, fc_row in selected_positions:
                dist_to_other = math.sqrt((col - fc_col)**2 + (row - fc_row)**2)
                if dist_to_other < 1.0:
                    too_close = True
                    break
            
            if too_close:
                continue
            
            # Gaussian probability
            prob = self.gaussian_probability(distance) * self.density
            
            if random.random() <= prob:
                food_obj = Food(col, row, self.food_per_cell)
                self.grid.set_food(col, row, food_obj)
                food_cells.append((col, row))
                selected_positions.add((col, row))
        
        return food_cells
    
    def generate_spiral_coordinates(self):
        """
        Generate coordinates in a spiral pattern starting from center.
        Returns list of (col, row, distance_from_center).
        """
        coords = []
        
        # Spiral algorithm
        x = y = 0
        dx = 0
        dy = -1
        
        # Calculate spiral size needed
        spiral_size = int(self.radius * 2 + 1)
        
        for i in range(spiral_size * spiral_size):
            # Check bounds
            if (abs(x) <= self.radius and abs(y) <= self.radius):
                col = self.grid_x + x
                row = self.grid_y + y
                
                if (0 <= col < self.grid.cols and 0 <= row < self.grid.rows):
                    distance = math.sqrt(x*x + y*y)
                    coords.append((col, row, distance))
            
            # Spiral logic
            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1-y):
                dx, dy = -dy, dx
            
            x += dx
            y += dy
        
        return coords
    
    def take_food(self, col, row):
        """Try to take food from a specific cell."""
        food_obj = self.grid.get_food(col, row)
        if food_obj and food_obj.amount > 0:
            amount_taken = food_obj.take(1)
            if amount_taken > 0:
                self.grid.update_food_in_cluster(self.cluster_index, -1)
                self.total_food -= 1
                
                if food_obj.amount <= 0:
                    self.grid.remove_food(col, row)
                    # Remove from our list if empty
                    if (col, row) in self.food_cells:
                        self.food_cells.remove((col, row))
                
                return amount_taken
        return 0
    
    def is_empty(self):
        return self.total_food <= 0
    
    def get_remaining_food(self):
        return self.total_food
    
    def draw(self, surface, cell_size):
        # Draw food cells
        for col, row in self.food_cells:
            food_obj = self.grid.get_food(col, row)
            if food_obj and food_obj.amount > 0:
                x, y = self.grid.grid_to_world(col, row)
                
                # Fixed size for all food
                food_size = cell_size // 2
                food_x = x + (cell_size - food_size) // 2
                food_y = y + (cell_size - food_size) // 2
                
                # Fixed color
                color = (0, 180, 0)
                
                pygame.draw.rect(surface, color,
                                (food_x, food_y, food_size, food_size))
        
        # Draw cluster info
        '''font = pygame.font.Font(None, 20)
        text = font.render(f"Food: {self.total_food}", True, (0, 0, 0))
        surface.blit(text, (int(center_x) - 20, int(center_y) - 30))'''
        
        # Draw Gaussian info
        '''info_text = font.render(f"σ: {self.gaussian_std:.1f}", True, (100, 100, 100))
        surface.blit(info_text, (int(center_x) - 15, int(center_y) - 50))'''


class Food:
    def __init__(self, col, row, amount):
        self.col = col
        self.row = row
        self.amount = amount
    
    def take(self, amount):
        """Take specified amount of food."""
        actual_taken = min(amount, self.amount)
        self.amount -= actual_taken
        return actual_taken