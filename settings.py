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
    'light_pink': (249, 159, 255)
    
}

HP_CONFIG = {
    'player_max_hp': 200,
    'player_hp_regen': 6,
    'player_regen_delay': 7, # Regen delay after hit
    'invulnerability_duration': 0.67, # For invicibility frames
    'hit_flash_duration': 0.1,
    'hit_knockback': 80, # Default fallback
    'enemy_contact_knockback': 120,
    'player_dagger_knockback': 30,
    'transparency_alpha': 100,
    'flicker_interval': 0.08,     
}

PLAYER_COMBAT_CONFIG = {
    'proj_pierce_count': 0,      
    'proj_count': 1,             
    'proj_spread_angle': 20,     
    'proj_burst_count': 1,       
    'proj_burst_delay': 0.1,     
    'proj_ricochet_count': 0 
    }

STEALTH_CONFIG = {
    'max_stealth': 100.0,
    'stealth_regen': 20.0,         # Per second
    'stealth_regen_delay': 1.5,    # Seconds before regen starts
    'attack_consumption': 25.0, # Normal attack reduction
    # Stealth Strike Multipliers
    'damage_mult': 2.3,
    'velocity_mult': 1.4,
    'count_add': 2,            
    'pierce_add': 1,
    'ricochet_add': 0,
    'frame_path': 'assets/ui/stealth_bar_frame.png',
    'fill_path': 'assets/ui/stealth_bar_fill.png'
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
    "R.I.P.",
    "damn.",
    "T_T T_T T_T"
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