import pygame
import math
import random

# Constants
COLUMNS = 100
ROWS = 100

NEST_C = 25
NEST_R = 25

FOOD_C = 50
FOOD_R = 50

MAX_ANTS = 1000

MIN_PHEROMONE = 1
MAX_PHEROMONE = 100
EVAPORATION = 0.95
DROPOFF = 0.995
TRAIL_STRENGTH = 5
ANT_FRAME_RATE = 60

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ant Simulation")
clock = pygame.time.Clock()

CELL_WIDTH = WIDTH // COLUMNS
CELL_HEIGHT = HEIGHT // ROWS

class Cell:
    def __init__(self, c, r):
        self.c = c
        self.r = r
        self.home_pheromone = 0
        self.food_pheromone = 0
        self.food_amount = 0
        self.obstacle = False
        
        self.x = self.c * CELL_WIDTH
        self.y = self.r * CELL_HEIGHT
    
    def get_neighbors(self, grid):
        neighbors = []
        if self.c > 0:
            neighbors.append(grid[self.c - 1][self.r])
        if self.c < COLUMNS - 1:
            neighbors.append(grid[self.c + 1][self.r])
        if self.r > 0:
            neighbors.append(grid[self.c][self.r - 1])
        if self.r < ROWS - 1:
            neighbors.append(grid[self.c][self.r + 1])
        
        neighbors = [cell for cell in neighbors if not cell.obstacle]
        return neighbors
    
    def step(self):
        self.home_pheromone *= EVAPORATION
        self.home_pheromone = max(MIN_PHEROMONE, min(self.home_pheromone, MAX_PHEROMONE))
        
        self.food_pheromone *= EVAPORATION
        self.food_pheromone = max(MIN_PHEROMONE, min(self.food_pheromone, MAX_PHEROMONE))
    
    def draw(self, screen):
        # Calculate intensities
        home_intensity = self.home_pheromone / MAX_PHEROMONE
        food_intensity = self.food_pheromone / MAX_PHEROMONE
        
        # Blend colors based on relative strengths
        total_intensity = home_intensity + food_intensity
        if total_intensity > 0:
            home_weight = home_intensity / total_intensity
            food_weight = food_intensity / total_intensity
            
            # Home color (green): (0, 255, 0)
            # Food color (blue): (0, 0, 255)
            # Blend them based on weights
            r = int(255 * food_weight * total_intensity)
            g = int(255 * home_weight * total_intensity)
            b = 0
            
            # Add white background and subtract based on intensity
            r = 255 - int(255 * home_intensity)
            g = 255 - int(255 * food_intensity)
            b = 255 - int(255 * total_intensity)
        else:
            r = g = b = 255
        
        # Clamp values
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        cell_color = (r, g, b)
        
        # Draw cell background
        pygame.draw.rect(screen, cell_color, (self.x, self.y, CELL_WIDTH, CELL_HEIGHT))
        pygame.draw.rect(screen, (100, 100, 100), (self.x, self.y, CELL_WIDTH, CELL_HEIGHT), 1)
        
        # Draw the nest
        if self.c == NEST_C and self.r == NEST_R:
            points = [
                (self.x + CELL_WIDTH * 0.5, self.y + CELL_HEIGHT * 0.25),
                (self.x + CELL_WIDTH * 0.75, self.y + CELL_HEIGHT * 0.75),
                (self.x + CELL_WIDTH * 0.25, self.y + CELL_HEIGHT * 0.75)
            ]
            pygame.draw.polygon(screen, (0, 255, 0), points)
            pygame.draw.polygon(screen, (0, 0, 0), points, 1)
        
        # Draw the food
        if self.food_amount > 0:
            points = [
                (self.x + CELL_WIDTH * 0.5, self.y + CELL_HEIGHT * 0.25),
                (self.x + CELL_WIDTH * 0.75, self.y + CELL_HEIGHT * 0.75),
                (self.x + CELL_WIDTH * 0.25, self.y + CELL_HEIGHT * 0.75)
            ]
            pygame.draw.polygon(screen, (0, 0, 255), points)
            pygame.draw.polygon(screen, (255, 255, 255), points, 1)
        
        # Draw obstacle
        if self.obstacle:
            pygame.draw.rect(screen, (32, 32, 32), (self.x, self.y, CELL_WIDTH, CELL_HEIGHT))


