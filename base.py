import pygame
import sys
import random
import math

# Base
pygame.init()

W, H = 900, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("PONG")
clock = pygame.time.Clock()
FPS = 60

# Colors
BG        = (10,  10,  20)
ACCENT    = (0,  220, 180)
WHITE     = (230, 230, 230)
DIMWHITE  = (80,  80,  80)
GLOW      = (0,  255, 200, 60)   # semi-transparent for glow surface

# Fonts
font_score = pygame.font.SysFont("consolas", 72, bold=True)
font_msg   = pygame.font.SysFont("consolas", 28)
font_small = pygame.font.SysFont("consolas", 18)

# Base Stats
PAD_W, PAD_H = 12, 90
PAD_SPEED     = 6
BALL_SIZE      = 12
BALL_SPEED_INIT = 5
BALL_SPEED_MAX  = 14
SPEED_INC       = 0.25
WIN_SCORE       = 11
PAD_MARGIN      = 30

# Game Classes / Stuff
class Paddle:
    def __init__(self, x):
        self.rect = pygame.Rect(x, H // 2 - PAD_H // 2, PAD_W, PAD_H)
        self.score = 0
        self.glow_timer = 0

    def move(self, up, down):
        if up:
            self.rect.y -= PAD_SPEED
        if down:
            self.rect.y += PAD_SPEED
        self.rect.clamp_ip(pygame.Rect(0, 0, W, H))

    def ai_move(self, ball):
        target = ball.rect.centery
        if self.rect.centery < target - 4:
            self.rect.y += PAD_SPEED - 1
        elif self.rect.centery > target + 4:
            self.rect.y -= PAD_SPEED - 1
        self.rect.clamp_ip(pygame.Rect(0, 0, W, H))

    def draw(self, surf):
        # Glow
        if self.glow_timer > 0:
            self.glow_timer -= 1
            glow_surf = pygame.Surface((PAD_W + 20, PAD_H + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (0, 255, 200, max(0, self.glow_timer * 8)),
                             (0, 0, PAD_W + 20, PAD_H + 20), border_radius=8)
            surf.blit(glow_surf, (self.rect.x - 10, self.rect.y - 10))
        pygame.draw.rect(surf, ACCENT, self.rect, border_radius=4)


class Ball:
    def __init__(self):
        self.reset()

    def reset(self, direction=1):
        self.rect = pygame.Rect(W // 2 - BALL_SIZE // 2,
                                H // 2 - BALL_SIZE // 2,
                                BALL_SIZE, BALL_SIZE)
        angle = random.uniform(-math.pi / 4, math.pi / 4)
        speed = BALL_SPEED_INIT
        self.vx = direction * speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.trail = []
        self.speed = speed

    def update(self):
        self.trail.append(self.rect.center)
        if len(self.trail) > 10:
            self.trail.pop(0)

        self.rect.x += self.vx
        self.rect.y += self.vy

        # Bounce top/bottom
        if self.rect.top <= 0:
            self.rect.top = 0
            self.vy *= -1
        if self.rect.bottom >= H:
            self.rect.bottom = H
            self.vy *= -1

    def bounce_off_paddle(self, paddle):
        # Relative hit position (-1 top +1 bottom)
        rel = (self.rect.centery - paddle.rect.centery) / (PAD_H / 2)
        rel = max(-1.0, min(1.0, rel))
        angle = rel * (math.pi / 3)          # up to 60degrees

        direction = 1 if self.vx < 0 else -1  # reflect
        self.speed = min(self.speed + SPEED_INC, BALL_SPEED_MAX)
        self.vx = direction * self.speed * math.cos(angle)
        self.vy = self.speed * math.sin(angle)
        paddle.glow_timer = 12

    def draw(self, surf):
        # Trail
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)) * 0.4)
            r = max(2, BALL_SIZE // 2 - (len(self.trail) - i))
            trail_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*ACCENT, alpha), (r, r), r)
            surf.blit(trail_surf, (pos[0] - r, pos[1] - r))
        # Ball
        pygame.draw.rect(surf, WHITE, self.rect, border_radius=3)


