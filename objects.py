import pygame
from settings import *

class Object(pygame.sprite.Sprite):
    def __init__(self, groups, pos, surf=pygame.Surface((TILE_SIZE, TILE_SIZE))):
        super().__init__(groups)

        # The visual look of the object
        self.image = surf
        
        # The position and size of the object (used for drawing)
        self.rect = self.image.get_rect(topleft=pos)
        
        # used for collisions
        # By default, it's the same size as the image
        self.hitbox = self.rect.copy().inflate(0, 0)
