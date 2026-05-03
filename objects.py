import pygame
from settings import *

class Collider(pygame.sprite.Sprite):
    # Invisible rectangle used to trigger events like scene changes
    def __init__(self, groups, pos, size, number):
        super().__init__(groups)
        self.image = pygame.Surface((size))
        self.rect = self.image.get_rect(topleft=pos)
        self.number = number
        
class Object(pygame.sprite.Sprite):
    def __init__(self, groups, pos, z="blocks", surf=pygame.Surface((TILE_SIZE, TILE_SIZE))):
        super().__init__(groups)
        self.image = surf # The visual look of the object
        
        # The position and size of the object (used for drawing)
        self.rect = self.image.get_rect(topleft=pos)
        # used for collisions
        # By default, it's the same size as the image
        self.hitbox = self.rect.copy()
        self.z = z

class Wall(Object):
    def __init__(self, group, pos, z, surf):
        super().__init__(group, pos, z, surf)
        self.hitbox = self.rect.copy()
        
class Holes(Object):
    def __init__(self, group, pos, z, surf):
        super().__init__(group, pos, z, surf)
        self.hitbox = self.rect.copy()

class Chest(Object):
    def __init__(self, scene, groups, pos, z, tmx_data):
        # We don't call super().__init__ with a surface yet because we'll build it
        pygame.sprite.Sprite.__init__(self, groups)
        self.scene = scene
        self.z = z
        self.pos = pygame.math.Vector2(pos)
        
        # Tile IDs (local to tileset_2)
        self.local_ids = {
            'closed_lid': 152,
            'closed_body': 167,
            'open_lid': 151,
            'open_body': 166
        }
        
        
        tileset_surf = pygame.image.load('assets/tilesets/tileset_2.png').convert_alpha()
        cols = tileset_surf.get_width() // 16
        
        self.surfaces = {}
        for name, lid in self.local_ids.items():
            col = lid % cols
            row = lid // cols
            # Create a copy to avoid subsurface issues if tileset_surf is cleared
            tile_rect = pygame.Rect(col * 16, row * 16, 16, 16)
            self.surfaces[name] = tileset_surf.subsurface(tile_rect).copy()
    

        self.is_open = False
        self.highlighted = False
        self.interaction_timer = 0
        self.interaction_duration = 1.0 # 1 second to open
        
        # Setup initial image (16x32)
        self.image = pygame.Surface((16, 32), pygame.SRCALPHA)
        self.update_appearance()
        
        # Rect and Hitbox
        # Position the chest so its base is at the 'pos' provided by Tiled
        self.rect = self.image.get_rect(topleft=(pos[0], pos[1] - 16))
        self.hitbox = pygame.Rect(pos[0], pos[1], 16, 16)

    def update_appearance(self):
        self.image.fill((0,0,0,0))
        # Lid at (0,0), Body at (0,16)
        if self.is_open:
            self.image.blit(self.surfaces['open_lid'], (0, 0))
            self.image.blit(self.surfaces['open_body'], (0, 16))
        else:
            self.image.blit(self.surfaces['closed_lid'], (0, 0))
            self.image.blit(self.surfaces['closed_body'], (0, 16))

    def update(self, dt):
        if self.is_open:
            self.highlighted = False
            return

        # Check distance to player
        player_pos = vect(self.scene.player.rect.center)
        chest_center = vect(self.hitbox.center)
        distance = (player_pos - chest_center).length()

        if distance < 32:
            self.highlighted = True
            if INPUTS['e']:
                self.interaction_timer += dt
                if self.interaction_timer >= self.interaction_duration:
                    self.is_open = True
                    self.scene.start_upgrade()
                    self.update_appearance()
                    self.interaction_timer = 0
            else:
                self.interaction_timer = 0
        else:
            self.highlighted = False
            self.interaction_timer = 0

    def save_data(self):
        return {
            'pos': (self.pos.x, self.pos.y),
            'is_open': self.is_open
        }
    
    def load_data(self, data):
        self.is_open = data.get('is_open', False)
        self.update_appearance()