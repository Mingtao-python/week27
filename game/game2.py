import pygame
import sys
import random
import math

pygame.init()

WIDTH, HEIGHT = 900, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("投篮物理游戏")
CLOCK = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 80, 80)
BLUE  = (80, 160, 255)
ORANGE = (255, 150, 50)

GRAVITY = 9.8 * 60
BALL_RADIUS = 12

RIM_WIDTH = 80
RIM_THICKNESS = 8
RIM_Y = 250


class Ball:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.active = True
        self.scored = False
        self.score_timer = 0

    def update(self, dt):
        # 进球后停留 1 秒再删除
        if self.scored:
            self.score_timer += dt
            if self.score_timer >= 1.0:
                self.active = False
            return

        if not self.active:
            return

        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        # 掉出屏幕
        if self.y > HEIGHT + 200:
            self.active = False

        # 左墙
        if self.x < BALL_RADIUS:
            self.x = BALL_RADIUS
            self.vx *= -0.7

        # 右墙
        if self.x > WIDTH - BALL_RADIUS:
            self.x = WIDTH - BALL_RADIUS
            self.vx *= -0.7

    def draw(self):
        pygame.draw.circle(SCREEN, ORANGE, (int(self.x), int(self.y)), BALL_RADIUS)


class Rim:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = RIM_Y
        self.speed = random.randint(80, 180)
        self.dir = random.choice([-1, 1])

    def randomize(self):
        self.x = random.randint(150, WIDTH - 150)
        self.speed = random.randint(80, 180)
        self.dir = random.choice([-1, 1])

    def update(self, dt):
        self.x += self.dir * self.speed * dt
        if self.x < 100 or self.x > WIDTH - 100:
            self.dir *= -1

    def draw(self):
        pygame.draw.rect(SCREEN, RED, (self.x - RIM_WIDTH//2, self.y, RIM_THICKNESS, RIM_THICKNESS))
        pygame.draw.rect(SCREEN, RED, (self.x + RIM_WIDTH//2 - RIM_THICKNESS, self.y, RIM_THICKNESS, RIM_THICKNESS))
        pygame.draw.line(SCREEN, RED, (self.x - RIM_WIDTH//2, self.y), (self.x + RIM_WIDTH//2, self.y), 2)


def ball_hits_rim(ball, rim):
    left_x = rim.x - RIM_WIDTH//2
    if abs(ball.x - left_x) < BALL_RADIUS and abs(ball.y - rim.y) < BALL_RADIUS:
        ball.vx *= -0.7

    right_x = rim.x + RIM_WIDTH//2
    if abs(ball.x - right_x) < BALL_RADIUS and abs(ball.y - rim.y) < BALL_RADIUS:
        ball.vx *= -0.7


def ball_scored(ball, rim):
    if ball.vy > 0:
        if rim.y - 5 < ball.y < rim.y + 5:
            if rim.x - RIM_WIDTH//2 < ball.x < rim.x + RIM_WIDTH//2:
                return True
    return False


def ball_ball_collision(b1, b2):
    dx = b2.x - b1.x
    dy = b2.y - b1.y
    dist = math.hypot(dx, dy)

    if dist < BALL_RADIUS * 2 and dist != 0:
        nx = dx / dist
        ny = dy / dist

        # 分离重叠
        overlap = BALL_RADIUS * 2 - dist
        b1.x -= nx * overlap / 2
        b2.x += nx * overlap / 2
        b1.y -= ny * overlap / 2
        b2.y += ny * overlap / 2

        # 相对速度
        dvx = b1.vx - b2.vx
        dvy = b1.vy - b2.vy

        impact = dvx * nx + dvy * ny
        if impact > 0:
            return

        j = -impact
        b1.vx += j * nx
        b1.vy += j * ny
        b2.vx -= j * nx
        b2.vy -= j * ny


def main():
    balls = []
    rim = Rim()
    score = 0
    font = pygame.font.Font(None, 40)

    while True:
        dt = CLOCK.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                vx = (mx - 100) * 2
                vy = (my - 400) * 2
                balls.append(Ball(100, 400, vx, vy))

        SCREEN.fill(BLACK)

        # 墙
        pygame.draw.rect(SCREEN, BLUE, (0, 0, 10, HEIGHT))
        pygame.draw.rect(SCREEN, BLUE, (WIDTH - 10, 0, 10, HEIGHT))

        rim.update(dt)
        rim.draw()

        # 球之间碰撞
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                ball_ball_collision(balls[i], balls[j])

        # 更新球
        for ball in balls:
            ball.update(dt)
            ball.draw()

            ball_hits_rim(ball, rim)

            if ball_scored(ball, rim) and not ball.scored:
                score += 1
                rim.randomize()
                ball.scored = True
                ball.vx = 0
                ball.vy = 0

            if not ball.active and not ball.scored:
                text = font.render("MISS!", True, WHITE)
                SCREEN.blit(text, (WIDTH//2 - 80, 80))

        # 删除 inactive 球（真正删除）
        balls = [b for b in balls if b.active or b.scored]

        score_text = font.render(f"Score: {score}", True, WHITE)
        SCREEN.blit(score_text, (20, 20))

        pygame.display.flip()


if __name__ == "__main__":
    main()
