import pygame
from settings import *

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

    def update(self, dt): # Loading a state/scene
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

    def update(self, dt):  # Loading a state/scene
        if INPUTS['space']:
            SplashScreen(self.game).enter_state()
            self.game.reset_inputs()

    def draw(self, screen):
        screen.fill((COLORS['blue']))
        self.game.render_text('Rogue Class GOAT, press space', COLORS['white'], self.game.head_font, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
