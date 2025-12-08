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
        self.distance_traveled = 0
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
        self._initialize_heading()  # Initialize heading immediately
    
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
                    neighbors.append((nc, nr, dc, dr))  # Include direction vectors
        return neighbors
    
    def _get_allowed_neighbors(self):
        """Return neighbors with their actual distances."""
        if self.heading is None:
            neighbors = self._get_valid_neighbors()
            return [(nc, nr, math.sqrt(dx*dx + dy*dy)) for nc, nr, dx, dy in neighbors]
        
        turning_patterns = {
            (-1, -1): [(-1, -1), (0, -1), (-1, 0)],
            (0, -1):  [(0, -1), (-1, -1), (1, -1)],
            (1, -1):  [(1, -1), (0, -1), (1, 0)],
            (-1, 0):  [(-1, 0), (-1, -1), (-1, 1)],
            (1, 0):   [(1, 0), (1, -1), (1, 1)],
            (-1, 1):  [(-1, 1), (0, 1), (-1, 0)],
            (0, 1):   [(0, 1), (-1, 1), (1, 1)],
            (1, 1):   [(1, 1), (0, 1), (1, 0)],
        }
        
        allowed_offsets = turning_patterns.get(self.heading, [])
        allowed_neighbors = []
        
        for nc, nr, dx, dy in self._get_valid_neighbors():
            if (dx, dy) in allowed_offsets:
                # Calculate actual Euclidean distance
                distance = math.sqrt(dx*dx + dy*dy)  # 1.0 or 1.414
                allowed_neighbors.append((nc, nr, distance))
        
        return allowed_neighbors
    
    def _update_heading_from_move(self):
        """Update heading based on the last movement."""
        if len(self.path) < 2:
            return
        
        prev_col, prev_row = self.path[-2]
        curr_col, curr_row = self.path[-1]
        
        # Calculate direction vector
        dx = curr_col - prev_col
        dy = curr_row - prev_row
        
        # Only update heading if we actually moved
        if dx != 0 or dy != 0:
            self.heading = (dx, dy)
    
    def move_random(self):
        """
        Random movement accounting for diagonal distances.
        LEGACY CODE, FOR TESTING ONLY
        """
        # Get neighbors with distances
        weighted_neighbors = self._get_allowed_neighbors()
        
        # If no moves within turning radius, expand search
        if not weighted_neighbors:
            all_neighbors = self._get_valid_neighbors()
            if not all_neighbors:
                return False  # Stuck - no valid moves at all
            
            # Convert all valid neighbors to weighted format
            weighted_neighbors = []
            for nc, nr, dx, dy in all_neighbors:
                distance = math.sqrt(dx*dx + dy*dy)
                weighted_neighbors.append((nc, nr, distance))
        
        # Create weights inversely proportional to distance
        positions = []
        weights = []
        distances = []
        
        for nc, nr, distance in weighted_neighbors:
            positions.append((nc, nr))
            distances.append(distance)
            # Prefer straight moves (lower distance)
            weights.append(1.0 / distance)
        
        # Choose with probability proportional to inverse distance
        total_weight = sum(weights)
        normalized = [w/total_weight for w in weights]
        chosen_idx = random.choices(range(len(positions)), weights=normalized, k=1)[0]
        
        old_col, old_row = self.col, self.row
        self.col, self.row = positions[chosen_idx]
        distance = distances[chosen_idx]
        
        # Track actual distance, not just steps
        self.distance_traveled += distance
        self.steps_taken += 1
        self.path.append((self.col, self.row))
        self._update_heading_from_move()
        
        return True
 
    def move_with_heuristic(self, explore_chance=0.1, temperature=0.02):
        """Minimal heuristic movement with food pickup/dropoff."""
        
        #print(self.has_food)
        # FIRST: Drop food if at nest
        if self.has_food:
            self._drop_food()
        
        # SECOND: Pick up food if available (only if not carrying)
        if not self.has_food:
            self._pickup_food()
        
        # THIRD: Move based on current state
        if random.random() < explore_chance:
            return self.move_random()
        
        # Get valid moves
        moves = self._get_allowed_neighbors()
        if not moves:
            moves = [(nc, nr, math.sqrt(dx*dx + dy*dy)) 
                    for nc, nr, dx, dy in self._get_valid_neighbors()]
        
        if not moves:
            return False
        
        # Choose heuristic based on food state
        if self.has_food:
            # Follow nest heuristic back to nest
            probs = []
            for col, row, dist in moves:
                h = self.grid.get_heuristic_to_nest(col, row)  # NEST heuristic!
                probs.append(math.exp(h / temperature) / max(dist, 0.001))
        else:
            # Follow food heuristic to find food
            probs = []
            for col, row, dist in moves:
                h = self.grid.get_heuristic_to_food(col, row)  # FOOD heuristic!
                probs.append(math.exp(h / temperature) / max(dist, 0.001))
        
        # Choose and move (same as before)
        idx = random.choices(range(len(moves)), weights=probs, k=1)[0]
        col, row, dist = moves[idx]
        
        # Update position
        self.col, self.row = col, row
        self.distance_traveled += dist
        self.steps_taken += 1
        self.path.append((col, row))
        
        # Update heading
        if len(self.path) >= 2:
            prev = self.path[-2]
            dx, dy = col - prev[0], row - prev[1]
            if dx or dy:
                self.heading = (dx, dy)
        
        return True

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
            'at_food': self.get_current_heuristic() > 2.0,
            'heading': self.heading
        }
    
    def _pickup_food(self):
        """Try to pick up food from current cell."""
        if not self.has_food and self.grid.has_food(self.col, self.row):
            # Find which cluster has food here
            for cluster in self.grid.food_clusters:
                if (self.col, self.row) in cluster.food_cells:
                    if cluster.take_food(self.col, self.row) > 0:
                        self.has_food = True
                        #print(f"✓ Ant picked up food at ({self.col}, {self.row})")  # Optional debug
                        return True
        return False
    
    def _drop_food(self):
        """Drop food at nest."""
        if self.has_food and self._at_nest():
            self.has_food = False
            # Optionally track total food collected
            #print(f"✓ Ant delivered food to nest")  # Optional debug
            return True
        return False

    def _at_nest(self):
        """Check if ant is at nest."""
        return self.grid.nest_position == (self.col, self.row)
    



    ########### DRAW #############

    def draw(self, surface, color=None):
        """Draw the ant as a filled grid cell."""
        if color is None:
            # Change color when carrying food
            color = Config.ANT_WITH_FOOD_COLOR if self.has_food else Config.ANT_COLOR
        
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