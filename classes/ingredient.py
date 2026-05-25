"""
Ingredient — a draggable item for the cooking plate
"""

import pygame
import math
from classes.constants import INGREDIENTS, C_BORDER, C_TEXT, C_PANEL


class IngredientButton:
    """
    A clickable ingredient button in the right panel.
    Clicking it spawns an ingredient on the plate.
    """

    def __init__(self, key: str, x: int, y: int, w: int, h: int):
        self.key    = key
        self.data   = INGREDIENTS[key]
        self.rect   = pygame.Rect(x, y, w, h)
        self.hovered = False
        self._pulse  = 0.0

    def update(self, dt: float, mx: int, my: int):
        self.hovered = self.rect.collidepoint(mx, my)
        self._pulse  = (self._pulse + dt * 3) % (2 * math.pi)

    def draw(self, surf: pygame.Surface, font_med, font_sm, affordable: bool):
        col    = self.data["color"]
        alpha  = 255 if affordable else 80

        # Background
        bg = (55, 45, 80) if self.hovered and affordable else (35, 28, 55)
        pygame.draw.rect(surf, bg, self.rect, border_radius=8)

        border = col if self.hovered and affordable else C_BORDER
        pygame.draw.rect(surf, border, self.rect, 2, border_radius=8)

        # Emoji
        emo  = font_med.render(self.data["emoji"], True, C_TEXT)
        surf.blit(emo, (self.rect.x + 8, self.rect.y + 8))

        # Label
        lbl  = font_sm.render(self.data["label"], True, C_TEXT)
        surf.blit(lbl, (self.rect.x + 8, self.rect.y + 38))

        # Cost
        cost_col = (80, 220, 80) if affordable else (180, 60, 40)
        cost = font_sm.render(f"${self.data['cost']}", True, cost_col)
        surf.blit(cost, (self.rect.x + 8, self.rect.y + 54))

        # Greyed overlay if can't afford
        if not affordable:
            ov = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 120))
            surf.blit(ov, self.rect.topleft)


class PlateItem:
    """
    An ingredient sitting on the cooking plate.
    Can be clicked to remove.
    """

    SIZE = 64

    def __init__(self, key: str, cx: int, cy: int):
        self.key   = key
        self.data  = INGREDIENTS[key]
        self.rect  = pygame.Rect(cx - self.SIZE // 2, cy - self.SIZE // 2,
                                  self.SIZE, self.SIZE)
        self._cook_progress = 0.0  # 0..1 cooking animation
        self.cooked = False
        self.hovered = False

    def update(self, dt: float, cook_speed: float, mx: int, my: int):
        self.hovered = self.rect.collidepoint(mx, my)
        if not self.cooked:
            self._cook_progress = min(1.0, self._cook_progress + dt * cook_speed * 0.4)
            if self._cook_progress >= 1.0:
                self.cooked = True

    def draw(self, surf: pygame.Surface, font_big, font_sm):
        col = self.data["color"]

        # Sizzle glow
        if not self.cooked:
            glow_alpha = int(60 * self._cook_progress)
            glow = pygame.Surface((self.SIZE + 20, self.SIZE + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*col, glow_alpha),
                               (self.SIZE // 2 + 10, self.SIZE // 2 + 10),
                               self.SIZE // 2 + 8)
            surf.blit(glow, (self.rect.x - 10, self.rect.y - 10))

        bg = col if self.cooked else tuple(max(0, c - 50) for c in col)
        pygame.draw.rect(surf, bg, self.rect, border_radius=10)
        pygame.draw.rect(surf, (255, 255, 255, 80) if self.hovered else col,
                         self.rect, 2, border_radius=10)

        # Emoji
        emo  = font_big.render(self.data["emoji"], True, (255, 255, 255))
        surf.blit(emo, (self.rect.x + 8, self.rect.y + 6))

        # Cook progress bar
        if not self.cooked:
            bx, by = self.rect.x, self.rect.bottom + 2
            pygame.draw.rect(surf, (30, 20, 10), (bx, by, self.SIZE, 6), border_radius=3)
            pygame.draw.rect(surf, (230, 160, 20),
                             (bx, by, int(self.SIZE * self._cook_progress), 6),
                             border_radius=3)
        else:
            # ✓ ready
            done = font_sm.render("✓ Ready", True, (80, 220, 80))
            surf.blit(done, (self.rect.x, self.rect.bottom + 2))

        # Remove hint on hover
        if self.hovered:
            hint = font_sm.render("✕", True, (220, 60, 40))
            surf.blit(hint, (self.rect.right - 16, self.rect.y + 2))
