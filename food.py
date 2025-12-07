# FOOD SOURCE
import random
import math
import pygame

class FoodCluster:
    def __init__(self, grid, grid_x, grid_y, radius, density, food_per_cell=1):
        self.grid = grid
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.radius = radius
        self.density = density
        self.food_per_cell = food_per_cell
        
        # Generate foods and add to grid
        self.food_cells = self.generate_foods()
        self.total_food = len(self.food_cells) * self.food_per_cell
        
        # Register with grid (grid stores the object)
        self.cluster_index = self.grid.add_food_cluster(self)  # Pass self, not tuple
    
    def generate_foods(self):
        """
        Generates food in a circular area around center.
        Returns list of (col, row) positions.
        """
        food_cells = []
        
        # Calculate bounding box
        min_col = max(0, self.grid_x - self.radius)
        max_col = min(self.grid.cols - 1, self.grid_x + self.radius)
        min_row = max(0, self.grid_y - self.radius)
        max_row = min(self.grid.rows - 1, self.grid_y + self.radius)
        
        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                # Check if within circle radius
                dx = col - self.grid_x
                dy = row - self.grid_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= self.radius:
                    # Apply density probability
                    if random.random() <= self.density:
                        # Check if cell is not an obstacle
                        if not self.grid.is_obstacle(col, row):
                            # Place food in grid
                            food_obj = Food(col, row, self.food_per_cell)
                            self.grid.set_food(col, row, food_obj)
                            food_cells.append((col, row))
        
        return food_cells
    
    def take_food(self, col, row):
        """
        Try to take food from a specific cell.
        Returns amount taken (0 if no food or already empty).
        """
        food_obj = self.grid.get_food(col, row)
        if food_obj and food_obj.amount > 0:
            amount_taken = food_obj.take(1)  # Take 1 unit
            if amount_taken > 0:
                # Update grid's cluster total
                self.grid.update_food_in_cluster(self.cluster_index, -1)
                self.total_food -= 1
                
                # Remove food from grid if empty
                if food_obj.amount <= 0:
                    self.grid.remove_food(col, row)
                    
                return amount_taken
        return 0
    
    def is_empty(self):
        """Check if cluster has no food left."""
        return self.total_food <= 0
    
    def get_remaining_food(self):
        """Get amount of food left in cluster."""
        return self.total_food
    
    def draw(self, surface, cell_size):
        """Draw the food cluster."""
        center_x, center_y = self.grid.grid_to_world_center(self.grid_x, self.grid_y)
        
        # Draw cluster radius outline
        pygame.draw.circle(surface, (100, 200, 100), 
                          (int(center_x), int(center_y)), 
                          int(self.radius * cell_size), 
                          2)
        
        # Draw food cells
        for col, row in self.food_cells:
            food_obj = self.grid.get_food(col, row)
            if food_obj and food_obj.amount > 0:
                x, y = self.grid.grid_to_world(col, row)
                # Draw as small rectangle in cell
                food_size = cell_size // 2
                food_x = x + (cell_size - food_size) // 2
                food_y = y + (cell_size - food_size) // 2
                pygame.draw.rect(surface, (0, 180, 0),
                                (food_x, food_y, food_size, food_size))
        
        # Draw cluster info
        font = pygame.font.Font(None, 20)
        text = font.render(f"Food: {self.total_food}", True, (0, 0, 0))
        surface.blit(text, (int(center_x) - 20, int(center_y) - 30))


# Simple Food class
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