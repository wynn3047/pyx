import pygame
import random
import math
from settings import *
from characters import GameCharacter

class Player(GameCharacter):
    def __init__(self, game, scene, groups, pos, z ,name, direction='right'):
        super().__init__(game, scene, groups, pos, z, name, direction)
        self.hitbox = self.rect.copy().inflate(-self.rect.width + 9, -self.rect.height + 1) # Custom mvment hitbox for player
        self.combat_hitbox = self.rect.copy().inflate(-5, -1) # Custom for combat hitbox
        self.combat_hitbox.center = self.rect.center
        self.hit_flash_color = COLORS['red']
        self.state = Idle(self)
        self.speed = 85
        
        # Tumble cooldown and usage
        self.tumble_charges = 2
        self.tumble_max_charges = 2
        self.tumble_cooldown = 1.5
        self.tumble_cooldown_timer = 0
        self.tumble_speed = 400
        # Player HP & Invincibility
        self.hp = HP_CONFIG['player_max_hp']
        self.max_hp = HP_CONFIG['player_max_hp']
        
        self.regen_delay_timer = 0 # Cooldown after taking  dmg
        self.hp_regen = HP_CONFIG['player_hp_regen']
        self.knockback_speed = 250
        
        self.throw_vel = 400
        self.throw_rate = 16.5 # Default 16.5
        self.throw_damage = random.uniform(10, 20)

        # Combat Upgrades
        self.proj_pierce = PLAYER_COMBAT_CONFIG['proj_pierce_count']
        self.proj_count = PLAYER_COMBAT_CONFIG['proj_count']
        self.proj_spread = PLAYER_COMBAT_CONFIG['proj_spread_angle']
        self.proj_burst_count = PLAYER_COMBAT_CONFIG['proj_burst_count']
        self.proj_burst_delay = PLAYER_COMBAT_CONFIG['proj_burst_delay']
        self.proj_ricochet = PLAYER_COMBAT_CONFIG['proj_ricochet_count']
        
        # Stealth System
        self.stealth = 0
        self.max_stealth = STEALTH_CONFIG['max_stealth']
        self.is_stealth_ready = False

    @property
    def is_low_hp(self):
        return self.hp <= (self.max_hp / 2)

    def update_stealth(self, dt):
        # Stealth fills faster when standing still
        regen = STEALTH_CONFIG['stealth_regen']
            
        self.stealth = min(self.max_stealth, self.stealth + regen * dt)
        self.is_stealth_ready = (self.stealth >= self.max_stealth)

    def take_damage(self, amount, knockback_dir=None, knockback_force=None, knockback_stun=0.3):
        super().take_damage(amount, knockback_dir, knockback_force, knockback_stun)
        self.regen_delay_timer = HP_CONFIG['player_regen_delay'] 

    def update_regen(self, dt):
        # Passive HP regen during only Idle/Run states
        if not isinstance(self.state, (Idle, Run)):
            return # exit
        
        # Cooldown after dmg
        if self.regen_delay_timer > 0:
            if isinstance(self.state, Idle): # Decrease regen delay when idling
                self.regen_delay_timer = max(0, self.regen_delay_timer - dt)
            self.regen_delay_timer = max(0, self.regen_delay_timer - dt)
            return # exit early if cooling down
            
        # Heal
        if self.hp < self.max_hp:
            if isinstance(self.state, Idle):
                self.hp = min(self.max_hp, self.hp + (self.hp_regen + 0.2) * dt)
            self.hp = min(self.max_hp, self.hp + self.hp_regen * dt)
    
    def get_heart_states(self):
        # Returns the HP ratio (0.0 to 1.0) for each heart
        ratios = []
        max_hearts = int(self.max_hp / HEART_CONFIG['hp_per_heart'])
        hp_per_heart = HEART_CONFIG['hp_per_heart']
        
        for heart_index in range(max_hearts):
            heart_start_hp = heart_index * hp_per_heart
            hp_in_heart = max(0, min(self.hp - heart_start_hp, hp_per_heart))
            ratio = hp_in_heart / hp_per_heart
            ratios.append(ratio)
        
        return ratios
            
            
    def movement(self):
        if self.knockback_timer > 0:
            self.move_direction = vect(0, 0)
        else:
            x = int(INPUTS['right']) - int(INPUTS['left'])
            y = int(INPUTS['down']) - int(INPUTS['up'])
            self.move_direction = vect(x, y)
            if self.move_direction.length() > 1:
                self.move_direction.normalize_ip()
        super().movement()

    def vect_to_mouse(self, speed):
        # Dash to mouse pointer
        direction = vect(pygame.mouse.get_pos()) - (vect(self.rect.center) - vect(self.scene.camera.offset))
        if direction.length() > 0: direction.normalize_ip()
        return direction * speed
    
    def exit_scene(self):
        # Scan for collisions with exit trigger boxes
        for exit in self.scene.exit_sprites:
            if self.hitbox.colliderect(exit.rect):
                # Retrieve destination scene and entry point from settings
                # Use strings for consistent lookup
                current_scene_id = str(self.scene.current_scene)
                exit_id = str(exit.number)
                
                if current_scene_id in SCENE_DATA and exit_id in SCENE_DATA[current_scene_id]:
                    self.scene.new_scene = SCENE_DATA[current_scene_id][exit_id]
                    self.scene.entry_point = exit_id # ID of the door to spawn at in the next scene
                    self.scene.transition.exiting = True # Start the visual fade out

    def save_data(self):
          # Return player data
          return {
            'hp': self.hp,
            'tumble_charges': self.tumble_charges,
            'tumble_cooldown_timer': self.tumble_cooldown_timer,
            'regen_delay_timer': self.regen_delay_timer,
            'stealth': self.stealth,
            'proj_count': self.proj_count,
            'proj_pierce': self.proj_pierce,
            'proj_ricochet': self.proj_ricochet,
            'proj_spread': self.proj_spread,
            'proj_burst_count': self.proj_burst_count
        }
    
    def load_data(self, data):
        # Restore player data
        if not data:
            return
        
        self.hp = data.get('hp', self.max_hp) 
        self.tumble_charges = data.get('tumble_charges', self.tumble_charges)
        self.tumble_cooldown_timer = data.get('tumble_cooldown_timer', self.tumble_cooldown_timer)
        self.regen_delay_timer = data.get('regen_delay_timer', self.regen_delay_timer)
        self.stealth = data.get('stealth', 0)
        self.proj_count = data.get('proj_count', self.proj_count)
        self.proj_pierce = data.get('proj_pierce', self.proj_pierce)
        self.proj_ricochet = data.get('proj_ricochet', self.proj_ricochet)
        self.proj_spread = data.get('proj_spread', self.proj_spread)
        self.proj_burst_count = data.get('proj_burst_count', self.proj_burst_count)

    def fire_projectile_shot(self, target_world_pos, is_stealth_strike=False):
        from projectiles import Projectile
        
        # Base stats
        damage = self.throw_damage
        speed = self.throw_vel
        count = self.proj_count
        pierce = self.proj_pierce
        ricochet = self.proj_ricochet
        
        # Apply Stealth Strike Multipliers
        if is_stealth_strike:
            damage *= STEALTH_CONFIG['damage_mult']
            speed *= STEALTH_CONFIG['velocity_mult']
            count += STEALTH_CONFIG['count_add']
            pierce += STEALTH_CONFIG['pierce_add']
            ricochet += STEALTH_CONFIG['ricochet_add']

        # Base direction to target
        base_direction = (target_world_pos - self.pos)
        if base_direction.length() > 0:
            base_direction = base_direction.normalize()
        else:
            base_direction = vect(1, 0)
            
        base_angle = math.degrees(math.atan2(base_direction.y, base_direction.x))
        
        # Calculate spread angles
        if count > 1 and self.proj_spread > 0:
            angle_step = self.proj_spread / (count - 1)
            start_angle = base_angle - self.proj_spread / 2
            angles = [start_angle + i * angle_step for i in range(count)]
        else:
            angles = [base_angle]
            
        # Spawn projectiles
        for angle in angles:
            direction = vect(1, 0).rotate(angle)
            Projectile(
                self.scene,
                [self.scene.update_sprites, self.scene.draw_sprites],
                self.pos,
                direction,
                speed=speed,
                damage=damage,
                knockback_force=HP_CONFIG['player_dagger_knockback'],
                pierce_count=pierce,
                ricochet_count=ricochet,
                sprite_path='assets\characters\player\weapon\dagger.png'
            )

    def update(self, dt):
        if self.hp <= 0:
            if not isinstance(self.state, Death):
                self.state = Death(self)
                self.scene.start_death_sequence()
            super().update(dt)
            return

        super().update(dt)
        self.exit_scene()
        self.update_stealth(dt)
        
        # Recharge tumble during Run/Idle not on Tumble
        if self.tumble_charges < self.tumble_max_charges and not isinstance(self.state, Tumble):
            self.tumble_cooldown_timer -= dt
            if self.tumble_cooldown_timer <= 0:
                self.tumble_charges += 1
                self.tumble_cooldown_timer = self.tumble_cooldown
        
        # HP & I-frame timers
        self.update_regen(dt)
        
        if INPUTS['backspace']:
            self.take_damage(150, vect(0,0), 0)
            self.proj_count -= 1
            
