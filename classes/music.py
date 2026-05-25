"""
music.py — Music manager for Dino Diner

Handles two tracks:
  Menu.mp3     → plays on title screen, loops
  GamePlay.mp3 → plays during restaurant/shop/upgrade, loops

Crossfades between tracks when state changes.
Volume is adjustable. Gracefully handles missing files.
"""

import os
import pygame


class MusicManager:
    MENU_TRACK     = "Menu"
    GAMEPLAY_TRACK = "GamePlay"

    def __init__(self):
        self._current  = None   # track name currently playing
        self._base_dir = ""
        self._tracks   = {}     # name → full path
        self._volume   = 0.6
        self._loaded   = False
        self._enabled  = True

    def load(self, base_path: str):
        """Find music files. base_path = folder containing main.py."""
        music_dir = os.path.join(base_path, "Assets", "SFX", "Music")
        if not os.path.isdir(music_dir):
            print(f"[Music] Directory not found: {music_dir}")
            return

        for name in (self.MENU_TRACK, self.GAMEPLAY_TRACK):
            # Prefer .mp3, fall back to .m4a
            for ext in (".mp3", ".m4a"):
                path = os.path.join(music_dir, f"{name}{ext}")
                if os.path.isfile(path):
                    self._tracks[name] = path
                    print(f"[Music] Found: {path}")
                    break
            else:
                print(f"[Music] Missing: {name}.mp3 / {name}.m4a in {music_dir}")

        self._loaded = bool(self._tracks)

    def play_menu(self):
        self._switch(self.MENU_TRACK)

    def play_gameplay(self):
        self._switch(self.GAMEPLAY_TRACK)

    def _switch(self, name: str):
        if not self._loaded or not self._enabled:
            return
        if self._current == name:
            return  # already playing this track
        path = self._tracks.get(name)
        if not path:
            return
        try:
            pygame.mixer.music.fadeout(400)
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.play(-1, fade_ms=600)   # -1 = loop forever
            self._current = name
        except Exception as e:
            print(f"[Music] Error playing {name}: {e}")

    def stop(self):
        pygame.mixer.music.fadeout(500)
        self._current = None

    def set_volume(self, v: float):
        self._volume = max(0.0, min(1.0, v))
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(self._volume)

    def toggle(self):
        self._enabled = not self._enabled
        if not self._enabled:
            self.stop()
        elif self._current:
            self._switch(self._current)

    @property
    def enabled(self) -> bool:
        return self._enabled


# Global singleton
MUSIC = MusicManager()
