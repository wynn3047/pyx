import pygame
import math
from settings import *

class Projectile(pygame.sprite.Sprite):
    def __init__(self, scene, groups, pos, direction, speed, damage, sprite_path):
        super().__init__(groups)
        self.scene = scene
        self.z = 'holes' 
        
        self.original_image = pygame.image.load(sprite_path).convert_alpha()
        
        self.pos = vect(pos)
        self.direction = direction
        self.speed = speed
        self.damage = damage
        
        # Sprite points UP, adjust by 90 degrees.
        angle = math.degrees(math.atan2(-direction.y, direction.x)) - 90
        self.image = pygame.transform.rotate(self.original_image, angle)
        
        self.rect = self.image.get_rect(center=pos)
        # Narrow hitbox for precision
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.85, -self.rect.height * 0.85)
        
        self.lifespan = 2 # Seconds before disappearing
        self.timer = 0

    def check_collisions(self):
        # Check Walls & Holes
        from objects import Holes
        for wall in self.scene.block_sprites:
            if self.hitbox.colliderect(wall.hitbox) and not isinstance(wall, Holes):
                self.on_wall_hit()
                return

        # Check Enemies
        for enemy in self.scene.enemy_sprites:
            if self.hitbox.colliderect(enemy.combat_hitbox):
                self.on_enemy_hit(enemy)
                return

    def on_wall_hit(self):
        self.kill()

    def on_enemy_hit(self, enemy):
        # Calculate knockback direction
        enemy.take_damage(self.damage, self.direction)
        enemy.got_hit = True
        self.kill() # Or not (piercing)
    def update(self, dt):
        self.timer += dt
        if self.timer >= self.lifespan:
            self.kill()
            
        # Movement
        self.pos += self.direction * self.speed * dt
        self.rect.center = self.pos
        self.hitbox.center = self.pos
        
        self.check_collisions()