# Center Line
def draw_center_line(surf):
    dash_h, gap = 16, 10
    x = W // 2 - 1
    y = 0
    while y < H:
        pygame.draw.rect(surf, DIMWHITE, (x, y, 2, dash_h))
        y += dash_h + gap


# Glowing Score
def draw_scores(surf, p1, p2):
    s1 = font_score.render(str(p1.score), True, WHITE)
    s2 = font_score.render(str(p2.score), True, WHITE)
    surf.blit(s1, (W // 2 - 90 - s1.get_width(), 20))
    surf.blit(s2, (W // 2 + 90, 20))


# Start Screen - Win Screen
def draw_start_screen(surf):
    surf.fill(BG)
    draw_center_line(surf)
    title = font_score.render("PONG", True, ACCENT)
    surf.blit(title, title.get_rect(center=(W // 2, H // 2 - 70)))

    lines = [
        "Player 1 (left):  W / S",
        "Player 2 (right): ↑ / ↓  or  AI",
        "",
        "Press  1  →  1 Player (vs AI)",
        "Press  2  →  2 Players",
    ]
    for i, line in enumerate(lines):
        t = font_small.render(line, True, WHITE if line else WHITE)
        surf.blit(t, t.get_rect(center=(W // 2, H // 2 + 10 + i * 26)))

    pygame.display.flip()


def draw_win_screen(surf, winner):
    surf.fill(BG)
    msg = font_score.render(f"Player {winner} Wins!", True, ACCENT)
    sub = font_msg.render("Press SPACE to play again  |  ESC to quit", True, WHITE)
    surf.blit(msg, msg.get_rect(center=(W // 2, H // 2 - 40)))
    surf.blit(sub, sub.get_rect(center=(W // 2, H // 2 + 40)))
    pygame.display.flip()

# Game Loop
def game_loop(two_players=False):
    p1 = Paddle(PAD_MARGIN)
    p2 = Paddle(W - PAD_MARGIN - PAD_W)
    ball = Ball()

    # 2 serves each, independent of who scored
    # serve_seq cycles: [1, 1, -1, -1, 1, 1, ...]  (1 = p1 serves, -1 = p2 serves)
    serve_count = 0   # total points played so far
    def next_serve_direction():
        # Every 2 serves the server flips; (serve_count // 2) % 2 toggles 0/1
        return 1 if (serve_count // 2) % 2 == 0 else -1

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return   # back to start

        keys = pygame.key.get_pressed()
        p1.move(keys[pygame.K_w], keys[pygame.K_s])

        if two_players:
            p2.move(keys[pygame.K_UP], keys[pygame.K_DOWN])
        else:
            p2.ai_move(ball)

        ball.update()

        # Paddle collisions
        if ball.vx < 0 and ball.rect.colliderect(p1.rect):
            ball.rect.left = p1.rect.right
            ball.bounce_off_paddle(p1)

        if ball.vx > 0 and ball.rect.colliderect(p2.rect):
            ball.rect.right = p2.rect.left
            ball.bounce_off_paddle(p2)

        # Scoring
        scored = False
        if ball.rect.right < 0:
            p2.score += 1
            scored = True
        elif ball.rect.left > W:
            p1.score += 1
            scored = True

        if scored:
            serve_count += 1
            pygame.time.delay(400)
            ball.reset(next_serve_direction())

        # Win check
        if p1.score >= WIN_SCORE:
            return 1
        if p2.score >= WIN_SCORE:
            return 2

        # Draw
        screen.fill(BG)
        draw_center_line(screen)
        draw_scores(screen, p1, p2)
        p1.draw(screen)
        p2.draw(screen)
        ball.draw(screen)

        hint = font_small.render("ESC: menu", True, DIMWHITE)
        screen.blit(hint, (8, H - 24))

        pygame.display.flip()


# Other
def main():
    while True:
        draw_start_screen(screen)

        waiting = True
        two_players = False
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        two_players = False
                        waiting = False
                    elif event.key == pygame.K_2:
                        two_players = True
                        waiting = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

        result = game_loop(two_players)

        if result in (1, 2):
            draw_win_screen(screen, result)
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            waiting = False
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit(); sys.exit()


if __name__ == "__main__":
    main()