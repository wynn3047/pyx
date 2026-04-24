import pygame
from settings import *

class Collider(pygame.sprite.Sprite):
    # Invisible rectangle used to trigger events like scene changes
    def __init__(self, groups, pos, size, number):
        super().__init__(groups)
        self.image = pygame.Surface((size))
        self.rect = self.image.get_rect(topleft=pos)
        self.number = number
        
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
        self.hitbox = self.rect.copy()
        
class Holes(Object):
    def __init__(self, group, pos, z, surf):
        super().__init__(group, pos, z, surf)
        self.hitbox = self.rect.copy()