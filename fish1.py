import arcade
import math
import random
from enum import Enum
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Fish Board Game"

# Colors
COLORS = {
    "red": arcade.color.RED,
    "white": arcade.color.WHITE,
    "brown": arcade.color.SADDLE_BROWN,
    "black": arcade.color.BLACK,
    "blue": arcade.color.BLUE,
    "background": arcade.color.DARK_BLUE_GRAY,
    "tile": arcade.color.LIGHT_BLUE,
    "tile_border": arcade.color.DARK_BLUE,
    "highlight": arcade.color.YELLOW,
    "valid_move": arcade.color.LIGHT_GREEN,
    "fish": arcade.color.ORANGE,
    "orange": arcade.color.ORANGE,
    "penguin_body": arcade.color.WHITE,
    "penguin_outline": arcade.color.BLACK
}

# Game constants
HEX_SIZE = 70  # Increased from 55 for larger tiles
HEX_WIDTH = HEX_SIZE * 2
HEX_HEIGHT = HEX_SIZE * math.sqrt(3)

class GameState(Enum):
    SETUP = "setup"
    PLACING_PENGUINS = "placing"
    PLAYING = "playing"
    GAME_OVER = "game_over"

@dataclass
class Player:
    name: str
    color: str
    age: int
    is_ai: bool = False
    fish_count: int = 0
    penguins: List[Tuple[int, int]] = None
    
    def __post_init__(self):
        if self.penguins is None:
            self.penguins = []

@dataclass
class Tile:
    row: int
    col: int
    fish: int
    exists: bool = True

@dataclass
class Move:
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    fish_gained: int
    
class GameStateSnapshot:
    """Represents a complete game state for minimax"""
    def __init__(self, tiles: Dict, penguin_positions: Dict, player_scores: List[int], current_player: int):
        self.tiles = tiles.copy()
        self.penguin_positions = penguin_positions.copy()
        self.player_scores = player_scores.copy()
        self.current_player = current_player

