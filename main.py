# MAIN.PY
import pygame
import sys
import random
from config import Config
from grid import Grid
from ant import Ant
from food import FoodCluster, Food

# In main.py, update the AntSimulation class:

class AntSimulation:
    def __init__(self):
        """Initialize the simulation."""
        # Initialize pygame
        pygame.init()
        
        # Calculate derived config values
        Config.calculate_derived()
        
        # Set up display
        self.screen = pygame.display.set_mode((Config.SCREENWIDTH, Config.SCREENHEIGHT))
        pygame.display.set_caption("Ant Colony Simulation - Heuristics Test")
        self.clock = pygame.time.Clock()
        
        # Create grid
        self.grid = Grid(Config.SCREENWIDTH, Config.SCREENHEIGHT, Config.CELL_SIZE)
        
        # TEST: Setup heuristics
        self.setup_test_environment()
        
        # Create ants at the nest position
        self.ants = []
        """for _ in range(Config.NUM_ANTS):
            ant = Ant(self.grid, Config.NEST_COL, Config.NEST_ROW)
            self.ants.append(ant)"""
        
        # State
        self.frame_count = 0
        self.running = True
        self.paused = False
    
    def setup_test_environment(self):
        """Setup nest position and food for testing."""
        print("\n=== Setting up test environment ===")
        
        # 1. Set nest position
        self.grid.set_nest_position(Config.NEST_COL, Config.NEST_ROW)
        print(f"✓ Nest position set to ({Config.NEST_COL}, {Config.NEST_ROW})")
        
        # 2. Create food clusters (they automatically register with grid)
        for i, (food_col, food_row) in enumerate(Config.TEST_FOOD_POSITIONS):
            # FoodCluster constructor adds itself to grid
            cluster = FoodCluster(
                grid=self.grid,
                grid_x=food_col,
                grid_y=food_row,
                radius=Config.FOOD_CLUSTER_RADIUS,
                density=Config.FOOD_CLUSTER_DENSITY,
                food_per_cell=Config.FOOD_PER_CELL
            )
            print(f"✓ Food cluster {i} at ({food_col}, {food_row}) "
                  f"radius={Config.FOOD_CLUSTER_RADIUS}, "
                  f"food={cluster.total_food}")
    
    def _draw_food(self):
        """Draw all food clusters stored in grid."""
        for cluster in self.grid.food_clusters:
            cluster.draw(self.screen, Config.CELL_SIZE)
    
    def print_nest_heuristics(self):
        """Print nest heuristic values around the nest."""
        print(f"\n--- Nest Heuristics (around nest {Config.NEST_COL}, {Config.NEST_ROW}) ---")
        
        # Print 3x3 area around nest
        for row_offset in range(-1, 2):
            row_vals = []
            for col_offset in range(-1, 2):
                col = Config.NEST_COL + col_offset
                row = Config.NEST_ROW + row_offset
                
                if 0 <= col < self.grid.cols and 0 <= row < self.grid.rows:
                    value = self.grid.get_heuristic_to_nest(col, row)
                    row_vals.append(f"{value:.3f}")
                else:
                    row_vals.append("  ---  ")
            
            print(f"Row {Config.NEST_ROW + row_offset}: [{', '.join(row_vals)}]")
    
    def print_food_heuristics_near(self, center_col, center_row, cluster_id=0):
        """Print food heuristic values around a point."""
        print(f"\n--- Food Heuristics (around cluster {cluster_id} at {center_col}, {center_row}) ---")
        
        # Print 3x3 area
        for row_offset in range(-1, 2):
            row_vals = []
            for col_offset in range(-1, 2):
                col = center_col + col_offset
                row = center_row + row_offset
                
                if 0 <= col < self.grid.cols and 0 <= row < self.grid.rows:
                    value = self.grid.get_heuristic_to_food(col, row)
                    row_vals.append(f"{value:.3f}")
                else:
                    row_vals.append("  ---  ")
            
            print(f"Row {center_row + row_offset}: [{', '.join(row_vals)}]")
    
    def print_full_heuristic_grid(self, heuristic_type="food"):
        """Print entire heuristic grid to terminal (for debugging)."""
        if heuristic_type == "food":
            grid_data = self.grid.heuristic_to_food
            name = "FOOD"
        else:
            grid_data = self.grid.heuristic_to_nest
            name = "NEST"
        
        print(f"\n=== FULL {name} HEURISTIC GRID ===")
        print(f"Grid size: {self.grid.cols} x {self.grid.rows}")
        
        # Print first 10x10 section for readability
        max_rows = min(10, self.grid.rows)
        max_cols = min(10, self.grid.cols)
        
        print(f"\nFirst {max_rows}x{max_cols} section:")
        print("Columns:", " ".join(f"{i:>5}" for i in range(max_cols)))
        
        for row in range(max_rows):
            row_vals = []
            for col in range(max_cols):
                value = grid_data[row][col]
                row_vals.append(f"{value:5.2f}")
            print(f"Row {row:2}: {' '.join(row_vals)}")
        
        # Find max value and its position
        max_value = 0
        max_pos = (0, 0)
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                if grid_data[row][col] > max_value:
                    max_value = grid_data[row][col]
                    max_pos = (col, row)
        
        print(f"\nMaximum {name} heuristic: {max_value:.3f} at position {max_pos}")
    
    def update(self):
        """Update simulation state."""
        # Move all ants randomly (for now)
        for ant in self.ants:
            ant.move_random()
        
        # Update frame counter
        self.frame_count += 1
        
        # Print debug info periodically
        if Config.PRINT_STATS_EVERY > 0 and self.frame_count % Config.PRINT_STATS_EVERY == 0:
            print(f"\n=== Frame {self.frame_count} ===")
            ants_with_food = sum(1 for ant in self.ants if ant.has_food)
            print(f"Ants with food: {ants_with_food}/{len(self.ants)}")
    
    # Add a key handler to print heuristics on demand
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    # Reset all ants to nest
                    for ant in self.ants:
                        ant.col = Config.NEST_COL
                        ant.row = Config.NEST_ROW
                    print("\n✓ All ants reset to nest")
                elif event.key == pygame.K_f:
                    # Print food heuristic grid
                    self.print_full_heuristic_grid("food")
                elif event.key == pygame.K_n:
                    # Print nest heuristic grid
                    self.print_full_heuristic_grid("nest")
                elif event.key == pygame.K_h:
                    # Print both heuristics around nest
                    self.print_nest_heuristics()
                elif event.key == pygame.K_SPACE:
                    # Toggle pause
                    self.paused = not self.paused
                    print(f"\n✓ Simulation {'PAUSED' if self.paused else 'RUNNING'}")
    
    # Update HUD to show controls
    def _draw_hud(self):
        """Draw heads-up display."""
        font = pygame.font.Font(None, 24)
        
        # Show FPS, ant count, and controls
        fps_text = f"FPS: {int(self.clock.get_fps())} | Ants: {len(self.ants)}"
        if self.paused:
            fps_text += " | PAUSED"
        
        text_surface = font.render(fps_text, True, (0, 0, 0))
        self.screen.blit(text_surface, (10, 10))
        
        # Show controls help
        controls = [
            "Controls: F=Food Heuristics, N=Nest Heuristics",
            "H=Local Heuristics, R=Reset Ants, SPACE=Pause"
        ]
        
        for i, text in enumerate(controls):
            control_surface = font.render(text, True, (100, 100, 100))
            self.screen.blit(control_surface, (10, 40 + i * 25))

    def _draw_grid_lines(self):
        """Draw grid lines for visualization."""
        # Vertical lines
        for col in range(self.grid.cols + 1):
            x = col * Config.CELL_SIZE
            pygame.draw.line(self.screen, Config.GRID_LINE_COLOR, 
                           (x, 0), (x, Config.SCREENHEIGHT), 1)
        
        # Horizontal lines
        for row in range(self.grid.rows + 1):
            y = row * Config.CELL_SIZE
            pygame.draw.line(self.screen, Config.GRID_LINE_COLOR,
                           (0, y), (Config.SCREENWIDTH, y), 1)
    
    def _draw_nest(self):
        """Draw the nest location."""
        # Convert nest grid position to pixel center
        center_x, center_y = self.grid.grid_to_world_center(Config.NEST_COL, Config.NEST_ROW)
        
        # Draw nest as a yellow circle
        nest_radius = Config.CELL_SIZE
        pygame.draw.circle(self.screen, (255, 255, 0),  # Yellow
                         (int(center_x), int(center_y)), 
                         nest_radius)
    
    def draw(self):
        """Draw everything to the screen."""
        # Clear screen
        self.screen.fill(Config.BACKGROUND_COLOR)
        
        # Draw grid lines if enabled
        if Config.SHOW_GRID_LINES:
            self._draw_grid_lines()

        self._draw_food()
        
        # Draw nest
        self._draw_nest()
        
        # Draw ants
        for ant in self.ants:
            ant.draw(self.screen, Config.ANT_COLOR)
        
        # Draw HUD
        self._draw_hud()
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """Main simulation loop."""
        print("\n=== Ant Simulation - Heuristics Test ===")
        print("Controls:")
        print("  F: Print food heuristic grid")
        print("  N: Print nest heuristic grid")
        print("  H: Print heuristics around nest")
        print("  R: Reset ants to nest")
        print("  SPACE: Pause/unpause")
        print("  ESC: Quit")
        print("=======================================\n")
        
        while self.running:
            # Handle events
            self.handle_events()
            
            # Update simulation
            if not self.paused:
                self.update()
            
            # Draw everything
            self.draw()
            
            # Control frame rate
            self.clock.tick(Config.FPS)
        
        # Cleanup
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    # Create and run the simulation
    simulation = AntSimulation()
    simulation.run()