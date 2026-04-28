import pygame
import random
from settings import *
from characters import GameCharacter

class Player(GameCharacter):
    def __init__(self, game, scene, groups, pos, z ,name, direction='right'):
        super().__init__(game, scene, groups, pos, z, name, direction)
        self.hitbox = self.rect.copy().inflate(-self.rect.width + 9, -self.rect.height + 1) # Custom mvment hitbox for player
        self.combat_hitbox = self.rect.copy().inflate(-5, -1) # Custom for combat hitbox
        self.combat_hitbox.center = self.rect.center
        self.state = Idle(self)
        self.speed = 90
        self.throw_damage = random.randint(15, 20)
        
        # Tumble cooldown and usage
        self.tumble_charges = 2
        self.tumble_max_charges = 2
        self.tumble_cooldown = 1.1
        self.tumble_cooldown_timer = 0
        self.tumble_speed = 450
        # Player HP & Invincibility
        self.hp = HP_CONFIG['player_max_hp']
        self.max_hp = HP_CONFIG['player_max_hp']
        
        self.regen_delay_timer = 0 # Cooldown after taking  dmg
        self.hp_regen = HP_CONFIG['player_hp_regen']
        self.knockback_speed = 250
        
        self.throw_vel = 600
        self.throw_rate = 20
        self.last_click = None
        
    @property
    def is_low_hp(self):
        return self.hp <= (self.max_hp / 2)

    def take_damage(self, amount, knockback_dir=None, knockback_stun=0.25):
        super().take_damage(amount, knockback_dir, knockback_stun)
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
                self.scene.new_scene = SCENE_DATA[int(self.scene.current_scene)][int(exit.number)]
                self.scene.entry_point = exit.number # ID of the door to spawn at in the next scene
                self.scene.transition.exiting = True # Start the visual fade out

    def save_data(self):
          # Return player data
          return {
            'hp': self.hp,
            'tumble_charges': self.tumble_charges,
            'tumble_cooldown_timer': self.tumble_cooldown_timer,
            'regen_delay_timer': self.regen_delay_timer
        }
    
    def load_data(self, data):
        # Restore player data
        if not data:
            return
        
        self.hp = data.get('hp', self.max_hp) 
        self.tumble_charges = data.get('tumble_charges', self.tumble_charges)
        self.tumble_cooldown_timer = data.get('tumble_cooldown_timer', self.tumble_cooldown_timer)
        self.regen_delay_timer = data.get('regen_delay_timer', self.regen_delay_timer)

    @property
    def is_low_hp(self):
        return self.hp <= self.max_hp / 2

    def update(self, dt):
        super().update(dt)
        self.exit_scene()
        
        # Recharge tumble during Run/Idle not on Tumble
        if self.tumble_charges < self.tumble_max_charges and not isinstance(self.state, Tumble):
            self.tumble_cooldown_timer -= dt
            if self.tumble_cooldown_timer <= 0:
                self.tumble_charges += 1
                self.tumble_cooldown_timer = self.tumble_cooldown
        
        # HP & I-frame timers
        self.update_regen(dt)
        
        if self.hp <= 0:
            self.scene.start_death_sequence() # # Trigger death seq
        
        if INPUTS['backspace']:
            self.take_damage(10)
            
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

        if is_inputting_movement and player.vel.magnitude() > 0.5: # Any movement transition to Run class
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
        self.spawned = False
        # Randomize which throw animation to use
        self.rand_anim = random.choice(['throw2', 'throw3'])

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
        # Once animation finishes, return to idle
        if int(player.frame_index) >= len(player.animations[f'{self.rand_anim}-{player.get_direction()}']) - 1:
            return Idle(player)
        return None

    def update(self, dt, player):
        player.animate(f'{self.rand_anim}-{player.get_direction()}', player.throw_rate, dt, False)

        # Spawn projectile at the "release" frame (mine is 4)

        if int(player.frame_index) == 4 and not self.spawned:
            self.spawn_dagger(player)
            self.spawned = True

        GameCharacter.movement(player) 
        player.physics(dt, player.frict)


    def spawn_dagger(self, player):
        from projectiles import Projectile
        # Use the captured target world position from the start of the throw
        direction = (self.target_world_pos - player.pos)
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = vect(1, 0) # Fallback to right
            
        # Spawn the dagger
        Projectile(
            player.scene,
            [player.scene.update_sprites, player.scene.draw_sprites],
            player.pos,
            direction,
            speed=player.throw_vel,
            damage=player.throw_damage,
            sprite_path='assets\characters\player\weapon\dagger.png'
        )

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