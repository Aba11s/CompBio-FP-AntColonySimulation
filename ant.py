import random
import math
import pygame

class Ant:
    def __init__(self, grid, start_col=None, start_row=None):
        """
        Initialize an ant at a specific grid position.
        If no position given, places ant at a random valid cell.
        """
        self.grid = grid
        self.has_food = False
        
        # Set starting position
        if start_col is not None and start_row is not None:
            self.col = start_col
            self.row = start_row
        else:
            # Find a random non-obstacle starting position
            self.col, self.row = self._find_random_start()
    
    def _find_random_start(self):
        """Find a random cell that's not an obstacle."""
        while True:
            col = random.randint(0, self.grid.cols - 1)
            row = random.randint(0, self.grid.rows - 1)
            if not self.grid.obstacles[row][col]:
                return col, row
            
    def move_aco(self):
        """
        Probablistic Move based on
        """

    def move_with_heursitic(self):
        """
        Probablistic move with cell heuristics
        """
    
    def move_random(self):
        """
        Move to a random neighboring cell (8 directions).
        Returns True if moved, False if stuck.
        For testing only.
        """
        # Get all possible neighbors
        neighbors = []
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue  # Skip current position
                
                nc = self.col + dc
                nr = self.row + dr
                
                # Check bounds and obstacles
                if (0 <= nc < self.grid.cols and 
                    0 <= nr < self.grid.rows and 
                    not self.grid.obstacles[nr][nc]):
                    neighbors.append((nc, nr))
        
        # If we have valid neighbors, pick one randomly
        if neighbors:
            self.col, self.row = random.choice(neighbors)
            return True
        return False  # Stuck (no valid moves)
    
    def draw(self, surface, color=(0, 0, 0)):
        """Draw the ant as a filled grid cell."""
        # Get the top-left corner of the cell
        x, y = self.grid.grid_to_world(self.col, self.row)
        
        # Create a rectangle that fills the entire cell
        cell_rect = pygame.Rect(
            int(x), 
            int(y), 
            self.grid.cell_size, 
            self.grid.cell_size
        )
        
        # Draw the ant as a filled rectangle
        pygame.draw.rect(surface, color, cell_rect)