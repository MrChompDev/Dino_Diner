"""
scenes.py — Three distinct gameplay scenes for Dino Papa's

Scene 1: ORDER TAKING
  - Dino walks up and talks, speech bubble shows what they want
  - Player reads the order, clicks "Got it!" to confirm
  - Receipt prints in corner with the order locked in
  - Patience timer runs slowly

Scene 2: COOKING STATION
  - Papa's-style grill with SLOTS
  - Drag ingredients from left shelf onto grill slots
  - Each slot has its own cook progress bar (fast!)
  - Player clicks cooked items to flip/finish them
  - Button → advance to Plating

Scene 3: MEAL PREP / PLATING
  - Finished cooked items sit on left
  - Dino's receipt is visible top-right
  - Player drags items onto the plate in order
  - Plate slot highlights to show expected ingredients
  - "Serve!" button sends it
"""

import pygame
import random
import math
from classes.constants import *
from classes.particles import ParticleSystem
from classes.assets import ASSETS


class OrderScene:
    """
    The dino walks up and places their order.
    Speech bubble shows what they want.
    Patience bar shown.
    Player clicks "Got it!" to advance to cooking.
    """

    SPEECH_BG = (255, 255, 240)
    SPEECH_BR = (180, 160, 100)

    def __init__(self, dino, receipt, particles: ParticleSystem,
                 fonts, on_confirm):
        self.dino       = dino
        self.receipt    = receipt
        self.particles  = particles
        self.fonts      = fonts          # (title, big, med, sm, xs)
        self.on_confirm = on_confirm     # callback → go to cook scene

        self.timer      = ORDER_PHASE_TIME
        self.confirmed  = False

        # Dino walk-in animation
        self._dino_x    = -200.0
        self._dino_target = 340.0
        self._bounce    = 0.0
        self._t         = 0.0

        # Speech bubble appear
        self._speech_alpha = 0.0

        # Confirm button hover
        self._hover_confirm = False

        # Blink tick
        self._blink = 0.0


    # ── Update ───────────────────────────────────────────
    def update(self, dt, mx, my):
        self._t      += dt
        self._blink  += dt

        # Walk in
        self._dino_x += (self._dino_target - self._dino_x) * min(1, dt * 5)
        self._bounce  = math.sin(self._t * 6) * 4 if abs(self._dino_x - self._dino_target) < 20 else 0

        # Speech fade in once arrived
        if abs(self._dino_x - self._dino_target) < 40:
            self._speech_alpha = min(1.0, self._speech_alpha + dt * 3)

        # Patience drain (slow)
        if not self.confirmed:
            drain = PATIENCE_RATE * self.dino.dino_type_data()["speed"]
            self.dino.patience -= drain * dt

        # Timer
        self.timer -= dt
        if self.timer <= 0 and not self.confirmed:
            self.on_confirm()   # auto-advance when time runs out

        # Button hover
        btn = self._confirm_rect()
        self._hover_confirm = btn.collidepoint(mx, my)

    def handle_click(self, mx, my):
        if self._confirm_rect().collidepoint(mx, my) and not self.confirmed:
            self.confirmed = True
            self.particles.stars(640, 360, color=(255, 220, 60), count=14)
            self.on_confirm()

    # ── Draw ─────────────────────────────────────────────
    def draw(self, surf):
        font_title, font_big, font_med, font_sm, font_xs = self.fonts
        dino = self.dino

        # Scene background — use Order.png if available, else fallback
        bg = ASSETS.get_scene_bg("order", (SCREEN_W, SCREEN_H))
        if bg:
            surf.blit(bg, (0, 0))
        else:
            surf.fill(C_ORDER_BG)
            self._draw_counter(surf)

        # Dino sprite — use character art if available, else emoji fallback
        dx = int(self._dino_x)
        dy = int(380 + self._bounce)
        dino_sprite = ASSETS.get_dino(dino.dino_type, size=(180, 180))
        if dino_sprite:
            surf.blit(dino_sprite, (dx - 90, dy - 90))
        else:
            dino_em = font_title.render(dino.emoji, True, (255, 255, 255))
            surf.blit(dino_em, (dx - dino_em.get_width() // 2, dy))

        # Speech bubble
        if self._speech_alpha > 0.05:
            self._draw_speech_bubble(surf, dx, dy, font_med, font_sm)

        # Scene label
        lbl = font_sm.render("SCENE 1  —  TAKING ORDER", True, C_TEXT_DIM)
        surf.blit(lbl, (20, 14))

        # Patience bar — at top
        self._draw_patience_bar(surf, font_sm)

        # Phase timer
        ratio = max(0, self.timer / ORDER_PHASE_TIME)
        col   = C_GOOD if ratio > 0.5 else (C_WARN if ratio > 0.25 else C_DANGER)
        pygame.draw.rect(surf, (20, 14, 6),  (20, 40, 200, 12), border_radius=4)
        pygame.draw.rect(surf, col,          (20, 40, int(200 * ratio), 12), border_radius=4)
        tl = font_xs.render(f"Order time: {int(self.timer)}s", True, C_TEXT_DIM)
        surf.blit(tl, (20, 55))

        # Confirm button
        if self._speech_alpha > 0.5:
            btn   = self._confirm_rect()
            bc    = (55, 140, 55) if self._hover_confirm else (35, 100, 35)
            pygame.draw.rect(surf, bc, btn, border_radius=10)
            pygame.draw.rect(surf, C_BORDER, btn, 2, border_radius=10)
            btext = font_big.render("Got it! →", True, C_TEXT)
            surf.blit(btext, (btn.centerx - btext.get_width() // 2,
                              btn.centery - btext.get_height() // 2))

    def _draw_counter(self, surf):
        # Diner counter surface
        pygame.draw.rect(surf, (55, 38, 18), (0, 480, SCREEN_W, 240))
        pygame.draw.rect(surf, (75, 55, 25), (0, 480, SCREEN_W, 14))
        # Wood planks
        for i in range(6):
            pygame.draw.line(surf, (45, 30, 12),
                             (0, 500 + i * 38), (SCREEN_W, 500 + i * 38), 1)

    def _draw_speech_bubble(self, surf, dino_x, dino_y, font_med, font_sm):
        alpha = int(self._speech_alpha * 255)
        bx, by = dino_x + 80, dino_y - 160
        bw, bh = 380, 140

        # Bubble panel
        bubble = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(bubble, (*self.SPEECH_BG, alpha), (0, 0, bw, bh), border_radius=14)
        pygame.draw.rect(bubble, (*self.SPEECH_BR, alpha), (0, 0, bw, bh), 2, border_radius=14)
        surf.blit(bubble, (bx, by))

        # Tail
        tail = pygame.Surface((30, 24), pygame.SRCALPHA)
        pygame.draw.polygon(tail, (*self.SPEECH_BG, alpha), [(0, 0), (30, 0), (0, 24)])
        surf.blit(tail, (bx + 10, by + bh - 2))

        # Speech text
        speech = self.dino.dino_type_data()["speech"]
        st = font_sm.render(speech, True, (30, 22, 10))
        st.set_alpha(alpha)
        surf.blit(st, (bx + 14, by + 10))

        # "I want:" label
        want = font_sm.render("I'd like to order:", True, (80, 60, 20))
        want.set_alpha(alpha)
        surf.blit(want, (bx + 14, by + 34))

        # Order items inline
        ox = bx + 14
        for i, key in enumerate(self.dino.order.items):
            data = INGREDIENTS[key]
            em   = font_med.render(data["emoji"], True, (30, 22, 10))
            em.set_alpha(alpha)
            surf.blit(em, (ox, by + 60))
            lbl  = font_sm.render(data["label"], True, (30, 22, 10))
            lbl.set_alpha(alpha)
            surf.blit(lbl, (ox, by + 90))
            ox  += max(em.get_width(), lbl.get_width()) + 18

    def _draw_patience_bar(self, surf, font_sm):
        ratio = self.dino.patience_ratio()
        col   = C_GOOD if ratio > 0.6 else (C_WARN if ratio > 0.3 else C_DANGER)
        pygame.draw.rect(surf, (20, 14, 6),  (SCREEN_W - 270, 14, 240, 16), border_radius=5)
        if ratio > 0:
            pygame.draw.rect(surf, col,      (SCREEN_W - 270, 14, int(240 * ratio), 16), border_radius=5)
        pl = font_sm.render(f"{self.dino.name} patience", True, C_TEXT_DIM)
        surf.blit(pl, (SCREEN_W - 270, 33))

    def _confirm_rect(self):
        return pygame.Rect(500, 560, 200, 56)


# ── Scene 2: COOKING STATION ───────────────────────────────────────
GRILL_SLOTS = 6

class GrillSlot:
    """One slot on the grill. Holds one ingredient and cooks it."""
    SIZE = 90

    def __init__(self, cx, cy):
        self.cx         = cx
        self.cy         = cy
        self.rect       = pygame.Rect(cx - self.SIZE // 2, cy - self.SIZE // 2,
                                      self.SIZE, self.SIZE)
        self.ingredient = None   # key string
        self.progress   = 0.0   # 0..1
        self.cooked     = False
        self.burnt      = False
        self._burn_timer = 0.0  # how long past done

    def place(self, key: str):
        self.ingredient = key
        self.progress   = 0.0
        self.cooked     = False
        self.burnt      = False
        self._burn_timer = 0.0

    def clear(self):
        key = self.ingredient
        self.ingredient  = None
        self.progress    = 0.0
        self.cooked      = False
        self.burnt       = False
        self._burn_timer = 0.0
        return key

    def update(self, dt, cook_speed):
        if self.ingredient and not self.burnt:
            data     = INGREDIENTS[self.ingredient]
            cook_t   = data["cook_time"] / cook_speed
            self.progress = min(1.0, self.progress + dt / cook_t)
            if self.progress >= 1.0:
                self.cooked = True
                self._burn_timer += dt
                if self._burn_timer > 6.0:   # 6 seconds grace before burn
                    self.burnt = True

    def draw(self, surf, font_big, font_sm, font_xs, hover):
        # Grill grate
        col = (60, 45, 20)
        if hover and not self.ingredient:
            col = (80, 60, 28)
        pygame.draw.rect(surf, col, self.rect, border_radius=8)
        pygame.draw.rect(surf, (90, 65, 28), self.rect, 2, border_radius=8)

        # Grate lines
        for i in range(3):
            gx = self.rect.x + 8 + i * 26
            pygame.draw.line(surf, (40, 28, 10),
                             (gx, self.rect.y + 4), (gx, self.rect.bottom - 4), 2)

        if not self.ingredient:
            if hover:
                ph = font_xs.render("+ drop here", True, (100, 75, 35))
                surf.blit(ph, (self.rect.centerx - ph.get_width() // 2,
                               self.rect.centery - ph.get_height() // 2))
            return

        data = INGREDIENTS[self.ingredient]

        # Heat glow
        if not self.cooked:
            glow_r = int(30 + self.progress * 50)
            glow_s = pygame.Surface((self.SIZE + 24, self.SIZE + 24), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (200, 80, 20, int(60 * self.progress)),
                               (self.SIZE // 2 + 12, self.SIZE // 2 + 12),
                               self.SIZE // 2 + 10)
            surf.blit(glow_s, (self.rect.x - 12, self.rect.y - 12))

        # Ingredient emoji
        bg_col = data["color"]
        if self.burnt:
            bg_col = (30, 20, 10)
        elif self.cooked:
            bg_col = tuple(min(255, c + 30) for c in bg_col)

        pygame.draw.rect(surf, bg_col, self.rect.inflate(-8, -8), border_radius=6)

        # Use food sprite if available
        food_sprite = ASSETS.get_food(self.ingredient, cooked=self.cooked,
                                       size=(self.SIZE - 16, self.SIZE - 16))
        if food_sprite and not self.burnt:
            surf.blit(food_sprite, (self.rect.x + 8, self.rect.y + 8))
        else:
            em = font_big.render(data["emoji"] if not self.burnt else "🖤", True, (255, 255, 255))
            surf.blit(em, (self.rect.centerx - em.get_width() // 2,
                           self.rect.centery - em.get_height() // 2 - 8))

        # Cook progress bar
        bx = self.rect.x + 2
        by = self.rect.bottom - 14
        bw = self.rect.width - 4

        if self.burnt:
            pygame.draw.rect(surf, (30, 20, 10), (bx, by, bw, 10), border_radius=3)
            txt = font_xs.render("BURNT! click=discard", True, C_DANGER)
            surf.blit(txt, (self.rect.centerx - txt.get_width() // 2, by - 14))
        elif self.cooked:
            pygame.draw.rect(surf, C_GOOD, (bx, by, bw, 10), border_radius=3)
            txt = font_xs.render("✓ DONE  click=tray", True, C_GOOD)
            surf.blit(txt, (self.rect.centerx - txt.get_width() // 2, by - 14))
        else:
            pygame.draw.rect(surf, (30, 20, 10), (bx, by, bw, 10), border_radius=3)
            fill_col = C_WARN if self.progress < 0.7 else C_GOOD
            pygame.draw.rect(surf, fill_col,
                             (bx, by, int(bw * self.progress), 10), border_radius=3)
            if hover:
                hint = font_xs.render("click=remove", True, (200, 140, 60))
                surf.blit(hint, (self.rect.centerx - hint.get_width() // 2, by - 14))


class CookScene:
    """
    Grill station. Papa's style.
    Left: ingredient shelf. Centre: 6 grill slots.
    Click ingredient on shelf → place on a grill slot.
    Click cooked slot → pull to finished tray.
    Right side: finished tray.
    "Serve Plate →" button once all ordered items are cooked.
    """

    def __init__(self, dino, receipt, particles, fonts,
                 cook_speed, on_done, shop_stock):
        self.dino       = dino
        self.receipt    = receipt
        self.particles  = particles
        self.fonts      = fonts
        self.cook_speed = cook_speed
        self.on_done    = on_done    # callback(cooked_items) → plate scene
        self.stock      = dict(shop_stock)

        # Build grill slots (2 rows × 3)
        self.slots: list[GrillSlot] = []
        slot_cx = [380, 520, 660]
        slot_cy = [200, 340]
        for cy in slot_cy:
            for cx in slot_cx:
                self.slots.append(GrillSlot(cx, cy))

        # Finished tray (cooked items ready for plating)
        self.finished: list[str] = []

        # Ingredient shelf buttons (left)
        self._shelf_hover = None
        self._selected_ingr = None   # key being held

        # Held item follows mouse
        self._held  = None    # key
        self._held_src = None  # "shelf" or slot index

        self._t = 0.0
        self._hover_serve = False
        self._msg = ""
        self._msg_timer = 0.0

        # Required items from the order
        self._required = list(self.dino.order.items)
        self._remaining = list(self._required)   # items still needed

    def update(self, dt, mx, my):
        self._t += dt
        for slot in self.slots:
            slot.update(dt, self.cook_speed)

        # Patience
        drain = PATIENCE_RATE * self.dino.dino_type_data()["speed"]
        self.dino.patience = max(0, self.dino.patience - drain * dt)

        if self._msg_timer > 0:
            self._msg_timer -= dt

        # Serve button hover
        self._hover_serve = self._serve_rect().collidepoint(mx, my)

    def handle_click(self, mx, my):
        # ── Serve button checked FIRST — highest priority ──
        if self._serve_rect().collidepoint(mx, my):
            if self._can_serve():
                self.on_done(list(self.finished))
            else:
                missing = self._missing_items()
                need_str = " ".join(INGREDIENTS[k]["emoji"] for k in missing)
                self._msg = f"Still need: {need_str}"
                self._msg_timer = 3.0
            return

        # Click any grill slot
        for slot in self.slots:
            if not slot.rect.collidepoint(mx, my):
                continue
            if slot.cooked and not slot.burnt:
                # Cooked → move to finished tray
                key = slot.clear()
                self.finished.append(key)
                self.particles.stars(slot.rect.centerx, slot.rect.centery,
                                     color=(80, 220, 80), count=8)
                return
            elif slot.burnt:
                # Burnt → discard, stock NOT returned (it's ruined)
                slot.clear()
                self._msg = "Burnt and wasted!"
                self._msg_timer = 2.0
                self.particles.angry_sparks(slot.rect.centerx, slot.rect.centery)
                return
            elif slot.ingredient is not None:
                # Still cooking → pull it off and return to stock
                key = slot.clear()
                self.stock[key] = self.stock.get(key, 0) + 1
                self._msg = f"Removed from grill — back in stock."
                self._msg_timer = 1.5
                return

        # Click a finished tray item → remove and return to stock
        for i, key in enumerate(self.finished):
            data  = INGREDIENTS[key]
            iy    = 100 + 36 + i * 52
            tray  = pygame.Rect(810 + 12, iy, 250 - 24, 44)
            if tray.collidepoint(mx, my):
                self.finished.pop(i)
                self.stock[key] = self.stock.get(key, 0) + 1
                self._msg = f"{data['label']} returned to stock."
                self._msg_timer = 1.5
                self.particles.smoke(tray.centerx, tray.centery)
                return

        # Click ingredient from shelf → place on first empty slot
        for key, data in INGREDIENTS.items():
            btn = self._shelf_rect(key)
            if btn.collidepoint(mx, my) and self.stock.get(key, 0) > 0:
                for slot in self.slots:
                    if slot.ingredient is None:
                        slot.place(key)
                        self.stock[key] -= 1
                        self.particles.smoke(btn.centerx, btn.centery)
                        return
                self._msg = "No empty grill slots!"
                self._msg_timer = 2.0
                return

    def _can_serve(self) -> bool:
        needed = sorted(self._required)
        have   = sorted(self.finished)
        return have == needed

    def _missing_items(self) -> list:
        have   = list(self.finished)
        needed = list(self._required)
        missing = []
        for item in needed:
            if item in have:
                have.remove(item)
            else:
                missing.append(item)
        return missing

    def draw(self, surf):
        font_title, font_big, font_med, font_sm, font_xs = self.fonts
        # Scene background
        cook_bg = ASSETS.get_scene_bg("cook", (SCREEN_W, SCREEN_H))
        if cook_bg:
            surf.blit(cook_bg, (0, 0))
        else:
            surf.fill(C_COOK_BG)

        # Grill surface overlay
        self._draw_grill_surface(surf)

        # Scene label
        lbl = font_sm.render("SCENE 2  —  COOKING STATION", True, C_TEXT_DIM)
        surf.blit(lbl, (20, 14))

        # Patience bar
        ratio = self.dino.patience_ratio()
        col   = C_GOOD if ratio > 0.6 else (C_WARN if ratio > 0.3 else C_DANGER)
        pygame.draw.rect(surf, (15, 10, 5), (SCREEN_W - 270, 14, 240, 16), border_radius=5)
        if ratio > 0:
            pygame.draw.rect(surf, col, (SCREEN_W - 270, 14, int(240 * ratio), 16), border_radius=5)
        pl = font_sm.render(f"{self.dino.name} waiting...", True, C_TEXT_DIM)
        surf.blit(pl, (SCREEN_W - 270, 33))

        # Ingredient shelf (left)
        self._draw_shelf(surf, font_med, font_sm, font_xs)

        # Grill slots
        mx, my = pygame.mouse.get_pos()
        for slot in self.slots:
            hover = slot.rect.collidepoint(mx, my)
            slot.draw(surf, font_big, font_sm, font_xs, hover)

        # Grill label
        gl = font_sm.render("GRILL — click ingredient to place, click cooked to remove", True, C_TEXT_DIM)
        surf.blit(gl, (310, 440))

        # Finished tray (right)
        self._draw_finished_tray(surf, font_med, font_sm, font_xs)

        # Serve button — always drawn last so it's always on top and clickable
        serve  = self._serve_rect()
        can    = self._can_serve()
        missing = self._missing_items()
        if can:
            sc = (35, 105, 35)
            sh = (50, 148, 50) if self._hover_serve else sc
            label = "✅  Plate it Up! →"
        else:
            sc = (55, 45, 18)
            sh = (75, 60, 22) if self._hover_serve else sc
            label = f"Still cooking... ({len(missing)} left)"
        pygame.draw.rect(surf, sh, serve, border_radius=10)
        pygame.draw.rect(surf, (C_GOOD if can else C_WARN), serve, 2, border_radius=10)
        st = font_big.render(label, True, C_TEXT)
        surf.blit(st, (serve.centerx - st.get_width() // 2,
                       serve.centery - st.get_height() // 2))

        # Message
        if self._msg_timer > 0:
            ms = font_med.render(self._msg, True, C_WARN)
            surf.blit(ms, (310, 470))

    def _draw_grill_surface(self, surf):
        # Dark grill background
        pygame.draw.rect(surf, (22, 32, 16), (300, 100, 480, 380), border_radius=16)
        pygame.draw.rect(surf, (40, 55, 28), (300, 100, 480, 380), 2, border_radius=16)
        # Heat shimmer bars
        for i in range(6):
            y = 120 + i * 60
            s = pygame.Surface((460, 4), pygame.SRCALPHA)
            alpha = int(20 + 10 * math.sin(self._t * 2 + i))
            s.fill((255, 120, 20, alpha))
            surf.blit(s, (310, y))

    def _draw_shelf(self, surf, font_med, font_sm, font_xs):
        # Shelf background
        pygame.draw.rect(surf, (35, 28, 14), (8, 80, 270, SCREEN_H - 100), border_radius=10)
        pygame.draw.rect(surf, C_BORDER,     (8, 80, 270, SCREEN_H - 100), 2, border_radius=10)
        lbl = font_sm.render("INGREDIENTS", True, C_TEXT_DIM)
        surf.blit(lbl, (20, 88))

        mx, my = pygame.mouse.get_pos()
        for key in INGREDIENTS:
            btn  = self._shelf_rect(key)
            data = INGREDIENTS[key]
            stock = self.stock.get(key, 0)
            hover = btn.collidepoint(mx, my) and stock > 0

            bg = (55, 44, 22) if hover else (40, 30, 14)
            pygame.draw.rect(surf, bg, btn, border_radius=8)
            border = data["color"] if hover else C_BORDER
            pygame.draw.rect(surf, border, btn, 2, border_radius=8)

            food_icon = ASSETS.get_food(key, cooked=False, size=(40, 40))
            if food_icon:
                surf.blit(food_icon, (btn.x + 6, btn.y + 10))
            else:
                em  = font_med.render(data["emoji"], True, C_TEXT)
                surf.blit(em, (btn.x + 6, btn.y + 8))
            nm  = font_sm.render(data["label"], True, C_TEXT if stock > 0 else C_TEXT_DIM)
            surf.blit(nm, (btn.x + 54, btn.y + 10))

            ct  = font_xs.render(f"Cook: {data['cook_time']}s", True, C_TEXT_DIM)
            surf.blit(ct, (btn.x + 44, btn.y + 28))

            stock_col = C_GOOD if stock > 0 else C_DANGER
            ss  = font_sm.render(f"x{stock}", True, stock_col)
            surf.blit(ss, (btn.right - ss.get_width() - 8, btn.y + 14))

            if stock == 0:
                ov = pygame.Surface((btn.w, btn.h), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 110))
                surf.blit(ov, btn.topleft)

    def _shelf_rect(self, key: str) -> pygame.Rect:
        keys = list(INGREDIENTS.keys())
        i    = keys.index(key)
        return pygame.Rect(14, 110 + i * 78, 256, 68)

    def _draw_finished_tray(self, surf, font_med, font_sm, font_xs):
        tx, ty = 810, 100
        tw, th = 250, SCREEN_H - 180
        pygame.draw.rect(surf, (30, 24, 40), (tx, ty, tw, th), border_radius=10)
        pygame.draw.rect(surf, C_BORDER,     (tx, ty, tw, th), 2, border_radius=10)
        lbl = font_sm.render("FINISHED TRAY", True, C_TEXT_DIM)
        surf.blit(lbl, (tx + 12, ty + 10))
        sub = font_xs.render("click item = return to stock", True, C_TEXT_DIM)
        surf.blit(sub, (tx + 12, ty + 22))

        mx, my = pygame.mouse.get_pos()
        for i, key in enumerate(self.finished):
            data   = INGREDIENTS[key]
            iy     = ty + 36 + i * 52
            item_r = pygame.Rect(tx + 12, iy, tw - 24, 44)
            hover  = item_r.collidepoint(mx, my)
            col    = tuple(max(0, c - 40) for c in data["color"]) if hover else data["color"]
            pygame.draw.rect(surf, col, item_r, border_radius=8)
            pygame.draw.rect(surf, (220, 100, 60) if hover else data["color"],
                             item_r, 2, border_radius=8)
            food_s = ASSETS.get_food(key, cooked=True, size=(36, 36))
            if food_s:
                surf.blit(food_s, (tx + 12, iy + 4))
            else:
                em = font_med.render(data["emoji"], True, (255, 255, 255))
                surf.blit(em, (tx + 18, iy + 8))
            label_txt = "x return" if hover else data["label"]
            label_col = (255, 160, 100) if hover else (255, 255, 255)
            nm = font_sm.render(label_txt, True, label_col)
            surf.blit(nm, (tx + 54, iy + 14))

        if not self.finished:
            ph = font_xs.render("Cook items then click to move here", True, C_TEXT_DIM)
            surf.blit(ph, (tx + 20, ty + 42))

    def _serve_rect(self):
        return pygame.Rect(310, SCREEN_H - 72, 460, 55)


# ── Scene 3: MEAL PREP / PLATING ──────────────────────────────────
class PlateScene:
    """
    Plating station.
    Left: cooked items (from CookScene).
    Centre: plate with highlighted slots showing expected ingredients.
    Receipt top-right shows the order.
    Drag cooked items onto plate slots.
    "Serve!" evaluates the plate.
    """

    def __init__(self, dino, cooked_items: list, receipt, particles, fonts,
                 on_serve):
        self.dino        = dino
        self.cooked      = list(cooked_items)
        self.receipt     = receipt
        self.particles   = particles
        self.fonts       = fonts
        self.on_serve    = on_serve   # callback(result_dict)

        self.plate: list[str] = []    # keys placed on plate (in order)
        self._required  = list(dino.order.items)

        self._t          = 0.0
        self._hover_serve = False
        self._hover_clear = False
        self._msg        = ""
        self._msg_timer  = 0.0

        self._plate_anim = 0.0   # spin

    def update(self, dt, mx, my):
        self._t       += dt
        self._plate_anim += dt * 0.5
        drain = PATIENCE_RATE * self.dino.dino_type_data()["speed"]
        self.dino.patience = max(0, self.dino.patience - drain * dt)

        self._hover_serve = self._serve_rect().collidepoint(mx, my)
        self._hover_clear = self._clear_rect().collidepoint(mx, my)

        if self._msg_timer > 0:
            self._msg_timer -= dt

    def handle_click(self, mx, my):
        # ── Serve and Clear checked first — highest priority ──
        if self._serve_rect().collidepoint(mx, my):
            self._do_serve()
            return

        if self._clear_rect().collidepoint(mx, my) and self.plate:
            self.cooked.extend(self.plate)
            self.plate = []
            return

        # Click cooked item from tray → add to plate
        for i, key in enumerate(self.cooked):
            btn = self._tray_item_rect(i)
            if btn.collidepoint(mx, my):
                self.plate.append(key)
                self.cooked.pop(i)
                self.particles.smoke(btn.centerx, btn.centery)
                return

        # Click plate slot → remove item back to tray
        for i, key in enumerate(self.plate):
            slot = self._plate_slot_rect(i)
            if slot.collidepoint(mx, my):
                self.cooked.append(key)
                self.plate.pop(i)
                return

    def _do_serve(self):
        result = self.dino.evaluate_plate(list(self.plate))
        if result["success"]:
            self.particles.coins(640, 360, count=20)
            self.particles.stars(640, 360, count=16)
        else:
            self.particles.angry_sparks(640, 360)
        self.on_serve(result)

    def draw(self, surf):
        font_title, font_big, font_med, font_sm, font_xs = self.fonts
        # Scene background
        plate_bg = ASSETS.get_scene_bg("plate", (SCREEN_W, SCREEN_H))
        if plate_bg:
            surf.blit(plate_bg, (0, 0))
        else:
            surf.fill(C_PLATE_BG)

        # Scene label
        lbl = font_sm.render("SCENE 3  —  PLATING", True, C_TEXT_DIM)
        surf.blit(lbl, (20, 14))

        # Patience bar
        ratio = self.dino.patience_ratio()
        col   = C_GOOD if ratio > 0.6 else (C_WARN if ratio > 0.3 else C_DANGER)
        pygame.draw.rect(surf, (15, 10, 5), (SCREEN_W - 270, 14, 240, 16), border_radius=5)
        if ratio > 0:
            pygame.draw.rect(surf, col, (SCREEN_W - 270, 14, int(240 * ratio), 16), border_radius=5)
        pl = font_sm.render(f"{self.dino.name} waiting...", True, C_TEXT_DIM)
        surf.blit(pl, (SCREEN_W - 270, 33))

        # Cooked items tray (left)
        self._draw_cooked_tray(surf, font_med, font_sm, font_xs)

        # Plate in centre
        self._draw_plate(surf, font_big, font_med, font_sm, font_xs)

        # Buttons
        self._draw_buttons(surf, font_big, font_sm)

        # Message
        if self._msg_timer > 0:
            ms = font_med.render(self._msg, True, C_WARN)
            surf.blit(ms, (400, 620))

    def _draw_cooked_tray(self, surf, font_med, font_sm, font_xs):
        tx, ty = 20, 80
        tw, th = 260, SCREEN_H - 130
        pygame.draw.rect(surf, (38, 28, 50), (tx, ty, tw, th), border_radius=10)
        pygame.draw.rect(surf, C_BORDER,     (tx, ty, tw, th), 2, border_radius=10)
        lbl = font_sm.render("COOKED — click to plate", True, C_TEXT_DIM)
        surf.blit(lbl, (tx + 10, ty + 10))

        mx, my = pygame.mouse.get_pos()
        for i, key in enumerate(self.cooked):
            btn  = self._tray_item_rect(i)
            data = INGREDIENTS[key]
            hover = btn.collidepoint(mx, my)
            bg   = tuple(min(255, c + 30) for c in data["color"]) if hover else data["color"]
            pygame.draw.rect(surf, bg, btn, border_radius=8)
            pygame.draw.rect(surf, (255, 255, 255) if hover else C_BORDER, btn, 2, border_radius=8)
            food_s = ASSETS.get_food(key, cooked=True, size=(38, 38))
            if food_s:
                surf.blit(food_s, (btn.x + 6, btn.y + 7))
            else:
                em   = font_med.render(data["emoji"], True, (255, 255, 255))
                surf.blit(em, (btn.x + 8, btn.y + 10))
            nm   = font_sm.render(data["label"], True, (255, 255, 255))
            surf.blit(nm, (btn.x + 52, btn.y + 16))

        if not self.cooked:
            ph = font_sm.render("All items plated!", True, C_GOOD)
            surf.blit(ph, (tx + 20, ty + 40))

    def _tray_item_rect(self, i: int) -> pygame.Rect:
        return pygame.Rect(28, 110 + i * 62, 244, 52)

    def _draw_plate(self, surf, font_big, font_med, font_sm, font_xs):
        # Plate base circle
        cx, cy = 640, 350
        r      = 220
        pygame.draw.circle(surf, (200, 190, 175), (cx, cy), r)
        pygame.draw.circle(surf, (180, 165, 145), (cx, cy), r, 3)
        pygame.draw.circle(surf, (215, 205, 190), (cx, cy), r - 24, 2)   # inner ring

        pl = font_sm.render("PLATE  —  click item to return", True, C_TEXT_DIM)
        surf.blit(pl, (cx - pl.get_width() // 2, cy - r - 32))

        # Expected slots (ghost items)
        for i, key in enumerate(self._required):
            slot_r  = self._plate_slot_rect(i)
            if i < len(self.plate):
                # Filled
                placed_key = self.plate[i]
                data = INGREDIENTS[placed_key]
                pygame.draw.rect(surf, data["color"], slot_r, border_radius=10)
                pygame.draw.rect(surf, (255, 255, 255), slot_r, 2, border_radius=10)
                food_s = ASSETS.get_food(placed_key, cooked=True,
                                         size=(slot_r.w - 8, slot_r.h - 8))
                if food_s:
                    surf.blit(food_s, (slot_r.x + 4, slot_r.y + 4))
                else:
                    em = font_big.render(data["emoji"], True, (255, 255, 255))
                    surf.blit(em, (slot_r.centerx - em.get_width() // 2,
                                   slot_r.centery - em.get_height() // 2))
            else:
                # Ghost / expected
                ghost_data = INGREDIENTS[key]
                ghost_s = pygame.Surface((slot_r.w, slot_r.h), pygame.SRCALPHA)
                alpha   = int(60 + 30 * math.sin(self._t * 3 + i))
                pygame.draw.rect(ghost_s, (*ghost_data["color"], alpha),
                                 (0, 0, slot_r.w, slot_r.h), border_radius=10)
                pygame.draw.rect(ghost_s, (*ghost_data["color"], 180),
                                 (0, 0, slot_r.w, slot_r.h), 2, border_radius=10)
                surf.blit(ghost_s, slot_r.topleft)
                # Show what goes here
                em = font_big.render(ghost_data["emoji"], True,
                                     (*ghost_data["color"], 120))
                em.set_alpha(100)
                surf.blit(em, (slot_r.centerx - em.get_width() // 2,
                               slot_r.centery - em.get_height() // 2))

    def _plate_slot_rect(self, i: int) -> pygame.Rect:
        """Arrange slots in a circle/grid on the plate."""
        n    = len(self._required)
        if n == 1:
            return pygame.Rect(605, 315, 70, 70)
        angle = (2 * math.pi * i / n) - math.pi / 2
        r     = 110 if n <= 4 else 130
        cx    = int(640 + r * math.cos(angle))
        cy    = int(350 + r * math.sin(angle))
        return pygame.Rect(cx - 35, cy - 35, 70, 70)

    def _draw_buttons(self, surf, font_big, font_sm):
        serve  = self._serve_rect()
        clear  = self._clear_rect()

        sc  = (40, 110, 40) if self._hover_serve else (28, 80, 28)
        pygame.draw.rect(surf, sc, serve, border_radius=10)
        pygame.draw.rect(surf, C_BORDER, serve, 2, border_radius=10)
        st  = font_big.render("🍽  Serve!", True, C_TEXT)
        surf.blit(st, (serve.centerx - st.get_width() // 2,
                       serve.centery - st.get_height() // 2))

        cc  = (100, 38, 22) if self._hover_clear else (70, 25, 14)
        pygame.draw.rect(surf, cc, clear, border_radius=10)
        pygame.draw.rect(surf, C_BORDER, clear, 2, border_radius=10)
        ct  = font_sm.render("Clear plate", True, C_TEXT)
        surf.blit(ct, (clear.centerx - ct.get_width() // 2,
                       clear.centery - ct.get_height() // 2))

    def _serve_rect(self):
        return pygame.Rect(860, 598, 130, 50)

    def _clear_rect(self):
        return pygame.Rect(860, 540, 130, 48)
