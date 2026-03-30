import pygame
from settings import *

# Characters will inherit from this class
class GameCharacter(pygame.sprite.Sprite): # acts as a foundation
    def __init__(self, game, scene, groups, pos, name):
        super().__init__(groups)

        self.game = game
        self.scene = scene
        self.name = name
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE * 1.5))
        self.image.fill(COLORS['red'])
        self.rect = self.image.get_rect(topleft = pos)
        self.speed = 60
        self.force = 2500
        self.accel = vect()
        self.vel = vect()
        self.frict = -15

    # Motions & Equations
    def physics(self, dt):
        # X Direction
        self.accel.x += self.vel.x * self.frict # Applying increasing friction when accelerating
        self.vel.x += self.accel.x * dt # Velocity change
        self.rect.centerx += self.vel.x * dt + 0.5 * self.accel.x * dt**2 # Moving center for intuitive interactions (Velret Integration)

        # Y Direction
        self.accel.y += self.vel.y * self.frict  # Applying increasing friction when accelerating
        self.vel.y += self.accel.y * dt  # Velocity change
        self.rect.centery += self.vel.y * dt + 0.5 * self.accel.x * dt**2 # Moving center for intuitive interactions (Velret Integration)

        # Fix diagonal speed boost
        if self.vel.magnitude() >= self.speed: # magnitude() gets the speed of vel.x and vel.y
            self.vel = self.vel.normalize() * self.speed # normalize() sets magnitude to 1.0 instead of going 40% faster

    def update(self, dt):
        self.physics(dt)

class Player(GameCharacter):
    def __init__(self, game, scene, groups, pos, name):
        super().__init__(game, scene, groups, pos, name)

    def movement(self):
        # X inputs
        if INPUTS['left']: self.accel.x = -self.force
        elif INPUTS['right']: self.accel.x = self.force
        else:
            self.accel.x = 0

        # Y inputs
        if INPUTS['up']: self.accel.y = -self.force
        elif INPUTS['down']: self.accel.y = self.force
        else: self.accel.y = 0

    def update(self, dt):
        self.physics(dt)
        self.movement()