class Config:
    # ===== WINDOW & RENDERING =====
    SCREENWIDTH = 500
    SCREENHEIGHT = 500
    FPS = 120
    BACKGROUND_COLOR = (255, 255, 255)
    GRID_LINE_COLOR = (150, 150, 150)
    SHOW_GRID_LINES = True  # Toggle grid visualization
    
    # ===== GRID =====
    CELL_SIZE = 5
    # Derived values (will be calculated)
    # GRID_COLS = SCREENWIDTH // CELL_SIZE
    # GRID_ROWS = SCREENHEIGHT // CELL_SIZE
    
    # ===== ANT COLONY =====
    NUM_ANTS = 100  # Few ants for testing
    NEST_COL = None
    NEST_ROW = None

    # ===== FOOD SETTINGS =====
    INITIAL_FOOD_CLUSTERS = 1
    FOOD_CLUSTER_RADIUS = 10
    FOOD_CLUSTER_DENSITY = 0.5
    FOOD_PER_CELL = 1
    FOOD_CLUSTER_INFLUENCE_RADIUS_MULT = 5
    FOOD_COLOR = (0, 180, 0)  # Green
    
    # ===== FOOD FOR TESTING =====
    TEST_FOOD_POSITIONS = [
        (10, 10)  # Food cluster 1
        # Food cluster 2
          # Food cluster 3
    ]
    
    # ===== ANT BEHAVIOR =====
    ANT_SPEED = 1  # Cells per frame when moving
    ANT_VISION_RANGE = 3  # Cells (for future sensing)
    ANT_TURN_PROBABILITY = 0.1  # For random movement phase
    ANT_COLOR = (0, 0, 0)  # White
    ANT_WITH_FOOD_COLOR = (0, 255, 0)  # Green
    
    # ===== ACO PARAMETERS =====
    # These control the ACO probability formula: (pheromone^ALPHA) * (heuristic^BETA)
    ALPHA = 1.0  # Pheromone importance
    BETA = 2.0   # Heuristic importance
    EVAPORATION_RATE = 0.05  # Pheromone evaporation per frame
    DIFFUSION_RATE = 0.1    # Pheromone spread to neighbors
    
    # ===== PHEROMONE SETTINGS =====
    PHEROMONE_DROP_STRENGTH = 10.0
    PHEROMONE_MAX_STRENGTH = 100.0
    TO_FOOD_PHEROMONE_COLOR = (255, 0, 0)    # RED
    TO_NEST_PHEROMONE_COLOR = (0, 0, 255)  # BLUE
    
    # ===== FOOD SETTINGS =====
    INITIAL_FOOD_SOURCES = 5
    FOOD_PER_SOURCE = 50
    FOOD_COLOR = (255, 255, 0)  # YELLOW
    FOOD_RESPAWN = True
    
    # ===== OBSTACLES =====
    OBSTACLE_COLOR = (100, 50, 25)
    
    # ===== VISUALIZATION =====
    DRAW_PHEROMONES = True
    ANT_SIZE_FACTOR = 0.7  # Relative to cell size (0.0-1.0)
    
    # ===== DEBUG =====
    PRINT_STATS_EVERY = 100  # Frames (0 to disable)
    DRAW_ANT_VISION = False
    DRAW_PATH_DEBUG = False
    
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