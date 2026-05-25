"""
Dino Diner — main entry point
Dynamic resolution: scales to any screen size from the native 1280×720 base.
"""

import pygame
import sys
import os

from classes.assets    import ASSETS
from classes.music     import MUSIC
from classes.game      import Game
from classes.constants import TITLE, FPS, init_scale


def main():
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()

    # ── Resolution: fullscreen uses native, windowed uses 1280×720 ──
    info = pygame.display.Info()
    native_w, native_h = info.current_w, info.current_h

    # Run windowed at 1280×720 by default; add --fullscreen flag to go native
    if "--fullscreen" in sys.argv:
        screen = pygame.display.set_mode((native_w, native_h), pygame.FULLSCREEN)
        sw, sh = native_w, native_h
    else:
        # Fit 16:9 window into 90% of the screen
        max_w = int(native_w * 0.90)
        max_h = int(native_h * 0.90)
        # Maintain 16:9
        if max_w / 16 * 9 <= max_h:
            sw, sh = max_w, max_w * 9 // 16
        else:
            sh, sw = max_h, max_h * 16 // 9
        # Floor to even numbers
        sw, sh = (sw // 2) * 2, (sh // 2) * 2
        screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)

    pygame.display.set_caption(TITLE)

    # Initialise scale system — must happen before any Game/Scene code runs
    init_scale(sw, sh)

    # Load assets
    base_path = os.path.dirname(os.path.abspath(__file__))
    ASSETS.load(base_path)
    MUSIC.load(base_path)

    game  = Game(screen)
    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Handle window resize
            if event.type == pygame.VIDEORESIZE:
                sw, sh = event.w, event.h
                screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)
                init_scale(sw, sh)
                game.on_resize(screen, sw, sh)

            game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()


if __name__ == "__main__":
    main()
