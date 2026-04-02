import pygame, sys, os
from settings import *
from state import SplashScreen

class Game:
    def __init__(self):

        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN|pygame.SCALED) # Scale to res
        self.head_font = pygame.font.Font(HEAD_FONT, TILE_SIZE)
        self.primary_font = pygame.font.Font(PRIMARY_FONT, 10)
        self.running = True
        self.fps = 60

        self.states = []
        self.splash_screen = SplashScreen(self)
        self.states.append(self.splash_screen)

    # Pygame events
    def get_inputs(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()

            # Key events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    INPUTS['escape'] = True
                    self.running = False
                elif event.key == pygame.K_BACKSPACE:
                    INPUTS['backspace'] = True
                elif event.key == pygame.K_SPACE:
                    INPUTS['space'] = True
                elif event.key in (pygame.K_UP, pygame.K_w):
                    INPUTS['up'] = True
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    INPUTS['down'] = True
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    INPUTS['left'] = True
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    INPUTS['right'] = True

            # When released
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    INPUTS['space'] = False
                elif event.key == pygame.K_BACKSPACE:
                    INPUTS['backspace'] = False
                elif event.key in (pygame.K_UP, pygame.K_w):
                    INPUTS['up'] = False
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    INPUTS['down'] = False
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    INPUTS['left'] = False
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    INPUTS['right'] = False

            # Mouse events
            if event.type == pygame.MOUSEWHEEL:
                if event.y == 1:
                    INPUTS['scroll_up'] = True
                elif event.y == -1:
                    INPUTS['scroll_down'] = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    INPUTS['left_click'] = True
                elif event.button == 2:
                    INPUTS['middle_click'] = True
                elif event.button == 3:
                    INPUTS['right_click'] = True
                # Optional mousewheel addition for certain cases
                elif event.button == 4:
                    INPUTS['scroll_up'] = True
                elif event.button == 5:
                    INPUTS['scroll_down'] = True

            # When released
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    INPUTS['left_click'] = False
                elif event.button == 2:
                    INPUTS['middle_click'] = False
                elif event.button == 3:
                    INPUTS['right_click'] = False
                # Optional mousewheel addition
                elif event.button == 4:
                    INPUTS['scroll_up'] = False
                elif event.button == 5:
                    INPUTS['scroll_down'] = False

    # Keys must reset so it shouldn't be held when performing another state
    def reset_inputs(self):
        for key in INPUTS:
            INPUTS[key] = False

    # Text rendering on screen
    def render_text(self, text, color, font, pos, centralized=True):
        text_surf = font.render(str(text), False, color)
        text_rect = text_surf.get_rect(center=pos) if centralized else text_surf.get_rect(topleft=pos)
        self.screen.blit(text_surf, text_rect)

    # Implementing custom cursor
    def custom_cursor(self, screen):
        pygame.mouse.set_visible(False)
        cursor_image = pygame.image.load('assets/mouse-cursor/my_custom_cursor.png').convert_alpha()
        cursor_rect = cursor_image.get_rect(center=pygame.mouse.get_pos()) # Get tuple of x and y pos
        cursor_image.set_alpha(235) # Slight transparency
        screen.blit(cursor_image, cursor_rect)

    # Load all images full file path from directory into a list
    def get_images(self, path):
        images = []
        for file in os.listdir(path): # listdir gets filenames on that path dir
            full_path = os.path.join(path, file) # combines and build the full formatted file path
            image = pygame.image.load(full_path).convert_alpha()
            images.append(image)
        return images

    # Creates empty dict to store filenames as keys
    def get_animations(self, path):
        animations = {}
        for file_name in os.listdir(path): # listdir iterates through all files from that file path
            animations.update({file_name: []}) # adds each filename as key with empty []
        return animations

    # Game loop
    def loop(self):
        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0
            self.get_inputs()
            # Always run the top of the state stack
            self.states[-1].update(dt)
            self.states[-1].draw(self.screen)
            self.custom_cursor(self.screen)
            pygame.display.flip()

if __name__ == '__main__':
    game = Game()
    game.loop()