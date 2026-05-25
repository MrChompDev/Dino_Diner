"""
Global constants for Dino Diner
Dynamic scaling: all layout values derived from actual screen size at runtime.
Call init_scale(w, h) once from main.py before anything else.
"""

TITLE = "Dino Diner"   # window name
FPS   = 60

# ── These are set by init_scale() ─────────────────────
SCREEN_W   = 1920
SCREEN_H   = 1080
SCALE_X    = 1.0
SCALE_Y    = 1.0
SCALE      = 1.0   # uniform min scale

# ── Layout zones (recalculated by init_scale) ─────────
RECEIPT_X  = 1000
RECEIPT_Y  = 10
RECEIPT_W  = 268
RECEIPT_H  = 340

def init_scale(w: int, h: int):
    """Call once from main.py after display mode is set."""
    global SCREEN_W, SCREEN_H, SCALE_X, SCALE_Y, SCALE
    global RECEIPT_X, RECEIPT_Y, RECEIPT_W, RECEIPT_H
    SCREEN_W = w
    SCREEN_H = h
    SCALE_X  = w / 1920.0
    SCALE_Y  = h / 1080.0
    SCALE    = min(SCALE_X, SCALE_Y)
    RECEIPT_W = int(268 * SCALE_X)
    RECEIPT_X = w - RECEIPT_W - int(10 * SCALE_X)
    RECEIPT_Y = int(10 * SCALE_Y)
    RECEIPT_H = int(340 * SCALE_Y)

def S(v: float) -> int:
    """Scale a base-1280x720 value to actual screen size (uniform)."""
    return int(v * SCALE)

def SX(v: float) -> int:
    """Scale a horizontal value."""
    return int(v * SCALE_X)

def SY(v: float) -> int:
    """Scale a vertical value."""
    return int(v * SCALE_Y)

def SF(size: int) -> int:
    """Scale a font size."""
    return max(8, int(size * SCALE))

# ─── Colors ───────────────────────────────────────────
C_BG          = (28,  18,   8)
C_PANEL       = (50,  36,  18)
C_PANEL_DARK  = (22,  15,   6)
C_PANEL_LIGHT = (65,  48,  24)
C_BORDER      = (100, 72,  32)
C_TEXT        = (245, 225, 185)
C_TEXT_DIM    = (145, 115,  72)
C_MONEY       = (80,  225,  80)
C_DANGER      = (225,  55,  35)
C_WARN        = (235, 165,  20)
C_GOOD        = (55,  205, 100)

C_ORDER_BG    = (32,  22,  10)
C_COOK_BG     = (18,  28,  14)
C_PLATE_BG    = (28,  20,  36)
C_RECEIPT_BG  = (255, 252, 235)

# ─── Game balance ─────────────────────────────────────
MAX_QUEUE          = 5
ORDER_PHASE_TIME   = 20
PATIENCE_RATE      = 0.3
CHAOS_BASE_CHANCE  = 0.002
CHAOS_SCALE        = 0.00015

# ─── Ingredients ──────────────────────────────────────
INGREDIENTS = {
    "meat":  {"label": "Dino Steak",  "cost": 8,  "emoji": "🥩", "sat": 25, "color": (180,60,40),   "cook_time": 4.0},
    "fish":  {"label": "River Fish",  "cost": 6,  "emoji": "🐟", "sat": 20, "color": (80,130,200),  "cook_time": 3.0},
    "leaf":  {"label": "Jungle Leaf", "cost": 3,  "emoji": "🌿", "sat": 12, "color": (60,160,60),   "cook_time": 1.5},
    "egg":   {"label": "Dino Egg",    "cost": 5,  "emoji": "🥚", "sat": 18, "color": (230,210,140), "cook_time": 3.5},
    "bone":  {"label": "Marrow Bone", "cost": 4,  "emoji": "🦴", "sat": 15, "color": (220,200,170), "cook_time": 5.0},
    "berry": {"label": "Lava Berry",  "cost": 4,  "emoji": "🍇", "sat": 14, "color": (140,60,180),  "cook_time": 1.0},
    "lava":  {"label": "Lava Spice",  "cost": 12, "emoji": "🌋", "sat": 35, "color": (220,90,20),   "cook_time": 2.0},
}

