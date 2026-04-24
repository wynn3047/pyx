import pygame
from settings import *
from characters import GameCharacter

class Player(GameCharacter):
    def __init__(self, game, scene, groups, pos, z ,name, direction='right'):
        super().__init__(game, scene, groups, pos, z, name, direction)
        self.hitbox = self.rect.copy().inflate(-self.rect.width + 9, -self.rect.height + 1) # Custom hitbox for player
        self.state = Idle(self)

    def movement(self):
        # X inputs
        if INPUTS['left']: self.accel.x = -self.force
        elif INPUTS['right']: self.accel.x = self.force
        else:
            self.accel.x = 0

        # Y inputs
        if INPUTS['up']: self.accel.y = -self.force
        elif INPUTS['down']: self.accel.y = self.force
        else: self.accel.y = 0

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
                
    def update(self, dt):
        self.get_direction()
        self.exit_scene()
        self.change_state()
        self.state.update(dt, self)  
        
class Idle:     
    def __init__(self, player):
        player.frame_index = 0 # Reset frame index

    def __str__(self):
        return self.__class__.__name__

    def enter_state(self, player):
        if player.vel.magnitude() > 1: # Any movement transition to Run class
            return Run(player)

        if INPUTS['space']:
            return Tumble(player)

    def update(self, dt, player):
        player.animate(f'idle-{player.get_direction()}', 10 * dt)
        player.movement()
        player.physics(dt, player.frict)

class Run:
    def __init__(self, player):
        Idle.__init__(self, player)

    def __str__(self):
        return self.__class__.__name__

    def enter_state(self, player):
        if INPUTS['space']:
            return Tumble(player)

        if player.vel.magnitude() < 1: # Flip back to idle
            return Idle(player)

    def update(self, dt, player):
        player.animate(f'run-{player.get_direction()}', 15 * dt)
        player.movement()
        player.physics(dt, player.frict)

class Tumble:
    def __init__(self, player):
        Idle.__init__(self, player)
        INPUTS['space'] = False
        self.timer = 0.45 # Animation timer
        self.dash_pending = False # Input buffer
        self.vel = player.vect_to_mouse(300) 

    def __str__(self):
        return self.__class__.__name__

    def enter_state(self, player):
        if INPUTS['space']:
            self.dash_pending = True # Buffer input to chain tumbles

        if self.timer < 0:
            if self.dash_pending:
                return Tumble(player) # Start a new tumble immediately
            else:
                return Idle(player) # Go back to standing

    def update(self, dt, player):
        self.timer -= dt
        player.animate(f'tumble-{player.get_direction()}', 18 * dt, False) # Play tumble animation once

        player.physics(dt, -5) # Apply physics with low friction to slide
        player.accel = vect() # No acceleration during tumble
        player.vel = self.vel # Maintain dash velocity towards target