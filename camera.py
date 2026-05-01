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

        # Stealth UI Assets
        self.stealth_frame = pygame.image.load(STEALTH_CONFIG['frame_path']).convert_alpha()
        self.stealth_fill = pygame.image.load(STEALTH_CONFIG['fill_path']).convert_alpha()

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
        
        if hasattr(sprite, 'invulnerable') and sprite.invulnerable and hasattr(sprite, 'transparent_flicker_timer'):
            flicker_cycle = sprite.transparent_flicker_timer % (TRANSPARENCY_FLICKER_CONFIG['flicker_interval'] * 2)
            if flicker_cycle < TRANSPARENCY_FLICKER_CONFIG['flicker_interval']:
                image.set_alpha(TRANSPARENCY_FLICKER_CONFIG['flicker_alpha_on']) 
            else:
                image.set_alpha(TRANSPARENCY_FLICKER_CONFIG['flicker_alpha_off'])
        
        return image
    
    def draw_hearts(self, screen, scene):
        if not scene.player or not hasattr(scene, 'heart_sprite'):
            return

        player = scene.player
        heart_ratios = player.get_heart_states()

        heart_size = HEART_CONFIG['heart_size']
        spacing = HEART_CONFIG['heart_spacing']

        total_width = (len(heart_ratios) * heart_size) + ((len(heart_ratios) - 1) * spacing)
        start_x = SCREEN_WIDTH - total_width - HEART_CONFIG['ui_offset_x']
        start_y = HEART_CONFIG['ui_offset_y']

        for heart_index, ratio in enumerate(heart_ratios):
            x = start_x + (heart_index * (heart_size + spacing))
            y = start_y

            # Always draw the full-sized black background heart
            if hasattr(scene, 'black_heart_sprite'):
                screen.blit(scene.black_heart_sprite, (x, y))

            #  Draw the scaled red heart on top
            if ratio > 0:
                if ratio >= 1:
                    screen.blit(scene.heart_sprite, (x, y))
                else:
                    # Dynamic scaling centered in the 16x16 slot
                    scaled_w = int(heart_size * ratio)
                    scaled_h = int(heart_size * ratio)

                    if scaled_w > 2 and scaled_h > 2:
                        scaled_heart = pygame.transform.scale(scene.heart_sprite, (scaled_w, scaled_h))

                        # Gradual Darkening: Multiply color by ratio (255 = full bright, 0 = black)
                        brightness = int(255 * ratio)
                        scaled_heart.fill((brightness, brightness, brightness), special_flags=pygame.BLEND_RGB_MULT)

                        # Calculate centered position
                        offset_x = (heart_size - scaled_w) // 2
                        offset_y = (heart_size - scaled_h) // 2
                        screen.blit(scaled_heart, (x + offset_x, y + offset_y))


    def draw_stealth_bar(self, screen, player):
        if not player: return
        
        # Position: Center-left
        frame_h = self.stealth_frame.get_height()
        pos_x = 375
        pos_y = 20 + (SCREEN_HEIGHT - frame_h) // 2
        
        screen.blit(self.stealth_frame, (pos_x, pos_y))
        
        ratio = player.stealth / player.max_stealth
        if ratio >= 0:
            fill_image = self.stealth_fill.copy()
            full_w, full_h = fill_image.get_size()
            
            padding = 9
            usable_h = full_h - (padding * 2)
            
            # Pulse when full
            if player.is_stealth_ready:
                fill_image.fill(COLORS['light_pink'], special_flags=pygame.BLEND_RGB_MULT)

                pulse = (math.sin(pygame.time.get_ticks() * 0.02) + 1) / 2 # 0 to 1
                alpha = 150 + int(105 * pulse) # 150 to 255
                fill_image.set_alpha(alpha)
            
            current_fill_h = int(usable_h * ratio)
            
            clip_rect = pygame.Rect(0, (full_h - padding) - current_fill_h, full_w, current_fill_h)
            
            # Align the slice cuz my image has 9px margin
            screen.blit(fill_image, (pos_x, pos_y + (full_h - padding - current_fill_h)), area=clip_rect)

    def draw_tumble_ui(self, screen, scene):
        if not scene.player or not hasattr(scene, 'tumble_frame'):
            return

        player = scene.player
        icon_w, icon_h = scene.tumble_frame.get_size()
        spacing = TUMBLE_UI_CONFIG['spacing']
        
        pos_y = HEART_CONFIG['ui_offset_y'] + HEART_CONFIG['heart_size'] + TUMBLE_UI_CONFIG['offset_y_below_hearts']
        
        for i in range(player.tumble_max_charges):
            x = (SCREEN_WIDTH - HEART_CONFIG['ui_offset_x'] - icon_w) - (i * (icon_w + spacing))
            
            screen.blit(scene.tumble_frame, (x, pos_y))
            
            fill_surf = scene.tumble_fill.copy()
            fill_w, fill_h = fill_surf.get_size()
            
            # If slot is full
            if i < player.tumble_charges:
                fill_surf.fill(COLORS['white'], special_flags=pygame.BLEND_RGB_MULT)
                screen.blit(fill_surf, (x, pos_y))
            
            elif i == player.tumble_charges:
                ratio = 1.0 - (player.tumble_cooldown_timer / player.tumble_cooldown)
                fill_surf.set_alpha(150)
                if ratio > 0:
                    current_w = int(fill_w * ratio)
                    clip_rect = pygame.Rect(fill_w - current_w, 0, current_w, fill_h)
                    screen.blit(fill_surf, (x + (fill_w - current_w), pos_y), area=clip_rect)

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
        
        self.draw_hearts(screen, scene)
        self.draw_tumble_ui(screen, scene)
        self.draw_stealth_bar(screen, scene.player)

        # Full-screen red flash if player is hit while at low HP (<= 50%)
        if scene.player and scene.player.is_low_hp and scene.player.hit_flash_timer > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill(COLORS['red'])
            overlay.set_alpha(70) # 0-255 opacity
            screen.blit(overlay, (0, 0))
