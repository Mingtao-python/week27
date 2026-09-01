import pygame
import random
import math

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("精准度练习器（完美修复版）")

clock = pygame.time.Clock()

pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

yaw = 0
pitch = 0

hits = 0
miss = 0
speed_penalty = 0

# --------------------------
# FPS 视角旋转
# --------------------------
def rotate(x, y, z, yaw, pitch):
    # yaw 左右
    cy = math.cos(math.radians(yaw))
    sy = math.sin(math.radians(yaw))
    x2 = x * cy - z * sy
    z2 = x * sy + z * cy

    # pitch 上下
    cp = math.cos(math.radians(pitch))
    sp = math.sin(math.radians(pitch))
    y2 = y * cp - z2 * sp
    z3 = y * sp + z2 * cp

    return x2, y2, z3

# --------------------------
# 目标类
# --------------------------
class Target:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.uniform(-1.2, 1.2)
        self.y = random.uniform(-0.8, 0.8)
        self.z = random.uniform(6, 14)
        self.speed = random.uniform(0.03, 0.06)

    def update(self):
        self.z -= self.speed
        if self.z <= 0.5:
            global speed_penalty
            speed_penalty += 1
            self.reset()

    def draw(self):
        rx, ry, rz = rotate(self.x, self.y, self.z, yaw, pitch)

        if rz <= 0.1:
            return None, None, None

        # 正确的 FPS 投影
        FOV_SCALE = 300
        sx = WIDTH // 2 + int((rx / rz) * FOV_SCALE)
        sy = HEIGHT // 2 + int((ry / rz) * FOV_SCALE)

        # 正确的大小公式
        BASE_SIZE = 40
        radius = int(BASE_SIZE / rz)
        radius = max(radius, 3)

        pygame.draw.circle(screen, (255, 80, 80), (sx, sy), radius)

        return sx, sy, radius

target = Target()

def draw_crosshair():
    cx, cy = WIDTH // 2, HEIGHT // 2
    color = (255, 255, 255)
    thickness = 3
    length = 15

    pygame.draw.line(screen, color, (cx - length, cy), (cx - 5, cy), thickness)
    pygame.draw.line(screen, color, (cx + 5, cy), (cx + length, cy), thickness)
    pygame.draw.line(screen, color, (cx, cy - length), (cx, cy - 5), thickness)
    pygame.draw.line(screen, color, (cx, cy + 5), (cx, cy + length), thickness)

running = True
while running:
    screen.fill((30, 30, 30))

    dx, dy = pygame.mouse.get_rel()
    sensitivity = 0.15
    
    yaw += dx * sensitivity
    pitch += dy * sensitivity
    
    pitch = max(-89, min(89, pitch))


    target.update()
    sx, sy, radius = target.draw()

    font = pygame.font.SysFont(None, 36)
    acc = hits / (hits + miss) * 100 if (hits + miss) > 0 else 0
    text = font.render(
        f"Hits: {hits}  Miss: {miss}  Accuracy: {acc:.1f}%  Speed Penalty: {speed_penalty}",
        True, (255, 255, 255)
    )
    screen.blit(text, (20, 20))

    draw_crosshair()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if sx is None:
                    miss += 1
                else:
                    mx, my = WIDTH // 2, HEIGHT // 2
                    if sy is None:
                        sy = 0 # Incase of bug, because vs code tell me that sy might be none even though is shouldn't be and I have neve saw it.
                    if radius is None:
                        radius = 0 # In case of bug, but should not happen
                    dist = math.hypot(mx - sx, float(my) - float(sy))
                    if (dist*1000) <= (float(radius)*1000):
                        hits += 1
                        target.reset()
                    else:
                        miss += 1

    pygame.display.update()
    clock.tick(60)

pygame.quit()
