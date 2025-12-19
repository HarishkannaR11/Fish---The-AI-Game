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
    "valid_move": arcade.color.LIGHT_GREEN
}

# Game constants
HEX_SIZE = 40
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
    
class HexGrid:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.tiles = {}
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
        """Convert hex coordinates to pixel coordinates"""
        # Use proper hex grid positioning
        size = HEX_SIZE
        x = size * 3/2 * col + 100
        y = size * math.sqrt(3) * (row + 0.5 * (col & 1)) + 100
        return x, y
    
    def pixel_to_hex(self, x: float, y: float) -> Tuple[int, int]:
        """Convert pixel coordinates to hex coordinates"""
        # Adjust for board offset
        x -= 100
        y -= 100
        
        # Convert to hex coordinates using proper hex grid math
        size = HEX_SIZE
        
        # Calculate fractional hex coordinates
        q = (x * 2/3) / size
        r = (-x / 3 + y * math.sqrt(3) / 3) / size
        
        # Convert to axial coordinates then to offset
        q_round = round(q)
        r_round = round(r)
        s_round = round(-q - r)
        
        q_diff = abs(q_round - q)
        r_diff = abs(r_round - r) 
        s_diff = abs(s_round - (-q - r))
        
        if q_diff > r_diff and q_diff > s_diff:
            q_round = -r_round - s_round
        elif r_diff > s_diff:
            r_round = -q_round - s_round
        
        # Convert from axial to offset coordinates
        col = q_round
        row = r_round + (q_round - (q_round & 1)) // 2
        
        return int(row), int(col)
    
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
        """Draw the hexagonal board"""
        for (row, col), tile in self.grid.tiles.items():
            x, y = self.grid.hex_to_pixel(row, col)
            
            # Draw hexagon
            self._draw_hexagon(x, y, HEX_SIZE, COLORS["tile"], COLORS["tile_border"])
            
            # Draw fish count
            arcade.draw_text(str(tile.fish), x - 10, y - 10, arcade.color.BLACK, 16)
    
    def _draw_hexagon(self, x: float, y: float, size: float, fill_color, border_color):
        """Draw a hexagon at given position"""
        points = []
        for i in range(6):
            angle = i * math.pi / 3
            px = x + size * math.cos(angle)
            py = y + size * math.sin(angle)
            points.append((px, py))
        
        arcade.draw_polygon_filled(points, fill_color)
        arcade.draw_polygon_outline(points, border_color, 2)
    
    def _draw_penguins(self):
        """Draw penguins on the board"""
        for (row, col), player_index in self.penguin_positions.items():
            x, y = self.grid.hex_to_pixel(row, col)
            player = self.players[player_index]
            
            # Highlight selected penguin
            if self.selected_penguin == (row, col):
                self._draw_hexagon(x, y, HEX_SIZE + 5, COLORS["highlight"], COLORS["highlight"])
            
            # Draw penguin (simple circle for now)
            arcade.draw_circle_filled(x, y, 15, COLORS[player.color])
            arcade.draw_circle_outline(x, y, 15, arcade.color.BLACK, 2)
    
    def _draw_valid_moves(self):
        """Draw valid move indicators"""
        for row, col in self.valid_moves:
            x, y = self.grid.hex_to_pixel(row, col)
            self._draw_hexagon(x, y, HEX_SIZE - 5, COLORS["valid_move"], COLORS["valid_move"])
    
    def _draw_ui(self):
        """Draw user interface"""
        y_offset = SCREEN_HEIGHT - 50
        
        # Game info
        arcade.draw_text(self.info_text, 10, y_offset, arcade.color.WHITE, 18)
        
        # Player scores
        y_offset -= 30
        for i, player in enumerate(self.players):
            text = f"{player.name}: {player.fish_count} fish"
            if i == self.current_player_index:
                text += " (Current)"
            arcade.draw_text(text, 10, y_offset - i * 25, COLORS[player.color], 14)
        
        # Game state info
        state_text = {
            GameState.PLACING_PENGUINS: f"Placing penguins ({self.penguins_to_place} left)",
            GameState.PLAYING: "Playing - Select penguin to move",
            GameState.GAME_OVER: "Game Over!"
        }
        arcade.draw_text(state_text.get(self.game_state, ""), 10, 50, arcade.color.WHITE, 16)
    
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
        """Get all valid moves for a penguin"""
        valid_moves = []
        
        # Check all 6 directions
        neighbors = self.grid.get_neighbors(start_row, start_col)
        
        for neighbor_row, neighbor_col in neighbors:
            # Can't move to occupied tiles
            if (neighbor_row, neighbor_col) in self.penguin_positions:
                continue
            
            # Trace the line in this direction
            current_row, current_col = neighbor_row, neighbor_col
            
            while True:
                # Add current position as valid move
                if (current_row, current_col) in self.grid.tiles:
                    valid_moves.append((current_row, current_col))
                
                # Find next position in same direction
                next_positions = self.grid.get_neighbors(current_row, current_col)
                next_row = next_col = None
                
                # Find the position that continues the line
                for nr, nc in next_positions:
                    dr1 = neighbor_row - start_row
                    dc1 = neighbor_col - start_col
                    dr2 = nr - current_row  
                    dc2 = nc - current_col
                    
                    # Check if direction is consistent (simplified)
                    if dr1 == dr2 and dc1 == dc2:
                        next_row, next_col = nr, nc
                        break
                
                if (next_row is None or 
                    (next_row, next_col) not in self.grid.tiles or 
                    (next_row, next_col) in self.penguin_positions):
                    break
                
                current_row, current_col = next_row, next_col
        
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
        """AI makes a strategic move"""
        current_player = self.players[self.current_player_index]
        best_move = None
        best_score = -1
        
        # Evaluate all possible moves
        for penguin_pos in current_player.penguins:
            valid_moves = self._get_valid_moves(*penguin_pos)
            
            for move_pos in valid_moves:
                score = self._evaluate_move(penguin_pos, move_pos)
                if score > best_score:
                    best_score = score
                    best_move = (penguin_pos, move_pos)
        
        if best_move:
            from_pos, to_pos = best_move
            self._move_penguin(from_pos, to_pos)
            self._next_turn()
    
    def _evaluate_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> float:
        """Evaluate the quality of a move for AI"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Base score is the fish on the tile we're leaving
        tile = self.grid.get_tile(from_row, from_col)
        score = tile.fish if tile else 0
        
        # Bonus for moving to positions with more future moves
        future_moves = len(self._get_valid_moves(to_row, to_col))
        score += future_moves * 0.5
        
        # Bonus for staying near high-fish tiles
        neighbors = self.grid.get_neighbors(to_row, to_col)
        for nr, nc in neighbors:
            neighbor_tile = self.grid.get_tile(nr, nc)
            if neighbor_tile and (nr, nc) not in self.penguin_positions:
                score += neighbor_tile.fish * 0.2
        
        # Penalty for moving too far from other penguins (stay connected)
        min_distance = float('inf')
        for other_penguin_pos in self.players[self.current_player_index].penguins:
            if other_penguin_pos != from_pos:
                dist = self._hex_distance(to_pos, other_penguin_pos)
                min_distance = min(min_distance, dist)
        
        if min_distance != float('inf'):
            score += max(0, 5 - min_distance) * 0.3
        
        return score
    
    def _hex_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate distance between two hex positions"""
        r1, c1 = pos1
        r2, c2 = pos2
        
        # Convert to cube coordinates for easier distance calculation
        x1 = c1 - (r1 - (r1 & 1)) // 2
        z1 = r1
        y1 = -x1 - z1
        
        x2 = c2 - (r2 - (r2 & 1)) // 2
        z2 = r2
        y2 = -x2 - z2
        
        return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) // 2
    
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


