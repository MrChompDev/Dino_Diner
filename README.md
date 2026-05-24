#  Dino Diner

> *Cook fast. Don't go extinct.*

A chaotic prehistoric food truck game built in Python and pygame. Serve picky, impatient dinosaurs across 3 distinct scenes — take the order, grill the food, plate it up — before they lose patience and stomp off without paying.

Built for a game jam in 72 hours.

---

## 📸 Screenshots

> Drop your screenshots here once you have them:
> `![Order Scene](screenshots/order.png)`
> `![Cook Scene](screenshots/cook.png)`
> `![Plate Scene](screenshots/plate.png)`

---

##  Quick Start

**Requirements:** Python 3.10+

```bash
# Clone the repo
git clone https://github.com/MrChompDev/dino-diner.git
cd dino-diner

# Install dependencies
pip install pygame

# Run
python main.py

# Optional: fullscreen mode
python main.py --fullscreen
```

---

##  How It Works

Dino Diner runs in **three scenes per customer**, Papa's-style:

### Scene 1 — Order Taking
A dino walks up and places their order via a speech bubble. A receipt prints in the corner showing exactly what they want. Their patience bar is already ticking. Click **"Got it!"** to confirm and head to the grill.

### Scene 2 — Cooking Station
A Papa's-style grill with 6 slots. Click ingredients from your shelf to drop them on. Each item has its own cook timer — watch the progress bar. Click a cooked item to move it to the finished tray. Changed your mind? Click anything still on the grill or in the tray to return it to stock. Hit **"Plate it Up!"** once the tray matches the order.

### Scene 3 — Plating
Click cooked items onto the plate. Ghost outlines show you exactly where each item goes. Serve when the plate is right — or clear it and start over.

### The Receipt
A persistent stacked receipt lives in the top-right corner across all three scenes, ticking off items as you cook them. Up to 4 orders stack at once, Papa's-style.

---

##  The 5-Day Loop

```
Day 1 ──► Day 2 ──► Day 3 ──► Day 4 ──► Day 5 ★
 Shop      Shop      Shop      Shop    Upgrade Shop
  │         │         │         │           │
Restaurant Restaurant Restaurant Restaurant Next Cycle
```

- **Daily allowance** — given each morning to buy food (starts $60, grows $10/cycle). Spent on ingredients only.
- **Carried savings** — everything you earn from customers. Persists across all days.
- **Day 5** — your savings unlock the upgrade shop. Unspent money rolls into the next cycle.
- **Food out = day over** — the restaurant closes the moment stock hits zero.

---

##  Dino Roster

| Dino | Patience | Tips | Likes | Personality |
|------|----------|------|-------|-------------|
|  T-Rex | Very Low | Very High | Meat, Bone, Lava Spice | Impatient. Pays huge if served fast. |
|  Brachiosaurus | Very High | Low | Leaf, Berry, Egg | Slow, massive orders, plants only. |
|  Raptor | Low | Medium | Meat, Egg, Fish | Fast, small orders, constant. |
|  Spinosaurus | Medium | Good | Fish only | Fish. Only ever fish. Non-negotiable. |
|  Ankylosaurus | Very High | Low | Berry, Leaf, Egg | Extremely chill. Great for beginners. |

Dinos only order ingredients **you actually have in stock**. If you have no fish, Spinosaurus won't spawn. Orders are rerolled against current stock the moment each dino reaches the front of the queue.

---

##  Chaos Events

Random events fire mid-service to keep things interesting:

| Event | Effect |
|-------|--------|
|  Volcano | Screen shake |
|  Prehistoric Rain | Patience drains slower |
|  Dino Fight | Front customer storms off |
|  Lunch Rush | Bonus dino joins queue |
|  Meteor | All patience halved instantly |

---

##  Upgrades

Unlocked every Day 5 with your carried savings:

| Upgrade | Effect | Max Level |
|---------|--------|-----------|
|  Speed Grill | Cook 25% faster | ×3 |
|  Extra Grill Slot | +1 grill slot | ×3 |
|  Dino Charm | All tips +20% | ×2 |
|  Amuse-Bouche | +15s dino patience | ×3 |

---

##  Project Structure

```
dino-diner/
│
├── main.py                  # Entry point — window, scaling, asset load, game loop
├── build.bat                # Double-click to compile with PyInstaller (Windows)
├── dino_diner.spec          # PyInstaller spec — single-file EXE output
│
├── Assets/                  # Art and audio (not committed — add your own)
│   ├── Characters/
│   │   ├── Dino_1.png       # Ankylosaurus
│   │   ├── Dino_2.png       # Brachiosaurus
│   │   ├── Dino_3.png       # Raptor
│   │   ├── Dino_4.png       # Spinosaurus
│   │   ├── Dino_5.png       # T-Rex
│   │   └── Dino_6/7/8.png   # Title screen extras
│   ├── Food/
│   │   ├── UnCooked_*.png   # Raw ingredients (7 items)
│   │   └── Cooked_*.png     # Cooked ingredients (7 items)
│   ├── Shop/
│   │   ├── Menu.png         # Title screen background
│   │   ├── Order.png        # Scene 1 background
│   │   ├── Cook.png         # Scene 2 background
│   │   ├── Plate.png        # Scene 3 background
│   │   └── Start_Button.png # Title screen start button
│   └── SFX/
│       └── Music/
│           ├── Menu.mp3     # Title screen music (loops)
│           └── GamePlay.mp3 # In-game music (loops)
│
└── classes/
    ├── constants.py         # All config, balance, scaling (S/SX/SY/SF helpers)
    ├── assets.py            # Asset loader singleton — graceful fallback
    ├── music.py             # Music manager — crossfade between tracks
    ├── game.py              # Central state machine (all screens)
    ├── scenes.py            # OrderScene, CookScene, PlateScene + StackedReceipt
    ├── dino.py              # Dino class — personality, patience, stock-aware orders
    ├── order.py             # Order generation
    ├── chaos.py             # Chaos event system
    ├── particles.py         # Particle FX (coins, sparks, smoke, text popups)
    └── ui.py                # Reusable draw helpers
```

---

##  Building an EXE (Windows)

```bash
pip install pyinstaller
pyinstaller dino_diner.spec --clean --noconfirm
```

Or just double-click `build.bat`.

Output: `dist/DinoDiner.exe` — single file, no installer needed.

Ship it alongside your `Assets/` folder:
```
DinoDiner.exe
Assets/
  Characters/
  Food/
  SFX/
  Shop/
```

---

## Dynamic Scaling

The game runs natively at any resolution. It detects your screen size at launch, fits a 16:9 window to 90% of the screen, and all fonts, layouts, and UI scale automatically. Pass `--fullscreen` for native resolution. The window is also resizable at runtime.

Base design resolution is 1280×720. All values use `S()`, `SX()`, `SY()`, `SF()` helper functions from `constants.py`.

---

## Tech Stack

- **Python 3.10+**
- **pygame 2.x**
- **PyInstaller** (optional, for building EXE)

No other dependencies.

---

## License

This project is open source under the [MIT License](LICENSE).

Art assets, music, and character sprites are not included in this repository and remain the property of their respective creators.

---

*Made by [MrChompDev](https://github.com/MrChompDev) · Game Jam 2026*
