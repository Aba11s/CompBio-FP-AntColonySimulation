# MAIN.PY
import pygame
import sys
import random
from config import Config
from grid import Grid
from ant import Ant
from food import FoodCluster, Food
from editor import Editor

import concurrent.futures
from functools import partial

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

        # Set Nest
        self.grid.set_nest_position(Config.NEST_COL, Config.NEST_ROW)
        
        # Create ants at the nest position
        self.ants = []
        for _ in range(Config.NUM_ANTS):
            ant = Ant(self.grid, Config.NEST_COL, Config.NEST_ROW)
            self.ants.append(ant)

        # Ant movement mode 
        self.movement_mode = "aco"

        # Editor setup
        self.editor = Editor(self.grid, self.ants)
        self.editor_mode = False  # Toggle with key
        
        # State
        self.frame_count = 0
        self.running = True
        self.paused = False

        # Optimization
        self.ph_counter = 0
        self.df_counter = 0
    
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
        """Update simulation with optimized pheromone updates."""
        total_heuristic = 0
        ants_at_food = 0
        
        # Grid updates
        self.grid.update_food_clusters()
        
        # OPTIMIZATION: Evaporate less frequently
        self.ph_counter += 1
        if self.ph_counter >= Config.EVAPORATION_INTERVAL:
            if self.movement_mode == "aco":
                self.grid.evaporate_pheromones()
            self.ph_counter = 0

        # OPTIMIZATION: DIFFUSE less frequently
        '''self.df_counter += 1
        if self.df_counter >= Config.DIFFUSION_INTERVAL:
            self.grid.diffuse_pheromones()
            self.df_counter = 0'''
        
        # Single-threaded ant updates (fastest for <500 ants)
        for ant in self.ants:
            if self.movement_mode == "heuristic":
                ant.move_with_heuristic()
            elif self.movement_mode == "random":
                ant.move_random()
            elif self.movement_mode == "aco":
                ant.move_aco()
            
    
    # Add a key handler to print heuristics on demand
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # FIRST: Always check for TAB to toggle editor mode
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.editor_mode = not self.editor_mode
                print(f"\n✓ Editor mode: {'ON' if self.editor_mode else 'OFF'}")
                continue  # Skip further processing
            
            # SECOND: If in editor mode, handle ALL events through editor
            elif self.editor_mode:
                #print(f"EDITOR handling event: {event.type}")  # DEBUG
                if self.editor.handle_events(event):
                    continue
                # Editor didn't handle it, check for ESCAPE
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    continue
            
            # THIRD: Handle simulation events (only when NOT in editor mode)
            elif not self.editor_mode and event.type == pygame.KEYDOWN:
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
                elif event.key == pygame.K_1:
                    # Switch to heuristic movement
                    self.movement_mode = "heuristic"
                    print(f"\n✓ Movement: HEURISTIC (β={Config.BETA})")
                    print("Ants should move toward food clusters")
                elif event.key == pygame.K_2:
                    # Switch to random movement
                    self.movement_mode = "random"
                    print(f"\n✓ Movement: RANDOM")
                    print("Ants move randomly for comparison")
                elif event.key == pygame.K_d:
                    # Print debug info for first ant
                    if self.ants:
                        info = self.ants[0].get_debug_info()
                        print(f"\n=== Ant 0 Debug ===")
                        print(f"Position: {info['position']}")
                        print(f"Steps taken: {info['steps']}")
                        print(f"Current food heuristic: {info['heuristic']:.3f}")
                        print(f"At food cluster: {info['at_food']}")
    
    # Update HUD to show only FPS
    def _draw_hud(self):
        """Draw heads-up display - only FPS."""
        font = pygame.font.Font(None, 24)
        
        # Show FPS
        fps_text = f"FPS: {int(self.clock.get_fps())}"
        fps_surface = font.render(fps_text, True, (0, 0, 0))
        self.screen.blit(fps_surface, (10, 10))

        # Show editor mode status
        if self.editor_mode:
            mode_text = "EDITOR MODE (TAB to exit)"
            mode_surface = font.render(mode_text, True, (200, 0, 0))
            self.screen.blit(mode_surface, (self.screen.get_width() - 250, 10))

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
        pygame.draw.circle(self.screen, (255, 255, 0),  # Yellow
                         (int(center_x), int(center_y)), 
                         Config.NEST_RADIUS * Config.CELL_SIZE)
    
    def draw(self):
        """Draw everything to the screen."""
        # Clear screen
        self.screen.fill(Config.BACKGROUND_COLOR)
        
        # Draw pheromones FIRST (background) - Grid handles its own drawing
        if self.movement_mode == "aco" and Config.DRAW_PHEROMONES:
            self.grid.draw_pheromones(self.screen)
        
        # Draw grid lines if enabled
        if Config.SHOW_GRID_LINES:
            self._draw_grid_lines()
        
        self.grid.draw_obstacles(self.screen, Config.OBSTACLE_COLOR)
        self._draw_food()
        
        # Draw ants (on top)
        for ant in self.ants:
            #ant.draw(self.screen)
            ...

        self._draw_nest()
        
        if self.editor_mode:
            mouse_pos = pygame.mouse.get_pos()
            self.editor.draw_brush_preview(self.screen, mouse_pos)
        
        self._draw_hud()
        
        if self.editor_mode:
            font = pygame.font.Font(None, 20)
            self.editor.draw_ui(self.screen, font)
        
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