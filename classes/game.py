"""
Game — Dino Papa's central controller

Loop structure:
  Days 1-4: SHOP → RESTAURANT (ends when food runs out) → END_DAY → SHOP ...
  Day 5:    SHOP → RESTAURANT → END_DAY → UPGRADE SHOP → back to Day 1 (harder)

Money carries across ALL days.
Daily spend allowance given each morning for restocking.
Upgrades only available every 5 days.
"""

import pygame
import random
import math

from classes.constants   import *
from classes.constants   import S, SX, SY, SF
from classes.dino        import Dino
from classes.scenes      import OrderScene, CookScene, PlateScene
from classes.chaos       import ChaosManager
from classes.particles   import ParticleSystem
from classes.ui          import draw_panel, draw_button, draw_money, pulse_alpha, draw_progress_bar
from classes.assets      import ASSETS
from classes.music       import MUSIC

# ── Top-level states ──────────────────────────────────
ST_TITLE      = "title"
ST_SHOP       = "shop"
ST_RESTAURANT = "restaurant"
ST_END_DAY    = "end_day"
ST_UPGRADE    = "upgrade"
ST_GAMEOVER   = "gameover"

# ── In-restaurant sub-states ──────────────────────────
SUB_QUEUE  = "queue"
SUB_ORDER  = "order"
SUB_COOK   = "cook"
SUB_PLATE  = "plate"
SUB_RESULT = "result"

# ── Game constants ────────────────────────────────────
CYCLE_LENGTH      = 5      # upgrade every N days
DAILY_ALLOWANCE   = 60     # free money to spend on food each morning (not kept)
ALLOWANCE_SCALE   = 10     # +$10 per completed cycle
STARTING_MONEY    = 0      # carried money starts at 0; allowance covers day 1


