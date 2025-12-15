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
        self.current_fps = Config.FPS
        
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

        # Tuning mode
        self.tuning_mode = False
        self.tuning_parameter = "alpha"  # Options: "alpha", "beta", "temperature", "explore_chance"
        self.tuning_step = 0.1  

        # visibility
        self.show_ants = Config.SHOW_ANTS
        self.show_pheromones = Config.SHOW_PHEROMONES  # Start with config value
        self.show_grid_lines = Config.SHOW_GRID_LINES   # Start with config value

        # diffuse state
        self.diffuse = False
        
        # State
        self.frame_count = 0
        self.running = True
        self.paused = True

        # Optimization
        self.ph_counter = 0
        self.df_counter = 0

        # Metrics tracking
        self.metrics = {
            'ants_with_food': 0,
            'ants_without_food': 0,
            'total_food_delivered': 0,
            'food_delivered_per_second': 0.0,
            'frames_since_last_reset': 0,
            'last_delivery_time': 0,
            'delivery_times': []  # Track timestamps for rate calculation
        }
        
        # Metrics display
        self.show_metrics = True
        self.metrics_font = pygame.font.Font(None, Config.METRICS_FONT_SIZE)
        self.metrics_update_interval = Config.FPS  # Update every second
        self.metrics_counter = 0

    def _update_metrics(self):
        """Update all metrics."""
        # Count ants with and without food
        with_food = 0
        without_food = 0
        
        for ant in self.ants:
            if ant.has_food:
                with_food += 1
            else:
                without_food += 1
        
        self.metrics['ants_with_food'] = with_food
        self.metrics['ants_without_food'] = without_food
        
        # Get total food delivered from grid
        self.metrics['total_food_delivered'] = self.grid.food_dropped
        
        # Calculate current time
        current_time = self.frame_count / Config.FPS
        
        # Update rate every second
        self.metrics_counter += 1
        if self.metrics_counter >= self.metrics_update_interval:
            # Remove old deliveries (older than 10 seconds)
            self.metrics['delivery_times'] = [
                t for t in self.metrics['delivery_times'] 
                if current_time - t <= 10.0
            ]
            
            # Calculate rate based on deliveries in last 10 seconds
            if self.metrics['delivery_times']:
                oldest_time = min(self.metrics['delivery_times'])
                time_window = current_time - oldest_time
                
                if time_window > 1.0:  # Need at least 1 second of data
                    self.metrics['food_delivered_per_second'] = (
                        len(self.metrics['delivery_times']) / time_window
                    )
                else:
                    # If less than 1 second, extrapolate
                    self.metrics['food_delivered_per_second'] = (
                        len(self.metrics['delivery_times']) / 1.0
                    )
            else:
                self.metrics['food_delivered_per_second'] = 0.0
            
            self.metrics_counter = 0
        
        # Increment frame count
        if not self.paused:
            self.frame_count += 1

    def _record_food_delivery(self):
        """Record when food is delivered."""
        current_time = self.frame_count / Config.FPS
        
        # Add current delivery time
        self.metrics['delivery_times'].append(current_time)
    
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
        # Grid updates
        self.grid.update_food_clusters()
        
        # Evap & Diffusion
        self.ph_counter += 1
        if self.ph_counter >= Config.EVAPORATION_INTERVAL:
            if self.movement_mode == "aco":
                self.grid.update_pheromones(True, self.diffuse)
            self.ph_counter = 0

        
        # Single-threaded ant updates (fastest for <500 ants)
        for ant in self.ants:
            if self.movement_mode == "random":
                ant.move_random()
            elif self.movement_mode == "aco":
                ant.move_aco()

        # Check if any food was delivered during this update
        food_dropped_this_frame = self.grid.food_dropped_this_frame
        if food_dropped_this_frame > 0:
            for _ in range(food_dropped_this_frame):
                self._record_food_delivery()

        self.grid.food_dropped_this_frame = 0
        
        # Update metrics
        self._update_metrics()

    def _adjust_parameter(self, direction):
        """Adjust the current tuning parameter."""
        if direction > 0:
            operation = "increased"
        else:
            operation = "decreased"
        
        old_value = None
        
        # Update all ants' parameters
        for ant in self.ants:
            if self.tuning_parameter == "alpha":
                old_value = ant.alpha
                ant.alpha = max(0.0, ant.alpha + direction * self.tuning_step)
            elif self.tuning_parameter == "beta":
                old_value = ant.beta
                ant.beta = max(0.0, ant.beta + direction * self.tuning_step)
            elif self.tuning_parameter == "temperature":
                old_value = ant.temperature
                ant.temperature = max(0.001, ant.temperature + direction * self.tuning_step * 0.05)
            elif self.tuning_parameter == "explore_chance":
                old_value = ant.explore_chance
                ant.explore_chance = max(0.0, min(1.0, ant.explore_chance + direction * self.tuning_step * 0.1))
        
        if old_value is not None:
            # Get new value from first ant
            first_ant = self.ants[0]
            if self.tuning_parameter == "alpha":
                new_value = first_ant.alpha
            elif self.tuning_parameter == "beta":
                new_value = first_ant.beta
            elif self.tuning_parameter == "temperature":
                new_value = first_ant.temperature
            elif self.tuning_parameter == "explore_chance":
                new_value = first_ant.explore_chance
            
            print(f"\n✓ {self.tuning_parameter.upper()} {operation}: {old_value:.3f} → {new_value:.3f}")
            
    
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
                    
                # Toggle tuning mode with 'T' key
                elif event.key == pygame.K_t:
                    self.tuning_mode = not self.tuning_mode
                    if self.tuning_mode:
                        print(f"\n✓ TUNING MODE ACTIVE")
                        print(f"Current parameter: {self.tuning_parameter}")
                        print(f"Use 1-4 to select parameter, +/- to adjust, T to exit")
                    else:
                        print(f"\n✓ Tuning mode deactivated")
                
                # If in tuning mode, handle tuning controls
                elif self.tuning_mode:
                    if event.key == pygame.K_1:
                        self.tuning_parameter = "alpha"
                        print(f"\n✓ Now tuning: ALPHA (pheromone importance)")
                        #self._print_current_parameters()
                    elif event.key == pygame.K_2:
                        self.tuning_parameter = "beta"
                        print(f"\n✓ Now tuning: BETA (heuristic importance)")
                        #self._print_current_parameters()
                    elif event.key == pygame.K_3:
                        self.tuning_parameter = "temperature"
                        print(f"\n✓ Now tuning: TEMPERATURE (exploration)")
                        #self._print_current_parameters()
                    elif event.key == pygame.K_4:
                        self.tuning_parameter = "explore_chance"
                        print(f"\n✓ Now tuning: EXPLORE CHANCE (random movement)")
                        #self._print_current_parameters()
                    
                    # Adjust parameter values
                    elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                        self._adjust_parameter(1)  # Increase
                    elif event.key == pygame.K_MINUS:
                        self._adjust_parameter(-1)  # Decrease
                    
                    # Change adjustment step size
                    elif event.key == pygame.K_LEFTBRACKET:  # [ to decrease step
                        self.tuning_step = max(0.01, self.tuning_step / 2)
                        print(f"\n✓ Adjustment step decreased to: {self.tuning_step:.3f}")
                    elif event.key == pygame.K_RIGHTBRACKET:  # ] to increase step
                        self.tuning_step = min(1.0, self.tuning_step * 2)
                        print(f"\n✓ Adjustment step increased to: {self.tuning_step:.3f}")
                
                # Regular simulation controls (only when not in tuning mode)
                elif not self.tuning_mode:
                    if event.key == pygame.K_r:
                        # Reset all ants to nest and metrics
                        for ant in self.ants:
                            ant.reset()

                        # Reset grid food counter
                        self.grid.food_dropped = 0
                        self.grid.food_dropped_this_frame = 0
                                        
                        self.metrics['total_food_delivered'] = 0
                        self.metrics['food_delivered_per_second'] = 0.0
                        self.metrics['delivery_times'] = []
                        self.frame_count = 0
                        
                        print("\n✓ All ants reset to nest, metrics cleared")
                    elif event.key == pygame.K_SPACE:
                        # Toggle pause
                        self.paused = not self.paused
                        print(f"\n✓ Simulation {'PAUSED' if self.paused else 'RUNNING'}")

                    elif event.key == pygame.K_a:  # Toggle ants
                        self.show_ants = not self.show_ants
                        print(f"\n✓ Ants: {'SHOWN' if self.show_ants else 'HIDDEN'}")
                    elif event.key == pygame.K_p:  # Toggle pheromones
                        self.show_pheromones = not self.show_pheromones
                        print(f"\n✓ Pheromones: {'SHOWN' if self.show_pheromones else 'HIDDEN'}")
                    elif event.key == pygame.K_g:  # Toggle grid lines
                        self.show_grid_lines = not self.show_grid_lines
                        print(f"\n✓ Grid lines: {'SHOWN' if self.show_grid_lines else 'HIDDEN'}")

                    elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:  # Increase speed
                        self.current_fps = min(60, self.current_fps + 5)
                        print(f"\n✓ Speed: {self.current_fps} FPS")
                    elif event.key == pygame.K_MINUS:  # Decrease speed
                        self.current_fps = max(10, self.current_fps - 5)
                        print(f"\n✓ Speed: {self.current_fps} FPS")

                    elif event.key == pygame.K_m:  # Toggle metrics display
                        self.show_metrics = not self.show_metrics
                        print(f"\n✓ Metrics: {'SHOWN' if self.show_metrics else 'HIDDEN'}")

                    elif event.key == pygame.K_d:
                        self.diffuse = not self.diffuse
                        print(f"\n✓ Diffusion: {'ON' if self.diffuse else 'OFF'}")
    
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
        
    def _draw_metrics(self):
        """Draw metrics on screen."""
        if not self.show_metrics:
            return
        
        metrics_text = [
            f"Ants with food: {self.metrics['ants_with_food']}",
            f"Ants without food: {self.metrics['ants_without_food']}",
            f"Total food delivered: {self.metrics['total_food_delivered']}",
            f"Food/sec: {self.metrics['food_delivered_per_second']:.2f}",
            f"Movement mode: {self.movement_mode.upper()}",
            f"Ants: {len(self.ants)}"
        ]
        
        # Create background surface for metrics
        metrics_surface = pygame.Surface((250, len(metrics_text) * 25 + 20), pygame.SRCALPHA)
        metrics_surface.fill(Config.METRICS_BACKGROUND)
        
        # Draw metrics text
        y_offset = 10
        for text in metrics_text:
            text_surface = self.metrics_font.render(text, True, Config.METRICS_COLOR)
            metrics_surface.blit(text_surface, (10, y_offset))
            y_offset += 25
        
        # Draw the metrics panel on screen (top-right corner)
        self.screen.blit(metrics_surface, (Config.SCREENWIDTH - 260, 10))
    
    def draw(self):
        """Draw everything to the screen."""
        # Clear screen
        self.screen.fill(Config.BACKGROUND_COLOR)
        
        # Draw pheromones FIRST (background) - Grid handles its own drawing
        if self.movement_mode == "aco" and self.show_pheromones:
            self.grid.draw_pheromones(self.screen)
        
        # Draw grid lines if enabled
        if self.show_grid_lines:
            self._draw_grid_lines()
        
        self.grid.draw_obstacles(self.screen, Config.OBSTACLE_COLOR)
        self._draw_food()
        
        # Draw ants (on top)
        for ant in self.ants:
            if self.show_ants:
                ant.draw(self.screen)

        self._draw_nest()
        
        if self.editor_mode:
            mouse_pos = pygame.mouse.get_pos()
            self.editor.draw_brush_preview(self.screen, mouse_pos)
        
        # Draw metrics BEFORE HUD (so HUD is on top)
        if self.show_metrics:
            self._draw_metrics()
        
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
        print("  M: Toggle metrics display")
        print("  A: Toggle ants visibility")
        print("  P: Toggle pheromones visibility")
        print("  G: Toggle grid lines")
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
            self.clock.tick(self.current_fps)
        
        # Cleanup
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    # Create and run the simulation
    simulation = AntSimulation()
    simulation.run()