from pygame.math import Vector2 as vect

SCREEN_WIDTH, SCREEN_HEIGHT = 400, 224
TILE_SIZE = 16

HEAD_FONT = "assets/fonts/alagard.ttf"
PRIMARY_FONT = "assets/fonts/homespun.ttf"

class DEBUG:
    HITBOXES = False
    TEXT = False

INPUTS = {
    'escape' : False,
    'backspace' : False,
    'space' : False,
    'up' : False,
    'down' : False,
    'left' : False,
    'right' : False,
    'left_click' : False,
    'middle_click' : False,
    'right_click' : False,
    'scroll_up' : False,
    'scroll_down' : False,
    'enter': False,
    'f8': False
}

COLORS = {
    'black' : (0, 0, 0),
    'white' : (255, 255, 255),
    'red' : (70, 0, 11),
    'green' : (0, 255, 0), 
    'blue' : (69,78,99),
    'charcoal_grey': (24, 29, 35),
    'medium_navy': (19,21,32),
    
}

HP_CONFIG = {
    'player_max_hp': 200,
    'player_hp_regen': 6,
    'player_regen_delay': 7, # Regen delay after hit
    'invulnerability_duration': 0.67, # For invicibility frames
    'hit_flash_duration': 0.1,
    'hit_knockback': 80, # Default fallback
    'enemy_contact_knockback': 120,
    'player_dagger_knockback': 50,
    'transparency_alpha': 100,
    'flicker_interval': 0.08,     
}

PLAYER_COMBAT_CONFIG = {
    'proj_pierce_count': 0,      # 0 = hits one enemy then dies
    'proj_count': 2,             # Number of projectiles per shot
    'proj_spread_angle': 10,     # Arc in degrees for spread shots
    'proj_burst_count': 1,       # Consecutive shots per attack
    'proj_burst_delay': 0.05 # Delay between consecutive shots
}

HEART_CONFIG = {            
    'hp_per_heart': 50,                 
    'heart_size': 16,             
    'heart_spacing': 2,                      
    'ui_offset_x': 10,            
    'ui_offset_y': 10,            
}
DEATH_SEQUENCE_CONFIG = {
    'slowdown_duration': 3,
    'slowdown_multiplier': 0.4,
    'bw_filter_duration': 0.8,
    'pause_duration': 1.2,
    'fade_color': COLORS['medium_navy'],
    'message_color': COLORS['red'],
    'button_color_active': COLORS['white'],
    'button_color_inactive': COLORS['charcoal_grey']
}

# Flicker effect during invulnerability
TRANSPARENCY_FLICKER_CONFIG = {
    'flicker_alpha_on': 255,           
    'flicker_alpha_off': 100,          
    'flicker_interval': 0.08,          
}

# Death message pool (randomized)
DEATH_MESSAGES = [
    "dang...",
    "ya ded.",
    "You Died.",
    "damn"
]


# Layer order top to bottom
LAYERS = ['background',
          'objects',
          'floors',
          'holes',
          'blocks',
          'characters',
          'detail 1',
          'particles',
          'foreground']

SHADOW_CONFIG = {
    'height': 6, # Pixel height of ellipse
    'alpha': 100, # Transparency
    'offset_y': 4, # Position above ground 
    'width_scale': 0.9 # Width percentage of sprite width (narrower)
}

SCENE_DATA = {
    '0': {'1': '1'},
    '1': {'1': '0'}
}