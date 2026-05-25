"""
assets.py — Asset loader for Dino Papa's

Expected folder structure (drop Assets/ next to main.py):

Assets/
  Characters/
    Dino_1.png  → ankylo
    Dino_2.png  → brachi
    Dino_3.png  → raptor
    Dino_4.png  → spino
    Dino_5.png  → trex
    Dino_6.png  → (extra / menu decoration)
    Dino_7.png  → (extra / menu decoration)
    Dino_8.png  → (extra / menu decoration)
    Dino.af     (Aseprite file — ignored at runtime)
  Food/
    UnCooked_DinoEgg.png      → egg   (raw)
    UnCooked_DinoSteak.png    → meat  (raw)
    UnCooked_JungleLeaf.png   → leaf  (raw)
    UnCooked_LavaBerry.png    → berry (raw)
    UnCooked_LavaSpice.png    → lava  (raw)
    UnCooked_MarrowBone.png   → bone  (raw)
    UnCooked_RiverFish.png    → fish  (raw)
    Cooked_DinoEgg.png        → egg   (cooked)
    Cooked_DinoSteak.png      → meat  (cooked)
    Cooked_JungleLeaf.png     → leaf  (cooked)
    Cooked_LavaBerry.png      → berry (cooked)
    Cooked_LavaSpice.png      → lava  (cooked)
    Cooked_MarrowBone.png     → bone  (cooked)
    Cooked_RiverFish.png      → fish  (cooked)
    Food.af                   (ignored)
  Shop/
    Cook.png    → cooking scene background
    Order.png   → order scene background
    Plate.png   → plating scene background
    Cook.af / Order.af / Plate.af  (ignored)
  SFX/          (reserved — load sounds here in future)

All images are loaded once at startup and cached.
Missing files degrade gracefully — fallback colored rectangles used.
"""

import os
import pygame


# ── Ingredient key → filename stem ────────────────────
FOOD_MAP = {
    "meat":  "DinoSteak",
    "fish":  "RiverFish",
    "leaf":  "JungleLeaf",
    "egg":   "DinoEgg",
    "bone":  "MarrowBone",
    "berry": "LavaBerry",
    "lava":  "LavaSpice",
}

# ── Dino type → Dino_N.png index ──────────────────────
DINO_MAP = {
    "ankylo": "Dino_1",
    "brachi": "Dino_2",
    "raptor": "Dino_3",
    "spino":  "Dino_4",
    "trex":   "Dino_5",
}

# Extra dinos for menu / decoration
DINO_EXTRAS = ["Dino_6", "Dino_7", "Dino_8"]


class AssetManager:
    """
    Loads all art assets once and provides scaled copies on demand.
    Always call AssetManager.load(base_path) before first use.
    """

    def __init__(self):
        self._food_raw:    dict[str, pygame.Surface] = {}
        self._food_cooked: dict[str, pygame.Surface] = {}
        self._dinos:       dict[str, pygame.Surface] = {}
        self._dino_extras: list[pygame.Surface]      = []
        self._scenes:      dict[str, pygame.Surface] = {}
        self._start_button: pygame.Surface | None = None
        self._loaded       = False
        self._base_path    = ""

    # ─── Loading ──────────────────────────────────────
    def load(self, base_path: str):
        """Call once at startup. base_path = folder containing main.py."""
        self._base_path = base_path
        assets_dir = os.path.join(base_path, "Assets")

        if not os.path.isdir(assets_dir):
            print(f"[AssetManager] Assets/ not found at {assets_dir} — using fallback rendering")
            self._loaded = False
            return

        food_dir  = os.path.join(assets_dir, "Food")
        char_dir  = os.path.join(assets_dir, "Characters")
        shop_dir  = os.path.join(assets_dir, "Shop")

        # Food — uncooked
        for key, stem in FOOD_MAP.items():
            path = os.path.join(food_dir, f"UnCooked_{stem}.png")
            self._food_raw[key] = self._load_img(path, label=f"UnCooked_{stem}")

        # Food — cooked
        for key, stem in FOOD_MAP.items():
            path = os.path.join(food_dir, f"Cooked_{stem}.png")
            self._food_cooked[key] = self._load_img(path, label=f"Cooked_{stem}")

        # Characters
        for dtype, stem in DINO_MAP.items():
            path = os.path.join(char_dir, f"{stem}.png")
            self._dinos[dtype] = self._load_img(path, label=stem)

        for stem in DINO_EXTRAS:
            path = os.path.join(char_dir, f"{stem}.png")
            surf = self._load_img(path, label=stem)
            if surf:
                self._dino_extras.append(surf)

        # Shop scene backgrounds + menu
        for scene in ("Cook", "Order", "Plate", "Menu"):
            path = os.path.join(shop_dir, f"{scene}.png")
            self._scenes[scene.lower()] = self._load_img(path, label=scene)

        # Start button
        btn_path = os.path.join(shop_dir, "Start_Button.png")
        self._start_button = self._load_img(btn_path, label="Start_Button")

        self._loaded = True
        print(f"[AssetManager] Loaded from {assets_dir}")

    def _load_img(self, path: str, label: str = "") -> pygame.Surface | None:
        if not os.path.isfile(path):
            print(f"[AssetManager] Missing: {path}")
            return None
        try:
            surf = pygame.image.load(path).convert_alpha()
            return surf
        except Exception as e:
            print(f"[AssetManager] Error loading {label}: {e}")
            return None

    # ─── Public getters ───────────────────────────────
    def has_assets(self) -> bool:
        return self._loaded

    def get_food(self, key: str, cooked: bool = False,
                 size: tuple[int, int] = (64, 64)) -> pygame.Surface | None:
        """Return a scaled food sprite, or None if not loaded."""
        src = self._food_cooked if cooked else self._food_raw
        surf = src.get(key)
        if surf is None:
            return None
        return pygame.transform.smoothscale(surf, size)

    def get_dino(self, dino_type: str,
                 size: tuple[int, int] = (120, 120)) -> pygame.Surface | None:
        surf = self._dinos.get(dino_type)
        if surf is None:
            return None
        return pygame.transform.smoothscale(surf, size)

    def get_dino_extra(self, index: int,
                       size: tuple[int, int] = (120, 120)) -> pygame.Surface | None:
        if not self._dino_extras:
            return None
        surf = self._dino_extras[index % len(self._dino_extras)]
        return pygame.transform.smoothscale(surf, size)

    def get_scene_bg(self, scene: str,
                     size: tuple[int, int] = (1280, 720)) -> pygame.Surface | None:
        """scene: 'order', 'cook', or 'plate'"""
        surf = self._scenes.get(scene)
        if surf is None:
            return None
        return pygame.transform.smoothscale(surf, size)

    def get_start_button(self, size: tuple[int,int] = (320, 80)) -> pygame.Surface | None:
        if self._start_button is None:
            return None
        return pygame.transform.smoothscale(self._start_button, size)

    def num_extras(self) -> int:
        return len(self._dino_extras)


# ── Global singleton ──────────────────────────────────
ASSETS = AssetManager()
