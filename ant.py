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
        self.just_changed_state = False
        
        # ACO parameters
        self.alpha = 1.0  # Pheromone importance (0 for heuristic-only)
        self.beta = 2.0   # Heuristic importance

        # Pheromone drop strength
        self.base_strength = Config.PHEROMONE_MAX_DROP_STRENGTH
        self.current_strength = self.base_strength
        self.strength_decay_rate = Config.PHEROMONE_DECAY_RATE  # 2% decay per step
        self.min_strength = Config.PHEROMONE_MIN_DROP_STRENGTH

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
 
    def move_with_heuristic(self, explore_chance=0.2, temperature=0.1):
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
    
    def move_aco(self, explore_chance=0.05, temperature=0.1):
        """
        Full ACO movement with pheromones AND heuristics.
        Uses temperature for softmax probability distribution.
        
        Args:
            explore_chance: Probability of random exploration (0-1)
            temperature: Controls exploration/exploitation (higher = more random)
        """
        # Food pickup/dropoff logic
        if self.has_food:
            self._drop_food()
        
        if not self.has_food:
            self._pickup_food()
        
        # Small chance to explore randomly
        if random.random() < explore_chance:
            return self.move_random()
        
        # Get allowed moves (respects heading restrictions)
        moves = self._get_allowed_neighbors()
        if not moves:
            # Fallback to all valid moves if restricted set is empty
            moves = [(nc, nr, math.sqrt(dx*dx + dy*dy)) 
                    for nc, nr, dx, dy in self._get_valid_neighbors()]
        
        if not moves:
            return False
        
        # Calculate "attractiveness" scores using ACO formula: (pheromone^α) * (heuristic^β)
        scores = []
        
        for col, row, dist in moves:
            # Choose which pheromone and heuristic to follow based on state
            if self.has_food:
                # Heading back to nest: follow NEST pheromones
                pheromone = self.grid.get_pheromone_to_nest(col, row)
                heuristic = self.grid.get_heuristic_to_nest(col, row)
            else:
                # Searching for food: follow FOOD pheromones
                pheromone = self.grid.get_pheromone_to_food(col, row)
                heuristic = self.grid.get_heuristic_to_food(col, row)
            
            # ACO attractiveness score
            p = (pheromone + 0.01) ** Config.ALPHA
            h = (heuristic + 0.01) ** Config.BETA
            
            # Combine and normalize by distance (prefer shorter moves)
            score = (p * h) / max(dist, 0.001)
            scores.append(score)
        
        # NUMERICALLY STABLE SOFTMAX with temperature
        # Use log-sum-exp trick to prevent overflow
        
        if temperature <= 0:
            temperature = 0.001  # Avoid division by zero
        
        # Find maximum score for numerical stability
        max_score = max(scores)
        
        # If all scores are 0, use uniform distribution
        if max_score == 0:
            probs = [1.0 / len(scores)] * len(scores)
        else:
            # Subtract max_score for numerical stability
            scaled_scores = [(s - max_score) / temperature for s in scores]
            
            # Cap very large negative values to prevent underflow
            scaled_scores = [max(s, -50) for s in scaled_scores]  # exp(-50) ≈ 1.9e-22
            
            # Calculate exponentials
            exp_scores = [math.exp(s) for s in scaled_scores]
            total_exp = sum(exp_scores)
            
            # If total_exp is 0 (all scores were -inf after scaling), fallback to uniform
            if total_exp == 0:
                probs = [1.0 / len(scores)] * len(scores)
            else:
                probs = [es / total_exp for es in exp_scores]
        
        # Choose move based on probabilities
        idx = random.choices(range(len(moves)), weights=probs, k=1)[0]
        col, row, dist = moves[idx]
        
        # Deposit pheromone BEFORE moving (at current position)
        self._deposit_pheromone()
        
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
    
    def move_aco_8dir(self, explore_chance=0.05):
        """
        ACO movement with TRUE 8-direction movement (no turning restrictions).
        Pheromone logic matches your corrected version.
        """
        # Food pickup/dropoff logic
        if self.has_food:
            self._drop_food()
        
        if not self.has_food:
            self._pickup_food()
        
        # Small chance to explore randomly (with 8-direction random movement)
        if random.random() < explore_chance:
            return self.move_random_8dir()
        
        # Get ALL valid neighbors (8 directions)
        moves = []
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
                    
                    # Calculate actual Euclidean distance
                    distance = math.sqrt(dc*dc + dr*dr)  # 1.0 or 1.414
                    moves.append((nc, nr, distance))
        
        if not moves:
            return False  # Completely stuck
        
        # Calculate probabilities using ACO formula: (pheromone^α) * (heuristic^β)
        probs = []
        
        for col, row, dist in moves:
            # Choose which pheromone and heuristic to follow based on state
            if self.has_food:
                # Heading back to nest: follow NEST pheromones
                pheromone = self.grid.get_pheromone_to_nest(col, row)
                heuristic = self.grid.get_heuristic_to_nest(col, row)
            else:
                # Searching for food: follow FOOD pheromones
                pheromone = self.grid.get_pheromone_to_food(col, row)
                heuristic = self.grid.get_heuristic_to_food(col, row)
            
            # ACO probability formula with your fixed constants
            p = (pheromone + 0.01) ** Config.ALPHA
            h = (heuristic + 0.01) ** Config.BETA
            
            # Combine and normalize by distance (prefer shorter moves)
            probability = (p * h) / max(dist, 0.001)
            probs.append(probability)
        
        # Choose move based on probabilities
        if sum(probs) > 0:
            idx = random.choices(range(len(moves)), weights=probs, k=1)[0]
        else:
            # Fallback: equal probability for all moves
            idx = random.randint(0, len(moves)-1)
        
        col, row, dist = moves[idx]
        
        # Deposit pheromone (using your corrected logic)
        self._deposit_pheromone()
        
        # Update position
        self.col, self.row = col, row
        self.distance_traveled += dist
        self.steps_taken += 1
        self.path.append((col, row))
        
        # Update heading (optional, for consistency)
        if len(self.path) >= 2:
            prev = self.path[-2]
            dx, dy = col - prev[0], row - prev[1]
            if dx != 0 or dy != 0:
                self.heading = (dx, dy)
        
        return True
    
    def move_random_8dir(self):
        """
        Random 8-direction movement (no turning restrictions).
        """
        # Get ALL valid neighbors
        moves = []
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue
                
                nc = self.col + dc
                nr = self.row + dr
                
                if (0 <= nc < self.grid.cols and 
                    0 <= nr < self.grid.rows and 
                    not self.grid.is_obstacle(nc, nr)):
                    
                    distance = math.sqrt(dc*dc + dr*dr)
                    moves.append((nc, nr, distance))
        
        if not moves:
            return False
        
        # Choose random move
        col, row, dist = random.choice(moves)
        
        # Update position
        self.col, self.row = col, row
        self.distance_traveled += dist
        self.steps_taken += 1
        self.path.append((col, row))
        
        # Update heading
        if len(self.path) >= 2:
            prev = self.path[-2]
            dx, dy = col - prev[0], row - prev[1]
            if dx != 0 or dy != 0:
                self.heading = (dx, dy)
        
        return True
    
    def _deposit_pheromone(self):
        """Deposit pheromone with decaying strength based on distance traveled."""
        # Current strength decays over time/steps
        current_strength = self.current_strength
        
        if self.has_food:
            # Heading to nest: deposit FOOD pheromone
            self.grid.add_pheromone(self.col, self.row, "to_food", current_strength)
        else:
            # Searching for food: deposit NEST pheromone  
            self.grid.add_pheromone(self.col, self.row, "to_nest", current_strength)
        
        # Decay strength for next deposit
        self.current_strength *= self.strength_decay_rate
        self.current_strength = max(self.current_strength, self.min_strength)

    def _reset_strength(self):
        """Reset pheromone strength (called when picking up or dropping food)."""
        self.current_strength = self.base_strength
    
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
    
    def _reverse_direction(self):
        """Reverse the ant's heading (180° turn)."""
        if self.heading is not None:
            hx, hy = self.heading
            self.heading = (-hx, -hy)
    
    def _pickup_food(self):
        """Try to pick up food from current cell."""
        if not self.has_food and self.grid.has_food(self.col, self.row):
            # Find which cluster has food here
            for cluster in self.grid.food_clusters:
                if (self.col, self.row) in cluster.food_cells:
                    if cluster.take_food(self.col, self.row) > 0:
                        self.has_food = True
                        #print(f"✓ Ant picked up food at ({self.col}, {self.row})")  # Optional debug
                        self._reset_strength()
                        self._reverse_direction()
                        return True
        return False
    
    def _drop_food(self):
        """Drop food at nest."""
        if self.has_food and self._at_nest():
            self.has_food = False
            # Optionally track total food collected
            #print(f"✓ Ant delivered food to nest")  # Optional debug
            self._reset_strength()
            self._reverse_direction()
            return True
        return False

    def _at_nest(self):
        """Check if ant is within nest radius."""
        if self.grid.nest_position is None:
            return False
            
        nest_col, nest_row = self.grid.nest_position
        dx = self.col - nest_col
        dy = self.row - nest_row
        distance = math.sqrt(dx*dx + dy*dy)
        
        return distance <= Config.NEST_RADIUS
    



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