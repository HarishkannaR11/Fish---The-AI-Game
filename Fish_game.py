import arcade
import math
import random
from enum import Enum
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import copy

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Fish Board Game"

# Colors
COLORS = {
    "red": arcade.color.RED,
    "yellow": arcade.color.YELLOW,
    "blue": arcade.color.BLUE,
    "green": arcade.color.GREEN,
    "white": arcade.color.WHITE,
    "brown": arcade.color.SADDLE_BROWN,
    "black": arcade.color.BLACK,
    "background": (65, 105, 225),  # Royal blue from the image
    "tile": arcade.color.LIGHT_BLUE,
    "tile_border": arcade.color.DARK_BLUE,
    "highlight": arcade.color.YELLOW,
    "valid_move": arcade.color.LIGHT_GREEN,
    "button": arcade.color.GRAY,
    "button_hover": arcade.color.LIGHT_GRAY,
    "button_text": arcade.color.BLACK,
    "panel": (40, 40, 60, 200),
    "panel_border": arcade.color.LIGHT_BLUE
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

# UI Enhancement Classes
class FishParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(2, 5)
        self.lifetime = 1.0
        self.size = random.uniform(3, 6)
    
    def update(self, delta_time):
        self.x += self.vx
        self.y += self.vy
        self.vy -= 0.2  # Gravity
        self.lifetime -= delta_time
        return self.lifetime > 0
    
    def draw(self):
        arcade.draw_circle_filled(self.x, self.y, self.size, arcade.color.ORANGE)

class FloatingNumber:
    def __init__(self, x, y, value, color):
        self.x = x
        self.y = y
        self.value = value
        self.color = color
        self.lifetime = 1.0
        self.vy = 2.0
    
    def update(self, delta_time):
        self.y += self.vy
        self.lifetime -= delta_time
        return self.lifetime > 0
    
    def draw(self):
        alpha = int(255 * self.lifetime)
        color_with_alpha = (*self.color[:3], alpha)
        arcade.draw_text(f"+{self.value}", self.x, self.y,
                        color_with_alpha, 16, anchor_x="center")

class Button:
    def __init__(self, x, y, width, height, text, color=COLORS["button"], 
                 hover_color=COLORS["button_hover"], text_color=COLORS["button_text"]):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
        self.callback = None
    
    def draw(self):
        # Draw button background
        color = self.hover_color if self.hovered else self.color
        arcade.draw_lbwh_rectangle_filled(
            self.x, self.y,
            self.width, self.height,
            color
        )
        
        # Draw button border
        arcade.draw_lbwh_rectangle_outline(
            self.x, self.y,
            self.width, self.height,
            arcade.color.WHITE, 2
        )
        
        # Draw button text
        arcade.draw_text(
            self.text,
            self.x + self.width / 2,
            self.y + self.height / 2,
            self.text_color,
            font_size=16,
            anchor_x="center", anchor_y="center"
        )
    
    def check_hover(self, x, y):
        self.hovered = (
            self.x <= x <= self.x + self.width and
            self.y <= y <= self.y + self.height
        )
        return self.hovered
    
    def check_click(self, x, y):
        if self.check_hover(x, y):
            if self.callback:
                self.callback()
            return True
        return False

def draw_sunburst_background():
    """Draw a sunburst background with blue rays emanating from the center"""
    # Base background color
    arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, COLORS["background"])
    
    # Center of the screen
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2
    
    # Maximum radius for the rays
    max_radius = max(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.7
    
    # Number of rays
    num_rays = 72  # More rays for a smoother effect
    
    # Different shades of blue for the rays
    blue_shades = [
        (65, 105, 225),    # Original royal blue
        (85, 125, 245),    # Lighter blue
        (105, 145, 255),   # Even lighter blue
        (125, 165, 255),   # Very light blue
        (45, 85, 205),     # Darker blue
        (25, 65, 185)      # Even darker blue
    ]
    
    # Draw rays
    for i in range(num_rays):
        # Calculate angle for this ray
        angle = i * (360 / num_rays)
        angle_rad = math.radians(angle)
        
        # Calculate end point of the ray
        end_x = center_x + max_radius * math.cos(angle_rad)
        end_y = center_y + max_radius * math.sin(angle_rad)
        
        # Calculate width of the ray at the end (wider at the edges)
        ray_width = 20 + (i % 3) * 10
        
        # Calculate perpendicular angle for ray width
        perp_angle = angle_rad + math.pi / 2
        
        # Calculate the four corners of the ray (trapezoid shape)
        near1_x = center_x + 5 * math.cos(perp_angle)
        near1_y = center_y + 5 * math.sin(perp_angle)
        near2_x = center_x - 5 * math.cos(perp_angle)
        near2_y = center_y - 5 * math.sin(perp_angle)
        
        far1_x = end_x + ray_width * math.cos(perp_angle)
        far1_y = end_y + ray_width * math.sin(perp_angle)
        far2_x = end_x - ray_width * math.cos(perp_angle)
        far2_y = end_y - ray_width * math.sin(perp_angle)
        
        # Select color for this ray (cycle through the blue shades)
        color_index = i % len(blue_shades)
        color = (*blue_shades[color_index], 100)  # Add transparency
        
        # Draw the ray as a polygon
        arcade.draw_polygon_filled(
            [
                (near1_x, near1_y),
                (near2_x, near2_y),
                (far2_x, far2_y),
                (far1_x, far1_y)
            ],
            color
        )
    
    # Draw a bright center point
    arcade.draw_circle_filled(center_x, center_y, 30, (135, 206, 250, 180))  # Light sky blue with transparency
    arcade.draw_circle_filled(center_x, center_y, 15, (173, 216, 230, 200))  # Even lighter blue

def draw_large_penguin(x, y, color, scale=2.0):
    """Draw a large penguin with distinctive player colors"""
    # Body (black oval)
    arcade.draw_ellipse_filled(x, y - 2 * scale, 20 * scale, 28 * scale, arcade.color.BLACK)
    
    # White belly
    arcade.draw_ellipse_filled(x, y - 2 * scale, 12 * scale, 20 * scale, arcade.color.WHITE)
    
    # Head (black circle)
    arcade.draw_circle_filled(x, y + 12 * scale, 10 * scale, arcade.color.BLACK)
    
    # White face patch
    arcade.draw_ellipse_filled(x - 3 * scale, y + 12 * scale, 6 * scale, 8 * scale, arcade.color.WHITE)
    arcade.draw_ellipse_filled(x + 3 * scale, y + 12 * scale, 6 * scale, 8 * scale, arcade.color.WHITE)
    
    # Eyes
    arcade.draw_circle_filled(x - 3 * scale, y + 14 * scale, 2 * scale, arcade.color.BLACK)
    arcade.draw_circle_filled(x + 3 * scale, y + 14 * scale, 2 * scale, arcade.color.BLACK)
    arcade.draw_circle_filled(x - 2 * scale, y + 15 * scale, 1 * scale, arcade.color.WHITE)
    arcade.draw_circle_filled(x + 4 * scale, y + 15 * scale, 1 * scale, arcade.color.WHITE)
    
    # Beak (orange triangle)
    beak_points = [
        (x, y + 11 * scale),
        (x - 2 * scale, y + 9 * scale),
        (x + 2 * scale, y + 9 * scale)
    ]
    arcade.draw_polygon_filled(beak_points, arcade.color.ORANGE)
    
    # Feet (orange)
    arcade.draw_ellipse_filled(x - 5 * scale, y - 16 * scale, 6 * scale, 4 * scale, arcade.color.ORANGE)
    arcade.draw_ellipse_filled(x + 5 * scale, y - 16 * scale, 6 * scale, 4 * scale, arcade.color.ORANGE)
    
    # Wings
    arcade.draw_ellipse_filled(x - 10 * scale, y, 8 * scale, 12 * scale, arcade.color.BLACK)
    arcade.draw_ellipse_filled(x + 10 * scale, y, 8 * scale, 12 * scale, arcade.color.BLACK)
    
    # Player color indicator - distinctive features for each color
    if color == COLORS["red"]:
        # RED PLAYER: Red scarf and hat
        arcade.draw_ellipse_filled(x, y + 5 * scale, 22 * scale, 8 * scale, arcade.color.RED)
        arcade.draw_ellipse_outline(x, y + 5 * scale, 22 * scale, 8 * scale, arcade.color.DARK_RED, 2)
        # Red hat
        arcade.draw_circle_filled(x, y + 20 * scale, 7 * scale, arcade.color.RED)
        arcade.draw_circle_outline(x, y + 20 * scale, 7 * scale, arcade.color.DARK_RED, 2)
        # Pompom
        arcade.draw_circle_filled(x, y + 25 * scale, 3 * scale, arcade.color.WHITE)
    elif color == COLORS["yellow"]:
        # YELLOW PLAYER: Yellow bowtie and cap
        # Bowtie
        bowtie_points = [
            (x - 8 * scale, y + 5 * scale),
            (x - 3 * scale, y + 5 * scale),
            (x, y + 8 * scale),
            (x, y + 2 * scale),
            (x - 8 * scale, y + 5 * scale)
        ]
        arcade.draw_polygon_filled(bowtie_points, arcade.color.YELLOW)
        arcade.draw_polygon_outline(bowtie_points, arcade.color.GOLD, 2)
        
        bowtie_points2 = [
            (x + 8 * scale, y + 5 * scale),
            (x + 3 * scale, y + 5 * scale),
            (x, y + 8 * scale),
            (x, y + 2 * scale),
            (x + 8 * scale, y + 5 * scale)
        ]
        arcade.draw_polygon_filled(bowtie_points2, arcade.color.YELLOW)
        arcade.draw_polygon_outline(bowtie_points2, arcade.color.GOLD, 2)
        
        # Center knot
        arcade.draw_circle_filled(x, y + 5 * scale, 3 * scale, arcade.color.GOLD)
        
        # Yellow cap
        arcade.draw_circle_filled(x, y + 20 * scale, 7 * scale, arcade.color.YELLOW)
        arcade.draw_circle_outline(x, y + 20 * scale, 7 * scale, arcade.color.GOLD, 2)
    elif color == COLORS["blue"]:
        # BLUE PLAYER: Blue scarf and hat
        arcade.draw_ellipse_filled(x, y + 5 * scale, 22 * scale, 8 * scale, arcade.color.BLUE)
        arcade.draw_ellipse_outline(x, y + 5 * scale, 22 * scale, 8 * scale, arcade.color.DARK_BLUE, 2)
        # Blue hat
        arcade.draw_circle_filled(x, y + 20 * scale, 7 * scale, arcade.color.BLUE)
        arcade.draw_circle_outline(x, y + 20 * scale, 7 * scale, arcade.color.DARK_BLUE, 2)
        # Pompom
        arcade.draw_circle_filled(x, y + 25 * scale, 3 * scale, arcade.color.WHITE)
    elif color == COLORS["green"]:
        # GREEN PLAYER: Green bowtie and cap
        # Bowtie
        bowtie_points = [
            (x - 8 * scale, y + 5 * scale),
            (x - 3 * scale, y + 5 * scale),
            (x, y + 8 * scale),
            (x, y + 2 * scale),
            (x - 8 * scale, y + 5 * scale)
        ]
        arcade.draw_polygon_filled(bowtie_points, arcade.color.GREEN)
        arcade.draw_polygon_outline(bowtie_points, arcade.color.DARK_GREEN, 2)
        
        bowtie_points2 = [
            (x + 8 * scale, y + 5 * scale),
            (x + 3 * scale, y + 5 * scale),
            (x, y + 8 * scale),
            (x, y + 2 * scale),
            (x + 8 * scale, y + 5 * scale)
        ]
        arcade.draw_polygon_filled(bowtie_points2, arcade.color.GREEN)
        arcade.draw_polygon_outline(bowtie_points2, arcade.color.DARK_GREEN, 2)
        
        # Center knot
        arcade.draw_circle_filled(x, y + 5 * scale, 3 * scale, arcade.color.DARK_GREEN)
        
        # Green cap
        arcade.draw_circle_filled(x, y + 20 * scale, 7 * scale, arcade.color.GREEN)
        arcade.draw_circle_outline(x, y + 20 * scale, 7 * scale, arcade.color.DARK_GREEN, 2)

class HowToPlayView(arcade.View):
    def __init__(self, landing_view):
        super().__init__()
        self.landing_view = landing_view
        
        # Load penguin image
        self.penguin_image = None
        try:
            self.penguin_image = arcade.load_texture(
                "https://z-cdn-media.chatglm.cn/files/2d1aeac8-ea06-4039-b86f-906755501741_pasted_image_1759774637246.png?auth_key=1791310739-9754ac2d6be24762b1c42511a7f27501-0-abc8f5afdf6a49707b0c1e4ba37c1808"
            )
        except:
            self.penguin_image = None
        
        # UI elements
        self.back_button = Button(50, 50, 100, 40, "Back")
        self.back_button.callback = self.on_back
    
    def on_back(self):
        self.window.show_view(self.landing_view)
    
    def on_draw(self):
        # Draw sunburst background
        draw_sunburst_background()
        
        # Draw semi-transparent overlay for content
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 
                                        (0, 0, 0, 200))
        
        # Draw title
        arcade.draw_text("HOW TO PLAY", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                        arcade.color.LIGHT_YELLOW, 32, anchor_x="center", bold=True)
        
        # Draw instructions
        instructions = [
            "1. SETUP",
            "   - Select the number of players (2-4)",
            "   - Each player chooses a unique color",
            "   - Players take turns placing their penguins on tiles",
            "",
            "2. GAMEPLAY",
            "   - Players take turns moving one of their penguins",
            "   - Penguins move like a chess queen in straight lines",
            "   - They cannot jump over holes or other penguins",
            "   - When a penguin leaves a tile, the tile is removed",
            "   - The player collects the fish from that tile",
            "",
            "3. WINNING",
            "   - The game ends when no player can move",
            "   - The player with the most fish wins!"
        ]
        
        y_pos = SCREEN_HEIGHT - 150
        for line in instructions:
            arcade.draw_text(line, SCREEN_WIDTH // 2, y_pos,
                            arcade.color.WHITE, 16, anchor_x="center")
            y_pos -= 30
        
        # Draw back button
        self.back_button.draw()
        
        # Draw penguin image on the right side
        if self.penguin_image:
            penguin_x = SCREEN_WIDTH - 100
            penguin_y = SCREEN_HEIGHT // 2
            scale = 0.4
            arcade.draw_texture_rectangle(
                penguin_x, penguin_y,
                self.penguin_image.width * scale,
                self.penguin_image.height * scale,
                self.penguin_image
            )
        else:
            # Fallback to drawn penguin
            draw_large_penguin(SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2, COLORS["blue"], scale=2.0)
    
    def on_mouse_press(self, x, y, button, modifiers):
        self.back_button.check_click(x, y)

