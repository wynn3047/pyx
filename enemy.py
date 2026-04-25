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

        # Movement & Stats
        self.speed = 40
        self.detection_radius = 150
        self.is_chasing = False
        
        # Combat
        self.contact_damage = 5
        self.contact_cooldown = 1
        self.contact_cooldown_timer = 0
        
        # Feedback
        self.knocked_back = False
        self.knockback_timer = 0
        
        # Wandering logic
        self.wander_waypoint = None
        self.wander_waypoint_radius = 40
        self.idle_duration = 2 
        self.idle_timer = 0
        
        self.spawn_pos = vect(pos)
        self.state = EnemyIdle(self)  # Initial AI state
        
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
        #Picks a random point around the spawn position to walk towards
        angle = random.uniform(0, 360)
        distance = random.uniform(20, self.wander_waypoint_radius)
        direction = vect(1, 0).rotate(angle)
        self.wander_waypoint = self.spawn_pos + (direction * distance)
        
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
            
        if 'spawn_pos' in data:
            x, y = data['spawn_pos']
            self.spawn_pos = vect(x, y)
            
    def is_wall_at(self, pos):
        # Helper to check if a specific position overlaps with collision tiles
        temp_rect = self.hitbox.copy()
        temp_rect.center = pos
        for sprite in self.scene.block_sprites:
            if temp_rect.colliderect(sprite.hitbox):
                return True
        return False

    def steer_to_direction(self, target_direction, dt, look_ahead=16, responsiveness=5.0, num_dir=8):
        # Calculates 'interest' in directions towards target vs 'danger' of hitting walls
        if not target_direction or target_direction.length() == 0:
            return

        # Setup sample directions 
        directions = [vect(1, 0).rotate(i * 45) for i in range(num_dir)]
        
        # Score directions based on target alignment (Interest)
        interest = [max(0, d.dot(target_direction)) for d in directions]

        # Detect obstacles in sample directions (Danger)
        danger = [0.0] * 8
        for i, d in enumerate(directions):
            if self.is_wall_at(self.pos + d * look_ahead): 
                danger[i] = 1.0
                # Add buffer to neighbors to prevent clipping corners
                danger[(i-1) % 8] += 0.5 
                danger[(i+1) % 8] += 0.5

        # Resolve the best direction by subtracting danger from interest
        chosen_dir = vect(0, 0)
        max_score = -float('inf')
        for i in range(8):
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
        
        # Handle state transitions and execution
        new_state = self.state.enter_state(self, player_direction)
        if new_state:
            self.state = new_state

        self.state.update(dt, self)
        self.check_player_contact(dt)
        self.get_direction()
        self.physics(dt, -3)

class EnemyIdle:
    """State when enemy is standing still."""
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
        enemy.animate(f'idle-{enemy.get_direction()}', 10 * dt)


class Wander:
    """State when enemy is moving towards a random waypoint."""
    def __init__(self, enemy):
        enemy.frame_index = 0
        enemy.stuck_timer = 0
        
    def __str__(self):
        return "Wander"
    
    def enter_state(self, enemy, player_direction):
        if player_direction:
            return Chase(enemy)
        
        if not enemy.wander_waypoint:
            enemy.pick_waypoint()
            
        direction = enemy.wander_waypoint - enemy.pos
        
        # Return to idle if we reached the destination
        if direction.length() < 10:
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
        enemy.animate(f'run-{enemy.get_direction()}', 15 * dt)
        
class Chase:
    # State when enemy is actively pursuing the player
    def __init__(self, enemy):
        enemy.frame_index = 0
        enemy.is_chasing = True
        
    def __str__(self):
        return "Chase"

    def enter_state(self, enemy, player_direction):
        if not player_direction:
            enemy.is_chasing = False
            return EnemyIdle(enemy)
        return None
    
    def update(self, dt, enemy):
        player_direction = enemy.detect_player()
        if player_direction:
            enemy.steer_to_direction(player_direction, dt)
        else:
            enemy.move_direction = vect(0, 0)

        enemy.movement()
        enemy.animate(f'run-{enemy.get_direction()}', 15 * dt)
