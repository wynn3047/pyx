import pygame
import random 
import math
from settings import * 
from characters import GameCharacter

class Enemy(GameCharacter):
    """
    Base enemy class. Handles AI state management, movement steering, 
    and player detection/interaction.
    """
    def __init__(self, game, scene, groups, pos, z, name, direction='right'):
        super().__init__(game, scene, groups, pos, z, name, direction)
        self.combat_hitbox = self.rect.copy().inflate(-16, -3)
        self.detection_radius = 150
        self.is_chasing = False
        
        # Combat
        self.contact_damage = random.randint(25, 40)
        self.contact_cooldown = 1
        self.contact_cooldown_timer = 0
        self.hp = 40
        self.max_hp = 40
        self.invulnerability_duration = 0
        
        # Wandering logic
        self.wander_waypoint = None
        self.wander_waypoint_radius = 60
        self.idle_duration = random.uniform(2, 4)
        self.idle_timer = 0
        
        # Aggro / Memory
        self.aggro_timer = 0
        self.aggro_duration = 4 # Stay aggroed for 4s after hit or detection
        
        self.spawn_pos = vect(pos)
        self.contact_knockback = HP_CONFIG['enemy_contact_knockback']
        self.state = EnemyIdle(self)  # Initial AI state
        self.frict = 10 
        self.knockback_speed = 50
        self.got_hit = False

    def movement(self):
        # Disable AI movement intent during knockback
        if self.knockback_timer > 0:
            self.move_direction = vect(0, 0)
        super().movement()
        
    def detect_player(self): 
        # Checks if player is within range. Returns normalized direction vector if found
        if not self.scene.player:
            return None
            
        distance = self.pos.distance_to(self.scene.player.pos)
        
        # If aggroed, we ignore the radius (up to a reasonable map limit)
        if self.aggro_timer > 0 or distance < self.detection_radius:
            direction = self.scene.player.pos - self.pos
            if direction.length() < 1:
                return vect(1, 0)  
            
            # Refresh aggro timer if player is still within normal detection range
            if distance < self.detection_radius:
                self.aggro_timer = self.aggro_duration
                
            return direction.normalize()
        return None
    
    def start_chase(self):
        # Only switch if not already in Chase state
        if not isinstance(self.state, Chase):
            self.state = Chase(self)
    
    def take_damage(self, amount, knockback_dir=None, knockback_stun=0.25):
        # Keep existing knockback logic
        super().take_damage(amount, knockback_dir, knockback_stun)
        # Set aggro timer and force a state transition to Chase
        self.aggro_timer = self.aggro_duration
        self.state = Chase(self)
        self.got_hit = True
        
    def pick_waypoint(self):
        # Picks a random point around the spawn position to walk towards
        map_w, map_h = self.scene.camera.scene_size
        
        angle = random.uniform(0, 360)
        distance = random.uniform(20, self.wander_waypoint_radius)
        direction = vect(1, 0).rotate(angle)
        
        target_pos = self.spawn_pos + (direction * distance)
        
        # Clamp target_pos within map boundaries
        target_pos.x = max(16, min(target_pos.x, map_w - 16))
        target_pos.y = max(16, min(target_pos.y, map_h - 16))
        
        self.wander_waypoint = target_pos
        
    def check_player_contact(self, dt):
        #Damages the player if they touch the enemy hitbox
        if not self.scene.player:
            return
            
        if self.contact_cooldown_timer > 0:
            self.contact_cooldown_timer -= dt
            return
            
        if self.combat_hitbox.colliderect(self.scene.player.combat_hitbox):
            hit_direction = (self.scene.player.pos - self.pos)
            if hit_direction.length() > 0:
                hit_direction.normalize_ip()  
            self.scene.player.take_damage(self.contact_damage, hit_direction, self.contact_knockback)
            self.contact_cooldown_timer = self.contact_cooldown
    
    def save_data(self):
        #Returns a dict for persistent state ddata
        return {
            'pos': (self.pos.x, self.pos.y),
            'is_chasing': self.is_chasing,
            'spawn_pos': (self.spawn_pos.x, self.spawn_pos.y),
            'hp': self.hp
        }
    
    def load_data(self, data):
        # Restores state from save data
        if not data:
            return
        
        if 'pos' in data:
            x, y = data['pos']
            self.pos = vect(x, y)
            self.rect.center = self.pos
            self.hitbox.center = self.pos
            self.combat_hitbox.center = self.pos
            
        if 'is_chasing' in data:
            self.is_chasing = data['is_chasing']
            if self.is_chasing:
                self.state = Chase(self) # Resume chase state immediately
            
        if 'spawn_pos' in data:
            x, y = data['spawn_pos']
            self.spawn_pos = vect(x, y)

        if 'hp' in data:
            self.hp = data['hp']
            
    def is_wall_at(self, pos):
        # Helper to check if a specific position overlaps with collision tiles or map boundaries
        temp_rect = self.hitbox.copy()
        temp_rect.center = pos
        
        # 1. Check Map Boundaries
        map_w, map_h = self.scene.camera.scene_size
        if (temp_rect.left < 0 or temp_rect.right > map_w or
           temp_rect.top < 0 or temp_rect.bottom > map_h):
            return True

        # 2. Check Collision Tiles
        for sprite in self.scene.block_sprites:
            if temp_rect.colliderect(sprite.hitbox):
                return True
        return False

    def steer_to_direction(self, target_direction, dt, look_ahead=17, responsiveness=5.0, num_dir=8):
        # Calculates 'interest' in directions towards target vs 'danger' of hitting walls/friends
        if not target_direction or target_direction.length() == 0:
            return

        # Setup sample directions 
        directions = [vect(1, 0).rotate(i * (360/num_dir)) for i in range(num_dir)]
        
        # 1. Score directions based on target alignment (Interest)
        interest = [max(0, d.dot(target_direction)) for d in directions]

        # 2. Detect obstacles (Danger)
        danger = [0.0] * num_dir
        for i, d in enumerate(directions):
            # WALL DANGER
            if self.is_wall_at(self.pos + d * look_ahead): 
                danger[i] += 1.0
                danger[(i-1) % num_dir] += 0.5 
                danger[(i+1) % num_dir] += 0.5
            
            # NEIGHBOR DANGER (Separation)
            # Check if any other enemy is in this direction
            for other in self.scene.enemy_sprites:
                if other == self: continue # Don't avoid yourself
                
                dist = self.pos.distance_to(other.pos)
                if dist < 24: # Separation radius
                    if dist > 0:
                        # Calculate direction to the other enemy
                        dir_to_other = (other.pos - self.pos).normalize()
                        # If this sample direction 'd' points towards the other enemy
                        dot_product = d.dot(dir_to_other)
                        if dot_product > 0.8: # Points roughly at them
                            danger[i] += 0.8 * (1.0 - dist/24) # More danger the closer they are
                    else:
                        # If exactly on top, apply max danger to all directions to force them apart
                        danger[i] += 1.0

        # Resolve the best direction by subtracting danger from interest
        chosen_dir = vect(0, 0)
        max_score = -float('inf')
        for i in range(num_dir):
            score = interest[i] - danger[i]
            if score > max_score:
                max_score = score
                chosen_dir = directions[i]

        # Smoothly transition the movement vector
        if chosen_dir.length() > 0:
            # Framerate independent LERP: v = v + (target - v) * (1 - exp(-rate * dt))
            lerp_factor = 1.0 - math.exp(-responsiveness * dt)
            self.move_direction += (chosen_dir - self.move_direction) * lerp_factor
            
            if self.move_direction.length() > 0:
                self.move_direction.normalize_ip()
    
    def update(self, dt):
        # Check for Death
        if self.hp <= 0 and not isinstance(self.state, Death):
            self.state = Death(self)

        # Timers
        if self.aggro_timer > 0:
            self.aggro_timer -= dt

        if self.invulnerable:
            self.invulnerability_timer -= dt
            if self.invulnerability_timer <= 0:
                self.invulnerable = False
                self.invulnerability_timer = 0
        
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= dt
            
        if self.transparent_flicker_timer > 0:
            self.transparent_flicker_timer -= dt

        if self.knockback_timer > 0:
            self.knockback_timer -= dt

        # State Logic
        if isinstance(self.state, Death):
            self.state.update(dt, self)
        else:
            player_direction = self.detect_player()
            
            # Transition to Chase if player detected or hit
            if (player_direction or self.got_hit) and not isinstance(self.state, Chase):
                self.got_hit = False
                self.state = Chase(self)
                
            new_state = self.state.enter_state(self)
            if new_state:
                self.state = new_state
            
            self.state.update(dt, self)
            self.check_player_contact(dt)
            self.get_direction()
            self.physics(dt, self.frict)