class Ant:
    def __init__(self):
        self.c = NEST_C
        self.r = NEST_R
        self.going_home = False
    
    def step(self, grid):
        cell = grid[self.c][self.r]
        neighbors = cell.get_neighbors(grid)
        
        if not neighbors:
            return
            
        total_chance = 0
        max_neighbor_home_pheromone = 0
        max_neighbor_food_pheromone = 0
        neighbor_data = []
        
        # Sniff the pheromones of neighbor cells
        for neighbor in neighbors:
            chance = math.pow(
                neighbor.home_pheromone if self.going_home else neighbor.food_pheromone,
                TRAIL_STRENGTH
            )
            neighbor_data.append({
                'chance': chance,
                'cell': neighbor
            })
            total_chance += chance
            
            if neighbor.home_pheromone > max_neighbor_home_pheromone:
                max_neighbor_home_pheromone = neighbor.home_pheromone
            
            if neighbor.food_pheromone > max_neighbor_food_pheromone:
                max_neighbor_food_pheromone = neighbor.food_pheromone
        
        # Release pheromones in the current cell
        if self.c == NEST_C and self.r == NEST_R:
            self.going_home = False
            cell.home_pheromone = MAX_PHEROMONE
        else:
            cell.home_pheromone = max_neighbor_home_pheromone * DROPOFF
        
        if cell.food_amount > 0:
            self.going_home = True
            cell.food_pheromone = MAX_PHEROMONE
        else:
            cell.food_pheromone = max_neighbor_food_pheromone * DROPOFF
        
        # Choose the next cell
        if total_chance > 0:
            chance = random.uniform(0, total_chance)
            current_chance = 0
            for data in neighbor_data:
                current_chance += data['chance']
                if chance < current_chance:
                    self.c = data['cell'].c
                    self.r = data['cell'].r
                    break
    
    def draw(self, screen):
        x = self.c * CELL_WIDTH + CELL_WIDTH // 2
        y = self.r * CELL_HEIGHT + CELL_HEIGHT // 2
        
        if self.going_home:
            color = (0, 0, 255)  # Blue when going home
        else:
            color = (0, 0, 0)    # Black when searching
        
        pygame.draw.circle(screen, color, (int(x), int(y)), int(CELL_WIDTH * 0.375))
        pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), int(CELL_WIDTH * 0.375), 1)


def main():
    # Initialize grid
    grid = []
    for c in range(COLUMNS):
        grid.append([])
        for r in range(ROWS):
            grid[c].append(Cell(c, r))
    
    # Place food
    grid[FOOD_C][FOOD_R].food_amount = 10
    
    # Initialize ants
    ants = [Ant() for _ in range(MAX_ANTS)]
    
    running = True
    frame_count = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Handle mouse for obstacles
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if mouse_pressed:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            mouse_c = mouse_x // CELL_WIDTH
            mouse_r = mouse_y // CELL_HEIGHT
            if 0 <= mouse_c < COLUMNS and 0 <= mouse_r < ROWS:
                grid[mouse_c][mouse_r].obstacle = True
        
        # Clear screen
        screen.fill((220, 220, 220))
        
        # Step and draw the grid
        for c in range(COLUMNS):
            for r in range(ROWS):
                if frame_count % max(1, 60 // ANT_FRAME_RATE) == 0:
                    grid[c][r].step()
                grid[c][r].draw(screen)
        
        # Step and draw the ants
        for ant in ants:
            if frame_count % max(1, 60 // ANT_FRAME_RATE) == 0:
                ant.step(grid)
            ant.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
        frame_count += 1
    
    pygame.quit()


if __name__ == "__main__":
    main()