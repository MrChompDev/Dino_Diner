"""
Particle system — juice for coins, smoke, stars, etc.
"""

import pygame
import random
import math


class Particle:
    def __init__(self, x, y, color, vx, vy, size, life, fade=True):
        self.x     = float(x)
        self.y     = float(y)
        self.color = color
        self.vx    = vx
        self.vy    = vy
        self.size  = size
        self.life  = life
        self.max_life = life
        self.fade  = fade

    def update(self, dt):
        self.x   += self.vx * dt * 60
        self.y   += self.vy * dt * 60
        self.vy  += 0.05 * dt * 60   # gravity
        self.life -= dt
        self.size  = max(0, self.size - dt * 2)

    def draw(self, surf):
        if self.life <= 0 or self.size <= 0:
            return
        alpha = int(255 * (self.life / self.max_life)) if self.fade else 255
        col   = (*self.color, alpha)
        s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, col, (int(self.size), int(self.size)), int(self.size))
        surf.blit(s, (int(self.x - self.size), int(self.y - self.size)))


class TextParticle:
    """Floating score/message text."""

    def __init__(self, x, y, text, color, font):
        self.x     = float(x)
        self.y     = float(y)
        self.text  = text
        self.color = color
        self.font  = font
        self.life  = 2.0
        self.max_life = 2.0
        self.vy    = -1.2

    def update(self, dt):
        self.y    += self.vy * dt * 60
        self.life -= dt

    def draw(self, surf):
        alpha = int(255 * (self.life / self.max_life))
        s = self.font.render(self.text, True, self.color)
        s.set_alpha(alpha)
        surf.blit(s, (int(self.x), int(self.y)))


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle | TextParticle] = []

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)

    # ─── Emitters ─────────────────────────────────────────
    def coins(self, x, y, count=8):
        for _ in range(count):
            angle = random.uniform(-math.pi, 0)
            speed = random.uniform(1.5, 4.0)
            self.particles.append(Particle(
                x, y, (255, 215, 0),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                random.uniform(4, 8), random.uniform(0.6, 1.2)
            ))

    def stars(self, x, y, color=(255, 255, 100), count=12):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)
            self.particles.append(Particle(
                x, y, color,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                random.uniform(3, 6), random.uniform(0.5, 1.0)
            ))

    def smoke(self, x, y):
        for _ in range(5):
            self.particles.append(Particle(
                x + random.uniform(-10, 10),
                y + random.uniform(-5, 5),
                (100, 80, 60),
                random.uniform(-0.5, 0.5),
                random.uniform(-1.5, -0.5),
                random.uniform(5, 12), random.uniform(0.5, 1.0)
            ))

    def angry_sparks(self, x, y):
        for _ in range(10):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            self.particles.append(Particle(
                x, y, (220, 60, 20),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                random.uniform(3, 7), random.uniform(0.3, 0.7)
            ))

    def text_popup(self, x, y, text, color, font):
        self.particles.append(TextParticle(x, y, text, color, font))
