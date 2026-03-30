import pygame
from settings import *
from characters import Player

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

# Scene
class Scene(State):
    def __init__(self, game):
        super().__init__(game)

        # For updating and drawing without having to do it individually
        # Takes my objects properties for control
        self.update_sprites = pygame.sprite.Group()
        self.draw_sprites = pygame.sprite.Group()

        self.player = Player(self.game, self, [self.update_sprites, self.draw_sprites], (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 'player')

    # For ingame debugging visualization (displays accel, vel, etc.)
    def debugger(self, debug_list):
        for index, name in enumerate(debug_list):
            self.game.render_text(name, COLORS['white'], self.game.primary_font, (10, 15 * index), False)

    def update(self, dt):
        if INPUTS['backspace']:
            self.exit_state()
            self.game.reset_inputs()
        self.update_sprites.update(dt)

    def draw(self, screen):
        screen.fill((COLORS['blue']))
        self.game.render_text('press backspace to BACK', COLORS['white'], self.game.head_font, (SCREEN_WIDTH // 2, 10))
        self.draw_sprites.draw(screen)
        self.debugger([
            str(f'FPS: {round(self.game.clock.get_fps(), 2)}')
        ])
