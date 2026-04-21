import pygame, csv
import math
from settings import *

class Camera(pygame.sprite.Group):
    def __init__(self, scene):
        # self.offset is the "Invisible Hand" that pushes the world map.
        # It stores how far we have scrolled from the top-left (0,0) of the world.
        self.offset = vect()
        
        # rectangle the size of the monitor
        self.visible_window = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.scene_size = self.get_scene_size(scene)
        self.delay = 5
        self.peek_limit = 3

    # Capturing screen size for tilemap
    def get_scene_size(self, scene):
        with open('scenes/0/0.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                cols = (len(row)) # Len of cells in row
                rows = (sum(1 for row in reader) + 1) # list of 1's and add the very first 1


        return (cols * TILE_SIZE, rows * TILE_SIZE)

    def update(self, dt, target):
        mouse = pygame.mouse.get_pos()

        # Calculate the center target offset by the player and mouse, and apply peek limit
        target_x = target.rect.centerx - SCREEN_WIDTH / 2 - (SCREEN_WIDTH / 2 - mouse[0]) / self.peek_limit
        target_y = target.rect.centery - SCREEN_HEIGHT / 2 - (SCREEN_HEIGHT / 2 - mouse[1]) / self.peek_limit

        # Smooth camera movement panning
        self.offset.x += (target_x - self.offset.x) * (self.delay * dt)
        self.offset.y += (target_y - self.offset.y) * (self.delay * dt)

        # Snaps if the offset is very close to 1 pixel
        if abs(target_x - self.offset.x) < 1.1:
            self.offset.x = target_x
        if abs(target_y - self.offset.y) < 1.1:
            self.offset.y = target_y

        # Set camera shot for map boundary (0 for left side, and 400 for right side
        self.offset.x = max(0, min(self.offset.x, self.scene_size[0] - SCREEN_WIDTH))
        self.offset.y = max(0, min(self.offset.y, self.scene_size[1] - SCREEN_HEIGHT))

        # We move our "visible window" to match where the camera is looking.
        self.visible_window.x = math.floor(self.offset.x)
        self.visible_window.y = math.floor(self.offset.y)

    def show_hitbox(self, screen, sprite, offset):
        # Visual hitbox
        temp_hitbox = sprite.hitbox.copy()
        temp_hitbox.topleft -= offset

        from characters import Player
        if isinstance(sprite, Player):
            color = (0, 255, 0)
        elif sprite.z == 'blocks':
            color = (255, 0, 0)
        else:
            color = (255, 255, 0)

        pygame.draw.rect(screen, color, temp_hitbox, 1)
        pygame.draw.circle(screen, color, temp_hitbox.center, 1)

    def draw(self, screen, group):
        screen.fill((COLORS['medium-navy']))
        draw_offset = vect(math.floor(self.offset.x), math.floor(self.offset.y))
        # Sort by the bottom of the rect (the feet) for depth
        sorted_sprites = sorted(group, key=lambda sprite: sprite.rect.bottom)
        for layer in LAYERS:
            # 2. Loop through every single object in the game
            for sprite in sorted_sprites:
                # colliderect returns True if the sprite is touching the visible_window.
                if self.visible_window.colliderect(sprite.rect) and sprite.z == layer:
                    # Subtract the camera offset from the object's real world position.
                    offset_pos = sprite.rect.topleft - draw_offset
                    screen.blit(sprite.image, offset_pos) # Put the image on the screen at that shifted position.

                    if DEBUG_HITBOXES:
                        self.show_hitbox(screen, sprite, draw_offset)