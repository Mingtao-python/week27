import pygame
import sys
import random
import time

pygame.init()

# 窗口设置
WIDTH, HEIGHT = 1500, 700
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("移动靶 CPS 训练")

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)

# 靶参数（你要更大目标，这里改成 45）
TARGET_RADIUS = 100
TARGET_SPEED =500  # 像素/秒

# CPS 统计
click_times = []
hits = 0
misses = 0
last_second_cps = 0
avg_cps = 0

clock = pygame.time.Clock()

# 初始靶位置和方向
target_x = random.randint(TARGET_RADIUS, WIDTH - TARGET_RADIUS)
target_y = random.randint(TARGET_RADIUS, HEIGHT - TARGET_RADIUS)
dir_x = random.choice([-1, 1])
dir_y = random.choice([-1, 1])

font = pygame.font.SysFont("consolas", 24)

def draw_text(surface, text, x, y, color=BLACK):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

running = True
start_time = time.time()

while running:
    dt = clock.tick(120) / 1000.0  # 秒

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 鼠标点击检测
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            dist_sq = (mx - target_x) ** 2 + (my - target_y) ** 2
            if dist_sq <= TARGET_RADIUS ** 2:
                # 命中（但球不消失）
                hits += 1
                now = time.time()
                click_times.append(now)
            else:
                misses += 1

    # 移动靶
    target_x += dir_x * TARGET_SPEED * dt
    target_y += dir_y * TARGET_SPEED * dt

    # 边界反弹
    if target_x <= TARGET_RADIUS or target_x >= WIDTH - TARGET_RADIUS:
        dir_x *= -1
    if target_y <= TARGET_RADIUS or target_y >= HEIGHT - TARGET_RADIUS:
        dir_y *= -1

    # 计算 CPS
    now = time.time()
    click_times = [t for t in click_times if now - t <= 1.0]
    last_second_cps = len(click_times)

    elapsed = now - start_time
    avg_cps = hits / elapsed if elapsed > 0 else 0

    # 绘制
    WIN.fill(WHITE)

    # 靶（不会消失）
    pygame.draw.circle(WIN, RED, (int(target_x), int(target_y)), TARGET_RADIUS)

    # 文本信息
    draw_text(WIN, f"Hits: {hits}", 10, 10)
    draw_text(WIN, f"Misses: {misses}", 10, 40)
    draw_text(WIN, f"CPS (last 1s): {last_second_cps:.2f}", 10, 70)
    draw_text(WIN, f"Avg CPS: {avg_cps:.2f}", 10, 100)

    pygame.display.flip()

pygame.quit()
sys.exit()
