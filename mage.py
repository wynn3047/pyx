import pygame
import random
from settings import *
from enemy import Enemy, EnemyIdle, Death, Wander
from characters import GameCharacter

class Explosion(pygame.sprite.Sprite):
    def __init__(self, scene, pos, groups, radius=20):
        super().__init__(*groups)
        self.scene = scene
        self.z = 'blocks'
        
        self.frames = self.scene.game.get_images('assets/characters/mage/explosion')
        self.frame_index = 0
        self.animation_speed = 12
        self.image = self.frames[0]
        
        self.rect = self.image.get_rect(midbottom=pos) # So it matches the sprite
        self.pos = vect(pos) 
        
        self.damage_frames = [2, 3, 4, 5, 6]
        self.has_damaged = False
        self.explosion_radius = radius 
        self.damage = random.uniform(40, 55)
        self.explosion_knockback = 450
        
    def update(self, dt):
        self.frame_index += self.animation_speed * dt
        if int(self.frame_index) < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
            
            if int(self.frame_index) in self.damage_frames and not self.has_damaged:
                if self.scene.player:
                    # Check distance from explosion center to player center
                    dist = self.pos.distance_to(self.scene.player.pos)
                    if dist < self.explosion_radius:
                        hit_dir = (self.scene.player.pos - self.pos)
                        if hit_dir.length() > 0: 
                            hit_dir.normalize_ip()
                            
                        self.scene.player.take_damage(self.damage, hit_dir, self.explosion_knockback)
                        self.has_damaged = True
        else:
            self.kill()

class Mage(Enemy):
    def __init__(self, game, scene, groups, pos, z, name, direction='right'):
        super().__init__(game, scene, groups, pos, z, name, direction)
        
        # Stats Overrides
        self.hp = 30
        self.max_hp = 30
        self.wander_speed = 30
        self.chase_speed = 0 
        
        self.attack_radius = 150
        self.cast_duration = 0.6
        self.aoe_radius = 20
        
        self.attack_cooldown = 1.8
        self.attack_cooldown_timer = 0
        
        self.knockback_speed = 50 
        self.frict = 10
        self.stun_resistance = 0.02
        
        self.contact_damage = 0
        self.state = MageIdle(self)
        self.target_pos = None 

    def take_damage(self, amount, knockback_dir=None, knockback_force=None, knockback_stun=0.25):
        GameCharacter.take_damage(self, amount, knockback_dir, knockback_force, knockback_stun)
        self.aggro_timer = self.aggro_duration
        self.got_hit = True

    def get_direction(self):
        if self.scene.player:
            player_dir = (self.scene.player.pos - self.pos)
            if player_dir.length() < self.detection_radius:
                if player_dir.x > 0:
                    self.last_direction = 'right'
                elif player_dir.x < 0:
                    self.last_direction = 'left'
                return self.last_direction
        return self.last_direction

    def check_player_contact(self, dt):
        pass

    def update(self, dt):
        if self.hp <= 0 and not isinstance(self.state, Death):
            self.state = Death(self)
            
        if self.aggro_timer > 0:
            self.aggro_timer -= dt
            
        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= dt
            
        if self.invulnerable:
            self.invulnerability_timer -= dt
            if self.invulnerability_timer <= 0:
                self.invulnerable = False
                
        if self.hit_flash_timer > 0: 
            self.hit_flash_timer -= dt
            
        if self.transparent_flicker_timer > 0: 
            self.transparent_flicker_timer -= dt
            
        if self.knockback_timer > 0: 
            self.knockback_timer -= dt

        if isinstance(self.state, Death):
            self.state.update(dt, self)
        else:
            new_state = self.state.enter_state(self)
            if new_state: self.state = new_state
            self.state.update(dt, self)
            self.check_player_contact(dt)
            self.get_direction()
            self.physics(dt, self.frict)

class MageIdle(EnemyIdle):
    def __init__(self, mage):
        super().__init__(mage)
        mage.speed = mage.wander_speed
        
    def __str__(self): 
        return "MageIdle"
    
    def enter_state(self, mage):
        if mage.attack_cooldown_timer <= 0 and mage.scene.player:
            dist = mage.pos.distance_to(mage.scene.player.pos)
            if dist < mage.attack_radius or mage.got_hit:
                mage.got_hit = False
                return MageCast(mage)
            
        if mage.idle_timer <= 0: return MageWander(mage)
        return None
    
    def update(self, dt, mage):
        mage.idle_timer -= dt
        mage.move_direction = vect(0, 0)
        mage.movement() # Ensures accel is zeroed
        mage.animate(f'idle-{mage.get_direction()}', 10, dt)

class MageWander(Wander):
    def __init__(self, mage):
        super().__init__(mage)
        mage.speed = mage.wander_speed
        
    def __str__(self): 
        return "MageWander"
    
    def enter_state(self, mage):
        if mage.attack_cooldown_timer <= 0 and mage.scene.player:
            dist = mage.pos.distance_to(mage.scene.player.pos)
            if dist < mage.attack_radius or mage.got_hit:
                mage.got_hit = False
                mage.vel = vect(0,0)
                return MageCast(mage)
            
        if not mage.wander_waypoint: 
            mage.pick_waypoint()
            
        direction = mage.wander_waypoint - mage.pos
        if direction.length() < 32:
            mage.vel = vect(0, 0)
            return MageIdle(mage)
        return None
    
    def update(self, dt, mage): 
        super().update(dt, mage)

class MageCast:
    def __init__(self, mage):
        mage.frame_index = 0
        self.timer = mage.cast_duration
        mage.speed = mage.wander_speed * 0.7 
        
        if mage.scene.player:
            # Pick a random point within a 16px radius of the player
            angle = random.uniform(0, 360)
            dist = random.uniform(0, 16)
            offset = vect(dist, 0).rotate(angle)
            mage.target_pos = vect(mage.scene.player.pos) + offset
        else:
            mage.target_pos = vect(mage.pos)
        mage.pick_waypoint()
        
    def __str__(self): 
        return "MageCast"
    
    def enter_state(self, mage):
        if self.timer <= 0:
            Explosion(mage.scene, mage.target_pos, [mage.scene.update_sprites, mage.scene.draw_sprites], radius=mage.aoe_radius)
            mage.attack_cooldown_timer = mage.attack_cooldown
            return MageIdle(mage)
        return None
    
    def update(self, dt, mage):
        self.timer -= dt
        
        if not mage.wander_waypoint:
            mage.pick_waypoint()
        direction = mage.wander_waypoint - mage.pos
        
        if direction.length() > 0:
            mage.steer_to_direction(direction.normalize(), dt)
        mage.movement()
        anim_base = 'idle'
        
        if mage.vel.length() > 5:
            anim_base = 'run'
        if f'cast-{mage.get_direction()}' in mage.animations: 
            anim_base = 'cast'
        mage.animate(f'{anim_base}-{mage.get_direction()}', 12, dt)
