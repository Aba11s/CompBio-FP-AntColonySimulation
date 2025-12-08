import pygame
import math

class Editor:
    def __init__(self, grid, ant_list_ref):
        """
        Editor for drawing/erasing elements on the grid.
        
        Args:
            grid: Reference to the Grid object
            ant_list_ref: Reference to the simulation's ant list
        """
        self.grid = grid
        self.ants = ant_list_ref  # Store reference to ant list
        self.current_tool = "obstacle"  # obstacle, food, ant, erase
        self.brush_size = 1  # Radius in cells
        self.is_drawing = False
        self.last_pos = None  # For continuous drawing
        
        # Colors for different tools
        self.tool_colors = {
            "obstacle": (80, 80, 80),
            "food": (0, 180, 0),
            "erase": (255, 100, 100),
            "ant": (0, 0, 0)
        }
        
        # Brush preview
        self.show_preview = True
        self.preview_alpha = 100  # Semi-transparent
        
    def handle_keyboard(self, event):
        """Handle keyboard shortcuts for editor."""
        handled = True
        
        if event.key == pygame.K_o:
            self.current_tool = "obstacle"
            print("✓ Tool: Obstacle")
        elif event.key == pygame.K_f:
            self.current_tool = "food"
            print("✓ Tool: Food")
        elif event.key == pygame.K_a:
            self.current_tool = "ant"
            print("✓ Tool: Ant")
        # REMOVED: elif event.key == pygame.K_e: (erase tool)
        elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
            self.brush_size = min(self.brush_size + 1, 10)
            print(f"✓ Brush size: {self.brush_size}")
        elif event.key == pygame.K_MINUS:
            self.brush_size = max(self.brush_size - 1, 1)
            print(f"✓ Brush size: {self.brush_size}")
        elif event.key == pygame.K_c:
            self.clear_all_obstacles()
            print("✓ Cleared all obstacles")
        elif event.key == pygame.K_p:
            self.show_preview = not self.show_preview
            print(f"✓ Brush preview: {'ON' if self.show_preview else 'OFF'}")
        else:
            handled = False
            
        return handled

    def handle_events(self, event):
        """Handle editor-specific events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click - draw with current tool
                print("CLICK")
                self.is_drawing = True
                self.apply_tool_at_position(event.pos, event.button)
                return True
            elif event.button == 3:  # Right click - erase current tool type only
                self.is_drawing = True
                self.apply_tool_at_position(event.pos, event.button)
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 3):
                self.is_drawing = False
                self.last_pos = None
                return True
                
        elif event.type == pygame.MOUSEMOTION:
            if self.is_drawing:
                mouse_buttons = pygame.mouse.get_pressed()
                if mouse_buttons[0]:  # Left mouse button
                    self.apply_tool_at_position(event.pos, 1)
                elif mouse_buttons[2]:  # Right mouse button
                    self.apply_tool_at_position(event.pos, 3)
                return True
                
        elif event.type == pygame.KEYDOWN:
            return self.handle_keyboard(event)
            
        return False

    def apply_tool_at_position(self, screen_pos, mouse_button):
        """Apply current tool at mouse position."""
        col, row = self.grid.world_to_grid(screen_pos[0], screen_pos[1])
        print(f"APPLYING at ({col}, {row}) with tool: {self.current_tool}, button: {mouse_button}")
        
        # Skip if out of bounds
        if not (0 <= col < self.grid.cols and 0 <= row < self.grid.rows):
            return
        
        # For continuous drawing, skip if we're still on the same cell
        current_pos = (col, row)
        if self.last_pos == current_pos:
            return
        self.last_pos = current_pos
        
        # Apply tool based on mouse button
        if mouse_button == 1:  # Left click - draw
            if self.current_tool == "obstacle":
                self.draw_obstacle_circle(col, row, True)
            elif self.current_tool == "food":
                self.place_food_cluster(col, row)
            elif self.current_tool == "ant":
                self.place_ant(col, row)
                
        elif mouse_button == 3:  # Right click - erase only current tool type
            if self.current_tool == "obstacle":
                self.draw_obstacle_circle(col, row, False)  # Remove obstacles
            elif self.current_tool == "food":
                self.erase_food_circle(col, row)  # Remove only food clusters
            elif self.current_tool == "ant":
                self.erase_ants_in_circle(col, row)  # Remove only ants

    def erase_food_circle(self, center_col, center_row):
        """Erase only food clusters in a circular area (doesn't erase obstacles or ants)."""
        clusters_to_remove = []
        
        for cluster in self.grid.food_clusters:
            # Check if cluster center is within erase radius
            dx = cluster.grid_x - center_col
            dy = cluster.grid_y - center_row
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance <= self.brush_size:
                clusters_to_remove.append(cluster)
        
        # Remove clusters from grid
        for cluster in clusters_to_remove:
            # First, clear all food cells from this cluster
            for col, row in cluster.food_cells:
                self.grid.remove_food(col, row)
            
            # Remove cluster from grid's list
            self.grid.food_clusters.remove(cluster)
            
            print(f"✓ Deleted food cluster at ({cluster.grid_x}, {cluster.grid_y})")
        
        # Update heuristics after deleting clusters
        if clusters_to_remove:
            self.grid.update_heuristic_to_food()
            print(f"✓ Updated food heuristics after deleting {len(clusters_to_remove)} clusters")

    def erase_ants_in_circle(self, center_col, center_row):
        """Remove ants in a circular area (doesn't erase obstacles or food)."""
        ants_to_remove = []
        
        for ant in self.ants:
            dx = ant.col - center_col
            dy = ant.row - center_row
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance <= self.brush_size:
                ants_to_remove.append(ant)
        
        # Remove ants
        for ant in ants_to_remove:
            self.ants.remove(ant)
        
        if ants_to_remove:
            print(f"✓ Removed {len(ants_to_remove)} ants")
    
    def draw_obstacle_circle(self, center_col, center_row, is_obstacle=True):
        """Draw/erase obstacles in a circular brush."""
        for r in range(self.brush_size):
            radius = r
            for angle in range(0, 360, 10):  # Sample points around circle
                rad = math.radians(angle)
                col = int(center_col + radius * math.cos(rad))
                row = int(center_row + radius * math.sin(rad))
                
                if 0 <= col < self.grid.cols and 0 <= row < self.grid.rows:
                    self.grid.set_obstacle(col, row, is_obstacle)
        
        # Fill the center
        self.grid.set_obstacle(center_col, center_row, is_obstacle)
        print(f"✓ {'Added' if is_obstacle else 'Removed'} obstacles in radius {self.brush_size}")
        
    def erase_ants_in_circle(self, center_col, center_row):
        """Remove ants in a circular area."""
        ants_to_remove = []
        
        for ant in self.ants:
            dx = ant.col - center_col
            dy = ant.row - center_row
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance <= self.brush_size:
                ants_to_remove.append(ant)
        
        # Remove ants
        for ant in ants_to_remove:
            self.ants.remove(ant)
        
        if ants_to_remove:
            print(f"✓ Removed {len(ants_to_remove)} ants")
    
    def place_food_cluster(self, center_col, center_row):
        """Place a food cluster at the clicked position."""
        from food import FoodCluster
        
        # Remove any existing food in the area first
        #self.erase_food_circle(center_col, center_row)
        
        # Create new food cluster
        cluster = FoodCluster(
            grid=self.grid,
            grid_x=center_col,
            grid_y=center_row,
            radius=self.brush_size,
            density=0.5,
            food_per_cell=5
        )
        print(f"✓ Placed food cluster at ({center_col}, {center_row}) radius={self.brush_size}")
    
    def place_ant(self, col, row):
        """Place an ant at the clicked position."""
        from ant import Ant
        
        # Only place if cell is not an obstacle
        if not self.grid.is_obstacle(col, row):
            new_ant = Ant(self.grid, col, row)
            self.ants.append(new_ant)
            print(f"✓ Placed ant at ({col}, {row}) - Total ants: {len(self.ants)}")
    
    def clear_all_obstacles(self):
        """Clear all obstacles from the grid."""
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                self.grid.set_obstacle(col, row, False)
        print("✓ Cleared all obstacles")
    
    def draw_brush_preview(self, surface, mouse_pos):
        """Draw brush preview at mouse position."""
        if not self.show_preview:
            return
        
        col, row = self.grid.world_to_grid(mouse_pos[0], mouse_pos[1])
        
        # Draw preview circle
        center_x, center_y = self.grid.grid_to_world_center(col, row)
        brush_radius_pixels = self.brush_size * self.grid.cell_size
        
        # Create a temporary surface for alpha blending
        preview_surf = pygame.Surface((brush_radius_pixels * 2, brush_radius_pixels * 2), pygame.SRCALPHA)
        
        # Draw circle with tool color
        color = self.tool_colors.get(self.current_tool, (100, 100, 100))
        pygame.draw.circle(
            preview_surf, 
            (*color, self.preview_alpha),  # Add alpha
            (brush_radius_pixels, brush_radius_pixels),
            brush_radius_pixels,
            2  # Outline only
        )
        
        # Draw center dot
        pygame.draw.circle(
            preview_surf,
            (*color, self.preview_alpha),
            (brush_radius_pixels, brush_radius_pixels),
            2
        )
        
        # Blit onto main surface
        surface.blit(preview_surf, (center_x - brush_radius_pixels, center_y - brush_radius_pixels))
    
    def draw_ui(self, surface, font):
        """Draw editor UI information."""
        # Tool info
        tool_text = f"Tool: {self.current_tool.upper()} (Size: {self.brush_size})"
        tool_surface = font.render(tool_text, True, (0, 0, 0))
        surface.blit(tool_surface, (10, 35))
        
        # Ant count
        ant_text = f"Ants: {len(self.ants)}"
        ant_surface = font.render(ant_text, True, (0, 0, 0))
        surface.blit(ant_surface, (10, 60))
        
        # Controls info - Updated to remove "E: Erase"
        controls = [
            "O: Obstacle  F: Food  A: Ant",
            "+/-: Brush Size  C: Clear All Obstacles  P: Toggle Preview",
            "LMB: Draw  RMB: Erase current tool type"
        ]
        
        for i, line in enumerate(controls):
            control_surface = font.render(line, True, (50, 50, 50))
            surface.blit(control_surface, (10, 85 + i * 20))