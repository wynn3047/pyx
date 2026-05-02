import pygame
import random
from settings import *
from camera import Camera
from transition import Transition
from player import Player
from objects import Collider,Object, Wall, Holes
from pytmx.util_pygame import load_pygame

class State:
    def __init__(self, game):
        self.game = game
        self.prev_state = None

    def enter_state(self):
        # Screen state handler [BACK > BACK > MAIN]
        if len(self.game.states) > 1:
            self.prev_state = self.game.states[-1]
        self.game.states.append(self)

    def exit_state(self):
        self.game.states.pop()

    def update(self, dt):
        pass

    def draw(self, screen):
        pass

class SplashScreen(State):
    # Screen before loading the game
    def __init__(self, game):
        super().__init__(game)
        self.transition = Transition()

    def start_game(self):
        # Reset transition for whenever we return to this screen
        self.transition.exiting = False
        self.transition.alpha = 255
        
        # Reset game data for freshstart
        self.game.player_data = {}
        self.game.scene_states = {}
        
        LoadingScreen(self.game, lambda: Scene(self.game, '0', '0')).enter_state()

    def update(self, dt):
        if INPUTS['enter'] and not self.transition.exiting:
            self.transition.exiting = True
            self.transition.callback = self.start_game
            self.game.reset_inputs()
        
        self.transition.update(dt)

    def draw(self, screen):
        screen.fill((COLORS['charcoal_grey']))
        self.game.render_text('PyX', COLORS['white'], HEAD_FONT, 32, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.transition.draw(screen)

# Loading Screen State
class LoadingScreen(State):
    def __init__(self, game, target_factory):
        super().__init__(game)
        self.target_factory = target_factory
        
        # Load animation frames
        self.frames = self.game.get_images('assets/ui/loading')
        self.frame_index = 0
        self.animation_speed = 10 
        self.animation_timer = 0
        
        # Transition and timing
        self.transition = Transition()
        self.min_duration = 1.7 # Minimum time to show animation
        self.timer = 0
        self.exiting = False

    def finish_loading(self):
        # Create next state
        next_state = self.target_factory()
        # Remove LoadingScreen from stack
        if self.game.states[-1] == self:
            self.game.states.pop()
        
        if next_state == self.game.splash_screen and next_state in self.game.states:
            return 
            
        next_state.enter_state()

    def update(self, dt):
        self.transition.update(dt)
        self.timer += dt
        
        # Animation
        self.animation_timer += dt
        if self.animation_timer >= 1 / self.animation_speed:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            
        # Trigger exit after min duration
        if self.timer >= self.min_duration and not self.exiting:
            if self.transition.alpha <= 0: 
                self.exiting = True
                self.transition.exiting = True
                self.transition.callback = self.finish_loading

    def draw(self, screen):
        # Draw current frame
        if self.frames:
            current_frame = self.frames[self.frame_index]
            screen.blit(current_frame, (0, 0))
        else:
            screen.fill(COLORS['black'])
            
        self.transition.draw(screen)

# After
class Scene(State):
    def __init__(self, game, current_scene, entry_point):
        super().__init__(game)
        
        # Scene switching 
        self.current_scene = current_scene 
        self.entry_point = entry_point 
        
        self.camera = Camera(self)
        
        # Containers for managing sprite objects 
        self.update_sprites = pygame.sprite.Group()
        self.draw_sprites = pygame.sprite.Group()
        self.block_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group() 
        self.exit_sprites = pygame.sprite.Group() 
        
        self.player = None
        self.trapdoor = None
        
        self.tmx_data = load_pygame(f'scenes/{self.current_scene}/{self.current_scene}.tmx') # Load Tilemap data
        self.create_scene() # Make the scene
        self.transition = Transition(self.go_to_scene)
        
        # Death sequence
        self.is_dead = False
        self.death_phase = None # slowdown-> blacken-> pause
        self.death_timer = 0
        self.death_message = None
        self.death_slowdown_dt = 1.0 
    
    def go_to_scene(self):
        # Create the next scene based on stored navigation data
        self.game.player_data = self.player.save_data() # Save before entering
        
        # Only save enemies that have HP > 0 to ensure dead ones stay dead
        enemy_states = [enemy.save_data() for enemy in self.enemy_sprites if enemy.hp > 0]
        scene_key = str(self.current_scene)
        self.game.scene_states[scene_key] = {
            'enemies': enemy_states,
            'time': pygame.time.get_ticks()
        }
            
        Scene(self.game, self.new_scene, self.entry_point).enter_state()
    
    def create_scene(self): 
        # Loads map data and iterates through its layers to build the scene.
        layers = []
        for layer in self.tmx_data.layers:
            layers.append(layer.name)
 
        if 'floors' in layers:
            for x, y, surf in self.tmx_data.get_layer_by_name('floors').tiles():
                Object([self.draw_sprites], (x * TILE_SIZE, y * TILE_SIZE), 'floors', surf)
                
        if 'blocks' in layers:
            for x, y, surf in self.tmx_data.get_layer_by_name('blocks').tiles():
                Wall([self.block_sprites, self.draw_sprites], (x * TILE_SIZE, y * TILE_SIZE), 'blocks', surf)

        if 'holes' in layers:
            for x, y, surf in self.tmx_data.get_layer_by_name('holes').tiles():
                # Add collisions for pit/hole tiles
                Holes([self.block_sprites, self.draw_sprites], (x * TILE_SIZE, y * TILE_SIZE), 'holes', surf)

        if "entries" in layers:
            for obj in self.tmx_data.get_layer_by_name('entries'): 
                if obj.name == self.entry_point:
                    obj_direction = obj.properties.get('direction', 'right') # Get my custom properties on Tiled
                    # Spawn player at the correct entry point
                    self.player = Player(self.game, self, [self.update_sprites, self.draw_sprites],
                                         (obj.x, obj.y),
                                         'blocks',
                                         'player',
                                         obj_direction)  
                    if hasattr(self.game, 'player_data'):
                        self.player.load_data(self.game.player_data)

                    # Center camera on player immediately
                    self.camera.offset.x = self.player.rect.centerx - SCREEN_WIDTH / 2
                    self.camera.offset.y = self.player.rect.centery - SCREEN_HEIGHT / 2

        if "exits" in layers:
            for obj in self.tmx_data.get_layer_by_name('exits'):  
                # Create collision boxes for map exits
                Collider([self.exit_sprites], (obj.x, obj.y), (obj.width, obj.height), obj.name)

        if "entities" in layers:
            from enemy import Enemy
            for obj in self.tmx_data.get_layer_by_name('entities'):  
                obj_direction = obj.properties.get('direction', 'right')
                if obj.name == 'enemy':
                    Enemy(self.game, self, [self.update_sprites, self.draw_sprites, self.enemy_sprites],
                                         (obj.x, obj.y),
                                         'blocks',
                                         'enemy',
                                         obj_direction)
        
        # Randomly spawn enemies within Tiled shapes (i'll be using rectangle)
        if "spawners" in layers:
            from enemy import Enemy
            for obj in self.tmx_data.get_layer_by_name('spawners'):
                count = obj.properties.get('count', 1)
                enemy_type = obj.properties.get('enemy_type', 'enemy')
                
                for i in range(count):
                    spawned = False
                    attempts = 0
                    while not spawned and attempts < 15: # Safety break to avoid infinite loops
                        attempts += 1
                        # Pick random point in shape
                        rx = random.uniform(obj.x, obj.x + obj.width)
                        ry = random.uniform(obj.y, obj.y + obj.height)
                        # Validate position (not in wall AND not on top of another enemy)
                        buffer_rect = pygame.Rect(0, 0, 24, 24) 
                        buffer_rect.center = (rx, ry)

                        is_blocked = False
                        # Check Walls
                        for block in self.block_sprites:
                            if buffer_rect.colliderect(block.hitbox):
                                is_blocked = True
                                break

                        # Check other enemies already in the scene
                        if not is_blocked:
                            for enemy in self.enemy_sprites:
                                if buffer_rect.colliderect(enemy.hitbox):
                                    is_blocked = True
                                    break

                        if not is_blocked:
                            Enemy(self.game, self, [self.update_sprites, self.draw_sprites, self.enemy_sprites],
                                  (rx, ry), 'blocks', enemy_type)
                            spawned = True


        # Re-apply saved states to the group of enemies
        saved_data = self.game.scene_states.get(str(self.current_scene))
        if saved_data:
            # Match saved data to current enemies
            for e in self.enemy_sprites: e.kill()
            from enemy import Enemy
            
            saved_enemies = saved_data['enemies']
            saved_time = saved_data['time']
            current_time = pygame.time.get_ticks()

            # If player has been gone for more than 15 seconds, enemies return to spawn
            reset_to_spawn = (current_time - saved_time) > 5000 
            
            for state in saved_enemies:
                # Decide position based on timer
                pos = state['spawn_pos'] if reset_to_spawn else state['pos']
                
                e = Enemy(self.game, self, [self.update_sprites, self.draw_sprites, self.enemy_sprites],
                          pos, 'blocks', 'enemy')
                
                # If we aren't resetting to spawn, load full state (HP, Chasing, etc.)
                if not reset_to_spawn:
                    e.load_data(state)

        if 'detail 1' in layers:
            for x, y, surf in self.tmx_data.get_layer_by_name('detail 1').tiles():
                Object([self.draw_sprites], (x * TILE_SIZE, y * TILE_SIZE), 'detail 1', surf) 
    
    def start_death_sequence(self):
        if self.is_dead:
            return 
        
        self.is_dead = True
        self.death_phase = 'slowdown'
        self.death_timer = DEATH_SEQUENCE_CONFIG['slowdown_duration']
        self.death_message = random.choice(DEATH_MESSAGES)
        self.death_slowdown_dt = DEATH_SEQUENCE_CONFIG['slowdown_multiplier'] # Start slowmo instantly
    
    def trigger_restart(self):
        if not self.transition.exiting:
            self.transition.exiting = True
            self.transition.callback = self.restart_game

    def restart_game(self):
        self.game.player_data = {} # Reset player stats
        self.game.scene_states = {} # Clear room persistence
        self.game.states.pop()
        LoadingScreen(self.game, lambda: Scene(self.game, '0', '0')).enter_state()

    def trigger_exit(self):
        if not self.transition.exiting:
            self.transition.exiting = True
            self.transition.callback = self.exit_to_splash

    def exit_to_splash(self):
        self.game.states = [self.game.splash_screen]
        # Show loading before actually being back at splash fully
        LoadingScreen(self.game, lambda: self.game.splash_screen).enter_state()

    def update_death_sequence(self, dt):
        if self.death_phase == 'slowdown':
            self.death_timer -= dt
            # Gradually slow down time
            progress = max(0, self.death_timer / DEATH_SEQUENCE_CONFIG['slowdown_duration'])
            self.death_slowdown_dt = max(DEATH_SEQUENCE_CONFIG['slowdown_multiplier'], progress)
            
            if self.death_timer <= 0:
                self.death_phase = 'paused'
                self.death_timer = DEATH_SEQUENCE_CONFIG['pause_duration']
                # Reset inputs to prevent accidental clicks
                self.game.reset_inputs()

        elif self.death_phase == 'paused':
            # Menu buttons and hover logic
            mouse_pos = pygame.mouse.get_pos()
            
            # Interaction
            if self.game.ui.restart_button_rect.collidepoint(mouse_pos) and not self.transition.exiting:
                if INPUTS['left_click']:
                    self.trigger_restart()
            
            if self.game.ui.exit_button_rect.collidepoint(mouse_pos) and not self.transition.exiting:
                if INPUTS['left_click']:
                    self.trigger_exit()

    def debugger(self, debug_list):
        # For ingame debugging visualization (displays accel, vel, etc.)
        for index, name in enumerate(debug_list):
            self.game.render_text(name, COLORS['white'], PRIMARY_FONT, 10, (10, 15 * (index + 1)), False)

    def update(self, dt):
        # Apply slow-motion multiplier if in death sequence
        effective_dt = dt * self.death_slowdown_dt
        
        # Trigger death sequence effects immediately
        if self.is_dead:
            self.update_death_sequence(dt)

        if not self.is_dead or self.death_phase == 'slowdown':
            self.update_sprites.update(effective_dt)
            if self.player:
                self.camera.update(effective_dt, self.player)
        
        self.transition.update(dt)


    def draw(self, screen):
        self.camera.draw(screen, self.draw_sprites, self)
        
        # UI Manager handles HUD, hit overlay, and death effects
        self.game.ui.draw(screen, self)

        self.transition.draw(screen)
                
        #  Debugger
        if DEBUG.TEXT:
            self.debugger([
                str(f'FPS: {round(self.game.clock.get_fps(), 2)}'),
                str(f'Vel: {round(self.player.vel, 2)}'),
                str(f'Pos: ({round(self.player.pos.x)}, {round(self.player.pos.y)})'),
                str(f'State: {self.player.state}'),
                str(f'Tumble Charge: {self.player.tumble_charges}'),
                str(f'Tumble CD: {round(self.player.tumble_cooldown_timer, 1)}'),
                str(f'HP: {round(self.player.hp, 1)}'),
                str(f'I-frame: {round(self.player.invulnerability_timer, 2)}'),
                str(f'HP delay: {round(self.player.regen_delay_timer, 1)}'),
                str(f'Time: {round(pygame.time.get_ticks() / 1000, 1)}')
            ])

    
    
            
            
                
    