import pygame
import math
from settings import *

class Projectile(pygame.sprite.Sprite):
    def __init__(self, scene, groups, pos, direction, speed, damage, sprite_path, knockback_force=100, pierce_count=0, ricochet_count=0):
        super().__init__(groups)
        self.scene = scene
        self.z = 'holes' 
        
        self.original_image = pygame.image.load(sprite_path).convert_alpha()
        
        self.pos = vect(pos)
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.knockback_force = knockback_force
        self.pierce_count = pierce_count
        self.ricochet_count = ricochet_count
        self.hit_enemies = [] # Track enemies hit to avoid multi-hits
        
        # Sprite points UP, adjust by 90 degrees.
        self.rotate_sprite()
        
        self.rect = self.image.get_rect(center=pos)
        # Narrow hitbox for precision
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.7, -self.rect.height * 0.7)
        
        self.lifespan = 2 # Seconds before disappearing
        self.timer = 0

    def rotate_sprite(self):
        angle = math.degrees(math.atan2(-self.direction.y, self.direction.x)) - 90
        self.image = pygame.transform.rotate(self.original_image, angle)

    def check_collisions(self):
        # Check Walls & Holes
        from objects import Holes
        for wall in self.scene.block_sprites:
            if self.hitbox.colliderect(wall.hitbox) and not isinstance(wall, Holes):
                self.on_wall_hit(wall)
                return

        # Check Enemies
        for enemy in self.scene.enemy_sprites:
            if enemy not in self.hit_enemies and self.hitbox.colliderect(enemy.combat_hitbox):
                self.on_enemy_hit(enemy)
                # If we killed the projectile, stop checking
                if not self.alive():
                    return

    def on_wall_hit(self, wall):
        if self.ricochet_count > 0:
            self.ricochet_count -= 1
            
            # Calculate overlap
            overlap_x = min(self.hitbox.right, wall.hitbox.right) - max(self.hitbox.left, wall.hitbox.left)
            overlap_y = min(self.hitbox.bottom, wall.hitbox.bottom) - max(self.hitbox.top, wall.hitbox.top)
            
            # Robust corner detection: if overlaps are very close, it's likely a corner hit
            # and we should flip both axes.
            if abs(overlap_x - overlap_y) < 1:
                self.direction.x *= -1
                self.direction.y *= -1
                # Nudge out of both axes
                if self.pos.x < wall.hitbox.centerx: self.pos.x -= overlap_x + 1
                else: self.pos.x += overlap_x + 1
                if self.pos.y < wall.hitbox.centery: self.pos.y -= overlap_y + 1
                else: self.pos.y += overlap_y + 1
            elif overlap_x < overlap_y:
                # Hit from left or right
                self.direction.x *= -1
                # Nudge out of wall
                if self.pos.x < wall.hitbox.centerx: self.pos.x -= overlap_x + 1
                else: self.pos.x += overlap_x + 1
            else:
                # Hit from top or bottom
                self.direction.y *= -1
                # Nudge out of wall
                if self.pos.y < wall.hitbox.centery: self.pos.y -= overlap_y + 1
                else: self.pos.y += overlap_y + 1
                
            self.rotate_sprite()
            # Sync rect and hitbox immediately to prevent double-triggering
            self.rect.center = self.pos
            self.hitbox.center = self.pos
        else:
            self.kill()

    def on_enemy_hit(self, enemy):
        # Calculate knockback direction
        enemy.take_damage(self.damage, self.direction, self.knockback_force)
        enemy.got_hit = True
        
        self.hit_enemies.append(enemy)
        
        if self.pierce_count > 0:
            self.pierce_count -= 1
        else:
            self.kill()
    def update(self, dt):
        self.timer += dt
        if self.timer >= self.lifespan:
            self.kill()
            
        # Movement
        self.pos += self.direction * self.speed * dt
        self.rect.center = self.pos
        self.hitbox.center = self.pos
        
        self.check_collisions()
