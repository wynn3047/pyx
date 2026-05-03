import pygame, sys, os
from settings import *
from state import SplashScreen
from ui import UI

class Game:
    def __init__(self):

        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen_flags = pygame.SCALED | pygame.DOUBLEBUF
        # Fall back to window if fullscreen doesn't work
        try:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), self.screen_flags | pygame.FULLSCREEN)
        except pygame.error:
            # Fallback to windowed
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), self.screen_flags)

        pygame.display.set_caption("PyX")
        
        self.ui = UI(self)
        self.fonts = {} 
        
        self.running = True
        self.fps = 60  

        self.states = []
        self.splash_screen = SplashScreen(self)
        self.states.append(self.splash_screen)

        self.player_data = {}
        self.scene_states = {} # Stores persistent data for each room/scene
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
                elif event.key == pygame.K_e:
                    INPUTS['e'] = True
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    INPUTS['enter'] = True
                elif event.key == pygame.K_F8:
                    INPUTS['f8'] = True
                    DEBUG.TEXT = not DEBUG.TEXT
                    DEBUG.HITBOXES = not DEBUG.HITBOXES

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
                elif event.key == pygame.K_e:
                    INPUTS['e'] = False
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    INPUTS['enter'] = False
                elif event.key == pygame.K_F8:
                    INPUTS['f8'] = False

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

    # Dynamic text rendering with font caching
    def render_text(self, text, color, font_path, size, pos, centralized=True):
        # Create a unique key for the font/size combination
        font_key = f"{font_path}_{size}"
        
        # Load and cache the font if it doesn't exist
        if font_key not in self.fonts:
            self.fonts[font_key] = pygame.font.Font(font_path, size)
            
        font = self.fonts[font_key]
        text_surf = font.render(str(text), False, color)
        text_rect = text_surf.get_rect(center=pos) if centralized else text_surf.get_rect(topleft=pos)
        self.screen.blit(text_surf, text_rect)

    # Implementing custom cursor
    def custom_cursor(self, screen):
        pygame.mouse.set_visible(False)
        cursor_image = pygame.image.load('assets/mouse-cursor/my_custom_cursor.png').convert_alpha()
        scaled_cursor_image = pygame.transform.scale(cursor_image, (10, 10)) # scale image
        cursor_rect = scaled_cursor_image.get_rect(topleft=(pygame.mouse.get_pos())) # Clicks for top left (0,0)
        cursor_image.set_alpha(235) # Slight transparency
        screen.blit(scaled_cursor_image, cursor_rect)

    # Load all images full file path from directory into a list
    def get_images(self, path):
        images = []
        # Sort files numerically to avoid [0, 1, 10, 11...] sorting issues
        file_list = sorted(os.listdir(path), key=lambda f: int(f.split('.')[0]) if f.split('.')[0].isdigit() else f)
        
        for file in file_list: 
            full_path = os.path.join(path, file) 
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
            # Cap dt to prevent teleporting and physics glitches at low FPS
            dt = min(dt, 0.1) 
            self.get_inputs()
            # Always run the top of the state stack
            self.states[-1].update(dt)
            self.states[-1].draw(self.screen)
            self.custom_cursor(self.screen)
            pygame.display.flip()

if __name__ == '__main__':
    game = Game()
    game.loop()