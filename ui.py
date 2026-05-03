import pygame
import math
import random
from settings import *

class UI:
    def __init__(self, game):
        self.game = game
        
        self.heart_sprite = pygame.image.load(HP_CONFIG['heart_path']).convert_alpha()
        self.black_heart_sprite = self.heart_sprite.copy()
        self.black_heart_sprite.fill(COLORS['black'], special_flags=pygame.BLEND_RGB_MULT)

        self.tumble_frame = pygame.image.load(TUMBLE_UI_CONFIG['frame_path']).convert_alpha()
        self.tumble_fill = pygame.image.load(TUMBLE_UI_CONFIG['fill_path']).convert_alpha()
        
        self.stealth_frame = pygame.image.load(STEALTH_CONFIG['frame_path']).convert_alpha()
        self.stealth_fill = pygame.image.load(STEALTH_CONFIG['fill_path']).convert_alpha()

        self.card_templates = {
            'red': pygame.image.load('assets/ui/card_red.png').convert_alpha(),
            'green': pygame.image.load('assets/ui/card_green.png').convert_alpha(),
            'blue': pygame.image.load('assets/ui/card_blue.png').convert_alpha()
        }

        self.restart_button_rect = pygame.Rect(0, 0, 80, 20)
        self.restart_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)
        
        self.exit_button_rect = pygame.Rect(0, 0, 80, 20)
        self.exit_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 45)

    def draw_hearts(self, screen, player):
        heart_ratios = player.get_heart_states()
        heart_size = HEART_CONFIG['heart_size']
        spacing = HEART_CONFIG['heart_spacing']

        total_width = (len(heart_ratios) * heart_size) + ((len(heart_ratios) - 1) * spacing)
        start_x = SCREEN_WIDTH - total_width - HEART_CONFIG['ui_offset_x']
        start_y = HEART_CONFIG['ui_offset_y']

        for heart_index, ratio in enumerate(heart_ratios):
            x = start_x + (heart_index * (heart_size + spacing))
            y = start_y

            screen.blit(self.black_heart_sprite, (x, y))

            if ratio > 0:
                if ratio >= 1:
                    screen.blit(self.heart_sprite, (x, y))
                else:
                    scaled_w = int(heart_size * ratio)
                    scaled_h = int(heart_size * ratio)

                    if scaled_w > 2 and scaled_h > 2:
                        scaled_heart = pygame.transform.scale(self.heart_sprite, (scaled_w, scaled_h))
                        brightness = int(255 * ratio)
                        scaled_heart.fill((brightness, brightness, brightness), special_flags=pygame.BLEND_RGB_MULT)

                        offset_x = (heart_size - scaled_w) // 2
                        offset_y = (heart_size - scaled_h) // 2
                        screen.blit(scaled_heart, (x + offset_x, y + offset_y))

    def draw_tumble_ui(self, screen, player):
        icon_w, icon_h = self.tumble_frame.get_size()
        spacing = TUMBLE_UI_CONFIG['spacing']
        pos_y = HEART_CONFIG['ui_offset_y'] + HEART_CONFIG['heart_size'] + TUMBLE_UI_CONFIG['offset_y_below_hearts']
        
        for i in range(player.tumble_max_charges):
            x = (SCREEN_WIDTH - HEART_CONFIG['ui_offset_x'] - icon_w) - (i * (icon_w + spacing))
            screen.blit(self.tumble_frame, (x, pos_y))
            
            fill_surf = self.tumble_fill.copy()
            fill_w, fill_h = fill_surf.get_size()
            
            if i < player.tumble_charges:
                fill_surf.fill(COLORS['white'], special_flags=pygame.BLEND_RGB_MULT)
                screen.blit(fill_surf, (x, pos_y))
            elif i == player.tumble_charges:
                ratio = 1.0 - (player.tumble_cooldown_timer / player.tumble_cooldown)
                fill_surf.set_alpha(150)
                if ratio > 0:
                    current_w = int(fill_w * ratio)
                    clip_rect = pygame.Rect(fill_w - current_w, 0, current_w, fill_h)
                    screen.blit(fill_surf, (x + (fill_w - current_w), pos_y), area=clip_rect)

    def draw_stealth_bar(self, screen, player):
        frame_h = self.stealth_frame.get_height()
        pos_x = 10
        pos_y = (SCREEN_HEIGHT - frame_h) // 2
        
        screen.blit(self.stealth_frame, (pos_x, pos_y))
        
        ratio = player.stealth / player.max_stealth
        if ratio >= 0:
            fill_image = self.stealth_fill.copy()
            full_w, full_h = fill_image.get_size()
            padding = 9
            usable_h = full_h - (padding * 2)
            
            if player.is_stealth_ready:
                fill_image.fill(COLORS['light_pink'], special_flags=pygame.BLEND_RGB_MULT)
                pulse = (math.sin(pygame.time.get_ticks() * 0.02) + 1) / 2
                alpha = 150 + int(105 * pulse)
                fill_image.set_alpha(alpha)
            
            current_fill_h = int(usable_h * ratio)
            clip_rect = pygame.Rect(0, (full_h - padding) - current_fill_h, full_w, current_fill_h)
            screen.blit(fill_image, (pos_x, pos_y + (full_h - padding - current_fill_h)), area=clip_rect)

    def draw_hit_overlay(self, screen, player):
        if player and player.is_low_hp and hasattr(player, 'hit_flash_timer') and player.hit_flash_timer > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill(COLORS['medium_red'])
            overlay.set_alpha(70)
            screen.blit(overlay, (0, 0))

    def draw_interaction_bars(self, screen, scene):
        from objects import Chest
        for sprite in scene.draw_sprites:
            if isinstance(sprite, Chest) and sprite.interaction_timer > 0 and not sprite.is_open:
                bar_width = 16
                bar_height = 2
                progress = sprite.interaction_timer / sprite.interaction_duration

                # Screen position calculation using camera offset
                offset = scene.camera.offset
                x = sprite.rect.left - offset.x
                y = sprite.rect.top - offset.y

                # Draw background
                pygame.draw.rect(screen, (0, 0, 0), (x, y, bar_width, bar_height))
                # Draw progress
                pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width * progress, bar_height))

    def draw_upgrade_overlay(self, screen, scene):
        if scene.is_upgrading:
            # Dim background
            dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            dim_surf.fill((0, 0, 0))
            dim_surf.set_alpha(150)
            screen.blit(dim_surf, (0, 0))

            # Draw cards
            for i, upgrade in enumerate(scene.upgrade_options):
                card_type = upgrade['type']
                card_surf = self.card_templates[card_type]
                rect = scene.upgrade_rects[i]

                # Draw card
                draw_rect = rect.copy()
                if scene.hovered_upgrade == i:
                    # Hover effect: move up slightly
                    draw_rect.y -= 4
                    screen.blit(card_surf, draw_rect)
                    highlight = card_surf.copy()
                    highlight.fill(COLORS['white'], special_flags=pygame.BLEND_RGB_MULT)
                    highlight.set_alpha(100)
                    screen.blit(highlight, draw_rect, special_flags=pygame.BLEND_RGB_ADD)
                else:
                    screen.blit(card_surf, draw_rect)

                header_y = draw_rect.centery
                header_color = COLORS.get(card_type, COLORS['white'])
                self.game.render_text(upgrade['header'], header_color, PRIMARY_FONT, 10, (draw_rect.centerx, header_y))

                desc_rect = draw_rect.inflate(-8, -25)
                desc_rect.top = draw_rect.top + 18
                self.draw_wrapped_text(screen, upgrade['desc'], COLORS['white'], PRIMARY_FONT, 9, desc_rect)

    def draw_wrapped_text(self, screen, text, color, font_path, size, rect):
        # Cache font
        font_key = f"{font_path}_{size}"
        if font_key not in self.game.fonts:
            self.game.fonts[font_key] = pygame.font.Font(font_path, size)
        font = self.game.fonts[font_key]

        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= rect.width - 6:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))

        # Render lines centered in rect
        total_height = len(lines) * font.get_linesize()
        start_y = 27 + rect.top + (rect.height - total_height) // 2

        for i, line in enumerate(lines):
            surf = font.render(line, False, color)
            line_rect = surf.get_rect(center=(rect.centerx, start_y + i * font.get_linesize()))
            screen.blit(surf, line_rect)

    def apply_grayscale_bleed(self, screen, amount):
        temp_surf = screen.copy()
        array = pygame.surfarray.pixels3d(temp_surf)
        weights = pygame.Vector3(0.299, 0.587, 0.114)
        gray = (array * weights).sum(axis=2)
        array[:, :, 0] = gray
        array[:, :, 1] = gray
        array[:, :, 2] = gray
        del array 
        temp_surf.set_alpha(int(255 * amount))
        screen.blit(temp_surf, (0, 0))

    def draw_death_menu(self, screen, scene):
        # Dim background
        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        dim_surf.fill((0, 0, 0))
        dim_surf.set_alpha(130)
        screen.blit(dim_surf, (0, 0))

        # Message random
        self.game.render_text(scene.death_message, DEATH_SEQUENCE_CONFIG['message_color'], HEAD_FONT, 24, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))

        mouse_pos = pygame.mouse.get_pos()

        restart_color = DEATH_SEQUENCE_CONFIG['button_color_active'] if self.restart_button_rect.collidepoint(mouse_pos) else DEATH_SEQUENCE_CONFIG['button_color_inactive']
        restart_text_color = COLORS['black'] if self.restart_button_rect.collidepoint(mouse_pos) else COLORS['white']
        pygame.draw.rect(screen, restart_color, self.restart_button_rect, border_radius=3)
        self.game.render_text('RESTART', restart_text_color, PRIMARY_FONT, 10, self.restart_button_rect.center)

        exit_color = DEATH_SEQUENCE_CONFIG['button_color_active'] if self.exit_button_rect.collidepoint(mouse_pos) else DEATH_SEQUENCE_CONFIG['button_color_inactive']
        exit_text_color = COLORS['black'] if self.exit_button_rect.collidepoint(mouse_pos) else COLORS['white']
        pygame.draw.rect(screen, exit_color, self.exit_button_rect, border_radius=3)
        self.game.render_text('EXIT', exit_text_color, PRIMARY_FONT, 10, self.exit_button_rect.center)

    def draw(self, screen, scene):
        player = scene.player
        if not player: return

        self.draw_hit_overlay(screen, player)

        if scene.is_dead:
            if scene.death_phase == 'slowdown':
                bleed_progress = 1.0 - (scene.death_timer / DEATH_SEQUENCE_CONFIG['slowdown_duration'])
            else:
                bleed_progress = 1.0
            
            if bleed_progress > 0.05:
                self.apply_grayscale_bleed(screen, bleed_progress)

            if scene.death_phase == 'paused':
                self.draw_death_menu(screen, scene)
        
        self.draw_hearts(screen, player)
        self.draw_tumble_ui(screen, player)
        self.draw_stealth_bar(screen, player)
        self.draw_interaction_bars(screen, scene)
        self.draw_upgrade_overlay(screen, scene)
