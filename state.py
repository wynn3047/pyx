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

    def update(self, dt):
        if INPUTS['enter']:
            Scene(self.game, '0', '0').enter_state()
            self.game.reset_inputs()

    def draw(self, screen):
        screen.fill((COLORS['charcoal_grey']))
        self.game.render_text('PyX', COLORS['white'], HEAD_FONT, 32, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

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
        self.transition = Transition(self)
        
        # Death sequence
        self.is_dead = False
        self.death_phase = None # slowdown-> blacken-> pause
        self.death_timer = 0
        self.death_message = None
        self.death_slowdown_dt = 1.0 # Multiplier for dt during slowmo
        
        # Buttons for death sequence
        self.restart_button_rect = pygame.Rect(0, 0, 80, 20)
        self.restart_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)
        
        self.exit_button_rect = pygame.Rect(0, 0, 80, 20)
        self.exit_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 45)
        
        # Load heart sprite
        self.heart_sprite = pygame.image.load('assets/ui/heart.png').convert_alpha()
        # Pre-render black heart for background
        self.black_heart_sprite = self.heart_sprite.copy()
        self.black_heart_sprite.fill(COLORS['black'], special_flags=pygame.BLEND_RGB_MULT)

    def go_to_scene(self):
        # Create the next scene based on stored navigation data
        self.game.player_data = self.player.save_data() # Save before entering
        
        # LOCAL PERSISTENCE: Save all enemies in this scene with a timestamp
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
                        # A 24x24 buffer for 8 px gap
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

        if 'Interactions' in layers:
            from objects import Trapdoor
            for obj in self.tmx_data.get_layer_by_name('Interactions'):
                if obj.name == 'trapdoor':
                    closed_id = obj.properties.get('closed_id')
                    open_id = obj.properties.get('open_id')
                    
                    # Fetch surfaces from Tiled data using GIDs
                    closed_surf = self.tmx_data.get_tile_image_by_gid(closed_id)
                    open_surf = self.tmx_data.get_tile_image_by_gid(open_id)
                    
                    self.trapdoor = Trapdoor([self.draw_sprites], (obj.x, obj.y), 'floors', closed_surf, open_surf)
    
    def start_death_sequence(self):
        if self.is_dead:
            return 
        
        self.is_dead = True
        self.death_phase = 'slowdown'
        self.death_timer = DEATH_SEQUENCE_CONFIG['slowdown_duration']
        self.death_message = random.choice(DEATH_MESSAGES)
        self.death_slowdown_dt = DEATH_SEQUENCE_CONFIG['slowdown_multiplier'] # Start slowmo instantly
    
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
            if self.restart_button_rect.collidepoint(mouse_pos):
                if INPUTS['left_click']:
                    # Restart to Scene 0
                    self.game.player_data = {} # Reset player stats
                    self.game.scene_states = {} # Clear room persistence
                    Scene(self.game, '0', '0').enter_state()
            
            if self.exit_button_rect.collidepoint(mouse_pos):
                if INPUTS['left_click']:
                    # Exit to Splash
                    self.game.states = [self.game.splash_screen]
    
    def draw_death_menu(self, screen):
        # Dim background further
        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        dim_surf.fill((0, 0, 0))
        dim_surf.set_alpha(150)
        screen.blit(dim_surf, (0, 0))

        # Death Message
        self.game.render_text(self.death_message, DEATH_SEQUENCE_CONFIG['message_color'], HEAD_FONT, 24, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))

        mouse_pos = pygame.mouse.get_pos()

        # Restart Button
        restart_color = DEATH_SEQUENCE_CONFIG['button_color_active'] if self.restart_button_rect.collidepoint(mouse_pos) else DEATH_SEQUENCE_CONFIG['button_color_inactive']
        restart_text_color = COLORS['black'] if self.restart_button_rect.collidepoint(mouse_pos) else COLORS['white']
        pygame.draw.rect(screen, restart_color, self.restart_button_rect, border_radius=3)
        self.game.render_text('RESTART', restart_text_color, PRIMARY_FONT, 10, self.restart_button_rect.center)

        # Exit Button
        exit_color = DEATH_SEQUENCE_CONFIG['button_color_active'] if self.exit_button_rect.collidepoint(mouse_pos) else DEATH_SEQUENCE_CONFIG['button_color_inactive']
        exit_text_color = COLORS['black'] if self.exit_button_rect.collidepoint(mouse_pos) else COLORS['white']
        pygame.draw.rect(screen, exit_color, self.exit_button_rect, border_radius=3)
        self.game.render_text('EXIT', exit_text_color, PRIMARY_FONT, 10, self.exit_button_rect.center)
    
    def apply_grayscale_bleed(self, screen, amount):
        # Capture the screen, grayscale it, and blit with alpha
        temp_surf = screen.copy()
        
        # Fast Grayscale using RGB weighting
        array = pygame.surfarray.pixels3d(temp_surf)
        weights = pygame.Vector3(0.299, 0.587, 0.114)
        gray = (array * weights).sum(axis=2)
        array[:, :, 0] = gray
        array[:, :, 1] = gray
        array[:, :, 2] = gray
        del array 
        
        temp_surf.set_alpha(int(255 * amount))
        screen.blit(temp_surf, (0, 0))

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
        
        if self.is_dead:
            # Calculate bleed amount based on phase/timer
            if self.death_phase == 'slowdown':
                bleed_progress = 1.0 - (self.death_timer / DEATH_SEQUENCE_CONFIG['slowdown_duration'])
            else:
                bleed_progress = 1.0 # Full grayscale
            
            if bleed_progress > 0.05:
                self.apply_grayscale_bleed(screen, bleed_progress)

            # Draw Menu if Paused
            if self.death_phase == 'paused':
                self.draw_death_menu(screen)

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

    
    
            
            
                
    