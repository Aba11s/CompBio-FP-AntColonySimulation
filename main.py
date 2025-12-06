# MAIN.PY
import pygame
import sys
import random
from config import Config
from grid import Grid
from ants import Ant

class AntSimulation:
    def __init__(self):
        """Initialize the simulation."""
        # Initialize pygame
        pygame.init()
        
        # Calculate derived config values
        Config.calculate_derived()
        
        # Set up display
        self.screen = pygame.display.set_mode((Config.SCREENWIDTH, Config.SCREENHEIGHT))
        pygame.display.set_caption("Ant Colony Simulation - Random Movement")
        self.clock = pygame.time.Clock()
        
        # Create grid
        self.grid = Grid(Config.SCREENWIDTH, Config.SCREENHEIGHT, Config.CELL_SIZE)
        
        # Create ants at the nest position
        self.ants = []
        for _ in range(Config.NUM_ANTS):
            ant = Ant(self.grid, Config.NEST_COL, Config.NEST_ROW)
            self.ants.append(ant)
        
        # State
        self.frame_count = 0
        self.running = True
        self.paused = False
    
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
    
    def update(self):
        """Update simulation state."""
        # Move all ants randomly
        for ant in self.ants:
            ant.move_random()
        
        # Update frame counter
        self.frame_count += 1
    
    def draw(self):
        """Draw everything to the screen."""
        # Clear screen
        self.screen.fill(Config.BACKGROUND_COLOR)
        
        # Draw grid lines if enabled
        if Config.SHOW_GRID_LINES:
            self._draw_grid_lines()
        
        # Draw nest
        self._draw_nest()
        
        # Draw ants
        for ant in self.ants:
            ant.draw(self.screen, Config.ANT_COLOR)
        
        # Draw minimal HUD
        self._draw_hud()
        
        # Update display
        pygame.display.flip()
    
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
    
    def _draw_hud(self):
        """Draw minimal heads-up display."""
        font = pygame.font.Font(None, 24)
        
        # Show only FPS and ant count
        fps_text = f"FPS: {int(self.clock.get_fps())} | Ants: {len(self.ants)}"
        text_surface = font.render(fps_text, True, (0, 0, 0))
        self.screen.blit(text_surface, (10, 10))
    
    def run(self):
        """Main simulation loop."""
        print("\n=== Ant Simulation ===")
        print("ESC: Quit")
        print("R: Reset ants to nest")
        print("======================\n")
        
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