class HexGrid:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.tiles = {}
        self.board_center_x = SCREEN_WIDTH // 2
        self.board_center_y = SCREEN_HEIGHT // 2
        self._generate_tiles()
    
    def _generate_tiles(self):
        """Generate tiles with random fish counts (1-3)"""
        for row in range(self.rows):
            for col in range(self.cols):
                # Randomly remove some tiles for challenge (10% chance)
                if random.random() < 0.1:
                    continue
                fish_count = random.randint(1, 3)
                self.tiles[(row, col)] = Tile(row, col, fish_count)
    
    def get_tile(self, row: int, col: int) -> Optional[Tile]:
        return self.tiles.get((row, col))
    
    def remove_tile(self, row: int, col: int) -> int:
        """Remove tile and return fish count"""
        tile = self.tiles.get((row, col))
        if tile:
            fish = tile.fish
            del self.tiles[(row, col)]
            return fish
        return 0
    
    def hex_to_pixel(self, row: int, col: int) -> Tuple[float, float]:
        """Convert hex coordinates to pixel coordinates - centered on screen"""
        size = HEX_SIZE
        
        # Calculate relative position from grid center
        grid_center_row = self.rows / 2
        grid_center_col = self.cols / 2
        
        # Calculate offset from grid center
        rel_col = col - grid_center_col
        rel_row = row - grid_center_row
        
        # Convert to pixel coordinates with proper hex spacing
        x = self.board_center_x + size * 3/2 * rel_col
        y = self.board_center_y + size * math.sqrt(3) * (rel_row + 0.5 * (col & 1))
        
        return x, y
    
    def pixel_to_hex(self, x: float, y: float) -> Tuple[int, int]:
        """Convert pixel coordinates to hex coordinates"""
        size = HEX_SIZE
        
        # Find the closest hex by checking all possible hexes
        min_distance = float('inf')
        closest_hex = (0, 0)
        
        for (row, col), tile in self.tiles.items():
            hex_x, hex_y = self.hex_to_pixel(row, col)
            distance = math.sqrt((x - hex_x)**2 + (y - hex_y)**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_hex = (row, col)
        
        return closest_hex
    
    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get valid neighboring hex coordinates"""
        neighbors = []
        
        # Hexagonal grid neighbors depend on whether column is even or odd
        if col % 2 == 0:  # Even column
            directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
        else:  # Odd column
            directions = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if (new_row, new_col) in self.tiles:
                neighbors.append((new_row, new_col))
        
        return neighbors

class MinimaxAI:
    """Advanced AI using minimax with alpha-beta pruning"""
    
    def __init__(self, max_depth: int = 4):
        self.max_depth = max_depth
        self.transposition_table = {}
        
    def get_best_move(self, game_state: GameStateSnapshot, grid: HexGrid, player_index: int) -> Optional[Move]:
        """Get the best move using minimax with alpha-beta pruning"""
        self.transposition_table.clear()  # Clear for new search
        
        best_move = None
        best_score = float('-inf')
        
        # Get all possible moves for current player
        possible_moves = self._get_all_moves(game_state, grid, player_index)
        
        if not possible_moves:
            return None
        
        # Evaluate each move
        for move in possible_moves:
            # Apply move
            new_state = self._apply_move(game_state, move, grid)
            
            # Evaluate with minimax
            score = self._minimax(new_state, grid, self.max_depth - 1, 
                                float('-inf'), float('inf'), False, player_index)
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _minimax(self, state: GameStateSnapshot, grid: HexGrid, depth: int, 
                alpha: float, beta: float, is_maximizing: bool, ai_player: int) -> float:
        """Minimax with alpha-beta pruning"""
        
        # Terminal conditions
        if depth == 0:
            return self._evaluate_state(state, ai_player)
        
        # Check transposition table
        state_key = self._get_state_key(state)
        if state_key in self.transposition_table:
            return self.transposition_table[state_key]
        
        current_player = state.current_player
        possible_moves = self._get_all_moves(state, grid, current_player)
        
        # No moves available - game over
        if not possible_moves:
            score = self._evaluate_state(state, ai_player)
            self.transposition_table[state_key] = score
            return score
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in possible_moves:
                new_state = self._apply_move(state, move, grid)
                eval_score = self._minimax(new_state, grid, depth - 1, alpha, beta, False, ai_player)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            
            self.transposition_table[state_key] = max_eval
            return max_eval
        else:
            min_eval = float('inf')
            for move in possible_moves:
                new_state = self._apply_move(state, move, grid)
                eval_score = self._minimax(new_state, grid, depth - 1, alpha, beta, True, ai_player)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            
            self.transposition_table[state_key] = min_eval
            return min_eval
    
    def _get_all_moves(self, state: GameStateSnapshot, grid: HexGrid, player_index: int) -> List[Move]:
        """Get all possible moves for a player"""
        moves = []
        
        # Find all penguins belonging to this player
        player_penguins = [pos for pos, pi in state.penguin_positions.items() if pi == player_index]
        
        for penguin_pos in player_penguins:
            valid_moves = self._get_valid_moves(state, grid, penguin_pos)
            
            for move_pos in valid_moves:
                # Calculate fish gained
                from_row, from_col = penguin_pos
                tile = state.tiles.get((from_row, from_col))
                fish_gained = tile.fish if tile else 0
                
                moves.append(Move(penguin_pos, move_pos, fish_gained))
        
        return moves
    
    def _get_valid_moves(self, state: GameStateSnapshot, grid: HexGrid, start_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid moves for a penguin from given position"""
        start_row, start_col = start_pos
        valid_moves = []
        
        # Check all 6 directions
        neighbors = grid.get_neighbors(start_row, start_col)
        
        for neighbor_row, neighbor_col in neighbors:
            # Can't move to occupied tiles
            if (neighbor_row, neighbor_col) in state.penguin_positions:
                continue
            
            # Can't move to non-existent tiles
            if (neighbor_row, neighbor_col) not in state.tiles:
                continue
            
            # Trace the line in this direction
            current_row, current_col = neighbor_row, neighbor_col
            
            while True:
                # Add current position as valid move
                if (current_row, current_col) in state.tiles:
                    valid_moves.append((current_row, current_col))
                
                # Find next position in same direction
                next_positions = grid.get_neighbors(current_row, current_col)
                next_row = next_col = None
                
                # Calculate direction vector
                dr1 = neighbor_row - start_row
                dc1 = neighbor_col - start_col
                
                # Find the position that continues the line
                for nr, nc in next_positions:
                    dr2 = nr - current_row  
                    dc2 = nc - current_col
                    
                    # Check if direction is consistent
                    if dr1 == dr2 and dc1 == dc2:
                        next_row, next_col = nr, nc
                        break
                
                if (next_row is None or 
                    (next_row, next_col) not in state.tiles or 
                    (next_row, next_col) in state.penguin_positions):
                    break
                
                current_row, current_col = next_row, next_col
        
        return valid_moves
    
    def _apply_move(self, state: GameStateSnapshot, move: Move, grid: HexGrid) -> GameStateSnapshot:
        """Apply a move and return new game state"""
        new_tiles = state.tiles.copy()
        new_positions = state.penguin_positions.copy()
        new_scores = state.player_scores.copy()
        
        # Remove penguin from old position
        player_index = new_positions[move.from_pos]
        del new_positions[move.from_pos]
        
        # Remove tile and add fish to score
        if move.from_pos in new_tiles:
            del new_tiles[move.from_pos]
        new_scores[player_index] += move.fish_gained
        
        # Place penguin at new position
        new_positions[move.to_pos] = player_index
        
        # Next player (simplified - assumes 2 players)
        next_player = (state.current_player + 1) % 2
        
        return GameStateSnapshot(new_tiles, new_positions, new_scores, next_player)
    
    def _evaluate_state(self, state: GameStateSnapshot, ai_player: int) -> float:
        """Evaluate game state from AI's perspective"""
        opponent = 1 - ai_player
        
        # Basic score difference
        score_diff = state.player_scores[ai_player] - state.player_scores[opponent]
        
        # Count available moves for each player
        ai_moves = len(self._get_all_moves(state, None, ai_player)) if hasattr(self, '_temp_grid') else 0
        opponent_moves = len(self._get_all_moves(state, None, opponent)) if hasattr(self, '_temp_grid') else 0
        
        # Mobility advantage
        mobility_advantage = (ai_moves - opponent_moves) * 0.5
        
        # Positional advantage - prefer positions near high-value tiles
        position_value = 0
        ai_penguins = [pos for pos, pi in state.penguin_positions.items() if pi == ai_player]
        
        for penguin_pos in ai_penguins:
            # Value based on potential future fish
            row, col = penguin_pos
            for (tr, tc), tile in state.tiles.items():
                if (tr, tc) not in state.penguin_positions:
                    distance = abs(tr - row) + abs(tc - col)
                    if distance <= 3:  # Only consider nearby tiles
                        position_value += tile.fish / (distance + 1)
        
        return score_diff + mobility_advantage + position_value * 0.1
    
    def _get_state_key(self, state: GameStateSnapshot) -> str:
        """Generate a key for the transposition table"""
        # Create a hashable representation of the game state
        tiles_key = tuple(sorted(state.tiles.keys()))
        positions_key = tuple(sorted(state.penguin_positions.items()))
        scores_key = tuple(state.player_scores)
        
        return f"{tiles_key}_{positions_key}_{scores_key}_{state.current_player}"

class FishGame(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color(COLORS["background"])
        
        # Game state
        self.game_state = GameState.SETUP
        self.players = []
        self.current_player_index = 0
        self.selected_penguin = None
        self.valid_moves = []
        
        # Board
        self.grid = None
        self.penguin_positions = {}  # (row, col) -> player_index
        
        # AI
        self.ai = MinimaxAI(max_depth=4)
        
        # UI elements
        self.info_text = ""
        self.debug_click_pos = None  # For debugging clicks
        
        self._setup_game()
    
    def _setup_game(self):
        """Initialize the game"""
        # Create players (Player vs AI)
        self.players = [
            Player("Player", "red", 25, is_ai=False),
            Player("AI", "white", 30, is_ai=True)
        ]
        
        # Sort by age (youngest first)
        self.players.sort(key=lambda p: p.age)
        
        # Create board
        self.grid = HexGrid(4, 6)
        
        # Give each player penguins
        num_penguins = 6 - len(self.players)
        for player in self.players:
            player.penguins = []
        
        self.game_state = GameState.PLACING_PENGUINS
        self.current_player_index = 0
        self.penguins_to_place = num_penguins
        self.info_text = f"{self.players[0].name} place a penguin"
        self.ai_move_timer = 0  # Timer for AI moves
    
    def on_update(self, delta_time: float):
        """Update game state"""
        current_player = self.players[self.current_player_index]
        
        # Handle AI turns
        if current_player.is_ai:
            self.ai_move_timer += delta_time
            
            if self.game_state == GameState.PLACING_PENGUINS and self.ai_move_timer > 1.0:
                self._ai_place_penguin()
                self.ai_move_timer = 0
            elif self.game_state == GameState.PLAYING and self.ai_move_timer > 1.5:
                self._ai_make_move()
                self.ai_move_timer = 0
    
    def on_draw(self):
        """Render the game"""
        self.clear()
        
        # Draw hexagonal tiles
        self._draw_board()
        
        # Draw penguins
        self._draw_penguins()
        
        # Draw valid moves if any
        self._draw_valid_moves()
        
        # Draw UI
        self._draw_ui()
        
        # Debug: show click position
        if self.debug_click_pos:
            x, y = self.debug_click_pos
            arcade.draw_circle_filled(x, y, 5, arcade.color.PURPLE)
    
    def _draw_board(self):
        """Draw the hexagonal board with enhanced graphics"""
        for (row, col), tile in self.grid.tiles.items():
            x, y = self.grid.hex_to_pixel(row, col)
            
            # Create gradient effect for water tiles
            tile_color = (135, 206, 250)  # Light sky blue
            border_color = (25, 25, 112)  # Midnight blue
            
            # Draw hexagon with gradient-like effect
            self._draw_hexagon(x, y, HEX_SIZE, tile_color, border_color, 3)
            
            # Draw inner hexagon for depth effect
            inner_color = (173, 216, 230)  # Light blue
            self._draw_hexagon(x, y, HEX_SIZE - 8, inner_color, None, 0)
            
            # Draw fish symbols based on count
            self._draw_fish_on_tile(x, y, tile.fish)
    
    def _draw_fish_on_tile(self, x: float, y: float, fish_count: int):
        """Draw fish symbols on a tile"""
        fish_positions = [
            [(0, 0)],  # 1 fish - center
            [(-12, 0), (12, 0)],  # 2 fish - left and right
            [(-15, -8), (15, -8), (0, 10)]  # 3 fish - triangle formation
        ]
        
        if fish_count > 0 and fish_count <= 3:
            positions = fish_positions[fish_count - 1]
            
            for fx, fy in positions:
                fish_x = x + fx
                fish_y = y + fy
                
                # Draw simple fish shape
                self._draw_fish(fish_x, fish_y, 8)
    
    def _draw_fish(self, x: float, y: float, size: float):
        """Draw a simple fish symbol"""
        # Fish body (oval)
        arcade.draw_ellipse_filled(x, y, size * 1.5, size, COLORS["fish"])
        arcade.draw_ellipse_outline(x, y, size * 1.5, size, arcade.color.DARK_ORANGE, 1)
        
        # Fish tail (triangle)
        tail_points = [
            (x - size * 0.8, y),
            (x - size * 1.3, y - size * 0.4),
            (x - size * 1.3, y + size * 0.4)
        ]
        arcade.draw_polygon_filled(tail_points, COLORS["orange"])
        arcade.draw_polygon_outline(tail_points, arcade.color.DARK_ORANGE, 1)
        
        # Fish eye
        arcade.draw_circle_filled(x + size * 0.3, y + size * 0.2, size * 0.15, arcade.color.BLACK)
    
    def _draw_hexagon(self, x: float, y: float, size: float, fill_color, border_color, border_width: int = 2):
        """Draw a hexagon at given position with enhanced graphics"""
        points = []
        for i in range(6):
            angle = i * math.pi / 3
            px = x + size * math.cos(angle)
            py = y + size * math.sin(angle)
            points.append((px, py))
        
        if fill_color:
            arcade.draw_polygon_filled(points, fill_color)
        if border_color and border_width > 0:
            arcade.draw_polygon_outline(points, border_color, border_width)
    
    def _draw_penguins(self):
        """Draw penguins on the board with enhanced graphics"""
        for (row, col), player_index in self.penguin_positions.items():
            x, y = self.grid.hex_to_pixel(row, col)
            player = self.players[player_index]
            
            # Highlight selected penguin
            if self.selected_penguin == (row, col):
                self._draw_hexagon(x, y, HEX_SIZE + 8, COLORS["highlight"], COLORS["highlight"], 4)
            
            # Draw penguin with better graphics
            self._draw_penguin(x, y, player.color)
    
    def _draw_penguin(self, x: float, y: float, color_name: str):
        """Draw a more detailed penguin - larger size"""
        # Penguin body (main circle) - increased size
        body_color = COLORS[color_name] if color_name == "red" else COLORS["penguin_body"]
        arcade.draw_circle_filled(x, y, 24, body_color)  # Increased from 18
        arcade.draw_circle_outline(x, y, 24, COLORS["penguin_outline"], 3)  # Thicker outline
        
        # Penguin belly (smaller circle)
        belly_color = arcade.color.WHITE if color_name != "white" else (240, 240, 240)
        arcade.draw_circle_filled(x, y - 4, 16, belly_color)  # Increased from 12
        
        # Penguin head (smaller circle on top)
        arcade.draw_circle_filled(x, y + 20, 14, body_color)  # Increased from 10
        arcade.draw_circle_outline(x, y + 20, 14, COLORS["penguin_outline"], 2)
        
        # Eyes - larger
        arcade.draw_circle_filled(x - 4, y + 23, 3, arcade.color.BLACK)  # Increased from 2
        arcade.draw_circle_filled(x + 4, y + 23, 3, arcade.color.BLACK)
        
        # Beak - larger
        beak_points = [
            (x, y + 16),
            (x - 4, y + 11),
            (x + 4, y + 11)
        ]
        arcade.draw_polygon_filled(beak_points, COLORS["orange"])
        
        # Flippers - larger
        arcade.draw_ellipse_filled(x - 22, y + 3, 10, 20, body_color)  # Increased size
        arcade.draw_ellipse_filled(x + 22, y + 3, 10, 20, body_color)
        arcade.draw_ellipse_outline(x - 22, y + 3, 10, 20, COLORS["penguin_outline"], 2)
        arcade.draw_ellipse_outline(x + 22, y + 3, 10, 20, COLORS["penguin_outline"], 2)
    
    def _draw_valid_moves(self):
        """Draw valid move indicators with enhanced graphics"""
        for row, col in self.valid_moves:
            x, y = self.grid.hex_to_pixel(row, col)
            
            # Draw pulsing valid move indicator
            self._draw_hexagon(x, y, HEX_SIZE - 5, (144, 238, 144), COLORS["valid_move"], 3)
            
            # Add arrow or movement indicator
            arcade.draw_circle_filled(x, y, 8, arcade.color.GREEN)
            arcade.draw_text("->", x - 8, y - 6, arcade.color.DARK_GREEN, 10)
    
    def _draw_ui(self):
        """Draw enhanced user interface - positioned in corners"""
        # Top-left corner - Game info
        info_width = 300
        info_height = 120
        arcade.draw_lrbt_rectangle_filled(10, 10 + info_width, SCREEN_HEIGHT - info_height - 10, SCREEN_HEIGHT - 10, (0, 0, 0))
        arcade.draw_lrbt_rectangle_outline(10, 10 + info_width, SCREEN_HEIGHT - info_height - 10, SCREEN_HEIGHT - 10, arcade.color.WHITE, 2)
        
        # Game title
        arcade.draw_text("FISH BOARD GAME", 20, SCREEN_HEIGHT - 30, arcade.color.CYAN, 18)
        
        # Current action info
        arcade.draw_text(self.info_text, 20, SCREEN_HEIGHT - 55, arcade.color.WHITE, 14)
        
        # Player scores with enhanced display
        for i, player in enumerate(self.players):
            color = COLORS[player.color] if player.color in COLORS else arcade.color.WHITE
            prefix = "Human" if not player.is_ai else "AI"
            current_marker = " <- TURN" if i == self.current_player_index else ""
            
            text = f"{prefix}: {player.fish_count} fish{current_marker}"
            arcade.draw_text(text, 20, SCREEN_HEIGHT - 80 - (i * 20), color, 12)
        
        # Bottom-right corner - Rules and controls
        rules_width = 350
        rules_height = 280
        rules_x = SCREEN_WIDTH - rules_width - 10
        rules_y = 10
        
        arcade.draw_lrbt_rectangle_filled(rules_x, SCREEN_WIDTH - 10, rules_y, rules_y + rules_height, (0, 0, 40))
        arcade.draw_lrbt_rectangle_outline(rules_x, SCREEN_WIDTH - 10, rules_y, rules_y + rules_height, arcade.color.LIGHT_BLUE, 2)
        
        # Game state
        state_text = {
            GameState.PLACING_PENGUINS: "SETUP: Place penguins",
            GameState.PLAYING: "GAME: Move penguins",
            GameState.GAME_OVER: "GAME OVER!"
        }
        
        arcade.draw_text("STATUS:", rules_x + 10, rules_y + rules_height - 25, arcade.color.YELLOW, 14)
        arcade.draw_text(state_text.get(self.game_state, ""), rules_x + 10, rules_y + rules_height - 45, arcade.color.WHITE, 12)
        
        # Movement rules
        arcade.draw_text("MOVEMENT RULES:", rules_x + 10, rules_y + rules_height - 75, arcade.color.CYAN, 12)
        
        rules = [
            "• Move in STRAIGHT lines only",
            "• Any distance in one direction", 
            "• CANNOT jump over holes/penguins",
            "• Stops at edge/hole/penguin",
            "• Collect fish from START tile",
            "• Start tile disappears after move"
        ]
        
        for i, rule in enumerate(rules):
            arcade.draw_text(rule, rules_x + 10, rules_y + rules_height - 100 - (i * 16), arcade.color.WHITE, 10)
        
        # Controls
        arcade.draw_text("CONTROLS:", rules_x + 10, rules_y + rules_height - 210, arcade.color.ORANGE, 12)
        controls = [
            "Click tile: Place penguin",
            "Click penguin: Select it",
            "Click green tile: Move there"
        ]
        
        for i, control in enumerate(controls):
            arcade.draw_text(control, rules_x + 10, rules_y + rules_height - 230 - (i * 16), arcade.color.LIGHT_GRAY, 10)
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse clicks"""
        # Debug: store click position
        self.debug_click_pos = (x, y)
        
        # Only process human player clicks
        current_player = self.players[self.current_player_index]
        if current_player.is_ai:
            return
            
        row, col = self.grid.pixel_to_hex(x, y)
        print(f"Clicked at pixel ({x}, {y}) -> hex ({row}, {col})")  # Debug
        
        if self.game_state == GameState.PLACING_PENGUINS:
            self._handle_penguin_placement(row, col)
        elif self.game_state == GameState.PLAYING:
            self._handle_gameplay_click(row, col)
    
    def _handle_penguin_placement(self, row: int, col: int):
        """Handle penguin placement during setup"""
        # Check if tile exists and is empty
        if (row, col) not in self.grid.tiles:
            return
        
        if (row, col) in self.penguin_positions:
            return
        
        self._place_penguin_at(row, col)
    
    def _handle_gameplay_click(self, row: int, col: int):
        """Handle clicks during gameplay"""
        if (row, col) in self.penguin_positions:
            # Clicking on a penguin
            if self.penguin_positions[(row, col)] == self.current_player_index:
                # Select own penguin
                self.selected_penguin = (row, col)
                self.valid_moves = self._get_valid_moves(row, col)
            else:
                # Can't select opponent's penguin
                pass
        elif self.selected_penguin and (row, col) in self.valid_moves:
            # Move selected penguin
            self._move_penguin(self.selected_penguin, (row, col))
            self.selected_penguin = None
            self.valid_moves = []
            self._next_turn()
    
    def _get_valid_moves(self, start_row: int, start_col: int) -> List[Tuple[int, int]]:
        """Get all valid moves for a penguin following strict rules"""
        valid_moves = []
        
        # Get all 6 hexagonal directions from this position
        neighbors = self.grid.get_neighbors(start_row, start_col)
        
        # For each neighboring position, trace a straight line in that direction
        for neighbor_row, neighbor_col in neighbors:
            # Skip if the immediate neighbor is blocked
            if ((neighbor_row, neighbor_col) in self.penguin_positions or 
                (neighbor_row, neighbor_col) not in self.grid.tiles):
                continue  # This direction is immediately blocked
            
            # Calculate the direction vector
            dr = neighbor_row - start_row
            dc = neighbor_col - start_col
            
            # Trace the straight line in this direction
            current_row, current_col = neighbor_row, neighbor_col
            
            while True:
                # Check if current position is valid
                if ((current_row, current_col) in self.grid.tiles and 
                    (current_row, current_col) not in self.penguin_positions):
                    # This is a valid landing spot
                    valid_moves.append((current_row, current_col))
                    
                    # Continue to next position in same direction
                    next_row = current_row + dr
                    next_col = current_col + dc
                    
                    # Check if we can continue (next position exists and is free)
                    if ((next_row, next_col) not in self.grid.tiles or 
                        (next_row, next_col) in self.penguin_positions):
                        # Next position is blocked, stop here
                        break
                    
                    # Move to next position
                    current_row, current_col = next_row, next_col
                else:
                    # Current position is invalid, stop
                    break
        
        return valid_moves
    
    def _move_penguin(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        """Move a penguin and collect fish"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Remove penguin from old position
        player_index = self.penguin_positions.pop(from_pos)
        
        # Collect fish from the tile the penguin was on
        fish_collected = self.grid.remove_tile(from_row, from_col)
        self.players[player_index].fish_count += fish_collected
        
        # Update penguin position
        self.penguin_positions[to_pos] = player_index
        
        # Update player's penguin list
        player = self.players[player_index]
        player.penguins.remove(from_pos)
        player.penguins.append(to_pos)
    
    def _next_turn(self):
        """Move to next player's turn"""
        # Find next player who can move
        original_player = self.current_player_index
        
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            
            # Check if current player can move any penguin
            can_move = False
            for penguin_pos in self.players[self.current_player_index].penguins:
                if self._get_valid_moves(*penguin_pos):
                    can_move = True
                    break
            
            if can_move:
                break
            
            # If we've checked all players and none can move
            if self.current_player_index == original_player:
                self._end_game()
                return
        
        current_player = self.players[self.current_player_index]
        self.info_text = f"{current_player.name}'s turn"
    
    def _ai_place_penguin(self):
        """AI places a penguin strategically"""
        # Find tiles with most fish that are unoccupied
        available_tiles = []
        for (row, col), tile in self.grid.tiles.items():
            if (row, col) not in self.penguin_positions:
                available_tiles.append((tile.fish, row, col))
        
        if not available_tiles:
            return
        
        # Sort by fish count (descending) and add some randomness
        available_tiles.sort(reverse=True)
        
        # Choose from top 3 tiles to add some variety
        top_tiles = available_tiles[:min(3, len(available_tiles))]
        fish_count, row, col = random.choice(top_tiles)
        
        self._place_penguin_at(row, col)
    
    def _ai_make_move(self):
        """AI makes a strategic move using minimax"""
        # Create current game state snapshot
        current_state = GameStateSnapshot(
            self.grid.tiles,
            self.penguin_positions,
            [p.fish_count for p in self.players],
            self.current_player_index
        )
        
        # Get best move from AI
        best_move = self.ai.get_best_move(current_state, self.grid, self.current_player_index)
        
        if best_move:
            self._move_penguin(best_move.from_pos, best_move.to_pos)
            self._next_turn()
    
    def _place_penguin_at(self, row: int, col: int):
        """Place a penguin at specified position (used by both human and AI)"""
        # Place penguin
        self.penguin_positions[(row, col)] = self.current_player_index
        self.players[self.current_player_index].penguins.append((row, col))
        
        # Next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # Check if all penguins placed
        total_penguins = sum(len(p.penguins) for p in self.players)
        expected_penguins = len(self.players) * (6 - len(self.players))
        
        if total_penguins >= expected_penguins:
            self.game_state = GameState.PLAYING
            self.current_player_index = 0
            current_player = self.players[self.current_player_index]
            self.info_text = f"{current_player.name}'s turn"
            self.ai_move_timer = 0
        else:
            current_player = self.players[self.current_player_index]
            self.info_text = f"{current_player.name} place a penguin"
    
    def _end_game(self):
        """End the game and determine winner"""
        self.game_state = GameState.GAME_OVER
        
        # Find winner(s)
        max_fish = max(p.fish_count for p in self.players)
        winners = [p for p in self.players if p.fish_count == max_fish]
        
        if len(winners) == 1:
            self.info_text = f"Game Over! {winners[0].name} wins with {max_fish} fish!"
        else:
            winner_names = ", ".join(p.name for p in winners)
            self.info_text = f"Game Over! Tie between {winner_names} with {max_fish} fish!"

def main():
    """Main function"""
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_view = FishGame()
    window.show_view(game_view)
    arcade.run()

if __name__ == "__main__":
    main()