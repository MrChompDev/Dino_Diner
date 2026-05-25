"""
UI helpers — reusable drawing utilities
"""

import pygame
import math
from classes.constants import C_BORDER, C_TEXT, C_TEXT_DIM, C_PANEL


def draw_panel(surf, x, y, w, h, color=C_PANEL, border=C_BORDER,
               radius=0, alpha=255):
    rect = pygame.Rect(x, y, w, h)
    if alpha < 255:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((*color, alpha))
        surf.blit(s, (x, y))
    else:
        pygame.draw.rect(surf, color, rect, border_radius=radius)
    pygame.draw.rect(surf, border, rect, 2, border_radius=radius)


def draw_label(surf, font, text, x, y, color=C_TEXT, center=False):
    s = font.render(text, True, color)
    if center:
        surf.blit(s, (x - s.get_width() // 2, y))
    else:
        surf.blit(s, (x, y))


def draw_button(surf, font, text, rect: pygame.Rect,
                hover: bool, enabled: bool = True,
                color_bg=(60, 45, 90), color_hover=(90, 65, 140),
                color_text=C_TEXT, color_disabled=(40, 35, 50)):
    bg = color_hover if hover and enabled else (color_bg if enabled else color_disabled)
    pygame.draw.rect(surf, bg, rect, border_radius=8)
    border = (150, 120, 200) if hover and enabled else C_BORDER
    pygame.draw.rect(surf, border, rect, 2, border_radius=8)

    txt = font.render(text, True, color_text if enabled else C_TEXT_DIM)
    surf.blit(txt, (rect.centerx - txt.get_width() // 2,
                    rect.centery - txt.get_height() // 2))


def draw_money(surf, font, amount: int, x, y):
    color = (80, 220, 80) if amount >= 0 else (220, 60, 40)
    s = font.render(f"${amount}", True, color)
    surf.blit(s, (x, y))


def pulse_alpha(t: float, speed: float = 2.0,
                lo: int = 140, hi: int = 255) -> int:
    """Oscillating alpha for animations."""
    return int(lo + (hi - lo) * (0.5 + 0.5 * math.sin(t * speed)))


def draw_progress_bar(surf, x, y, w, h, ratio,
                      color_fill=(80, 200, 100),
                      color_bg=(30, 20, 10),
                      color_border=C_BORDER,
                      radius=4):
    pygame.draw.rect(surf, color_bg, (x, y, w, h), border_radius=radius)
    if ratio > 0:
        pygame.draw.rect(surf, color_fill,
                         (x, y, int(w * ratio), h), border_radius=radius)
    pygame.draw.rect(surf, color_border, (x, y, w, h), 1, border_radius=radius)
