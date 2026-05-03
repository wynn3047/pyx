import pygame, csv
import math
from settings import *

class Camera(pygame.sprite.Group):
    def __init__(self, scene):
        super().__init__()
        # It stores how far we have scrolled from the top-left (0,0) of the world.
        self.offset = vect()
        
        # rectangle the size of the monitor
        self.visible_window = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.scene_size = self.get_scene_size(scene)
        self.delay = 5
        self.peek_limit = 3

    # Capturing screen size for tilemap
    def get_scene_size(self, scene):
        # Open current scene's CSV to get its dimensions
        with open(f'scenes/{scene.current_scene}/{scene.current_scene}.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                cols = (len(row)) # Len of cells in row
                rows = (sum(1 for row in reader) + 1) # list of 1's and add the very first 1


        return (cols * TILE_SIZE, rows * TILE_SIZE)
        
    def apply_hit_effects(self, sprite, image):
        # Red flash & transparent flicker
        image = image.copy()
        
        # Check if this is the player and they are at low HP
        from player import Player
        is_player_low_hp = isinstance(sprite, Player) and sprite.is_low_hp
        if hasattr(sprite, 'hit_flash_timer') and sprite.hit_flash_timer > 0:
            # Create color overlay
            overlay_color = getattr(sprite, 'hit_flash_color', COLORS['white'])

            # Use a mask to create a solid-color silhouette of the sprite
            mask = pygame.mask.from_surface(image)
            # to_surface creates a new surface where the mask is 'setcolor' and empty space is 'unsetcolor'
            flash_surf = mask.to_surface(setcolor=overlay_color, unsetcolor=(0, 0, 0, 0))

            alpha = 180 if is_player_low_hp else 128
            flash_surf.set_alpha(alpha)

            image.blit(flash_surf, (0, 0))
            return image
        
        if hasattr(sprite, 'highlighted') and sprite.highlighted:
            mask = pygame.mask.from_surface(image)
            highlight_surf = mask.to_surface(setcolor=COLORS['white'], unsetcolor=(0, 0, 0, 0))
            highlight_surf.set_alpha(100)
            image.blit(highlight_surf, (0, 0))

        if hasattr(sprite, 'invulnerable') and sprite.invulnerable and hasattr(sprite, 'transparent_flicker_timer'):
            flicker_cycle = sprite.transparent_flicker_timer % (TRANSPARENCY_FLICKER_CONFIG['flicker_interval'] * 2)
            if flicker_cycle < TRANSPARENCY_FLICKER_CONFIG['flicker_interval']:
                image.set_alpha(TRANSPARENCY_FLICKER_CONFIG['flicker_alpha_on']) 
            else:
                image.set_alpha(TRANSPARENCY_FLICKER_CONFIG['flicker_alpha_off'])
        
        return image
    
    def show_hitbox(self, screen, sprite, offset):
        # Visual hitbox
        from player import Player
        from projectiles import Projectile
        
        if isinstance(sprite, Player):
            color = (0, 255, 0)
        elif sprite.z in ('blocks', 'holes'):
            color = (255, 0, 0)
        elif isinstance(sprite, Projectile):
            color = COLORS['blue']
        else:
            color = None
            
        combat_color = (0, 200, 255)

        if color:
            temp_hitbox = sprite.hitbox.copy()
            temp_hitbox.topleft -= offset
            pygame.draw.rect(screen, color, temp_hitbox, 1)
            pygame.draw.circle(screen, color, temp_hitbox.center, 1)
        
        if hasattr(sprite, 'combat_hitbox'):
            # For sprites that have combat hitbox attribute
            temp_combat = sprite.combat_hitbox.copy()
            temp_combat.topleft -= offset
            pygame.draw.rect(screen, combat_color, temp_combat, 1)
    
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
         
    def draw(self, screen, group, scene):
        screen.fill((COLORS['medium_navy']))
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
                    
                    if layer == 'blocks' and hasattr(sprite, 'shadow_surf'):
                        # Draws sprite's shadow  on bottom
                        actual_width = sprite.image.get_width()
                        shadow_x = offset_pos[0] + (actual_width - sprite.shadow_surf.get_width() - 0.5)
                        shadow_y = offset_pos[1] + sprite.rect.height - sprite.shadow_offset_y
                        screen.blit(sprite.shadow_surf, (shadow_x, shadow_y))

                    sprite_image = self.apply_hit_effects(sprite, sprite.image)
                    screen.blit(sprite_image, offset_pos) # Put the image on the screen at that shifted position.

                    if DEBUG.HITBOXES:
                        self.show_hitbox(screen, sprite, draw_offset)
