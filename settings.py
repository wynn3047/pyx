from pygame.math import Vector2 as vect

SCREEN_WIDTH, SCREEN_HEIGHT = 400, 224
TILE_SIZE = 16

HEAD_FONT = "assets/fonts/alagard.ttf"
PRIMARY_FONT = "assets/fonts/homespun.ttf"

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
}

COLORS = {
    'black' : (0, 0, 0),
    'white' : (255, 255, 255),
    'red' : (255, 0, 0),
    'green' : (0, 255, 0),
    'blue' : (69,78,99),
    'charcoal_grey': (24, 29, 35),
    'medium-navy': (19,21,32)
}

LAYERS = ['background',
          'objects',
          'blocks',
          'characters',
          'particles',
          'foreground']