class SettingsView(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.minimax_depth = game_view.minimax_depth
        
        # Load penguin image
        self.penguin_image = None
        try:
            self.penguin_image = arcade.load_texture(
                "https://z-cdn-media.chatglm.cn/files/2d1aeac8-ea06-4039-b86f-906755501741_pasted_image_1759774637246.png?auth_key=1791310739-9754ac2d6be24762b1c42511a7f27501-0-abc8f5afdf6a49707b0c1e4ba37c1808"
            )
        except:
            self.penguin_image = None
        
        # UI elements
        self.back_button = Button(50, 50, 100, 40, "Back")
        self.back_button.callback = self.on_back
        
        self.depth_buttons = []
        for i in range(1, 6):
            x = SCREEN_WIDTH // 2 - 100 + (i-1) * 50
            y = SCREEN_HEIGHT // 2
            btn = Button(x, y, 40, 40, str(i))
            btn.callback = lambda depth=i: self.set_depth(depth)
            self.depth_buttons.append(btn)
    
    def set_depth(self, depth):
        self.minimax_depth = depth
        self.game_view.minimax_depth = depth
    
    def on_back(self):
        self.window.show_view(self.game_view)
    
    def on_draw(self):
        # Draw sunburst background
        draw_sunburst_background()
        
        # Draw semi-transparent overlay for content
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 
                                        (0, 0, 0, 200))
        
        # Draw title
        arcade.draw_text("SETTINGS", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                        arcade.color.LIGHT_YELLOW, 32, anchor_x="center", bold=True)
        
        # Draw minimax depth options
        arcade.draw_text("AI Difficulty (Minimax Depth):", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50,
                        arcade.color.WHITE, 16, anchor_x="center")
        
        # Draw buttons
        self.back_button.draw()
        for btn in self.depth_buttons:
            # Highlight current depth
            if int(btn.text) == self.minimax_depth:
                arcade.draw_lbwh_rectangle_filled(
                    btn.x - 5, btn.y - 5,
                    btn.width + 10, btn.height + 10,
                    COLORS["highlight"]
                )
            btn.draw()
        
        # Draw penguin image on the right side
        if self.penguin_image:
            penguin_x = SCREEN_WIDTH - 100
            penguin_y = SCREEN_HEIGHT // 2
            scale = 0.4
            arcade.draw_texture_rectangle(
                penguin_x, penguin_y,
                self.penguin_image.width * scale,
                self.penguin_image.height * scale,
                self.penguin_image
            )
    
    def on_mouse_press(self, x, y, button, modifiers):
        self.back_button.check_click(x, y)
        for btn in self.depth_buttons:
            btn.check_click(x, y)

