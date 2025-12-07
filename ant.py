import random
import math
import pygame
from config import Config

class Ant:
    def __init__(self, grid, start_col=None, start_row=None):
        """
        Initialize an ant at a specific grid position.
        If no position given, places ant at a random valid cell.
        """
        self.grid = grid
        self.has_food = False
        
        # ACO parameters
        self.alpha = 1.0  # Pheromone importance (0 for heuristic-only)
        self.beta = 2.0   # Heuristic importance
        
        # Direction persistence for smoother movement
        self.heading = None  # (dx, dy) - will be initialized on first move
        
        # Track movement
        self.steps_taken = 0
        self.path = []
        
        # Set starting position
        if start_col is not None and start_row is not None:
            self.col = start_col
            self.row = start_row
        else:
            # Find a random non-obstacle starting position
            self.col, self.row = self._find_random_start()
        
        # Initialize tracking
        self.path.append((self.col, self.row))
    
    def _find_random_start(self):
        """Find a random cell that's not an obstacle."""
        while True:
            col = random.randint(0, self.grid.cols - 1)
            row = random.randint(0, self.grid.rows - 1)
            if not self.grid.is_obstacle(col, row):
                return col, row
    
    def _initialize_heading(self):
        """Set random initial heading if not set."""
        if self.heading is None:
            # Choose random direction from 8 possibilities
            directions = [(-1, -1), (0, -1), (1, -1),
                         (-1,  0),          (1,  0),
                         (-1,  1), (0,  1), (1,  1)]
            self.heading = random.choice(directions)
    
    def _get_valid_neighbors(self):
        """Get all valid neighboring cells."""
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
                    not self.grid.is_obstacle(nc, nr)):
                    neighbors.append((nc, nr))
        return neighbors
    
    def move_with_heuristic(self, explore_chance=0.1):
        """
        Simple heuristic movement: probability ∝ (heuristic^β)
        With small chance to explore randomly.
        """
        # 10% chance to explore randomly
        if random.random() < explore_chance:
            return self.move_random()
        
        # Get valid neighbors
        neighbors = self._get_valid_neighbors()
        
        if not neighbors:
            return False  # Stuck
        
        # Calculate heuristic-based probabilities
        probabilities = []
        
        for nc, nr in neighbors:
            # Get food heuristic value at neighbor
            heuristic = self.grid.get_heuristic_to_food(nc, nr)
            
            # Probability ∝ heuristic^β (β=2.0 from Config)
            probability = heuristic ** self.beta
            
            # Ensure minimum probability
            probabilities.append(max(0.001, probability))
        
        # Normalize probabilities
        total = sum(probabilities)
        if total <= 0:
            # Fallback to random
            self.col, self.row = random.choice(neighbors)
        else:
            # Probabilistic selection
            normalized = [p/total for p in probabilities]
            chosen_idx = random.choices(range(len(neighbors)), weights=normalized, k=1)[0]
            self.col, self.row = neighbors[chosen_idx]
        
        # Update tracking
        self.steps_taken += 1
        self.path.append((self.col, self.row))
        
        return True
    
    def move_random(self):
        """
        Move to a random neighboring cell (8 directions).
        Returns True if moved, False if stuck.
        """
        # Get all possible neighbors
        neighbors = self._get_valid_neighbors()
        
        # If we have valid neighbors, pick one randomly
        if neighbors:
            self.col, self.row = random.choice(neighbors)
            self.steps_taken += 1
            self.path.append((self.col, self.row))
            return True
        return False  # Stuck (no valid moves)
    
    def move_aco(self):
        """
        Full ACO movement with pheromones AND heuristics.
        Will implement after pheromone system is ready.
        """
        # For now, use heuristic-only movement
        return self.move_with_heuristic()
    
    def get_current_heuristic(self):
        """Get current food heuristic value."""
        return self.grid.get_heuristic_to_food(self.col, self.row)
    
    def get_debug_info(self):
        """Get debug information."""
        return {
            'position': (self.col, self.row),
            'steps': self.steps_taken,
            'heuristic': self.get_current_heuristic(),
            'at_food': self.get_current_heuristic() > 2.0
        }
    
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