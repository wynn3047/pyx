import pygame
from settings import *

# Characters will inherit from this class
class GameCharacter(pygame.sprite.Sprite): # acts as a foundation
    def __init__(self, game, scene, groups, pos, name):
        super().__init__(groups)

        self.game = game
        self.scene = scene
        self.name = name

        self.speed = 70
        self.force = 2000
        self.accel = vect()
        self.vel = vect()
        self.frict = -15

        # Load images
        self.import_images(f'assets/characters/{self.name}/')  # calls the char's dir path
        self.frame_index = 0  # frame number

        # from local var to stored in self*instance (can access self.animations)
        self.image = self.animations['idle-right'][self.frame_index].convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)

    def import_images(self, path):
        self.animations = self.game.get_animations(path) # scans char dir {"idle": [], ...}

        for animation in self.animations.keys():
            full_path = path + animation # builds the full path with the animation dir name
            self.animations[animation] = self.game.get_images(full_path) # appends the images for the specific dir name

        # Whats actually gonn happen
        # {
        #     "idle": [surface1, surface2, surface3],
        #     "walk": [surface4, surface5, surface6],
        #     "run": [surface7, surface8]
        # }

    # ANIMATIONN!!
    def animate(self, state, fps, loop=True):
        self.frame_index += fps

        if self.frame_index >= len(self.animations[state]): #
            if loop:
                self.frame_index = 0 # playback loop
            else:
                self.frame_index = len(self.animations[state]) - 1 # last frame image

        # Rounds down for smoother animation increment by decimal (0,3 =0, 0.4=0, 0.5=0, ..., 1.0=1)
        self.image = self.animations[state][int(self.frame_index)]

    # Motions & Equations
    def physics(self, dt):
        # X Direction
        self.accel.x += self.vel.x * self.frict # Applying increasing friction when accelerating
        self.vel.x += self.accel.x * dt # Velocity change
        self.rect.centerx += self.vel.x * dt + 0.5 * self.accel.x * dt**2 # Moving center for intuitive interactions (Velret Integration)

        # Y Direction
        self.accel.y += self.vel.y * self.frict  # Applying increasing friction when accelerating
        self.vel.y += self.accel.y * dt  # Velocity change
        self.rect.centery += self.vel.y * dt + 0.5 * self.accel.y * dt**2 # Moving center for intuitive interactions (Velret Integration)

        # Fix diagonal speed boost
        if self.vel.magnitude() >= self.speed: # magnitude() gets the speed of vel.x and vel.y
            self.vel = self.vel.normalize() * self.speed # normalize() sets magnitude to 1.0 instead of going 40% faster

    def update(self, dt):
        self.physics(dt)
        self.animate('idle-right', 15 * dt) # 15 times smoother

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
        if self.vel.magnitude() < 1:
            self.animate('idle-right', 10 * dt)
        else:
            self.animate('run-right', 13 * dt)