class StackedReceipt:
    PAPER  = (255, 252, 228)
    INK    = (30,  22,  10)
    DIM    = (130, 105,  60)
    STRIPE = (245, 238, 205)
    DONE_G = (40,  160,  55)

    def __init__(self):
        self.orders: list[dict] = []

    def push(self, dino, items: list):
        self.orders.append({
            "dino":  dino,
            "items": list(items),
            "done":  [False] * len(items),
            "id":    id(dino),
        })

    def tick_item(self, dino_id: int, item_key: str):
        for order in self.orders:
            if order["id"] == dino_id:
                for i, key in enumerate(order["items"]):
                    if key == item_key and not order["done"][i]:
                        order["done"][i] = True
                        return

    def complete_order(self, dino_id: int):
        self.orders = [o for o in self.orders if o["id"] != dino_id]

    def draw(self, surf, font_sm, font_xs):
        if not self.orders:
            return
        x, y, pad = RECEIPT_X, RECEIPT_Y, 10
        for oi, order in enumerate(self.orders[:4]):
            dino  = order["dino"]
            items = order["items"]
            done  = order["done"]
            row_h = 38 + len(items) * 22 + pad
            paper = pygame.Surface((RECEIPT_W, row_h), pygame.SRCALPHA)
            paper.fill((*self.PAPER, 240))
            surf.blit(paper, (x, y))
            if oi == 0:
                for tx in range(0, RECEIPT_W, 10):
                    tip = y - 3 if (tx // 10) % 2 == 0 else y
                    pygame.draw.polygon(surf, self.PAPER,
                                        [(x+tx, y), (x+tx+5, tip), (x+tx+10, y)])
            border_col = dino.color if oi == 0 else (160, 140, 90)
            pygame.draw.rect(surf, border_col, (x, y, RECEIPT_W, row_h), 2)
            dn = font_sm.render(f"{dino.emoji} {dino.name}", True,
                                dino.color if oi == 0 else self.DIM)
            surf.blit(dn, (x + pad, y + pad - 2))
            for i, key in enumerate(items):
                iy   = y + 30 + i * 22
                data = INGREDIENTS[key]
                if i % 2 == 0:
                    stripe = pygame.Surface((RECEIPT_W - pad*2, 20), pygame.SRCALPHA)
                    stripe.fill((*self.STRIPE, 160))
                    surf.blit(stripe, (x + pad, iy))
                chk = "✓" if done[i] else "·"
                cs  = font_xs.render(chk, True, self.DONE_G if done[i] else self.DIM)
                surf.blit(cs, (x + pad + 2, iy + 2))
                em  = font_xs.render(data["emoji"], True, self.DIM if done[i] else self.INK)
                surf.blit(em, (x + pad + 14, iy + 2))
                nm  = font_xs.render(data["label"], True, self.DIM if done[i] else self.INK)
                surf.blit(nm, (x + pad + 32, iy + 2))
            y += row_h + 4
        if len(self.orders) > 4:
            more = font_xs.render(f"+ {len(self.orders)-4} more...", True, self.DIM)
            surf.blit(more, (RECEIPT_X + 8, y + 4))


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._load_fonts()
        self._init_state()

    def on_resize(self, screen, w, h):
        """Called from main.py when window is resized."""
        self.screen = screen
        self._load_fonts()   # rebuild font sizes for new scale

    def _load_fonts(self):
        def f(size, bold=False):
            scaled = SF(size)
            for name in ["couriernew", "courier", "monospace"]:
                try:
                    return pygame.font.SysFont(name, scaled, bold=bold)
                except Exception:
                    pass
            return pygame.font.Font(None, scaled)
        self.font_title = f(64, bold=True)
        self.font_big   = f(32)
        self.font_med   = f(22)
        self.font_sm    = f(16)
        self.font_xs    = f(13)
        self._fonts     = (self.font_title, self.font_big, self.font_med,
                           self.font_sm, self.font_xs)

    # ─── State init ───────────────────────────────────
    def _init_state(self):
        self.state        = ST_TITLE
        self.sub_state    = SUB_QUEUE
        self.day          = 0        # 1-indexed when playing
        self.cycle        = 1        # which 5-day cycle we're in
        self.money        = STARTING_MONEY   # CARRIED across days
        self.score        = 0
        self.total_served = 0
        self._day_served  = 0
        self.day_earnings = 0
        self.day_losses   = 0

        # Daily spend allowance (given each morning, not kept if unspent)
        self._allowance   = DAILY_ALLOWANCE
        self._spend_budget = 0   # what's available in shop this morning

        self.upgrades       = {k: 0 for k in UPGRADES}
        self.cook_speed     = 1.0
        self.plate_slots    = 6
        self.tip_bonus      = 0.0
        self.patience_bonus = 0.0

        self.queue: list[Dino]     = []
        self.active_dino           = None
        self.shop_stock: dict      = {}
        self.receipt               = StackedReceipt()
        self.scene                 = None

        self._spawn_timer = 4.0
        self._food_out    = False   # triggers end-of-day

        self.chaos = ChaosManager()
        self.chaos.set_callbacks(self._chaos_fight, self._chaos_rush, self._chaos_meteor)

        self.particles  = ParticleSystem()
        self._result    = {}
        self._result_timer = 0.0
        self._t         = 0.0
        self._shop_cart = {}
        MUSIC.play_menu()
        self._end_summary = {}
        self._shake_frames = 0

    def _recalc_stats(self):
        self.cook_speed     = 1.0
        self.plate_slots    = 6
        self.tip_bonus      = 0.0
        self.patience_bonus = 0.0
        for k, lvl in self.upgrades.items():
            if lvl == 0:
                continue
            upg  = UPGRADES[k]
            stat = upg["stat"]
            val  = upg["value"] * lvl
            if   stat == "cook_speed":      self.cook_speed += val
            elif stat == "plate_slots":     self.plate_slots = int(6 + val)
            elif stat == "tip_bonus":       self.tip_bonus += val
            elif stat == "patience_bonus":  self.patience_bonus += val

    def _day_in_cycle(self) -> int:
        """1-5, where 5 is upgrade day."""
        return ((self.day - 1) % CYCLE_LENGTH) + 1

    def _is_upgrade_day(self) -> bool:
        return self._day_in_cycle() == CYCLE_LENGTH

    def _total_stock(self) -> int:
        return sum(self.shop_stock.values())

    # ─── Events ───────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        mx, my = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._on_click(mx, my)

    def _on_click(self, mx, my):
        if   self.state == ST_TITLE:      self._click_title(mx, my)
        elif self.state == ST_SHOP:       self._click_shop(mx, my)
        elif self.state == ST_RESTAURANT:
            if self.scene:
                self.scene.handle_click(mx, my)
            if self.sub_state == SUB_RESULT:
                self._advance_from_result()
        elif self.state == ST_END_DAY:    self._click_end_day(mx, my)
        elif self.state == ST_UPGRADE:    self._click_upgrade(mx, my)
        elif self.state == ST_GAMEOVER:
            self._init_state()
            self.state = ST_TITLE

    # ─── Update ───────────────────────────────────────
    def update(self, dt: float):
        self._t += dt
        if self._shake_frames > 0:
            self._shake_frames -= 1
        mx, my = pygame.mouse.get_pos()
        if self.state == ST_RESTAURANT:
            self._update_restaurant(dt, mx, my)
        self.particles.update(dt)

    def _update_restaurant(self, dt, mx, my):
        self.chaos.update(dt, self.day)

        # ── Food-out detection ────────────────────────
        # Check if ALL stock is gone AND no active dino is being served
        if not self._food_out:
            if self._total_stock() == 0 and not self.active_dino:
                self._food_out = True
                self.queue     = []   # clear any pre-spawned queue

        # ── Spawn dinos (only while food remains) ─────
        if not self._food_out:
            self._spawn_timer -= dt
            interval = max(3.5, 9.0 - self.day * 0.3)
            if self._spawn_timer <= 0 and len(self.queue) < MAX_QUEUE:
                self._spawn_timer = interval + random.uniform(-0.5, 0.5)
                dino = Dino.random_dino(self.day, self.patience_bonus,
                                        stock=self.shop_stock)
                # Only add if there's food that matches their order
                if dino.order.items:
                    self.queue.append(dino)

        # ── Sub-state machine ─────────────────────────
        if self.sub_state == SUB_QUEUE:
            if self.queue:
                self._start_order_scene(self.queue.pop(0))
            elif self._food_out and not self.active_dino:
                self._end_day()
            return

        if self.sub_state == SUB_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0:
                self._advance_from_result()
            return

        if self.scene:
            self.scene.update(dt, mx, my)

        # Patience ran out
        if self.active_dino and self.active_dino.patience <= 0:
            if self.sub_state in (SUB_COOK, SUB_PLATE):
                self._show_result({
                    "success": False,
                    "earnings": 0,
                    "msg": f"{self.active_dino.name} lost patience and LEFT! 😡",
                })
                self.day_losses += 10
                self.money = max(0, self.money - 10)

    # ─── Scene transitions ────────────────────────────
    def _start_order_scene(self, dino: Dino):
        dino.reroll_order(self.shop_stock)
        if not dino.order.items:
            self._show_result({
                "success": False, "earnings": 0,
                "msg": f"{dino.name} left — nothing in stock! 😔",
            })
            return
        self.active_dino = dino
        self.sub_state   = SUB_ORDER
        self.receipt.push(dino, dino.order.items)
        self.scene = OrderScene(
            dino=dino, receipt=None, particles=self.particles,
            fonts=self._fonts, on_confirm=self._on_order_confirmed,
        )

    def _on_order_confirmed(self):
        self.sub_state = SUB_COOK
        self.scene = CookScene(
            dino=self.active_dino, receipt=None, particles=self.particles,
            fonts=self._fonts, cook_speed=self.cook_speed,
            on_done=self._on_cooking_done, shop_stock=self.shop_stock,
        )

    def _on_cooking_done(self, cooked_items: list):
        self.shop_stock = dict(self.scene.stock)
        self.sub_state  = SUB_PLATE
        self.scene = PlateScene(
            dino=self.active_dino, cooked_items=cooked_items,
            receipt=None, particles=self.particles,
            fonts=self._fonts, on_serve=self._on_served,
        )

    def _on_served(self, result: dict):
        tip_bonus = int(result.get("earnings", 0) * self.tip_bonus)
        total     = result.get("earnings", 0) + tip_bonus
        if result["success"]:
            self.money        += total
            self.day_earnings += total
            self.score        += total
            self.total_served += 1
            self._day_served  += 1
            if tip_bonus:
                result["msg"] += f" (+${tip_bonus} tip)"
        if self.active_dino:
            self.receipt.complete_order(id(self.active_dino))
        self._show_result(result)

    def _show_result(self, result: dict):
        self._result       = result
        self._result_timer = 2.2
        self.sub_state     = SUB_RESULT
        self.scene         = None

    def _advance_from_result(self):
        self.active_dino = None
        self.sub_state   = SUB_QUEUE
        self.scene       = None

    # ─── Chaos ────────────────────────────────────────
    def _chaos_fight(self):
        if self.queue:
            self.queue.pop(0)
            self.particles.angry_sparks(SCREEN_W // 2, 300)

    def _chaos_rush(self):
        if len(self.queue) < MAX_QUEUE:
            d = Dino.random_dino(self.day, self.patience_bonus, stock=self.shop_stock)
            if d.order.items:
                self.queue.append(d)

    def _chaos_meteor(self):
        for d in self.queue:
            d.patience *= 0.5
        if self.active_dino:
            self.active_dino.patience *= 0.5
        self._shake_frames = 25

    # ─── End day ──────────────────────────────────────
    def _end_day(self):
        self._end_summary = {
            "earnings": self.day_earnings,
            "losses":   self.day_losses,
            "net":      self.day_earnings - self.day_losses,
            "served":   self._day_served,
            "day_in_cycle": self._day_in_cycle(),
            "is_upgrade_day": self._is_upgrade_day(),
        }
        self.state     = ST_END_DAY
        self.sub_state = SUB_QUEUE

    # ─── Shop ─────────────────────────────────────────
    def _start_shop(self):
        # Daily allowance scales with cycle
        self._spend_budget = DAILY_ALLOWANCE + (self.cycle - 1) * ALLOWANCE_SCALE
        self._shop_cart    = {k: 0 for k in INGREDIENTS}
        self.state         = ST_SHOP
        self._recalc_stats()

    def _begin_restaurant(self):
        self.state        = ST_RESTAURANT
        self.sub_state    = SUB_QUEUE
        self.queue        = []
        self.active_dino  = None
        self.scene        = None
        self.receipt      = StackedReceipt()
        self.day_earnings = 0
        self.day_losses   = 0
        self._spawn_timer = 3.0
        self._food_out    = False
        self._day_served  = 0
        self.particles    = ParticleSystem()

    # ═══════════════════════════════════════════════════
    # DRAW
    # ═══════════════════════════════════════════════════
    def draw(self):
        sx = sy = 0
        if self._shake_frames > 0 or self.chaos.volcano_active:
            shake = self.chaos.get_screen_shake() if self.chaos.volcano_active else 4
            sx    = random.randint(-shake, shake)
            sy    = random.randint(-shake, shake)
        surf = pygame.Surface((SCREEN_W, SCREEN_H))
        surf.fill(C_BG)

        if   self.state == ST_TITLE:      self._draw_title(surf)
        elif self.state == ST_SHOP:       self._draw_shop(surf)
        elif self.state == ST_RESTAURANT: self._draw_restaurant(surf)
        elif self.state == ST_END_DAY:    self._draw_end_day(surf)
        elif self.state == ST_UPGRADE:    self._draw_upgrade(surf)
        elif self.state == ST_GAMEOVER:   self._draw_gameover(surf)

        self.particles.draw(surf)
        self.screen.blit(surf, (sx, sy))

    # ─── Title ────────────────────────────────────────
    def _draw_title(self, surf):
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        mx, my = pygame.mouse.get_pos()

        # ── Background: Menu.png or procedural fallback ──
        menu_bg = ASSETS.get_scene_bg("menu", (SCREEN_W, SCREEN_H))
        if menu_bg:
            surf.blit(menu_bg, (0, 0))
        else:
            # Procedural background
            for row in range(SCREEN_H):
                t = row / SCREEN_H
                pygame.draw.line(surf,
                    (int(18+t*42), int(10+t*22), int(5+t*12)),
                    (0, row), (SCREEN_W, row))
            # Animated stripes
            for i in range(14):
                y = (i * SY(60) + int(self._t * 18)) % SCREEN_H
                s = pygame.Surface((SCREEN_W, SY(30)), pygame.SRCALPHA)
                s.fill((60, 40, 10, 20))
                surf.blit(s, (0, y))
            # Ground strip
            pygame.draw.rect(surf, (40,28,12), (0, SCREEN_H-SY(130), SCREEN_W, SY(130)))
            pygame.draw.rect(surf, (60,42,18), (0, SCREEN_H-SY(134), SCREEN_W, SY(6)))
            # Dino parade (fallback only — not shown over Menu.png)
            dino_types  = ["ankylo","brachi","raptor","spino","trex"]
            dino_emojis = ["🛡️","🦕","🐊","🐉","🦖"]
            dino_sz     = S(120)
            for i, (dtype, emoji) in enumerate(zip(dino_types, dino_emojis)):
                x     = int((self._t*65 + i*SX(260)) % (SCREEN_W+200)) - 100
                y_bob = SCREEN_H - SY(160) + int(math.sin(self._t*4+i*1.3)*S(8))
                sprite = ASSETS.get_dino(dtype, size=(dino_sz, dino_sz))
                if sprite:
                    surf.blit(sprite, (x, y_bob))
                else:
                    em = self.font_title.render(emoji, True, (255,255,255))
                    surf.blit(em, (x, y_bob))
            # Title card
            cw, ch = SX(680), SY(200)
            card = pygame.Surface((cw, ch), pygame.SRCALPHA)
            card.fill((15,10,4,200))
            pygame.draw.rect(card, (100,72,32,180), (0,0,cw,ch), 2, border_radius=S(12))
            surf.blit(card, (cx - cw//2, SY(140)))
            t1 = self.font_title.render("DINO DINER", True, (230,165,35))
            t2 = self.font_med.render("Cook fast.  Don't go extinct.", True, (210,185,145))
            surf.blit(t1, (cx - t1.get_width()//2, SY(158)))
            surf.blit(t2, (cx - t2.get_width()//2, SY(248)))

        # ── Start button: sprite or fallback drawn button ──
        btn_w, btn_h = SX(320), SY(80)
        btn_x = cx - btn_w // 2
        start_sprite = ASSETS.get_start_button(size=(btn_w, btn_h))
        if start_sprite:
            btn_y = SY(420)
            # Pulsing glow behind sprite
            glow_a = int(50 + 35 * math.sin(self._t * 2.5))
            glow_s = pygame.Surface((btn_w+S(24), btn_h+S(24)), pygame.SRCALPHA)
            pygame.draw.rect(glow_s, (225,185,40, glow_a),
                             (0,0,btn_w+S(24),btn_h+S(24)), border_radius=S(14))
            surf.blit(glow_s, (btn_x - S(12), btn_y - S(12)))
            # Scale slightly on hover
            if pygame.Rect(btn_x, btn_y, btn_w, btn_h).collidepoint(mx, my):
                hovered = ASSETS.get_start_button(size=(int(btn_w*1.04), int(btn_h*1.04)))
                if hovered:
                    surf.blit(hovered, (btn_x - int(btn_w*0.02),
                                        btn_y - int(btn_h*0.02)))
                else:
                    surf.blit(start_sprite, (btn_x, btn_y))
            else:
                surf.blit(start_sprite, (btn_x, btn_y))
        else:
            btn_y = SY(348)
            btn = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            glow_a = int(60 + 40 * math.sin(self._t * 3))
            glow_s = pygame.Surface((btn_w+S(20), btn_h+S(20)), pygame.SRCALPHA)
            pygame.draw.rect(glow_s, (225,155,30,glow_a),
                             (0,0,btn_w+S(20),btn_h+S(20)), border_radius=S(14))
            surf.blit(glow_s, (btn_x-S(10), btn_y-S(10)))
            draw_button(surf, self.font_big, "▶  OPEN THE RESTAURANT", btn,
                        hover=btn.collidepoint(mx, my),
                        color_bg=(55,40,14), color_hover=(85,62,22))

        # Music toggle (top-right of title)
        mute_lbl = self.font_xs.render(
            "♪ ON" if MUSIC.enabled else "♪ OFF", True, C_TEXT_DIM)
        mute_r = pygame.Rect(SCREEN_W - SX(60), SY(10), SX(50), SY(22))
        pygame.draw.rect(surf, C_PANEL_DARK, mute_r, border_radius=4)
        surf.blit(mute_lbl, (mute_r.x + 4, mute_r.y + 3))

        # Credit
        cr = self.font_xs.render("github: MrChompDev", True, C_TEXT_DIM)
        surf.blit(cr, (S(16), SCREEN_H - S(24)))

    def _click_title(self, mx, my):
        # Music toggle
        mute_r = pygame.Rect(SCREEN_W - SX(60), SY(10), SX(50), SY(22))
        if mute_r.collidepoint(mx, my):
            MUSIC.toggle()
            return

        btn_w, btn_h = SX(320), SY(80)
        btn_x = SCREEN_W//2 - btn_w//2
        start_sprite = ASSETS.get_start_button(size=(btn_w, btn_h))
        btn_y = SY(420) if start_sprite else SY(348)
        btn = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        if btn.collidepoint(mx, my):
            self.day   = 1
            self.cycle = 1
            MUSIC.play_gameplay()
            self._start_shop()

    # ─── Shop draw / click ────────────────────────────
    def _draw_shop(self, surf):
        cx = SCREEN_W // 2
        day_label = f"Day {self.day}  (Day {self._day_in_cycle()} of {CYCLE_LENGTH})"
        is_upgrade_next = self._is_upgrade_day()

        # Background
        draw_panel(surf, 60, 30, SCREEN_W-120, SCREEN_H-60,
                   C_PANEL_DARK, C_BORDER, radius=14)

        # Header
        hdr = self.font_big.render(f"🛒  {day_label} — Stock Up!", True, (225, 155, 30))
        surf.blit(hdr, (cx - hdr.get_width()//2, 48))

        # Budget line — spend_budget is the allowance, money is carried savings
        cart_cost = sum(INGREDIENTS[k]["cost"] * v for k, v in self._shop_cart.items())
        remaining = self._spend_budget - cart_cost
        b1 = self.font_med.render(
            f"Daily allowance: ${self._spend_budget}   Cart: ${cart_cost}   Left: ${remaining}",
            True, C_TEXT)
        surf.blit(b1, (cx - b1.get_width()//2, 88))
        b2 = self.font_sm.render(
            f"Carried savings: ${self.money}  (saved for upgrades on Day {CYCLE_LENGTH})",
            True, C_TEXT_DIM)
        surf.blit(b2, (cx - b2.get_width()//2, 112))

        # Upgrade day notice
        if is_upgrade_next:
            note = self.font_sm.render(
                "★  UPGRADE DAY — after today you can spend your savings on upgrades!",
                True, (220, 180, 40))
            surf.blit(note, (cx - note.get_width()//2, 132))

        # Ingredient grid
        keys   = list(INGREDIENTS.keys())
        cols   = 4
        bw, bh = 218, 118
        pad    = 14
        gw     = cols * bw + (cols-1) * pad
        gx, gy = cx - gw//2, 158

        mx, my = pygame.mouse.get_pos()
        for i, key in enumerate(keys):
            row, col = divmod(i, cols)
            x  = gx + col * (bw + pad)
            y  = gy + row * (bh + pad)
            r  = pygame.Rect(x, y, bw, bh)
            data       = INGREDIENTS[key]
            affordable = remaining >= data["cost"]
            hover      = r.collidepoint(mx, my)

            bg = (60, 50, 80) if hover and affordable else C_PANEL
            pygame.draw.rect(surf, bg, r, border_radius=10)
            pygame.draw.rect(surf, data["color"] if hover else C_BORDER, r, 2, border_radius=10)

            icon = ASSETS.get_food(key, cooked=False, size=(48, 48))
            if icon:
                surf.blit(icon, (x+8, y+8))
            else:
                em = self.font_big.render(data["emoji"], True, C_TEXT)
                surf.blit(em, (x+10, y+10))
            lbl = self.font_med.render(data["label"], True, C_TEXT)
            surf.blit(lbl, (x+64, y+14))
            cs  = self.font_sm.render(f"${data['cost']} each", True,
                                       C_MONEY if affordable else C_DANGER)
            surf.blit(cs, (x+64, y+40))
            ct  = self.font_xs.render(f"Cook: {data['cook_time']}s", True, C_TEXT_DIM)
            surf.blit(ct, (x+10, y+86))

            qty = self._shop_cart[key]
            qs  = self.font_med.render(f"x{qty}", True, (225, 185, 80))
            surf.blit(qs, (x + bw - 46, y + 10))

            pr = pygame.Rect(x + bw - 26, y + 42, 20, 20)
            mr = pygame.Rect(x + bw - 52, y + 42, 20, 20)
            draw_button(surf, self.font_sm, "+", pr,
                        hover=pr.collidepoint(mx, my), enabled=affordable)
            draw_button(surf, self.font_sm, "-", mr,
                        hover=mr.collidepoint(mx, my), enabled=qty > 0)
            if not affordable:
                ov = pygame.Surface((bw, bh), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 100))
                surf.blit(ov, (x, y))

        # Start button
        can_start = cart_cost > 0
        sr = pygame.Rect(cx - 160, SCREEN_H - 88, 320, 52)
        draw_button(surf, self.font_big, "🦖  Open the Restaurant!", sr,
                    hover=sr.collidepoint(mx, my), enabled=can_start,
                    color_bg=(38, 72, 28), color_hover=(52, 105, 38))
        if not can_start:
            err = self.font_sm.render("Add at least one item!", True, C_DANGER)
            surf.blit(err, (cx - err.get_width()//2, SCREEN_H - 36))

    def _click_shop(self, mx, my):
        cx    = SCREEN_W // 2
        keys  = list(INGREDIENTS.keys())
        cols  = 4
        bw, bh = 218, 118
        pad    = 14
        gw     = cols * bw + (cols-1) * pad
        gx, gy = cx - gw//2, 158

        cart_cost = sum(INGREDIENTS[k]["cost"] * v for k, v in self._shop_cart.items())

        for i, key in enumerate(keys):
            row, col = divmod(i, cols)
            x  = gx + col * (bw + pad)
            y  = gy + row * (bh + pad)
            pr = pygame.Rect(x + bw - 26, y + 42, 20, 20)
            mr = pygame.Rect(x + bw - 52, y + 42, 20, 20)
            data = INGREDIENTS[key]
            if pr.collidepoint(mx, my):
                if self._spend_budget - cart_cost >= data["cost"]:
                    self._shop_cart[key] += 1
                return
            elif mr.collidepoint(mx, my):
                if self._shop_cart[key] > 0:
                    self._shop_cart[key] -= 1
                return

        sr = pygame.Rect(cx - 160, SCREEN_H - 88, 320, 52)
        cart_cost = sum(INGREDIENTS[k]["cost"] * v for k, v in self._shop_cart.items())
        if sr.collidepoint(mx, my) and cart_cost > 0:
            # Allowance is spent on food (NOT deducted from carried money)
            self.shop_stock = dict(self._shop_cart)
            self._begin_restaurant()

    # ─── Restaurant ───────────────────────────────────
    def _draw_restaurant(self, surf):
        if   self.sub_state == SUB_ORDER  and self.scene: self.scene.draw(surf)
        elif self.sub_state == SUB_COOK   and self.scene: self.scene.draw(surf)
        elif self.sub_state == SUB_PLATE  and self.scene: self.scene.draw(surf)
        elif self.sub_state == SUB_RESULT: self._draw_result(surf)
        else:                              self._draw_queue_idle(surf)

        self._draw_hud_strip(surf)
        self.receipt.draw(surf, self.font_sm, self.font_xs)
        if self.chaos.current_event:
            self.chaos.draw(surf, self.font_big, self.font_sm, SCREEN_W//2, 80)

    def _draw_hud_strip(self, surf):
        pygame.draw.rect(surf, C_PANEL_DARK, (0, 0, RECEIPT_X-10, 52))
        pygame.draw.rect(surf, C_BORDER,     (0, 0, RECEIPT_X-10, 52), 1)

        # Savings (green = good)
        ms = self.font_big.render(f"${self.money}", True, C_MONEY)
        surf.blit(ms, (14, 10))
        sl = self.font_xs.render("savings", True, C_TEXT_DIM)
        surf.blit(sl, (14, 36))

        day_s = self.font_sm.render(
            f"Day {self.day}  [{self._day_in_cycle()}/{CYCLE_LENGTH}]",
            True, (225, 185, 80))
        surf.blit(day_s, (150, 16))

        # Food remaining bar
        total_bought = sum(self._shop_cart.values()) if self._shop_cart else 1
        total_left   = self._total_stock()
        ratio        = total_left / max(1, total_bought)
        col          = C_GOOD if ratio > 0.5 else (C_WARN if ratio > 0.2 else C_DANGER)
        pygame.draw.rect(surf, (20,14,6), (310, 18, 200, 14), border_radius=4)
        pygame.draw.rect(surf, col,       (310, 18, int(200*ratio), 14), border_radius=4)
        fl = self.font_xs.render(f"Food: {total_left} left", True, C_TEXT_DIM)
        surf.blit(fl, (310, 34))

        # Scene badge
        badge = {SUB_QUEUE:"● WAITING", SUB_ORDER:"● ORDER",
                 SUB_COOK:"● COOKING", SUB_PLATE:"● PLATING",
                 SUB_RESULT:"● RESULT"}.get(self.sub_state, "")
        bc    = {SUB_ORDER:C_WARN, SUB_COOK:(80,200,80),
                 SUB_PLATE:(180,120,220), SUB_RESULT:C_MONEY}.get(self.sub_state, C_TEXT_DIM)
        bs    = self.font_sm.render(badge, True, bc)
        surf.blit(bs, (530, 16))

    def _draw_queue_idle(self, surf):
        bg = ASSETS.get_scene_bg("order", (SCREEN_W, SCREEN_H))
        if bg: surf.blit(bg, (0, 0))
        else:  surf.fill(C_ORDER_BG)

        cx = SCREEN_W // 2
        if self._food_out:
            msg = self.font_big.render("All food used up — closing!", True, C_WARN)
        elif self.queue:
            msg = self.font_big.render("Next customer coming up...", True, C_TEXT)
        else:
            msg = self.font_big.render("Waiting for customers...", True, C_TEXT_DIM)
        surf.blit(msg, (cx - msg.get_width()//2, 280))

        for i, d in enumerate(self.queue[:4]):
            sprite = ASSETS.get_dino(d.dino_type, size=(100, 100))
            bx     = cx - 220 + i * 120
            if sprite:
                surf.blit(sprite, (bx, 370))
            else:
                em = self.font_title.render(d.emoji, True, d.color)
                surf.blit(em, (bx, 370))
            nt = self.font_xs.render(d.name, True, d.color)
            surf.blit(nt, (bx + 50 - nt.get_width()//2, 478))

    def _draw_result(self, surf):
        surf.fill(C_BG)
        cx  = SCREEN_W // 2
        res = self._result
        col = C_GOOD if res.get("success") else C_DANGER
        em_s = self.font_title.render("✅" if res.get("success") else "❌", True, col)
        surf.blit(em_s, (cx - em_s.get_width()//2, 220))
        msg = self.font_big.render(res.get("msg", ""), True, col)
        surf.blit(msg, (cx - msg.get_width()//2, 320))
        skip = self.font_sm.render("(tap to continue)", True, C_TEXT_DIM)
        surf.blit(skip, (cx - skip.get_width()//2, 400))
        dots = int(self._result_timer * 3) % 4
        dt_s = self.font_med.render("●"*dots + "○"*(3-dots), True, C_TEXT_DIM)
        surf.blit(dt_s, (cx - dt_s.get_width()//2, 440))

    # ─── End day ──────────────────────────────────────
    def _draw_end_day(self, surf):
        cx = SCREEN_W // 2
        s  = self._end_summary
        is_upg = s.get("is_upgrade_day", False)

        draw_panel(surf, 110, 50, SCREEN_W-220, SCREEN_H-100,
                   C_PANEL_DARK, C_BORDER, radius=14)

        title_col = (220, 180, 40) if is_upg else (225, 155, 30)
        title_txt = f"★  Day {self.day} Complete — UPGRADE TIME!" if is_upg \
                    else f"📋  End of Day {self.day}  [{s['day_in_cycle']}/{CYCLE_LENGTH}]"
        t = self.font_big.render(title_txt, True, title_col)
        surf.blit(t, (cx - t.get_width()//2, 72))

        lines = [
            (f"Earned today:    +${s['earnings']}", C_GOOD),
            (f"Fines:            -${s['losses']}",  C_DANGER),
            (f"Today's net:      ${s['net']}",
             C_MONEY if s["net"] >= 0 else C_DANGER),
            ("", C_TEXT),
            (f"💰  Total savings: ${self.money}", C_MONEY),
            (f"🦖  Dinos served:  {s['served']}", C_TEXT),
        ]
        for i, (line, col) in enumerate(lines):
            ls = self.font_med.render(line, True, col)
            surf.blit(ls, (cx - ls.get_width()//2, 148 + i*40))

        # Progress pips (days in cycle)
        pip_y = 420
        for pip in range(CYCLE_LENGTH):
            filled = pip < s["day_in_cycle"]
            pc     = (220, 180, 40) if filled else (45, 38, 22)
            pygame.draw.circle(surf, pc, (cx - 80 + pip * 40, pip_y), 12)
            if pip < CYCLE_LENGTH - 1:
                lx = cx - 80 + pip * 40 + 12
                pygame.draw.line(surf, (60, 50, 25) if not filled else (180, 140, 30),
                                 (lx, pip_y), (lx+16, pip_y), 3)
        pip_lbl = self.font_xs.render(
            f"Day {s['day_in_cycle']} of {CYCLE_LENGTH}  —  upgrade on day {CYCLE_LENGTH}",
            True, C_TEXT_DIM)
        surf.blit(pip_lbl, (cx - pip_lbl.get_width()//2, pip_y + 18))

        mx, my = pygame.mouse.get_pos()
        if self.money <= 0 and not is_upg:
            broke = self.font_big.render("💀  BROKE — GAME OVER", True, C_DANGER)
            surf.blit(broke, (cx - broke.get_width()//2, 460))
            br = pygame.Rect(cx - 120, 516, 240, 50)
            draw_button(surf, self.font_big, "Try Again", br,
                        hover=br.collidepoint(mx, my), color_bg=(80, 28, 18))
        elif is_upg:
            nr = pygame.Rect(cx - 160, 472, 320, 52)
            draw_button(surf, self.font_big, f"★  Spend Savings (${self.money}) →", nr,
                        hover=nr.collidepoint(mx, my),
                        color_bg=(55, 42, 10), color_hover=(88, 68, 16))
        else:
            nr = pygame.Rect(cx - 160, 472, 320, 52)
            draw_button(surf, self.font_big, f"Next Day →  (saves ${self.money})", nr,
                        hover=nr.collidepoint(mx, my),
                        color_bg=(28, 72, 28), color_hover=(38, 108, 38))

    def _click_end_day(self, mx, my):
        cx = SCREEN_W // 2
        s  = self._end_summary
        is_upg = s.get("is_upgrade_day", False)

        if self.money <= 0 and not is_upg:
            br = pygame.Rect(cx - 120, 516, 240, 50)
            if br.collidepoint(mx, my):
                self.state = ST_GAMEOVER
            return

        nr = pygame.Rect(cx - 160, 472, 320, 52)
        if nr.collidepoint(mx, my):
            if is_upg:
                self.state = ST_UPGRADE
            else:
                self.day  += 1
                self._start_shop()

    # ─── Upgrade ──────────────────────────────────────
    def _draw_upgrade(self, surf):
        cx = SCREEN_W // 2
        draw_panel(surf, 60, 40, SCREEN_W-120, SCREEN_H-80,
                   C_PANEL_DARK, C_BORDER, radius=16)

        t = self.font_big.render("★  UPGRADE SHOP  —  Spend Your Savings", True, (225, 180, 40))
        surf.blit(t, (cx - t.get_width()//2, 58))
        m = self.font_med.render(f"💰  Savings: ${self.money}", True, C_MONEY)
        surf.blit(m, (cx - m.get_width()//2, 98))
        sub = self.font_sm.render(
            "Unspent money carries into the next cycle.", True, C_TEXT_DIM)
        surf.blit(sub, (cx - sub.get_width()//2, 122))

        keys  = list(UPGRADES.keys())
        bw, bh = 270, 138
        pad    = 18
        cols   = 2
        gw     = cols * bw + (cols-1) * pad
        gx, gy = cx - gw//2, 150

        mx, my = pygame.mouse.get_pos()
        for i, key in enumerate(keys):
            row, col = divmod(i, cols)
            x  = gx + col * (bw + pad)
            y  = gy + row * (bh + pad)
            r  = pygame.Rect(x, y, bw, bh)
            upg    = UPGRADES[key]
            lvl    = self.upgrades[key]
            maxed  = lvl >= upg["max"]
            can    = not maxed and self.money >= upg["cost"]
            hover  = r.collidepoint(mx, my)

            bg = (55, 44, 75) if hover and can else C_PANEL
            pygame.draw.rect(surf, bg, r, border_radius=10)
            pygame.draw.rect(surf, (155, 115, 225) if hover and can else C_BORDER,
                             r, 2, border_radius=10)

            ic = self.font_big.render(upg["icon"], True, C_TEXT)
            surf.blit(ic, (x+10, y+10))
            nm = self.font_med.render(upg["label"], True, C_TEXT)
            surf.blit(nm, (x+54, y+14))
            ds = self.font_sm.render(upg["desc"], True, C_TEXT_DIM)
            surf.blit(ds, (x+10, y+52))

            for pip in range(upg["max"]):
                pc = C_MONEY if pip < lvl else (50, 40, 30)
                pygame.draw.circle(surf, pc, (x+16+pip*20, y+88), 7)

            info = "MAX ✓" if maxed else f"${upg['cost']}  Lv {lvl}/{upg['max']}"
            ic2  = self.font_sm.render(info, True,
                    C_GOOD if maxed else (C_MONEY if can else C_DANGER))
            surf.blit(ic2, (x+10, y+110))

        # Done button → start next cycle
        done = pygame.Rect(cx - 180, SCREEN_H - 80, 360, 52)
        draw_button(surf, self.font_big,
                    f"Continue to Cycle {self.cycle+1}  →  (keep ${self.money})",
                    done, hover=done.collidepoint(mx, my),
                    color_bg=(35, 72, 28), color_hover=(50, 108, 38))

    def _click_upgrade(self, mx, my):
        cx    = SCREEN_W // 2
        keys  = list(UPGRADES.keys())
        bw, bh = 270, 138
        pad    = 18
        cols   = 2
        gw     = cols * bw + (cols-1) * pad
        gx, gy = cx - gw//2, 150

        for i, key in enumerate(keys):
            row, col = divmod(i, cols)
            x  = gx + col * (bw + pad)
            y  = gy + row * (bh + pad)
            r  = pygame.Rect(x, y, bw, bh)
            upg = UPGRADES[key]
            lvl = self.upgrades[key]
            if r.collidepoint(mx, my) and lvl < upg["max"] and self.money >= upg["cost"]:
                self.money -= upg["cost"]
                self.upgrades[key] += 1
                self._recalc_stats()
                self.particles.stars(x + bw//2, y + bh//2)
                return

        done = pygame.Rect(cx - 180, SCREEN_H - 80, 360, 52)
        if done.collidepoint(mx, my):
            # Start new cycle — day counter continues, cycle increments
            self.cycle += 1
            self.day   += 1
            self._start_shop()

    # ─── Game over ────────────────────────────────────
    def _draw_gameover(self, surf):
        cx = SCREEN_W // 2
        flicker = int(abs(math.sin(self._t*4)) * 28)
        surf.fill((28+flicker, 8, 8))
        t1 = self.font_title.render("💀  EXTINCT", True, C_DANGER)
        t2 = self.font_big.render("You ran out of money.", True, (200, 140, 120))
        t3 = self.font_med.render(
            f"Survived {self.day} days  ·  Cycle {self.cycle}  ·  Score: {self.score}",
            True, C_TEXT)
        surf.blit(t1, (cx - t1.get_width()//2, 170))
        surf.blit(t2, (cx - t2.get_width()//2, 260))
        surf.blit(t3, (cx - t3.get_width()//2, 320))
        mx, my = pygame.mouse.get_pos()
        r = pygame.Rect(cx-150, 410, 300, 55)
        draw_button(surf, self.font_big, "🦖  Try Again", r,
                    hover=r.collidepoint(mx, my),
                    color_bg=(60, 18, 18), color_hover=(95, 28, 28))