class EnemyIdle:
    # State when enemy is standing still
    def __init__(self, enemy):
        enemy.frame_index = 0
        enemy.idle_timer = enemy.idle_duration
    
    def __str__(self):
        return "EnemyIdle"
    
    def enter_state(self, enemy):
        if enemy.idle_timer <= 0:
            enemy.pick_waypoint()
            return Wander(enemy)
        return None
    
    def update(self, dt, enemy):
        enemy.idle_timer -= dt
        enemy.move_direction = vect(0, 0)
        enemy.movement()
        enemy.animate(f'idle-{enemy.get_direction()}', 10, dt)


class Wander:
    # State when enemy is moving towards a random waypoint
    def __init__(self, enemy):
        enemy.frame_index = 0
        enemy.speed = 25
        
    def __str__(self):
        return "Wander"
    
    def enter_state(self, enemy):
        if not enemy.wander_waypoint:
            enemy.pick_waypoint()
            
        direction = enemy.wander_waypoint - enemy.pos
        
        # Return to idle if we reached the destination
        if direction.length() < 32: # 32 px threshold
            enemy.vel = vect(0, 0)
            return EnemyIdle(enemy)
        
        return None

    def update(self, dt, enemy):
        if not enemy.wander_waypoint: 
            enemy.pick_waypoint()
            
        direction = enemy.wander_waypoint - enemy.pos
        if direction.length() > 0:
            enemy.steer_to_direction(direction.normalize(), dt)

        enemy.movement()
        enemy.animate(f'run-{enemy.get_direction()}', 15, dt)
        
