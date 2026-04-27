import random 
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
        self.hp = 50
        self.max_hp = 50
        self.invulnerability_duration = 0
        
        # Wandering logic
        self.wander_waypoint = None
        self.wander_waypoint_radius = 40
        self.idle_duration = random.uniform(2, 4)
        self.idle_timer = 0
        
        self.spawn_pos = vect(pos)
        self.state = EnemyIdle(self)  # Initial AI state
        self.frict = -10 # Custom friction for enemies (lower = more slide)

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
        if distance < self.detection_radius:
            direction = self.scene.player.pos - self.pos
            if direction.length() < 1:
                return vect(1, 0)  
            return direction.normalize()
        return None
    
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
            self.scene.player.take_damage(self.contact_damage, hit_direction)
            self.contact_cooldown_timer = self.contact_cooldown
    
    def save_data(self):
        #Returns a dict for persistent state ddata
        return {
            'pos': (self.pos.x, self.pos.y),
            'is_chasing': self.is_chasing,
            'spawn_pos': (self.spawn_pos.x, self.spawn_pos.y),
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
            
    def is_wall_at(self, pos):
        # Helper to check if a specific position overlaps with collision tiles or map boundaries
        temp_rect = self.hitbox.copy()
        temp_rect.center = pos
        
        # 1. Check Map Boundaries
        map_w, map_h = self.scene.camera.scene_size
        if temp_rect.left < 0 or temp_rect.right > map_w or \
           temp_rect.top < 0 or temp_rect.bottom > map_h:
            return True

        # 2. Check Collision Tiles
        for sprite in self.scene.block_sprites:
            if temp_rect.colliderect(sprite.hitbox):
                return True
        return False

    def steer_to_direction(self, target_direction, dt, look_ahead=16, responsiveness=5.0, num_dir=8):
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
            self.move_direction += (chosen_dir - self.move_direction) * responsiveness * dt
            if self.move_direction.length() > 0:
                self.move_direction.normalize_ip()
    
    def update(self, dt):
        player_direction = self.detect_player()
        
        # AI state transitions
        new_state = self.state.enter_state(self, player_direction)
        if new_state:
            self.state = new_state
            
        # Update HP & I-frame timers (from base class logic)
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
    
    def enter_state(self, enemy, player_direction):
        if player_direction:
            return Chase(enemy)
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
        enemy.speed = 5
        
    def __str__(self):
        return "Wander"
    
    def enter_state(self, enemy, player_direction):
        if player_direction:
            return Chase(enemy)
        
        if not enemy.wander_waypoint:
            enemy.pick_waypoint()
            
        direction = enemy.wander_waypoint - enemy.pos
        
        # Return to idle if we reached the destination
        if direction.length() < 20: # 20 px threshold
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
        enemy.speed = 20
        
    def __str__(self):
        return "Chase"

    def enter_state(self, enemy, player_direction):
        if not player_direction:
            enemy.is_chasing = False
            return EnemyIdle(enemy)
        return None
    
    def update(self, dt, enemy):
        player_direction = enemy.detect_player()
        if not player_direction:
            self.lose_timer -= dt
            # Move towards last known direction or just slow down
            enemy.move_direction *= 0.9
        else:
            enemy.steer_to_direction(player_direction, dt)

        enemy.movement()
        enemy.animate(f'run-{enemy.get_direction()}', 15, dt)
