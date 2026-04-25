import pygame
import random
from settings import *
from camera import Camera
from transition import Transition
from characters import GameCharacter
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
        self.game.render_text('PyX', COLORS['white'], self.game.head_font, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

# After
class Scene(State):
    def __init__(self, game, current_scene, entry_point):
        super().__init__(game)
        
        # Scene switching 
        self.current_scene = current_scene # Folder name of the map
        self.entry_point = entry_point # Door or spawn point ID
        
        self.camera = Camera(self)
        
        # Containers for managing sprite objects 
        self.update_sprites = pygame.sprite.Group()
        self.draw_sprites = pygame.sprite.Group()
        self.block_sprites = pygame.sprite.Group()
        self.exit_sprites = pygame.sprite.Group() # Invisible trigger boxes for scene swaps
        
        self.player = None
        
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
        self.restart_button_rect = None
        self.exit_button_rect = None
        
    def go_to_scene(self):
        # Create the next scene based on stored navigation data
        self.game.player_data = self.player.save_data() # Save before entering
        if hasattr(self, 'enemy') and self.enemy: # Save enemy data
            self.game.enemy_data = self.enemy.save_data()
        else:
            self.game.enemy_data = None
            
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
                    self.enemy = Enemy(self.game, self, [self.update_sprites, self.draw_sprites],
                                         (obj.x, obj.y),
                                         'blocks',
                                         'enemy',
                                         obj_direction)
                    if hasattr(self.game, 'enemy_data') and self.game.enemy_data:
                        self.enemy.load_data(self.game.enemy_data)

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
        
    def debugger(self, debug_list):
        # For ingame debugging visualization (displays accel, vel, etc.)
        for index, name in enumerate(debug_list):
            self.game.render_text(name, COLORS['white'], self.game.primary_font, (10, 15 * (index + 1)), False)

    def update(self, dt):
        self.update_sprites.update(dt) # Update all character logic (player movement, etc.)
        if self.player:
            self.camera.update(dt, self.player) # figure out where the player moved.
        
        self.transition.update(dt)
        
    def draw(self, screen):
        # Instead of drawing sprites normally, we let the CAMERA do it.
        # It takes all our draw_sprites and only draws the ones on screen
        self.camera.draw(screen, self.draw_sprites)
        self.transition.draw(screen)
        
        if self.is_dead:
            if self.death_phase == 'bw_filter':
                self._draw_bw_filter(screen, self.bw_intensity)
            
            elif self.death_phase == 'pause':
                self._draw_death_screen(screen)
                
        #  Draw debug text
        if DEBUG_TEXT:
            self.debugger([
                str(f'FPS: {round(self.game.clock.get_fps(), 2)}'),
                str(f'Vel: {round(self.player.vel, 2)}'),
                str(f'State: {self.player.state}'),
                str(f'Tumble Charge: {self.player.tumble_charges}'),
                str(f'Tumble CD: {round(self.player.tumble_cooldown_timer, 1)}'),
                str(f'HP: {round(self.player.hp, 1)}'),
                str(f'I-frame: {round(self.player.invulnerability_timer, 2)}'),
                str(f'HP delay: {round(self.player.regen_delay_timer, 1)}'),
                str(f'Death Msg: {self.death_message}'),
                str(f'Death Phase: {self.death_phase}')
            ])
                
    