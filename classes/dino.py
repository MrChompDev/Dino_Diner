"""
Dino customer class — Papa's edition
"""

import pygame
import random
from classes.constants import DINO_TYPES, INGREDIENTS, C_TEXT, C_DANGER, C_WARN, C_GOOD, C_PANEL, C_BORDER
from classes.order import Order


class Dino:
    def __init__(self, dino_type: str, patience_bonus: float = 0):
        data = DINO_TYPES[dino_type]
        self.dino_type    = dino_type
        self.name         = data["name"]
        self.emoji        = data["emoji"]
        self.color        = data["color"]
        self.desc         = data["desc"]
        self.tip_mult     = data["tip_mult"]
        self.speed        = data["speed"]
        self.likes        = data["likes"]
        self.hates        = data["hates"]
        self._data        = data

        base_patience     = data["patience"] + patience_bonus
        self.patience     = float(base_patience)
        self.max_patience = float(base_patience)

        min_items, max_items = data["order_size"]
        n = random.randint(min_items, max_items)
        pool = self.likes if self.likes else list(INGREDIENTS.keys())
        self.order = Order(pool, n)

        self.served   = False
        self.leaving  = False

    def dino_type_data(self) -> dict:
        return self._data

    def patience_ratio(self) -> float:
        return max(0.0, self.patience / self.max_patience)

    def evaluate_plate(self, plate_items: list) -> dict:
        required = sorted(self.order.items)
        given    = sorted(plate_items)
        base_pay = sum(INGREDIENTS[i]["sat"] for i in self.order.items)

        if given == required:
            for item in plate_items:
                if item in self.hates:
                    return {"success": False, "earnings": 0,
                            "msg": f"{self.name} HATES that! 😤 $0"}
            tip   = int(base_pay * self.tip_mult * (0.5 + self.patience_ratio()))
            total = base_pay + tip
            self.served  = True
            self.leaving = True
            return {"success": True, "earnings": total,
                    "msg": f"{self.name} loved it! +${total} 💰"}

        self.leaving = True
        return {"success": False, "earnings": 0,
                "msg": f"{self.name} got the wrong order! 😡 $0"}


    def reroll_order(self, stock: dict):
        """Regenerate order using only items that are in stock."""
        available = [k for k, v in stock.items() if v > 0]
        if not available:
            self.order.items = []
            return

        liked_available = [k for k in self.likes if k in available]
        pool = liked_available if liked_available else available

        min_items, max_items = self._data["order_size"]
        max_possible = sum(stock[k] for k in pool if k in stock)
        if max_possible == 0:
            self.order.items = []
            return
        n = min(random.randint(min_items, max_items), max_possible, 5)
        n = max(1, n)

        items = []
        remaining = {k: stock.get(k, 0) for k in pool}
        for _ in range(n):
            chooseable = [k for k in remaining if remaining[k] > 0]
            if not chooseable:
                break
            pick = random.choice(chooseable)
            items.append(pick)
            remaining[pick] -= 1

        self.order.items = items

    @staticmethod
    def random_dino(day: int, patience_bonus: float = 0, stock: dict = None) -> "Dino":
        pool    = ["raptor", "ankylo", "brachi", "trex", "spino"]
        weights = [
            max(0.5, 2.0 - day * 0.1),
            max(0.3, 1.5 - day * 0.05),
            1.0,
            min(2.5, 0.3 + day * 0.2),
            min(1.5, 0.2 + day * 0.15),
        ]

        # Filter out dinos whose entire liked pool is out of stock
        available = set(k for k, v in stock.items() if v > 0) if stock else set(INGREDIENTS.keys())
        filtered_pool, filtered_weights = [], []
        for dtype, w in zip(pool, weights):
            likes = DINO_TYPES[dtype]["likes"]
            if not likes or any(l in available for l in likes):
                filtered_pool.append(dtype)
                filtered_weights.append(w)

        if not filtered_pool:
            filtered_pool, filtered_weights = pool, weights

        chosen = random.choices(filtered_pool, weights=filtered_weights, k=1)[0]
        dino   = Dino(chosen, patience_bonus)
        if stock:
            dino.reroll_order(stock)
        return dino