class Idle:     
    def __init__(self, player):
        player.frame_index = 0 # Reset frame index

    def __str__(self):
        return self.__class__.__name__

    def enter_state(self, player):
        x = int(INPUTS['right']) - int(INPUTS['left'])
        y = int(INPUTS['down']) - int(INPUTS['up'])
        is_inputting_movement = (x != 0 or y != 0)
        
        if INPUTS['left_click']:
            return Throw(player)

        if is_inputting_movement and player.vel.magnitude() > 1: # Any movement transition to Run class
            return Run(player)

        if INPUTS['space'] and player.tumble_charges > 0:
            return Tumble(player)

    def update(self, dt, player):
        player.animate(f'idle-{player.get_direction()}', 10, dt)
        player.movement()
        player.physics(dt, player.frict)

class Run:
    def __init__(self, player):
        Idle.__init__(self, player)

    def __str__(self):
        return self.__class__.__name__

    def enter_state(self, player):
        x = int(INPUTS['right']) - int(INPUTS['left'])
        y = int(INPUTS['down']) - int(INPUTS['up'])
        is_inputting_movement = (x != 0 or y != 0)
        
        if INPUTS['left_click']:
            return Throw(player)

        if INPUTS['space'] and player.tumble_charges > 0:
            return Tumble(player)

        if not is_inputting_movement: # Flip back to idle
            return Idle(player)

    def update(self, dt, player):
        player.animate(f'run-{player.get_direction()}', 15, dt)
        player.movement()
        player.physics(dt, player.frict)

