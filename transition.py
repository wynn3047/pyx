import pygame
from settings import *

class Transition:
    def __init__(self, scene):
        self.fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.scene = scene
        self.exiting = False
        self.fade_speed = 700
        self.alpha = 255
        
    def update(self, dt):
        # Handle the fading logic based on the exiting state
        if self.exiting:
            # Increase alpha (get darker) over time
            self.alpha = min(255, self.alpha + self.fade_speed * dt)
            if self.alpha >= 200:
                # Once fully dark, trigger the scene swap
                self.scene.go_to_scene()
        else:
            # Decrease alpha (get lighter) over time
            self.alpha = max(0, self.alpha - self.fade_speed * dt) 
    
    def draw(self, screen):
        # Draw the solid navy rectangle with the current alpha (transparency)
        self.fade_surf.fill(COLORS['medium_navy'])
        self.fade_surf.set_alpha(self.alpha)
        screen.blit(self.fade_surf, (0, 0))