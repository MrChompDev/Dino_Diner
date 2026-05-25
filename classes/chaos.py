"""
Chaos event system — random prehistoric disasters
"""

import random
import pygame
from classes.constants import CHAOS_EVENTS, CHAOS_BASE_CHANCE, CHAOS_SCALE, C_TEXT


class ChaosEvent:
    """Represents a single active chaos event."""

    def __init__(self, data: dict):
        self.id       = data["id"]
        self.label    = data["label"]
        self.desc     = data["desc"]
        self.duration = float(data["duration"])
        self.color    = data["color"]
        self.elapsed  = 0.0
        self.show_timer = 3.0   # how long to show the banner

    @property
    def active(self) -> bool:
        return self.elapsed < self.duration

    @property
    def ratio(self) -> float:
        return 1.0 - min(1.0, self.elapsed / self.duration)

    def update(self, dt: float):
        self.elapsed += dt
        self.show_timer = max(0, self.show_timer - dt)


class ChaosManager:
    """Manages chaos event spawning and state."""

    def __init__(self):
        self.current_event: ChaosEvent | None = None
        self._cooldown = 15.0   # seconds before next event can fire
        self._timer    = self._cooldown

        # Convenience flags read by Game
        self.volcano_active = False
        self.rain_active    = False

    # ─── Callbacks set by Game ────────────────────────────
    # Game assigns these after init so ChaosManager can signal effects
    def set_callbacks(self, on_fight, on_rush, on_meteor):
        self._on_fight  = on_fight
        self._on_rush   = on_rush
        self._on_meteor = on_meteor

    # ─── Update ───────────────────────────────────────────
    def update(self, dt: float, day: int):
        self._timer -= dt

        if self.current_event:
            self.current_event.update(dt)
            if not self.current_event.active:
                self._finish_event(self.current_event)
                self.current_event = None
                self._timer = self._cooldown

        # Try to spawn a new event
        if self.current_event is None and self._timer <= 0:
            chance = CHAOS_BASE_CHANCE + CHAOS_SCALE * day
            if random.random() < chance * 60:   # normalise to per-second
                self._spawn(day)

    def _spawn(self, day: int):
        data = random.choice(CHAOS_EVENTS)
        event = ChaosEvent(data)
        self.current_event = event

        # Instant-effect events
        if event.id == "fight"  and hasattr(self, "_on_fight"):
            self._on_fight()
        if event.id == "rush"   and hasattr(self, "_on_rush"):
            self._on_rush()
        if event.id == "meteor" and hasattr(self, "_on_meteor"):
            self._on_meteor()

        self.volcano_active = event.id == "volcano"
        self.rain_active    = event.id == "rain"

    def _finish_event(self, event: ChaosEvent):
        if event.id in ("volcano", "rain"):
            self.volcano_active = False
            self.rain_active    = False

    # ─── Draw ─────────────────────────────────────────────
    def draw(self, surf: pygame.Surface, font_big, font_sm, cx: int, cy: int):
        if not self.current_event:
            return
        ev = self.current_event
        if ev.show_timer <= 0 and ev.elapsed > 3.0:
            return   # banner faded

        alpha = int(min(255, ev.show_timer / 3.0 * 255))
        panel = pygame.Surface((560, 80), pygame.SRCALPHA)
        panel.fill((*ev.color, int(alpha * 0.85)))

        lbl  = font_big.render(ev.label, True, (255, 255, 255))
        desc = font_sm.render(ev.desc, True, (240, 220, 200))
        panel.blit(lbl,  (16, 8))
        panel.blit(desc, (16, 44))

        surf.blit(panel, (cx - 280, cy - 40))

    def get_screen_shake(self) -> int:
        if self.volcano_active and self.current_event:
            return int(5 * self.current_event.ratio)
        return 0
