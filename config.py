class Config:
    # ===== WINDOW & RENDERING =====
    SCREENWIDTH = 700
    SCREENHEIGHT = 700
    FPS = 30
    BACKGROUND_COLOR = (175, 150, 120)
    GRID_LINE_COLOR = (75, 75, 75)
    
    # ===== GRID =====
    CELL_SIZE = 7  
    # Derived values (will be calculated)
    # GRID_COLS = SCREENWIDTH // CELL_SIZE
    # GRID_ROWS = SCREENHEIGHT // CELL_SIZE
    
    # ===== ANT COLONY =====
    NEST_RADIUS = 3
    NUM_ANTS = 200  # Few ants for testing

    # ===== FOOD SETTINGS =====
    FOOD_CLUSTER_RADIUS = 10
    FOOD_CLUSTER_DENSITY = 1
    FOOD_PER_CELL = 5
    FOOD_CLUSTER_INFLUENCE_RADIUS_MULT = 4
    FOOD_COLOR = (0, 180, 0)  # Green
    
    # ===== FOOD FOR TESTING =====
    TEST_FOOD_POSITIONS = [
        (10, 10)  # Food cluster 1
        # Food cluster 2
          # Food cluster 3
    ]
    
    # ===== ANT BEHAVIOR =====
    ANT_COLOR = (0, 0, 0)  # BLACK
    ANT_WITH_FOOD_COLOR = (0, 255, 0)  # Green
    
    # ===== ACO PARAMETERS =====
    # These control the ACO probability formula: (pheromone^ALPHA) * (heuristic^BETA)
    ALPHA = 1.0  # Pheromone importance
    BETA = 3.0   # Heuristic importance
    EVAPORATION_RATE = 0.1  # Pheromone evaporation per frame
    DIFFUSION_RATE = 0.1    # Pheromone spread to neighbors
    EVAPORATION_INTERVAL = 10
    DIFFUSION_INTERVAL = 10
    
    # ===== PHEROMONE SETTINGS =====
    PHEROMONE_MAX_DROP_STRENGTH = 15.0
    PHEROMONE_MIN_DROP_STRENGTH = 0.0
    PHEROMONE_DECAY_RATE = 0.995
    PHEROMONE_MAX_STRENGTH = 100.0
    TO_FOOD_PHEROMONE_COLOR = (255, 0, 0)    # RED
    TO_NEST_PHEROMONE_COLOR = (0, 0, 255)  # BLUE
    
    # ===== FOOD SETTINGS =====
    INITIAL_FOOD_SOURCES = 5
    FOOD_PER_SOURCE = 50
    FOOD_COLOR = (0, 255, 0)  # GREEN
    FOOD_RESPAWN = True
    
    # ===== OBSTACLES =====
    OBSTACLE_COLOR = (100, 70, 55)

    # ===== SHOW =====
    SHOW_PHEROMONES = True
    SHOW_ANTS = True
    SHOW_GRID_LINES = False
    
    # ===== DEBUG =====
    PRINT_STATS_EVERY = 100  # Frames (0 to disable)
    

    
    @classmethod
    def calculate_derived(cls):
        """Calculate values that depend on other configs."""
        cls.GRID_COLS = cls.SCREENWIDTH // cls.CELL_SIZE
        cls.GRID_ROWS = cls.SCREENHEIGHT // cls.CELL_SIZE
        cls.NEST_COL = cls.GRID_COLS // 2
        cls.NEST_ROW = cls.GRID_ROWS // 2
        print(f"Grid: {cls.GRID_COLS} x {cls.GRID_ROWS} cells")
        print(f"Nest at: ({cls.NEST_COL}, {cls.NEST_ROW})")


# Add to Config:
class Debug:
    ENABLED = True
    DRAW_ANT_IDS = False
    DRAW_PHEROMONE_VALUES = False
    DRAW_HEURISTIC_VALUES = False
    LOG_MOVEMENT = False