class Throw:
    def __init__(self, player):
        player.frame_index = 0
        player.regen_delay_timer = HP_CONFIG['player_regen_delay'] 
        
        # Stealth Strike detection
        self.is_stealth_strike = player.is_stealth_ready
        if self.is_stealth_strike:
            self.rand_anim = 'throw1' # Force stealth animation
        else:
            # Randomize normal throw
            self.rand_anim = random.choice(['throw2', 'throw3'])

        # Burst logic
        self.bursts_left = player.proj_burst_count
        self.burst_timer = 0
        self.started_firing = False

        # Capture target position at the moment of the click
        mouse_pos = vect(pygame.mouse.get_pos())
        self.target_world_pos = mouse_pos + player.scene.camera.offset
        
        # Determine direction based on captured target
        if self.target_world_pos.x >= player.pos.x:
            player.last_direction = 'right'
        else:
            player.last_direction = 'left'

        # Kill all momentum and movement intent
        player.vel = vect(0, 0)
        player.accel = vect(0, 0)
        player.move_direction = vect(0, 0)


    def __str__(self):
        return "Throw"

    def enter_state(self, player):
        # Once animation finishes AND all bursts are fired, return to idle
        anim_finished = int(player.frame_index) >= len(player.animations[f'{self.rand_anim}-{player.get_direction()}']) - 1
        burst_finished = self.bursts_left <= 0
        
        if anim_finished and burst_finished:
            return Idle(player)
        
        if INPUTS['space'] and player.tumble_charges > 0:
            return Tumble(player)
        return None

    def update(self, dt, player):
        player.animate(f'{self.rand_anim}-{player.get_direction()}', player.throw_rate, dt, False)

        # Handle Burst Firing
        if int(player.frame_index) >= 4:
            self.started_firing = True
            
        if self.started_firing and self.bursts_left > 0:
            if self.burst_timer <= 0:
                player.fire_projectile_shot(self.target_world_pos, self.is_stealth_strike)
                self.bursts_left -= 1
                self.burst_timer = player.proj_burst_delay
                
                # Consume Stealth
                if self.is_stealth_strike:
                    player.stealth = 0 # Full reset for strike
                else:
                    player.stealth = max(0, player.stealth - STEALTH_CONFIG['attack_consumption'])
            else:
                self.burst_timer -= dt

        GameCharacter.movement(player) 
        player.physics(dt, player.frict)


class Tumble:
    def __init__(self, player):
        Idle.__init__(self, player)
        INPUTS['space'] = False
        self.timer = 0.45 
        self.dash_pending = False # Input buffer
        self.vel = player.vect_to_mouse(player.tumble_speed) 
        player.tumble_charges -= 1 # Consume a charge
        player.tumble_cooldown_timer = player.tumble_cooldown
        
    def __str__(self):
        return self.__class__.__name__

    def enter_state(self, player):
        if INPUTS['space'] and player.tumble_charges > 0: # Prevent from buffering further
            self.dash_pending = True # Buffer input to chain tumbles

        if self.timer < 0:
            if self.dash_pending:
                return Tumble(player) # Start a new tumble immediately
            else:
                return Idle(player) # Go back to standing

    def update(self, dt, player):
        self.timer -= dt
        player.animate(f'tumble-{player.get_direction()}', 18, dt, False) # Play tumble animation once

        player.physics(dt, 5) # Apply physics with low friction to slide
        player.accel = vect() # No acceleration during tumble
        player.vel = self.vel # Maintain dash velocity towards target
        
class Death:
    # Death state: Play death animation, no movement, no state transitions
    
    def __init__(self, player):
        player.frame_index = 0
        # Kill all momentum
        player.vel = vect(0, 0)
        player.accel = vect(0, 0)
        player.move_direction = vect(0, 0)
        self.anim_name = f'death-{player.get_direction()}'
        # Disable hitboxes
        player.hitbox = pygame.Rect(0,0,0,0)
        player.combat_hitbox = pygame.Rect(0,0,0,0)
        
    def __str__(self):
        return "Death"
    
    def enter_state(self, player):
        return None  # Never transition out (Scene handles restart)
    
    def update(self, dt, player):
        player.animate(self.anim_name, 14, dt, loop=False)
        # Kill all movement intent
        player.vel = vect(0, 0)
        player.accel = vect(0, 0)
        player.move_direction = vect(0, 0)
        # Sync rect to position
        player.rect.center = player.pos