class LandingPageView(arcade.View):
    def __init__(self):
        super().__init__()
        
        # Load the background image
        self.background = None
        try:
            # Try to load the image from the provided URL
            self.background = arcade.load_texture(
                "https://z-cdn-media.chatglm.cn/files/2d1aeac8-ea06-4039-b86f-906755501741_pasted_image_1759774637246.png?auth_key=1791310739-9754ac2d6be24762b1c42511a7f27501-0-abc8f5afdf6a49707b0c1e4ba37c1808"
            )
        except:
            # If loading fails, use a solid color background
            self.background = None
        
        # Load penguin image for right side
        self.penguin_image = None
        try:
            self.penguin_image = arcade.load_texture(
                "https://z-cdn-media.chatglm.cn/files/2d1aeac8-ea06-4039-b86f-906755501741_pasted_image_1759774637246.png?auth_key=1791310739-9754ac2d6be24762b1c42511a7f27501-0-abc8f5afdf6a49707b0c1e4ba37c1808"
            )
        except:
            self.penguin_image = None
        
        # Game setup state
        self.num_players = 2
        self.player_colors = ["red", "yellow", "blue", "green"]
        self.selected_colors = [None, None, None, None]
        self.penguin_counts = {
            2: 4,
            3: 3,
            4: 2
        }
        
        # UI elements
        self.player_buttons = []
        self.color_buttons = []
        self.start_button = None
        self.how_to_play_button = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI elements for the landing page"""
        # Title
        self.title_text = arcade.Text(
            "HEY, THAT'S MY FISH!",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 100,
            arcade.color.LIGHT_YELLOW,
            font_size=48,
            anchor_x="center",
            bold=True
        )
        
        # Player selection buttons - now on the left side
        button_width = 100
        button_height = 50
        button_spacing = 20
        start_x = 50
        start_y = SCREEN_HEIGHT - 200
        
        self.player_buttons = []
        for i, num in enumerate([2, 3, 4]):
            x = start_x
            y = start_y - i * (button_height + button_spacing)
            
            button = Button(
                x=x,
                y=y,
                width=button_width,
                height=button_height,
                text=f"{num} Players"
            )
            button.callback = lambda n=num: self.on_player_count_click(n)
            self.player_buttons.append(button)
        
        # Player color selection area
        self.color_buttons = []
        self.update_color_selection()
        
        # Start button
        self.start_button = Button(
            x=SCREEN_WIDTH / 2 - 100,
            y=100,
            width=200,
            height=60,
            text="START GAME"
        )
        self.start_button.callback = self.on_start_game
        
        # How to Play button
        self.how_to_play_button = Button(
            x=SCREEN_WIDTH / 2 - 100,
            y=170,
            width=200,
            height=50,
            text="HOW TO PLAY"
        )
        self.how_to_play_button.callback = self.on_how_to_play
    
    def on_how_to_play(self):
        """Open the How to Play view"""
        how_to_view = HowToPlayView(self)
        self.window.show_view(how_to_view)
    
    def update_color_selection(self):
        """Update the color selection UI based on number of players"""
        self.color_buttons = []
        
        # Setup color selection for each player
        player_width = 250
        player_height = 200
        start_x = SCREEN_WIDTH / 2 - (self.num_players * player_width + (self.num_players - 1) * 20) / 2
        start_y = SCREEN_HEIGHT - 350
        
        for player_idx in range(self.num_players):
            x = start_x + player_idx * (player_width + 20)
            
            # Color selection buttons
            color_size = 40
            color_spacing = 10
            colors_start_x = x + (player_width - (4 * color_size + 3 * color_spacing)) / 2
            colors_start_y = start_y + 80
            
            for color_idx, color_name in enumerate(self.player_colors):
                color_x = colors_start_x + color_idx * (color_size + color_spacing)
                color_y = colors_start_y
                
                # Create a color button
                button = Button(
                    x=color_x,
                    y=color_y,
                    width=color_size,
                    height=color_size,
                    text="",
                    color=COLORS[color_name]
                )
                button.callback = lambda p_idx=player_idx, c_idx=color_idx: self.on_color_select(p_idx, c_idx)
                
                # Store the button with its position
                self.color_buttons.append((button, color_name, player_idx))
    
    def on_player_count_click(self, num):
        """Handle player count selection"""
        self.num_players = num
        self.selected_colors = [None, None, None, None]
        self.update_color_selection()
    
    def on_color_select(self, player_idx, color_idx):
        """Handle color selection for a player"""
        color_name = self.player_colors[color_idx]
        
        # Check if color is already selected by another player
        for i in range(self.num_players):
            if i != player_idx and self.selected_colors[i] == color_name:
                return  # Color already taken
        
        # Set the color for this player
        self.selected_colors[player_idx] = color_name
    
    def on_start_game(self):
        """Handle start game button click"""
        # Check if all players have selected a color
        for i in range(self.num_players):
            if self.selected_colors[i] is None:
                return  # Not all players have selected a color
        
        # Create players with selected colors
        players = []
        for i in range(self.num_players):
            player = Player(
                name=f"Player {i+1}",
                color=self.selected_colors[i],
                age=25 + i,
                is_ai=(i > 0)
            )
            players.append(player)
        
        # Create the game view with the selected players
        game_view = FishGame(players)
        self.window.show_view(game_view)
    
    def on_draw(self):
        """Draw the landing page"""
        # Draw sunburst background
        draw_sunburst_background()
        
        # Draw background image or fallback color
        if self.background:
            # Draw the background image to cover the entire screen
            arcade.draw_texture_rectangle(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                SCREEN_WIDTH, SCREEN_HEIGHT,
                self.background
            )
        
        # Draw title with shadow for better visibility
        arcade.draw_text(
            "HEY, THAT'S MY FISH!",
            SCREEN_WIDTH / 2 + 2,
            SCREEN_HEIGHT - 102,
            arcade.color.BLACK,
            font_size=48,
            anchor_x="center",
            bold=True
        )
        self.title_text.draw()
        
        # Draw player count buttons on the left side
        for button in self.player_buttons:
            # Highlight selected button
            if int(button.text.split()[0]) == self.num_players:
                arcade.draw_lbwh_rectangle_filled(
                    button.x - 5, button.y - 5,
                    button.width + 10, button.height + 10,
                    COLORS["highlight"]
                )
            button.draw()
        
        # Draw "Select Players" label with background for better visibility
        arcade.draw_lbwh_rectangle_filled(
            50, SCREEN_HEIGHT - 130,
            100, 30,
            (0, 0, 0, 150)
        )
        arcade.draw_text(
            "Select Players",
            100,
            SCREEN_HEIGHT - 120,
            arcade.color.LIGHT_YELLOW,
            font_size=18,
            anchor_x="center",
            bold=True
        )
        
        # Draw player panels
        player_width = 250
        player_height = 200
        start_x = SCREEN_WIDTH / 2 - (self.num_players * player_width + (self.num_players - 1) * 20) / 2
        start_y = SCREEN_HEIGHT - 350
        
        for player_idx in range(self.num_players):
            x = start_x + player_idx * (player_width + 20)
            
            # Draw panel with semi-transparent background for better visibility
            panel_points = [
                (x, start_y),
                (x + player_width, start_y),
                (x + player_width, start_y + player_height),
                (x, start_y + player_height)
            ]
            arcade.draw_polygon_filled(panel_points, (0, 0, 0, 180))
            arcade.draw_polygon_outline(panel_points, COLORS["panel_border"], 3)
            
            # Draw player label
            arcade.draw_text(
                f"Player {player_idx + 1}",
                x + player_width / 2,
                start_y + player_height - 30,
                arcade.color.WHITE,
                font_size=20,
                anchor_x="center"
            )
            
            # Draw penguin count
            penguin_count = self.penguin_counts[self.num_players]
            arcade.draw_text(
                f"Penguins: {penguin_count}",
                x + player_width / 2,
                start_y + player_height - 60,
                arcade.color.LIGHT_YELLOW,
                font_size=16,
                anchor_x="center"
            )
            
            # Draw color buttons
            for button, color_name, _ in self.color_buttons:
                if _ == player_idx:  # Only draw buttons for this player
                    # Highlight selected color
                    if self.selected_colors[player_idx] == color_name:
                        arcade.draw_lbwh_rectangle_filled(
                            button.x - 3, button.y - 3,
                            button.width + 6, button.height + 6,
                            COLORS["highlight"]
                        )
                    
                    # Disable button if color is taken by another player
                    is_taken = False
                    for j in range(self.num_players):
                        if j != player_idx and self.selected_colors[j] == color_name:
                            is_taken = True
                            break
                    
                    if is_taken:
                        # Draw disabled button
                        arcade.draw_lbwh_rectangle_filled(
                            button.x, button.y,
                            button.width, button.height,
                            (100, 100, 100, 128)
                        )
                        arcade.draw_lbwh_rectangle_outline(
                            button.x, button.y,
                            button.width, button.height,
                            arcade.color.DARK_GRAY, 2
                        )
                    else:
                        button.draw()
        
        # Draw start button
        # Check if all players have selected colors
        all_selected = all(self.selected_colors[i] is not None for i in range(self.num_players))
        if all_selected:
            self.start_button.draw()
        else:
            # Draw disabled start button
            arcade.draw_lbwh_rectangle_filled(
                self.start_button.x, self.start_button.y,
                self.start_button.width, self.start_button.height,
                (100, 100, 100, 128)
            )
            arcade.draw_lbwh_rectangle_outline(
                self.start_button.x, self.start_button.y,
                self.start_button.width, self.start_button.height,
                arcade.color.DARK_GRAY, 2
            )
            arcade.draw_text(
                "START GAME",
                self.start_button.x + self.start_button.width / 2,
                self.start_button.y + self.start_button.height / 2,
                arcade.color.DARK_GRAY,
                font_size=16,
                anchor_x="center", anchor_y="center"
            )
        
        # Draw How to Play button
        self.how_to_play_button.draw()
        
        # Draw instructions with background for better visibility
        # instructions = [
        #     "1. Select the number of players",
        #     "2. Each player chooses a unique penguin color",
        #     "3. Click START GAME to begin"
        # ]
        
        # y_pos = 300
        # for instruction in instructions:
        #     # Draw background text
        #     arcade.draw_text(
        #         instruction,
        #         SCREEN_WIDTH / 2 + 1,
        #         y_pos - 1,
        #         arcade.color.BLACK,
        #         font_size=18,
        #         anchor_x="center"
        #     )
        #     # Draw foreground text
        #     arcade.draw_text(
        #         instruction,
        #         SCREEN_WIDTH / 2,
        #         y_pos,
        #         arcade.color.LIGHT_YELLOW,
        #         font_size=18,
        #         anchor_x="center"
        #     )
        #     y_pos -= 30
        
        # Draw penguin image on the right side
        if self.penguin_image:
            penguin_x = SCREEN_WIDTH - 150
            penguin_y = SCREEN_HEIGHT // 2
            scale = 0.6
            arcade.draw_texture_rectangle(
                penguin_x, penguin_y,
                self.penguin_image.width * scale,
                self.penguin_image.height * scale,
                self.penguin_image
            )
            
            # Add a speech bubble for the penguin
            bubble_x = penguin_x - 120
            bubble_y = penguin_y + 80
            bubble_width = 200
            bubble_height = 60
            
            # Draw speech bubble
            arcade.draw_lbwh_rectangle_filled(
                bubble_x, bubble_y,
                bubble_width, bubble_height,
                arcade.color.WHITE
            )
            arcade.draw_lbwh_rectangle_outline(
                bubble_x, bubble_y,
                bubble_width, bubble_height,
                arcade.color.BLACK, 2
            )
            
            # Draw speech bubble tail
            tail_points = [
                (bubble_x + bubble_width - 20, bubble_y + bubble_height),
                (bubble_x + bubble_width - 40, bubble_y + bubble_height + 20),
                (bubble_x + bubble_width - 60, bubble_y + bubble_height)
            ]
            arcade.draw_polygon_filled(tail_points, arcade.color.WHITE)
            arcade.draw_polygon_outline(tail_points, arcade.color.BLACK, 2)
            
            # Draw text in speech bubble
            arcade.draw_text(
                "Let's go fishing!",
                bubble_x + bubble_width // 2,
                bubble_y + bubble_height // 2,
                arcade.color.BLACK,
                font_size=14,
                anchor_x="center", anchor_y="center"
            )
        else:
            # Fallback to drawn penguin
            draw_large_penguin(SCREEN_WIDTH - 150, SCREEN_HEIGHT // 2, COLORS["blue"], scale=2.5)
            
            # Add a speech bubble for the penguin
            bubble_x = SCREEN_WIDTH - 270
            bubble_y = SCREEN_HEIGHT // 2 + 80
            bubble_width = 200
            bubble_height = 60
            
            # Draw speech bubble
            arcade.draw_lbwh_rectangle_filled(
                bubble_x, bubble_y,
                bubble_width, bubble_height,
                arcade.color.WHITE
            )
            arcade.draw_lbwh_rectangle_outline(
                bubble_x, bubble_y,
                bubble_width, bubble_height,
                arcade.color.BLACK, 2
            )
            
            # Draw speech bubble tail
            tail_points = [
                (bubble_x + bubble_width - 20, bubble_y + bubble_height),
                (bubble_x + bubble_width - 40, bubble_y + bubble_height + 20),
                (bubble_x + bubble_width - 60, bubble_y + bubble_height)
            ]
            arcade.draw_polygon_filled(tail_points, arcade.color.WHITE)
            arcade.draw_polygon_outline(tail_points, arcade.color.BLACK, 2)
            
            # Draw text in speech bubble
            arcade.draw_text(
                "Let's go fishing!",
                bubble_x + bubble_width // 2,
                bubble_y + bubble_height // 2,
                arcade.color.BLACK,
                font_size=14,
                anchor_x="center", anchor_y="center"
            )
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Handle mouse motion for button hover effects"""
        # Check player buttons
        for button in self.player_buttons:
            button.check_hover(x, y)
        
        # Check color buttons
        for button, _, _ in self.color_buttons:
            button.check_hover(x, y)
        
        # Check start button
        self.start_button.check_hover(x, y)
        
        # Check how to play button
        self.how_to_play_button.check_hover(x, y)
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse clicks"""
        # Check player buttons
        for btn in self.player_buttons:
            if btn.check_click(x, y):
                return
        
        # Check color buttons
        for btn, _, _ in self.color_buttons:
            if btn.check_click(x, y):
                return
        
        # Check start button
        self.start_button.check_click(x, y)
        
        # Check how to play button
        self.how_to_play_button.check_click(x, y)

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
        size = HEX_SIZE
        # Calculate board dimensions
        board_width = size * 3/2 * (self.cols - 1) + size * 2
        board_height = size * math.sqrt(3) * (self.rows + 0.5)
        
        # Center the board
        offset_x = (SCREEN_WIDTH - board_width) / 2
        offset_y = (SCREEN_HEIGHT - board_height) / 2 + 50
        
        x = size * 3/2 * col + offset_x
        y = size * math.sqrt(3) * (row + 0.5 * (col & 1)) + offset_y
        return x, y
    
    def pixel_to_hex(self, x: float, y: float) -> Tuple[int, int]:
        """Convert pixel coordinates to hex coordinates"""
        size = HEX_SIZE
        
        # Calculate board dimensions and offsets (same as hex_to_pixel)
        board_width = size * 3/2 * (self.cols - 1) + size * 2
        board_height = size * math.sqrt(3) * (self.rows + 0.5)
        offset_x = (SCREEN_WIDTH - board_width) / 2
        offset_y = (SCREEN_HEIGHT - board_height) / 2 + 50
        
        # Adjust for board offset
        x -= offset_x
        y -= offset_y
        
        # Convert to hex coordinates using proper hex grid math
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
    
    def get_direction_neighbors(self, row: int, col: int) -> List[Tuple[int, int, int, int]]:
        """Get neighbors with their direction deltas for straight-line movement"""
        if col % 2 == 0:  # Even column
            directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
        else:  # Odd column
            directions = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
        
        result = []
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            result.append((new_row, new_col, dr, dc))
        
        return result

class GameOverView(arcade.View):
    """View shown when the game is over, displaying the winner"""
    def __init__(self, winners, game_view):
        super().__init__()
        self.winners = winners
        self.game_view = game_view
        
        # Load penguin image
        self.penguin_image = None
        try:
            self.penguin_image = arcade.load_texture(
                "https://z-cdn-media.chatglm.cn/files/2d1aeac8-ea06-4039-b86f-906755501741_pasted_image_1759774637246.png?auth_key=1791310739-9754ac2d6be24762b1c42511a7f27501-0-abc8f5afdf6a49707b0c1e4ba37c1808"
            )
        except:
            self.penguin_image = None
        
        # Store popup and button positions for consistent drawing and click detection
        self.popup_width = 500
        self.popup_height = 300
        self.popup_x = (SCREEN_WIDTH - self.popup_width) / 2
        self.popup_y = (SCREEN_HEIGHT - self.popup_height) / 2
        
        self.button_width = 200
        self.button_height = 50
        self.button_x = (SCREEN_WIDTH - self.button_width) / 2
        self.button_y = self.popup_y + 50
        
    def on_draw(self):
        # Draw sunburst background
        draw_sunburst_background()
        
        # Draw semi-transparent overlay
        arcade.draw_lbwh_rectangle_filled(
            0, 0,
            SCREEN_WIDTH, SCREEN_HEIGHT,
            (0, 0, 0, 180)
        )
        
        # Draw popup background
        arcade.draw_lbwh_rectangle_filled(
            self.popup_x, self.popup_y,
            self.popup_width, self.popup_height,
            COLORS["panel"]
        )
        
        arcade.draw_lbwh_rectangle_outline(
            self.popup_x, self.popup_y,
            self.popup_width, self.popup_height,
            COLORS["panel_border"], 3
        )
        
        # Draw title
        arcade.draw_text(
            "GAME OVER",
            SCREEN_WIDTH / 2,
            self.popup_y + self.popup_height - 50,
            arcade.color.LIGHT_YELLOW,
            font_size=36,
            anchor_x="center",
            bold=True
        )
        
        # Draw winner(s)
        if len(self.winners) == 1:
            winner_text = f"{self.winners[0].name} WINS!"
            fish_text = f"with {self.winners[0].fish_count} fish"
        else:
            winner_names = ", ".join(p.name for p in self.winners)
            winner_text = f"TIE: {winner_names}"
            fish_text = f"with {self.winners[0].fish_count} fish each"
        
        arcade.draw_text(
            winner_text,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 + 30,
            arcade.color.WHITE,
            font_size=28,
            anchor_x="center",
            bold=True
        )
        
        arcade.draw_text(
            fish_text,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 - 20,
            arcade.color.ORANGE,
            font_size=22,
            anchor_x="center"
        )
        
        # Draw play again button
        arcade.draw_lbwh_rectangle_filled(
            self.button_x, self.button_y,
            self.button_width, self.button_height,
            COLORS["button"]
        )
        
        arcade.draw_lbwh_rectangle_outline(
            self.button_x, self.button_y,
            self.button_width, self.button_height,
            arcade.color.WHITE, 2
        )
        
        arcade.draw_text(
            "PLAY AGAIN",
            self.button_x + self.button_width / 2,
            self.button_y + self.button_height / 2,
            arcade.color.WHITE,
            font_size=18,
            anchor_x="center",
            anchor_y="center"
        )
        
        # Draw penguin image on the right side
        if self.penguin_image:
            penguin_x = SCREEN_WIDTH - 100
            penguin_y = SCREEN_HEIGHT // 2
            scale = 0.4
            arcade.draw_texture_rectangle(
                penguin_x, penguin_y,
                self.penguin_image.width * scale,
                self.penguin_image.height * scale,
                self.penguin_image
            )
    
    def on_mouse_press(self, x, y, button, modifiers):
        # Check if play again button was clicked
        if (self.button_x <= x <= self.button_x + self.button_width and 
            self.button_y <= y <= self.button_y + self.button_height):
            # Return to landing page
            landing_view = LandingPageView()
            self.window.show_view(landing_view)

class FishGame(arcade.View):
    def __init__(self, players=None):
        super().__init__()
        arcade.set_background_color(COLORS["background"])
        
        # Game state
        self.game_state = GameState.SETUP
        self.players = players if players else []
        self.current_player_index = 0
        self.selected_penguin = None
        self.valid_moves = []
        
        # Board
        self.grid = None
        self.penguin_positions = {}  # (row, col) -> player_index
        
        # UI elements
        self.info_text = ""
        self.debug_click_pos = None  # For debugging clicks
        
        # Minimax settings
        self.minimax_depth = 3  # Depth for minimax search
        
        # UI Enhancements
        self.animation_queue = []  # Queue of (from_pos, to_pos, player_index)
        self.current_animation = None  # (start_pos, end_pos, progress, player_index)
        self.animation_speed = 0.05  # Animation speed
        self.fish_particles = []
        self.floating_numbers = []
        self.move_history = []  # List of (player_name, from_pos, to_pos, fish_collected)
        self.hovered_tile = None
        self.settings_button = Button(SCREEN_WIDTH - 70, 20, 50, 30, "⚙")
        self.settings_button.callback = self.open_settings
        
        # Load penguin image
        self.penguin_image = None
        try:
            self.penguin_image = arcade.load_texture(
                "https://z-cdn-media.chatglm.cn/files/2d1aeac8-ea06-4039-b86f-906755501741_pasted_image_1759774637246.png?auth_key=1791310739-9754ac2d6be24762b1c42511a7f27501-0-abc8f5afdf6a49707b0c1e4ba37c1808"
            )
        except:
            self.penguin_image = None
        
        self._setup_game()
    
    def _setup_game(self):
        """Initialize the game"""
        # If no players provided, create default players
        if not self.players:
            # Create players (Player vs AI)
            self.players = [
                Player("Player", "red", 25, is_ai=False),
                Player("AI", "yellow", 30, is_ai=True)
            ]
        
        # Sort by age (youngest first)
        self.players.sort(key=lambda p: p.age)
        
        # Create board
        self.grid = HexGrid(6, 8)
        
        # Give each player penguins
        num_penguins = 6 - len(self.players)
        for player in self.players:
            player.penguins = []
        
        self.game_state = GameState.PLACING_PENGUINS
        self.current_player_index = 0
        self.penguins_to_place = num_penguins
        self.info_text = f"{self.players[0].name} place a penguin"
        self.ai_move_timer = 0  # Timer for AI moves
    
    def open_settings(self):
        settings_view = SettingsView(self)
        self.window.show_view(settings_view)
    
    def on_update(self, delta_time: float):
        """Update game state"""
        current_player = self.players[self.current_player_index]
        
        # Handle animations
        if self.current_animation:
            start_pos, end_pos, progress, player_index = self.current_animation
            progress += self.animation_speed
            
            if progress >= 1.0:
                # Animation complete
                self._complete_move(start_pos, end_pos, player_index)
                self.current_animation = None
                
                # Start next animation if any
                if self.animation_queue:
                    next_anim = self.animation_queue.pop(0)
                    self.current_animation = (next_anim[0], next_anim[1], 0.0, next_anim[2])
            else:
                # Update animation progress
                self.current_animation = (start_pos, end_pos, progress, player_index)
        
        # Update particles
        self.fish_particles = [p for p in self.fish_particles if p.update(delta_time)]
        self.floating_numbers = [fn for fn in self.floating_numbers if fn.update(delta_time)]
        
        # Handle AI turns
        if current_player.is_ai and not self.current_animation:
            self.ai_move_timer += delta_time
            
            if self.game_state == GameState.PLACING_PENGUINS and self.ai_move_timer > 1.0:
                self._ai_place_penguin()
                self.ai_move_timer = 0
            elif self.game_state == GameState.PLAYING and self.ai_move_timer > 1.5:
                self._ai_make_move()
                self.ai_move_timer = 0
    
    def on_draw(self):
        """Render the game"""
        # Draw sunburst background
        draw_sunburst_background()
        
        # Draw hexagonal tiles
        self._draw_board()
        
        # Draw penguins
        self._draw_penguins()
        
        # Draw valid moves if any
        self._draw_valid_moves()
        
        # Draw fish particles
        for particle in self.fish_particles:
            particle.draw()
        
        # Draw floating numbers
        for number in self.floating_numbers:
            number.draw()
        
        # Draw UI
        self._draw_ui()
        
        # Draw penguin image on the right side
        if self.penguin_image:
            penguin_x = SCREEN_WIDTH - 100
            penguin_y = SCREEN_HEIGHT // 2
            scale = 0.4
            arcade.draw_texture_rectangle(
                penguin_x, penguin_y,
                self.penguin_image.width * scale,
                self.penguin_image.height * scale,
                self.penguin_image
            )
        
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
            
            # Draw fish using simple fish shapes
            self._draw_fish(x, y, tile.fish)
        
        # Draw hovered tile highlight
        if self.hovered_tile:
            row, col = self.hovered_tile
            if (row, col) in self.grid.tiles:
                x, y = self.grid.hex_to_pixel(row, col)
                self._draw_hexagon(x, y, HEX_SIZE + 3, 
                                  (*COLORS["highlight"][:3], 100), 
                                  COLORS["highlight"])
    
    def _draw_fish(self, x: float, y: float, count: int):
        """Draw fish icons on the tile"""
        fish_positions = [
            [(0, 0)],  # 1 fish - center
            [(-12, 0), (12, 0)],  # 2 fish - side by side
            [(-12, 8), (12, 8), (0, -8)]  # 3 fish - triangle
        ]
        
        if count < 1 or count > 3:
            return
        
        positions = fish_positions[count - 1]
        
        for dx, dy in positions:
            fish_x = x + dx
            fish_y = y + dy
            
            # Draw simple fish shape
            # Body (ellipse)
            arcade.draw_ellipse_filled(fish_x, fish_y, 16, 8, arcade.color.ORANGE)
            
            # Tail (triangle)
            tail_points = [
                (fish_x - 8, fish_y),
                (fish_x - 12, fish_y + 4),
                (fish_x - 12, fish_y - 4)
            ]
            arcade.draw_polygon_filled(tail_points, arcade.color.ORANGE)
            
            # Eye
            arcade.draw_circle_filled(fish_x + 4, fish_y + 1, 2, arcade.color.BLACK)
            
            # Outline
            arcade.draw_ellipse_outline(fish_x, fish_y, 16, 8, arcade.color.DARK_ORANGE, 1)
    
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
    
    def _draw_penguin(self, x: float, y: float, color):
        """Draw a detailed penguin with distinct player colors"""
        # Body (black oval)
        arcade.draw_ellipse_filled(x, y - 2, 20, 28, arcade.color.BLACK)
        
        # White belly
        arcade.draw_ellipse_filled(x, y - 2, 12, 20, arcade.color.WHITE)
        
        # Head (black circle)
        arcade.draw_circle_filled(x, y + 12, 10, arcade.color.BLACK)
        
        # White face patch
        arcade.draw_ellipse_filled(x - 3, y + 12, 6, 8, arcade.color.WHITE)
        arcade.draw_ellipse_filled(x + 3, y + 12, 6, 8, arcade.color.WHITE)
        
        # Eyes
        arcade.draw_circle_filled(x - 3, y + 14, 2, arcade.color.BLACK)
        arcade.draw_circle_filled(x + 3, y + 14, 2, arcade.color.BLACK)
        arcade.draw_circle_filled(x - 2, y + 15, 1, arcade.color.WHITE)
        arcade.draw_circle_filled(x + 4, y + 15, 1, arcade.color.WHITE)
        
        # Beak (orange triangle)
        beak_points = [
            (x, y + 11),
            (x - 2, y + 9),
            (x + 2, y + 9)
        ]
        arcade.draw_polygon_filled(beak_points, arcade.color.ORANGE)
        
        # Feet (orange)
        arcade.draw_ellipse_filled(x - 5, y - 16, 6, 4, arcade.color.ORANGE)
        arcade.draw_ellipse_filled(x + 5, y - 16, 6, 4, arcade.color.ORANGE)
        
        # Wings
        arcade.draw_ellipse_filled(x - 10, y, 8, 12, arcade.color.BLACK)
        arcade.draw_ellipse_filled(x + 10, y, 8, 12, arcade.color.BLACK)
        
        # Player color indicator - distinctive features for each color
        if color == COLORS["red"]:
            # RED PLAYER: Red scarf and hat
            arcade.draw_ellipse_filled(x, y + 5, 22, 8, arcade.color.RED)
            arcade.draw_ellipse_outline(x, y + 5, 22, 8, arcade.color.DARK_RED, 2)
            # Red hat
            arcade.draw_circle_filled(x, y + 20, 7, arcade.color.RED)
            arcade.draw_circle_outline(x, y + 20, 7, arcade.color.DARK_RED, 2)
            # Pompom
            arcade.draw_circle_filled(x, y + 25, 3, arcade.color.WHITE)
        elif color == COLORS["yellow"]:
            # YELLOW PLAYER: Yellow bowtie and cap
            # Bowtie
            bowtie_points = [
                (x - 8, y + 5),
                (x - 3, y + 5),
                (x, y + 8),
                (x, y + 2),
                (x - 8, y + 5)
            ]
            arcade.draw_polygon_filled(bowtie_points, arcade.color.YELLOW)
            arcade.draw_polygon_outline(bowtie_points, arcade.color.GOLD, 2)
            
            bowtie_points2 = [
                (x + 8, y + 5),
                (x + 3, y + 5),
                (x, y + 8),
                (x, y + 2),
                (x + 8, y + 5)
            ]
            arcade.draw_polygon_filled(bowtie_points2, arcade.color.YELLOW)
            arcade.draw_polygon_outline(bowtie_points2, arcade.color.GOLD, 2)
            
            # Center knot
            arcade.draw_circle_filled(x, y + 5, 3, arcade.color.GOLD)
            
            # Yellow cap
            arcade.draw_circle_filled(x, y + 20, 7, arcade.color.YELLOW)
            arcade.draw_circle_outline(x, y + 20, 7, arcade.color.GOLD, 2)
        elif color == COLORS["blue"]:
            # BLUE PLAYER: Blue scarf and hat
            arcade.draw_ellipse_filled(x, y + 5, 22, 8, arcade.color.BLUE)
            arcade.draw_ellipse_outline(x, y + 5, 22, 8, arcade.color.DARK_BLUE, 2)
            # Blue hat
            arcade.draw_circle_filled(x, y + 20, 7, arcade.color.BLUE)
            arcade.draw_circle_outline(x, y + 20, 7, arcade.color.DARK_BLUE, 2)
            # Pompom
            arcade.draw_circle_filled(x, y + 25, 3, arcade.color.WHITE)
        elif color == COLORS["green"]:
            # GREEN PLAYER: Green bowtie and cap
            # Bowtie
            bowtie_points = [
                (x - 8, y + 5),
                (x - 3, y + 5),
                (x, y + 8),
                (x, y + 2),
                (x - 8, y + 5)
            ]
            arcade.draw_polygon_filled(bowtie_points, arcade.color.GREEN)
            arcade.draw_polygon_outline(bowtie_points, arcade.color.DARK_GREEN, 2)
            
            bowtie_points2 = [
                (x + 8, y + 5),
                (x + 3, y + 5),
                (x, y + 8),
                (x, y + 2),
                (x + 8, y + 5)
            ]
            arcade.draw_polygon_filled(bowtie_points2, arcade.color.GREEN)
            arcade.draw_polygon_outline(bowtie_points2, arcade.color.DARK_GREEN, 2)
            
            # Center knot
            arcade.draw_circle_filled(x, y + 5, 3, arcade.color.DARK_GREEN)
            
            # Green cap
            arcade.draw_circle_filled(x, y + 20, 7, arcade.color.GREEN)
            arcade.draw_circle_outline(x, y + 20, 7, arcade.color.DARK_GREEN, 2)
    
    def _draw_penguins(self):
        """Draw penguins on the board"""
        # Draw static penguins
        for (row, col), player_index in self.penguin_positions.items():
            x, y = self.grid.hex_to_pixel(row, col)
            player = self.players[player_index]
            
            # Highlight selected penguin
            if self.selected_penguin == (row, col):
                self._draw_hexagon(x, y, HEX_SIZE + 5, COLORS["highlight"], COLORS["highlight"])
            
            # Draw detailed penguin
            self._draw_penguin(x, y, COLORS[player.color])
        
        # Draw animating penguin
        if self.current_animation:
            from_pos, to_pos, progress, player_index = self.current_animation
            from_x, from_y = self.grid.hex_to_pixel(*from_pos)
            to_x, to_y = self.grid.hex_to_pixel(*to_pos)
            
            # Interpolate position
            current_x = from_x + (to_x - from_x) * progress
            current_y = from_y + (to_y - from_y) * progress
            
            player = self.players[player_index]
            self._draw_penguin(current_x, current_y, COLORS[player.color])
    
    def _draw_valid_moves(self):
        """Draw valid move indicators"""
        for row, col in self.valid_moves:
            x, y = self.grid.hex_to_pixel(row, col)
            self._draw_hexagon(x, y, HEX_SIZE - 5, COLORS["valid_move"], COLORS["valid_move"])
    
    def _draw_ui(self):
        """Draw user interface with rich panels"""
        # Left panel - Turn info
        panel_width = 250
        panel_height = 200
        panel_x = 20
        panel_y = SCREEN_HEIGHT - panel_height - 20
        
        # Draw left panel background using polygon
        left_panel_points = [
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (panel_x, panel_y + panel_height)
        ]
        arcade.draw_polygon_filled(left_panel_points, (0, 0, 0, 200))
        arcade.draw_polygon_outline(left_panel_points, arcade.color.LIGHT_BLUE, 3)
        
        # Title
        arcade.draw_text("TURN INFO", panel_x + 15, panel_y + panel_height - 35,
                        arcade.color.LIGHT_YELLOW, 16, bold=True)
        arcade.draw_line(panel_x + 10, panel_y + panel_height - 45,
                        panel_x + panel_width - 10, panel_y + panel_height - 45,
                        arcade.color.LIGHT_BLUE, 2)
        
        # Current player info
        y_pos = panel_y + panel_height - 70
        current_player = self.players[self.current_player_index]
        
        # Player indicator with colored circle
        arcade.draw_circle_filled(panel_x + 30, y_pos, 12, COLORS[current_player.color])
        arcade.draw_circle_outline(panel_x + 30, y_pos, 12, arcade.color.WHITE, 2)
        arcade.draw_text(f"{current_player.name}'s Turn", panel_x + 50, y_pos - 8,
                        arcade.color.WHITE, 14, bold=True)
        
        # Game state instructions
        y_pos -= 40
        state_text = {
            GameState.PLACING_PENGUINS: "Place your penguins\non the board",
            GameState.PLAYING: "Select penguin,\nthen move it",
            GameState.GAME_OVER: "Game Finished!"
        }
        instructions = state_text.get(self.game_state, "")
        for i, line in enumerate(instructions.split('\n')):
            arcade.draw_text(line, panel_x + 15, y_pos - i * 20,
                           arcade.color.LIGHT_GRAY, 12)
        
        # Status message
        y_pos -= 50
        arcade.draw_text(self.info_text[:30], panel_x + 15, y_pos,
                        arcade.color.LIGHT_YELLOW, 11)
        if len(self.info_text) > 30:
            arcade.draw_text(self.info_text[30:60], panel_x + 15, y_pos - 15,
                           arcade.color.LIGHT_YELLOW, 11)
        
        # Enhanced score panel with progress bars
        score_panel_width = 300
        score_panel_height = 250
        score_panel_x = SCREEN_WIDTH - score_panel_width - 20
        score_panel_y = SCREEN_HEIGHT - score_panel_height - 20
        
        # Draw panel background
        arcade.draw_lbwh_rectangle_filled(
            score_panel_x, score_panel_y,
            score_panel_width, score_panel_height,
            COLORS["panel"]
        )
        
        # Draw title
        arcade.draw_text("PLAYER STATS", score_panel_x + 15, score_panel_y + score_panel_height - 35,
                        arcade.color.LIGHT_YELLOW, 18, bold=True)
        arcade.draw_line(score_panel_x + 10, score_panel_y + score_panel_height - 45,
                        score_panel_x + score_panel_width - 10, score_panel_y + score_panel_height - 45,
                        arcade.color.LIGHT_BLUE, 2)
        
        # Draw player stats
        y_pos = score_panel_y + score_panel_height - 80
        max_fish = max(p.fish_count for p in self.players) if self.players else 1
        
        for i, player in enumerate(self.players):
            # Player header
            arcade.draw_circle_filled(score_panel_x + 25, y_pos, 12, COLORS[player.color])
            arcade.draw_text(player.name, score_panel_x + 45, y_pos + 5,
                            arcade.color.WHITE, 14, bold=True)
            
            # Fish count with progress bar
            fish_text = f"Fish: {player.fish_count}"
            arcade.draw_text(fish_text, score_panel_x + 45, y_pos - 15,
                            arcade.color.ORANGE, 12)
            
            # Progress bar
            bar_width = 200
            bar_height = 10
            bar_x = score_panel_x + 45
            bar_y = y_pos - 30
            
            # Background
            arcade.draw_lbwh_rectangle_filled(bar_x, bar_y, bar_width, bar_height, (50, 50, 50))
            
            # Progress
            if max_fish > 0:
                progress = player.fish_count / max_fish
                arcade.draw_lbwh_rectangle_filled(bar_x, bar_y, bar_width * progress, bar_height, 
                                                COLORS[player.color])
            
            # Penguin count
            penguin_text = f"Penguins: {len(player.penguins)}"
            arcade.draw_text(penguin_text, score_panel_x + 45, y_pos - 45,
                            arcade.color.LIGHT_BLUE, 11)
            
            # Active indicator
            if i == self.current_player_index:
                arcade.draw_lbwh_rectangle_outline(
                    score_panel_x + 10, y_pos - 50,
                    score_panel_width - 20, 60,
                    arcade.color.YELLOW, 2
                )
            
            y_pos -= 80
        
        # Turn indicator with timer
        turn_indicator_width = 400
        turn_indicator_height = 60
        turn_x = SCREEN_WIDTH // 2 - turn_indicator_width // 2
        turn_y = SCREEN_HEIGHT - 80
        
        # Background
        arcade.draw_lbwh_rectangle_filled(
            turn_x, turn_y, turn_indicator_width, turn_indicator_height,
            COLORS["panel"]
        )
        
        # Current player
        current_player = self.players[self.current_player_index]
        arcade.draw_circle_filled(turn_x + 30, turn_y + turn_indicator_height // 2, 
                               15, COLORS[current_player.color])
        arcade.draw_text(f"{current_player.name}'s Turn", 
                    turn_x + 55, turn_y + turn_indicator_height // 2 + 5,
                    arcade.color.WHITE, 16, bold=True)
        
        # Timer for AI
        if current_player.is_ai:
            timer_width = 150
            timer_height = 10
            timer_x = turn_x + turn_indicator_width - timer_width - 20
            timer_y = turn_y + turn_indicator_height // 2 - 5
            
            # Background
            arcade.draw_lbwh_rectangle_filled(timer_x, timer_y, timer_width, timer_height, (50, 50, 50))
            
            # Progress
            if self.game_state == GameState.PLAYING:
                progress = min(self.ai_move_timer / 1.5, 1.0)
            else:
                progress = min(self.ai_move_timer / 1.0, 1.0)
            
            arcade.draw_lbwh_rectangle_filled(timer_x, timer_y, timer_width * progress, timer_height, 
                                            arcade.color.GREEN)
        
        # Move history panel
        history_width = 250
        history_height = 200
        history_x = 20
        history_y = 20
        
        arcade.draw_lbwh_rectangle_filled(
            history_x, history_y, history_width, history_height,
            COLORS["panel"]
        )
        
        arcade.draw_text("MOVE HISTORY", history_x + 10, history_y + history_height - 30,
                        arcade.color.LIGHT_YELLOW, 14, bold=True)
        
        # Draw recent moves
        y_pos = history_y + history_height - 60
        for i, (player_name, from_pos, to_pos, fish) in enumerate(reversed(self.move_history[-5:])):
            move_text = f"{player_name}: {from_pos} → {to_pos} (+{fish})"
            arcade.draw_text(move_text, history_x + 10, y_pos - i * 25,
                            arcade.color.WHITE, 10)
        
        # Settings button
        self.settings_button.draw()
        
        # Bottom instruction bar
        if self.game_state == GameState.PLAYING:
            instruction_text = "Move like a chess queen - straight lines only!"
            arcade.draw_text(instruction_text, SCREEN_WIDTH/2, 15,
                           arcade.color.LIGHT_YELLOW, 12, anchor_x="center")
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Handle mouse motion for button hover effects and tile highlighting"""
        # Check settings button
        self.settings_button.check_hover(x, y)
        
        # Check if hovering over a tile
        row, col = self.grid.pixel_to_hex(x, y)
        if (row, col) in self.grid.tiles:
            self.hovered_tile = (row, col)
        else:
            self.hovered_tile = None
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse clicks"""
        # Debug: store click position
        self.debug_click_pos = (x, y)
        
        # Check settings button
        self.settings_button.check_click(x, y)
        
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
                self.info_text = f"Selected penguin - click a green tile to move"
            else:
                # Can't select opponent's penguin
                self.info_text = "Cannot select opponent's penguin!"
        elif self.selected_penguin and (row, col) in self.valid_moves:
            # Move selected penguin
            self._start_animation(self.selected_penguin, (row, col))
            self.selected_penguin = None
            self.valid_moves = []
        else:
            if self.selected_penguin:
                self.info_text = "Invalid move! Must move in a straight line without jumping"
    
    def _start_animation(self, from_pos, to_pos):
        """Start an animation for a penguin move"""
        player_index = self.penguin_positions[from_pos]
        
        if not self.current_animation:
            self.current_animation = (from_pos, to_pos, 0.0, player_index)
        else:
            self.animation_queue.append((from_pos, to_pos, player_index))
    
    def _complete_move(self, from_pos, to_pos, player_index):
        """Complete a move after animation"""
        # Actually move the penguin
        self._move_penguin(from_pos, to_pos)
        self._next_turn()
    
    def _get_valid_moves(self, start_row: int, start_col: int) -> List[Tuple[int, int]]:
        """
        Get all valid moves for a penguin following Hey, That's My Fish! rules:
        - Move in straight line in any of 6 hex directions
        - Cannot pass through holes (removed tiles) or other penguins
        - Can move any number of tiles until blocked
        """
        valid_moves = []
        
        # Get all 6 neighboring positions as starting points for each direction
        neighbors = self._get_hex_neighbors_with_direction(start_row, start_col)
        
        # Trace each direction
        for direction_id, (first_row, first_col) in neighbors.items():
            current_row, current_col = first_row, first_col
            
            # Continue in this direction until blocked
            while True:
                # Check if current tile exists
                if (current_row, current_col) not in self.grid.tiles:
                    # Hit a hole or edge, stop this direction
                    break
                
                # Check if current tile is occupied by any penguin
                if (current_row, current_col) in self.penguin_positions:
                    # Hit another penguin, stop this direction
                    break
                
                # This tile is valid - add it to valid moves
                valid_moves.append((current_row, current_col))
                
                # Get next position in the same direction
                next_pos = self._get_next_in_direction(current_row, current_col, direction_id)
                if next_pos is None:
                    break
                
                current_row, current_col = next_pos
        
        return valid_moves
    
    def _get_hex_neighbors_with_direction(self, row: int, col: int) -> Dict[str, Tuple[int, int]]:
        """
        Get the 6 hex neighbors labeled by direction.
        Returns dict mapping direction_id to (row, col)
        """
        if col % 2 == 0:  # Even column
            # For even columns, the neighbors are:
            neighbors = {
                'E': (row, col + 1),      # East
                'NE': (row - 1, col + 1), # Northeast
                'NW': (row - 1, col),     # Northwest
                'W': (row, col - 1),      # West
                'SW': (row + 1, col),     # Southwest
                'SE': (row + 1, col + 1)  # Southeast
            }
        else:  # Odd column
            # For odd columns, the neighbors are:
            neighbors = {
                'E': (row, col + 1),      # East
                'NE': (row - 1, col),     # Northeast
                'NW': (row - 1, col - 1), # Northwest
                'W': (row, col - 1),      # West
                'SW': (row + 1, col - 1), # Southwest
                'SE': (row + 1, col)      # Southeast
            }
        
        return neighbors
    
    def _get_next_in_direction(self, row: int, col: int, direction_id: str) -> Optional[Tuple[int, int]]:
        """
        Given current position and direction, return the next position in that direction.
        Returns None if direction is invalid.
        """
        neighbors = self._get_hex_neighbors_with_direction(row, col)
        return neighbors.get(direction_id)
    
    def _move_penguin(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        """Move a penguin and collect fish"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Remove penguin from old position
        player_index = self.penguin_positions.pop(from_pos)
        
        # Collect fish from the tile the penguin was on
        fish_collected = self.grid.remove_tile(from_row, from_col)
        self.players[player_index].fish_count += fish_collected
        
        # Create fish particles
        from_x, from_y = self.grid.hex_to_pixel(*from_pos)
        for _ in range(fish_collected * 3):
            self.fish_particles.append(FishParticle(from_x, from_y))
        
        # Create floating number
        self.floating_numbers.append(FloatingNumber(from_x, from_y + 20, 
                                                   fish_collected, arcade.color.ORANGE))
        
        # Update penguin position
        self.penguin_positions[to_pos] = player_index
        
        # Update player's penguin list
        player = self.players[player_index]
        player.penguins.remove(from_pos)
        player.penguins.append(to_pos)
        
        # Add to move history
        self.move_history.append((player.name, from_pos, to_pos, fish_collected))
        
        # Keep only last 10 moves
        if len(self.move_history) > 10:
            self.move_history.pop(0)
    
    def _next_turn(self):
        """Move to next player's turn"""
        # Find next player who can move
        original_player = self.current_player_index
        attempts = 0
        
        while attempts < len(self.players):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            attempts += 1
            
            # Check if current player can move any penguin
            can_move = False
            for penguin_pos in self.players[self.current_player_index].penguins:
                if self._get_valid_moves(*penguin_pos):
                    can_move = True
                    break
            
            if can_move:
                current_player = self.players[self.current_player_index]
                self.info_text = f"{current_player.name}'s turn"
                self.ai_move_timer = 0
                return
        
        # No player can move - game over
        self._end_game()
    
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
    
    # ===== MINIMAX IMPLEMENTATION STARTS HERE =====
    
    def _ai_make_move(self):
        """AI makes a move using Minimax algorithm with alpha-beta pruning"""
        # Store the current game state
        original_grid = copy.deepcopy(self.grid)
        original_penguin_positions = copy.deepcopy(self.penguin_positions)
        original_players = copy.deepcopy(self.players)
        original_current_player_index = self.current_player_index
        
        # Find the best move using minimax
        best_score = float('-inf')
        best_move = None
        alpha = float('-inf')
        beta = float('inf')
        
        # Get all possible moves for the current player
        current_player = self.players[self.current_player_index]
        for penguin_pos in current_player.penguins:
            valid_moves = self._get_valid_moves(*penguin_pos)
            
            for move_pos in valid_moves:
                # Make a temporary move
                fish_collected = self._make_temp_move(penguin_pos, move_pos)
                
                # Evaluate the move using minimax
                score = self._minimax(self.minimax_depth - 1, alpha, beta, False)
                
                # Undo the temporary move
                self._undo_temp_move(penguin_pos, move_pos, fish_collected)
                
                # Update best move if this move is better
                if score > best_score:
                    best_score = score
                    best_move = (penguin_pos, move_pos)
                
                # Update alpha for alpha-beta pruning
                alpha = max(alpha, best_score)
        
        # Restore the original game state
        self.grid = original_grid
        self.penguin_positions = original_penguin_positions
        self.players = original_players
        self.current_player_index = original_current_player_index
        
        # Make the best move
        if best_move:
            from_pos, to_pos = best_move
            self._start_animation(from_pos, to_pos)
        else:
            # AI cannot move, skip turn
            self._next_turn()
    
    def _minimax(self, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning"""
        # Check if we've reached the depth limit or game over
        if depth == 0 or self._is_game_over():
            return self._evaluate_board()
        
        current_player = self.players[self.current_player_index]
        
        if maximizing_player:
            max_eval = float('-inf')
            
            # Get all possible moves for the current player
            for penguin_pos in current_player.penguins:
                valid_moves = self._get_valid_moves(*penguin_pos)
                
                for move_pos in valid_moves:
                    # Make a temporary move
                    fish_collected = self._make_temp_move(penguin_pos, move_pos)
                    
                    # Switch to the next player
                    self.current_player_index = (self.current_player_index + 1) % len(self.players)
                    
                    # Recursive minimax call
                    eval_score = self._minimax(depth - 1, alpha, beta, False)
                    
                    # Switch back to the current player
                    self.current_player_index = (self.current_player_index - 1) % len(self.players)
                    
                    # Undo the temporary move
                    self._undo_temp_move(penguin_pos, move_pos, fish_collected)
                    
                    # Update max_eval
                    max_eval = max(max_eval, eval_score)
                    
                    # Update alpha for alpha-beta pruning
                    alpha = max(alpha, eval_score)
                    
                    # Alpha-beta pruning
                    if beta <= alpha:
                        break
            
            return max_eval
        
        else:  # Minimizing player
            min_eval = float('inf')
            
            # Get all possible moves for the current player
            for penguin_pos in current_player.penguins:
                valid_moves = self._get_valid_moves(*penguin_pos)
                
                for move_pos in valid_moves:
                    # Make a temporary move
                    fish_collected = self._make_temp_move(penguin_pos, move_pos)
                    
                    # Switch to the next player
                    self.current_player_index = (self.current_player_index + 1) % len(self.players)
                    
                    # Recursive minimax call
                    eval_score = self._minimax(depth - 1, alpha, beta, True)
                    
                    # Switch back to the current player
                    self.current_player_index = (self.current_player_index - 1) % len(self.players)
                    
                    # Undo the temporary move
                    self._undo_temp_move(penguin_pos, move_pos, fish_collected)
                    
                    # Update min_eval
                    min_eval = min(min_eval, eval_score)
                    
                    # Update beta for alpha-beta pruning
                    beta = min(beta, eval_score)
                    
                    # Alpha-beta pruning
                    if beta <= alpha:
                        break
            
            return min_eval
    
    def _make_temp_move(self, from_pos, to_pos):
        """Make a temporary move for minimax evaluation"""
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
        
        return fish_collected  # Return fish count for undo
    
    def _undo_temp_move(self, from_pos, to_pos, fish_collected):
        """Undo a temporary move for minimax evaluation"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Remove penguin from new position
        player_index = self.penguin_positions.pop(to_pos)
        
        # Restore the tile with the original fish count
        self.grid.tiles[(from_row, from_col)] = Tile(from_row, from_col, fish_collected)
        
        # Subtract the fish from the player
        self.players[player_index].fish_count -= fish_collected
        
        # Update penguin position
        self.penguin_positions[from_pos] = player_index
        
        # Update player's penguin list
        player = self.players[player_index]
        player.penguins.remove(to_pos)
        player.penguins.append(from_pos)
    
    def _is_game_over(self):
        """Check if the game is over (no player can move)"""
        for player in self.players:
            for penguin_pos in player.penguins:
                if self._get_valid_moves(*penguin_pos):
                    return False
        return True
    
    def _evaluate_board(self):
        """Evaluate the board state for the current player"""
        current_player = self.players[self.current_player_index]
        
        # Base score: current player's fish count
        score = current_player.fish_count
        
        # Subtract average fish count of opponents
        opponent_fish_total = 0
        opponent_count = 0
        for i, player in enumerate(self.players):
            if i != self.current_player_index:
                opponent_fish_total += player.fish_count
                opponent_count += 1
        
        if opponent_count > 0:
            avg_opponent_fish = opponent_fish_total / opponent_count
            score -= avg_opponent_fish
        
        # Add mobility score (number of possible moves)
        mobility = 0
        for penguin_pos in current_player.penguins:
            mobility += len(self._get_valid_moves(*penguin_pos))
        score += mobility * 0.5
        
        # Subtract opponent mobility
        opponent_mobility = 0
        for i, player in enumerate(self.players):
            if i != self.current_player_index:
                for penguin_pos in player.penguins:
                    opponent_mobility += len(self._get_valid_moves(*penguin_pos))
        
        if opponent_count > 0:
            score -= (opponent_mobility / opponent_count) * 0.3
        
        return score
    
    # ===== MINIMAX IMPLEMENTATION ENDS HERE =====
    
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
        
        # Show game over popup
        game_over_view = GameOverView(winners, self)
        self.window.show_view(game_over_view)

def main():
    """Main function"""
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    landing_view = LandingPageView()
    window.show_view(landing_view)
    arcade.run()

if __name__ == "__main__":
    main()