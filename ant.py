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
        """Random movement accounting for diagonal distances."""
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
 
    def move_with_heuristic(self, explore_chance=0.5, debug=False):
        """
        Heuristic movement with EXPONENTIAL scaling.
        Probability ∝ exp(heuristic/temperature) / distance

        LEGACY CODE: keep just in case
        """
        if random.random() < explore_chance:
            return self.move_random()
        
        weighted_neighbors = self._get_allowed_neighbors()
        
        if not weighted_neighbors:
            all_neighbors = self._get_valid_neighbors()
            if not all_neighbors:
                return False
            
            weighted_neighbors = []
            for nc, nr, dx, dy in all_neighbors:
                distance = math.sqrt(dx*dx + dy*dy)
                weighted_neighbors.append((nc, nr, distance))
        
        positions = []
        distances = []
        probabilities = []
        heuristic_values = []
        
        # COLLECT ALL DATA FIRST
        for nc, nr, distance in weighted_neighbors:
            heuristic = self.grid.get_heuristic_to_food(nc, nr)
            heuristic_values.append(heuristic)
            positions.append((nc, nr))
            distances.append(distance)
        
        if debug:
            print(f"  Available positions: {positions}")
            print(f"  Heuristics: {[f'{h:.3f}' for h in heuristic_values]}")
        
        # FIND MIN/MAX FOR NORMALIZATION
        min_h = min(heuristic_values)
        max_h = max(heuristic_values)
        
        # If all heuristics are similar, fall back to random
        if max_h - min_h < 0.01:
            if debug:
                print("  All heuristics similar, falling back to random")
            chosen_idx = random.randint(0, len(positions) - 1)
        else:
            # NORMALIZE to 0-1 range
            normalized_heuristics = []
            for h in heuristic_values:
                norm = (h - min_h) / (max_h - min_h)
                normalized_heuristics.append(norm)
            
            # EXPONENTIAL SCALING with temperature
            temperature = 0.3  # Lower = more extreme probabilities
            for i, (norm_h, distance) in enumerate(zip(normalized_heuristics, distances)):
                # Exponential: exp(norm_h / temperature)
                # This amplifies small differences dramatically!
                exponent = norm_h / temperature
                # Cap exponent to avoid overflow
                exponent = min(exponent, 10)
                
                probability = math.exp(exponent) / distance if distance > 0 else 0.001
                probabilities.append(max(0.001, probability))
            
            if debug:
                print(f"  Normalized heuristics: {[f'{h:.3f}' for h in normalized_heuristics]}")
                print(f"  Probabilities: {[f'{p:.3f}' for p in probabilities]}")
                max_idx = probabilities.index(max(probabilities))
                min_idx = probabilities.index(min(probabilities))
                print(f"  Max prob: {probabilities[max_idx]:.3f} at {positions[max_idx]} (heuristic={heuristic_values[max_idx]:.3f})")
                print(f"  Min prob: {probabilities[min_idx]:.3f} at {positions[min_idx]} (heuristic={heuristic_values[min_idx]:.3f})")
                print(f"  Ratio max/min: {probabilities[max_idx]/probabilities[min_idx]:.2f}x")
            
            total = sum(probabilities)
            if total <= 0:
                chosen_idx = random.randint(0, len(positions) - 1)
            else:
                normalized = [p/total for p in probabilities]
                chosen_idx = random.choices(range(len(positions)), weights=normalized, k=1)[0]
        
        if debug:
            print(f"  Chose: {positions[chosen_idx]} (heuristic={heuristic_values[chosen_idx]:.3f})")
        
        old_col, old_row = self.col, self.row
        self.col, self.row = positions[chosen_idx]
        distance = distances[chosen_idx]
        
        self.distance_traveled += distance
        self.steps_taken += 1
        self.path.append((self.col, self.row))
        
        dx = self.col - old_col
        dy = self.row - old_row
        if dx != 0 or dy != 0:
            self.heading = (dx, dy)
        
        return True
    
    def move_with_heuristic(self, explore_chance=0.1, temperature=0.1):
        """Minimal heuristic movement - just the essentials."""
        if random.random() < explore_chance:
            return self.move_random()
        
        # Get moves with (col, row, distance)
        moves = self._get_allowed_neighbors()
        if not moves:
            # Fallback
            moves = [(nc, nr, math.sqrt(dx*dx + dy*dy)) 
                    for nc, nr, dx, dy in self._get_valid_neighbors()]
        
        if not moves:
            return False
        
        # Calculate probabilities
        probs = []
        for col, row, dist in moves:
            h = self.grid.get_heuristic_to_food(col, row)
            probs.append(math.exp(h / temperature) / max(dist, 0.001))
        
        # Choose and move
        idx = random.choices(range(len(moves)), weights=probs, k=1)[0]
        col, row, dist = moves[idx]
        
        # Update position
        self.col, self.row = col, row
        self.distance_traveled += dist
        self.steps_taken += 1
        self.path.append((col, row))
        
        # Update heading (simplified)
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
    
    def _get_direction_name(self, dx, dy):
        """Convert direction vector to readable name."""
        if dx == -1 and dy == -1: return "UP-LEFT"
        if dx == 0 and dy == -1: return "UP"
        if dx == 1 and dy == -1: return "UP-RIGHT"
        if dx == -1 and dy == 0: return "LEFT"
        if dx == 1 and dy == 0: return "RIGHT"
        if dx == -1 and dy == 1: return "DOWN-LEFT"
        if dx == 0 and dy == 1: return "DOWN"
        if dx == 1 and dy == 1: return "DOWN-RIGHT"
        return "STAY"
    
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
        
        # Draw heading indicator (optional, for debugging)
        if self.heading:
            center_x = x + self.grid.cell_size // 2
            center_y = y + self.grid.cell_size // 2
            
            # Calculate endpoint for heading line
            line_length = self.grid.cell_size // 2
            end_x = center_x + self.heading[0] * line_length
            end_y = center_y + self.heading[1] * line_length
            
            # Draw heading line
            '''pygame.draw.line(surface, (255, 255, 255), 
                           (center_x, center_y), 
                           (end_x, end_y), 2)'''