# ─── Dino definitions ─────────────────────────────────
DINO_TYPES = {
    "trex":   {"name":"T-Rex",         "emoji":"🦖","patience":60, "tip_mult":2.5,"speed":0.8, "color":(180,50,30), "desc":"Impatient. Big tipper.",  "likes":["meat","bone","lava"],"hates":["leaf","berry"],"order_size":(1,2),"speech":"RAWR! I'm STARVING!"},
    "brachi": {"name":"Brachiosaurus", "emoji":"🦕","patience":90, "tip_mult":1.2,"speed":0.35,"color":(80,160,80), "desc":"Slow. Huge appetite.",    "likes":["leaf","berry","egg"],"hates":["meat","lava"],"order_size":(3,5),"speech":"Could I get... everything please?"},
    "raptor": {"name":"Raptor",        "emoji":"🐊","patience":45, "tip_mult":1.0,"speed":1.0, "color":(100,180,50),"desc":"Quick. Small orders.",    "likes":["meat","egg","fish"],"hates":[],"order_size":(1,2),"speech":"Fast, fast, FAST!"},
    "spino":  {"name":"Spinosaurus",   "emoji":"🐉","patience":75, "tip_mult":1.5,"speed":0.55,"color":(50,100,200),"desc":"Fish ONLY. Good tipper.", "likes":["fish"],"hates":["meat","bone","leaf","lava","berry","egg"],"order_size":(2,4),"speech":"I'll have the fish... all of it."},
    "ankylo": {"name":"Ankylosaurus",  "emoji":"🛡️","patience":120,"tip_mult":0.8,"speed":0.25,"color":(120,100,60),"desc":"Very chill. Low tips.",  "likes":["berry","leaf","egg"],"hates":["lava"],"order_size":(2,3),"speech":"No rush... whenever you're ready."},
}

# ─── Chaos events ─────────────────────────────────────
CHAOS_EVENTS = [
    {"id":"volcano","label":"🌋 VOLCANO!",    "desc":"Screen shaking!",             "duration":8, "color":(220,55,35)},
    {"id":"rain",   "label":"🌧 RAIN!",        "desc":"Patience drains slower.",     "duration":14,"color":(80,130,200)},
    {"id":"fight",  "label":"🦖 DINO FIGHT!", "desc":"Front customer brawled off!", "duration":4, "color":(235,165,20)},
    {"id":"rush",   "label":"⚡ LUNCH RUSH!", "desc":"Extra dino joins the queue!", "duration":3, "color":(55,205,100)},
    {"id":"meteor", "label":"☄️ METEOR!",      "desc":"Everyone's patience halved!", "duration":2, "color":(200,150,50)},
]

# ─── Upgrades ─────────────────────────────────────────
UPGRADES = {
    "faster_cook":    {"label":"Speed Grill",      "desc":"Cook 25% faster",    "cost":60,"icon":"⚡","stat":"cook_speed",     "value":0.25,"max":3},
    "extra_slot":     {"label":"Extra Grill Slot", "desc":"+1 grill slot",      "cost":50,"icon":"🍽️","stat":"plate_slots",    "value":1,   "max":3},
    "better_tips":    {"label":"Dino Charm",       "desc":"All tips +20%",      "cost":80,"icon":"💰","stat":"tip_bonus",      "value":0.20,"max":2},
    "patience_boost": {"label":"Amuse-Bouche",     "desc":"+15s dino patience", "cost":70,"icon":"⏳","stat":"patience_bonus", "value":15,  "max":3},
}
