import pygame
from settings import *

class Object(pygame.sprite.Sprite):
    def __init__(self, groups, pos, z="blocks", surf=pygame.Surface((TILE_SIZE, TILE_SIZE))):
        super().__init__(groups)
        self.image = surf # The visual look of the object
        
        # The position and size of the object (used for drawing)
        self.rect = self.image.get_rect(topleft=pos)
        # used for collisions
        # By default, it's the same size as the image
        self.hitbox = self.rect.copy()
        self.z = z

class Wall(Object):
    def __init__(self, group, pos, z, surf):
        super().__init__(group, pos, z, surf)
        #self.hitbox = self.rect.copy().inflate(0, -self.rect.height / 2)
        self.hitbox = self.rect.copy()