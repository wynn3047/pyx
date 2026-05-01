import pygame
import math
from settings import *

# Characters will inherit from this class
class GameCharacter(pygame.sprite.Sprite): # acts as a foundation
    def __init__(self, game, scene, groups, pos, z, name, direction='right'):
        super().__init__(groups)

        self.game = game
        self.scene = scene
        self.name = name
        self.z = z
        self.speed = 50
        self.force = 2000
        self.accel = vect()
        self.vel = vect()
        self.frict = 15
        self.move_direction = vect()
        
        # Load images
        self.import_images(f'assets/characters/{self.name}/')  # calls the char's dir path
        self.frame_index = 0  

        self.image = self.animations[f'idle-{direction}'][self.frame_index].convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)

        # Movement hitbox (for wall collisions & p6)
        self.hitbox = self.rect.copy().inflate(-self.rect.width + 9, -self.rect.height + 1)
        self.hitbox.center = self.rect.center
        
        # Combat hitbox (for contact dmg detection)
        self.combat_hitbox = self.rect.copy().inflate(-4, -4)
        self.combat_hitbox.center = self.rect.center
        
        self.pos = vect(self.rect.center) 
        self.last_direction = direction
        self.state = Idle(self)
        self.knockback_timer = 0

        # Circle/Ellpise shadow 
        shadow_width = int(self.rect.width * SHADOW_CONFIG['width_scale'])
        shadow_height = SHADOW_CONFIG['height']
        self.shadow_surf = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA) 
        pygame.draw.ellipse(self.shadow_surf, (0, 0, 0, SHADOW_CONFIG['alpha']), self.shadow_surf.get_rect())
        self.shadow_offset_y = SHADOW_CONFIG['offset_y'] 

        # HP & Combat
        self.hp = 100
        self.max_hp = 100
        self.invulnerable = False
        self.invulnerability_timer = 0
        self.hit_flash_timer = 0
        self.hit_flash_color = COLORS['white']
        self.transparent_flicker_timer = 0
        self.knockback_speed = HP_CONFIG['hit_knockback']
        self.invulnerability_duration = HP_CONFIG['invulnerability_duration']
        
    def import_images(self, path):
        self.animations = self.game.get_animations(path) # scans char dir {"idle": [], ...}

        for animation in self.animations.keys():
            full_path = path + animation # builds the full path with the animation dir name
            self.animations[animation] = self.game.get_images(full_path) # appends the images for the specific dir name

    # ANIMATIONN!!
    def animate(self, state, fps, dt, loop=True):
        self.frame_index += fps * dt

        if self.frame_index >= len(self.animations[state]): #
            if loop:
                self.frame_index = 0 # playback loop
            else:
                self.frame_index = len(self.animations[state]) - 1 # last frame image

        # Rounds down for smoother animation increment by decimal (0,3 =0, 0.4=0, 0.5=0, ..., 1.0=1)
        self.image = self.animations[state][int(self.frame_index)]

    def get_direction(self):
        # For all angles
        DEAD_ZONE = 0.1 # Tiny threshold to prevent float noise
        # Check actual horizontal velocity
        if self.vel.x > DEAD_ZONE:
            self.last_direction = 'right'
            return 'right'
        elif self.vel.x < -DEAD_ZONE:
            self.last_direction = 'left'
            return 'left'
        else:
            # No horizontal movement return last direction (up & down
            return self.last_direction

    def movement(self):
        self.accel.x = self.move_direction.x * self.force
        self.accel.y = self.move_direction.y * self.force

    def get_collides(self, group):
        collidable_lists = pygame.sprite.spritecollide(self, group, False)
        return collidable_lists

    def collisions(self, axis, collidable_sprites):
        for sprite in collidable_sprites:
            if self.hitbox.colliderect(sprite.hitbox):
                if axis == 'x':
                    if self.vel.x > 0: # Moving Right
                        self.hitbox.right = sprite.hitbox.left
                    elif self.vel.x < 0: # Moving Left
                        self.hitbox.left = sprite.hitbox.right
                    self.vel.x = 0
                    self.pos.x = self.hitbox.centerx
                if axis == 'y':
                    if self.vel.y > 0: # Moving Down
                        self.hitbox.bottom = sprite.hitbox.top
                    elif self.vel.y < 0: # Moving Up
                        self.hitbox.top = sprite.hitbox.bottom
                    self.vel.y = 0
                    self.pos.y = self.hitbox.centery

    # Motions & Equations
    def physics(self, dt, frict):
        self.vel += self.accel * dt

        self.vel *= math.exp(-frict * dt)

        
        # X Direction
        self.pos.x += self.vel.x * dt
        self.hitbox.centerx = self.pos.x
        self.collisions('x', self.scene.block_sprites)

        # Y Direction
        self.pos.y += self.vel.y * dt
        self.hitbox.centery = self.pos.y
        self.collisions('y', self.scene.block_sprites)

        # MAP BOUNDARIES
        map_w, map_h = self.scene.camera.scene_size
        
        # Allow player a small bleed to hit exit triggers at map edges
        from player import Player
        margin = 8 if isinstance(self, Player) else 0
        
        # X Boundaries
        if self.hitbox.left < -margin:
            self.hitbox.left = -margin
            self.pos.x = self.hitbox.centerx
            self.vel.x = 0
        elif self.hitbox.right > map_w + margin:
            self.hitbox.right = map_w + margin
            self.pos.x = self.hitbox.centerx
            self.vel.x = 0
            
        # Y Boundaries
        if self.hitbox.top < -margin:
            self.hitbox.top = -margin
            self.pos.y = self.hitbox.centery
            self.vel.y = 0
        elif self.hitbox.bottom > map_h + margin:
            self.hitbox.bottom = map_h + margin
            self.pos.y = self.hitbox.centery
            self.vel.y = 0

        # SPEED CLAMPING
        if self.knockback_timer <= 0:
            current_speed = self.vel.magnitude()
            if current_speed > self.speed:
                self.vel = self.vel.normalize() * self.speed

        # Keep hitboxes synced
        self.rect.center = self.pos
        self.combat_hitbox.center = self.rect.center
        
    def change_state(self):
        new_state = self.state.enter_state(self)
        if new_state: self.state = new_state
        else: self.state

    def take_damage(self, amount, knockback_dir=None, knockback_force=None, knockback_stun=0.25):
        if self.invulnerable: 
            return # Don't take damage
        
        self.hp = max(0, self.hp - amount)
        
        if self.invulnerability_duration > 0:
            self.invulnerable = True
            self.invulnerability_timer = self.invulnerability_duration
            self.transparent_flicker_timer = self.invulnerability_duration

        self.hit_flash_timer = HP_CONFIG['hit_flash_duration'] # Red flash
            
        # Knockback effect
        self.knockback_timer = knockback_stun # Short stun duration
        
        if knockback_dir is None:
            knockback_dir = vect(1, 0)
        
        if knockback_dir.length() > 0:
            knockback_dir.normalize_ip()
        
        # Use provided force or fallback to character default
        force = knockback_force if knockback_force is not None else self.knockback_speed
        self.vel += knockback_dir * force

    def update(self, dt):
        if self.knockback_timer > 0:
            self.knockback_timer -= dt
            
        # Update HP & I-frame timers
        if self.invulnerable:
            self.invulnerability_timer -= dt
            if self.invulnerability_timer <= 0:
                self.invulnerable = False
                self.invulnerability_timer = 0
        
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= dt
            
        if self.transparent_flicker_timer > 0:
            self.transparent_flicker_timer -= dt
            
        # 1. Execute current state logic (Physics happens here)
        self.state.update(dt, self)

        # 2. Update direction and state for the NEXT frame based on resolved physics
        self.get_direction()
        self.change_state()

class Idle:
    def __init__(self, character):
        character.frame_index = 0

    def __str__(self):
        return self.__class__.__name__

    def enter_state(self, character):
        if character.vel.magnitude() > 1: # Any movement transition to Run class
            return Run(character)

    def update(self, dt, character):
        character.move_direction = vect(0, 0)
        character.animate(f'idle-{character.get_direction()}', 10, dt)
        character.movement()
        character.physics(dt, character.frict)


class Run:
    def __init__(self, character):
        Idle.__init__(self, character)

    def __str__(self):
        return self.__class__.__name__

    def enter_state(self, character):
        if character.vel.magnitude() < 1: # Flip back to idle
            return Idle(character)

    def update(self, dt, character):
        character.animate(f'run-{character.get_direction()}', 15, dt)
        character.movement()
        character.physics(dt, character.frict)
