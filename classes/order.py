"""
Order class — the list of ingredients a dino wants
"""

import random
from classes.constants import INGREDIENTS


class Order:
    """Represents a dino's food order as a list of ingredient keys."""

    def __init__(self, pool: list, count: int):
        self.items: list[str] = []
        for _ in range(count):
            self.items.append(random.choice(pool))

    def is_complete(self, plate: list) -> bool:
        return sorted(plate) == sorted(self.items)

    def cost(self) -> int:
        """Raw ingredient cost of this order."""
        return sum(INGREDIENTS[i]["cost"] for i in self.items)

    def satisfaction(self) -> int:
        """Base earnings if fulfilled."""
        return sum(INGREDIENTS[i]["sat"] for i in self.items)

    def display_str(self) -> str:
        counts = {}
        for item in self.items:
            counts[item] = counts.get(item, 0) + 1
        return "  ".join(
            f"{INGREDIENTS[k]['emoji']} {INGREDIENTS[k]['label']} x{v}"
            for k, v in counts.items()
        )
