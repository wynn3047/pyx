import pygame
from settings import *
from characters import Player
from objects import Object
from pytmx.util_pygame import load_pygame

class State:
    def __init__(self, game):
        self.game = game
        self.prev_state = None

    # Screen state handler [BACK > BACK > MAIN]
    def enter_state(self):
        if len(self.game.states) > 1:
            self.prev_state = self.game.states[-1]
        self.game.states.append(self)

    def exit_state(self):
        self.game.states.pop()

    def update(self, dt):
        pass

    def draw(self, screen):
        pass

# Screen before loading the game
class SplashScreen(State):
    def __init__(self, game):
        super().__init__(game)

    def update(self, dt):
        if INPUTS['space']:
            Scene(self.game).enter_state()
            self.game.reset_inputs()

    def draw(self, screen):
        screen.fill((COLORS['charcoal_grey']))
        self.game.render_text('ROGUEDAGOAT', COLORS['white'], self.game.head_font, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

# After
class Scene(State):
    def __init__(self, game):
        super().__init__(game)

        # For updating and drawing without having to do it individually
        # Takes my objects properties for control
        self.update_sprites = pygame.sprite.Group()
        self.draw_sprites = pygame.sprite.Group()

        # Load Tilemap data
        self.tmx_data = load_pygame('scenes/0/0.tmx')
        # Make the scene
        self.create_scene()

    # Loads map data and iterates through its layers to build the scene.
    def create_scene(self):
        # Get a list of all layer names in the TMX file (e.g., 'blocks', 'ground')
        layers = []
        for layer in self.tmx_data.layers:
            layers.append(layer.name)

        # We loop through every tile in that layer:
        if 'blocks' in layers: # Walls/obstacles
            for x, y, surf in self.tmx_data.get_layer_by_name('blocks').tiles():
                # calculate the position (x * TILE_SIZE)
                # and create a new Object for it.
                Object([self.draw_sprites], (x * TILE_SIZE, y * TILE_SIZE), surf)

        # If there's an object layer named 'entries'
        if "entries" in layers:
            for obj in self.tmx_data.get_layer_by_name('entries'): # get the name on this layer (0)
                if obj.name == '0':
                    # Create player from this entry point
                    self.player = Player(self.game, self, [self.update_sprites, self.draw_sprites],
                                         (obj.x, obj.y), 'player') # position where the object entry    point is

    # For ingame debugging visualization (displays accel, vel, etc.)
    def debugger(self, debug_list):
        for index, name in enumerate(debug_list):
            self.game.render_text(name, COLORS['white'], self.game.primary_font, (10, 15 * (index + 1)), False)

    def update(self, dt):
        if INPUTS['backspace']:
            self.exit_state()
            self.game.reset_inputs()
        # if INPUTS['left_click']:
        #     print(pygame.mouse.get_pos())
        self.update_sprites.update(dt)

    def draw(self, screen):
        screen.fill((COLORS['blue']))
        self.draw_sprites.draw(screen)
        self.debugger([
            str(f'FPS: {round(self.game.clock.get_fps(), 2)}'),
            str(f'Vel: {round(self.player.vel, 2)}')
        ])