class Chase:
    # State when enemy is actively pursuing the player
    def __init__(self, enemy):
        enemy.frame_index = 0
        enemy.is_chasing = True
        enemy.speed = 55
        enemy.force = 2250
        
    def __str__(self):
        return "Chase"

    def enter_state(self, enemy):
        # Only stop chasing if player is gone AND aggro timer is out
        if enemy.aggro_timer <= 0:
            enemy.is_chasing = False
            return EnemyIdle(enemy)
        return None
    
    def update(self, dt, enemy):
        player_direction = enemy.detect_player()
        if not player_direction:
            # Frame-rate independent decay
            enemy.move_direction *= math.exp(-10 * dt)
        else:
            enemy.steer_to_direction(player_direction, dt)

        enemy.movement()
        enemy.animate(f'run-{enemy.get_direction()}', 15, dt)
    
class Death:
    def __init__(self, enemy):
        enemy.frame_index = 0
        # Stop all movement
        enemy.vel = vect(0, 0)
        enemy.accel = vect(0, 0)
        enemy.move_direction = vect(0, 0)
        
        enemy.z = 'blocks'
        
        # Disable hitboxes
        enemy.hitbox = pygame.Rect(0,0,0,0)
        enemy.combat_hitbox = pygame.Rect(0,0,0,0)
        
        self.death_anim = f'death-{enemy.get_direction()}'
        self.despawn_timer = 7 # Linger time
        
    def __str__(self):
        return "Death"
        
    def enter_state(self, enemy):
        return None
        
    def update(self, dt, enemy):
        # Play animation once
        enemy.animate(self.death_anim, 13, dt, loop=False)
        
        # Once at last frame, wait to despawn
        if int(enemy.frame_index) >= len(enemy.animations[self.death_anim]) - 1:
            self.despawn_timer -= dt
            if self.despawn_timer <= 0:
                enemy.kill()
