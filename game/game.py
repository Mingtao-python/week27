import pygame
import random
import json
import os
import time

pygame.init()

WIDTH, HEIGHT = 480, 520
ROWS, COLS = 8, 8
TILE = WIDTH // COLS
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("消消乐 Match-3")

colors = [
    (255, 100, 100),
    (100, 255, 100),
    (100, 100, 255),
    (255, 255, 100),
    (255, 100, 255),
    (100, 255, 255)
]

score = 0
start_time = time.time()
GAME_DURATION = 120  # 2分钟
def lerp(a, b, t):
    return a + (b - a) * t


# -----------------------
# 读取历史最高分
# -----------------------

def flash_animation(board, matched):
    for _ in range(3):  # 闪烁三次
        # 隐藏 matched 的格子
        screen.fill((30, 30, 30))
        for r in range(ROWS):
            for c in range(COLS):
                if matched[r][c]:
                    continue  # 不画
                if board[r][c] is not None:
                    draw_tile(board[r][c], c*TILE, r*TILE)
        pygame.display.update()
        pygame.time.delay(120)

        # 显示 matched 的格子（正常画）
        screen.fill((30, 30, 30))
        for r in range(ROWS):
            for c in range(COLS):
                if board[r][c] is not None:
                    draw_tile(board[r][c], c*TILE, r*TILE)
        pygame.display.update()
        pygame.time.delay(120)

def draw_tile(value, x, y):
    if value is None:
        return
    color = colors[value]
    rect = pygame.Rect(x, y, TILE, TILE)
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, (0,0,0), rect, 2)
def swap_animation(board, r1, c1, r2, c2):
    tile1 = board[r1][c1]
    tile2 = board[r2][c2]

    x1, y1 = c1 * TILE, r1 * TILE
    x2, y2 = c2 * TILE, r2 * TILE

    frames = 12  # 动画帧数（越大越慢）

    for i in range(frames + 1):
        t = i / frames

        # 插值位置
        cx1 = lerp(x1, x2, t)
        cy1 = lerp(y1, y2, t)
        cx2 = lerp(x2, x1, t)
        cy2 = lerp(y2, y1, t)

        # 先画背景棋盘
        screen.fill((30, 30, 30))
        for r in range(ROWS):
            for c in range(COLS):
                if (r == r1 and c == c1) or (r == r2 and c == c2):
                    continue
                if board[r][c] is not None:
                    draw_tile(board[r][c], c*TILE, r*TILE)

        # 再画两个移动中的方块
        draw_tile(tile1, cx1, cy1)
        draw_tile(tile2, cx2, cy2)

        pygame.display.update()
        pygame.time.delay(20)  # 每帧延迟（越大越慢）

def load_best_score():
    if os.path.exists("game/score.json"):
        with open("game/score.json", "r", encoding="utf-8") as f:
            return json.load(f).get("best_score", 0)
    return 0

def save_best_score(best):
    with open("game/score.json", "w", encoding="utf-8") as f:
        json.dump({"best_score": best}, f)

best_score = load_best_score()

# -----------------------
# 生成棋盘
# -----------------------
def random_board():
    return [[random.randint(0, 5) for _ in range(COLS)] for _ in range(ROWS)]

board = random_board()

# -----------------------
# 检查三消
# 返回 matched 和每组连消长度
# -----------------------
def find_matches(board):
    matched = [[False]*COLS for _ in range(ROWS)]
    groups = []  # 每组连消的长度

    # 横向
    for r in range(ROWS):
        c = 0
        while c < COLS - 2:
            length = 1
            while c + length < COLS and board[r][c] == board[r][c+length]:
                length += 1
            if length >= 3:
                for k in range(length):
                    matched[r][c+k] = True
                groups.append(length)
            c += length

    # 纵向
    for c in range(COLS):
        r = 0
        while r < ROWS - 2:
            length = 1
            while r + length < ROWS and board[r][c] == board[r+length][c]:
                length += 1
            if length >= 3:
                for k in range(length):
                    matched[r+k][c] = True
                groups.append(length)
            r += length

    return matched, groups

# -----------------------
# 下落动画 + 积分
# -----------------------

def collapse(board, matched, groups):
    global score

    # 按连消长度加分
    for g in groups:
        if g == 3:
            score += 30
        elif g == 4:
            score += 50
        elif g == 5:
            score += 200
        elif g >= 6:
            score += 500

    # 先把要消除的格子设为 None
    for r in range(ROWS):
        for c in range(COLS):
            if matched[r][c]:
                board[r][c] = None

    # 动画：逐帧下落
    falling = True
    while falling:
        falling = False
        for r in range(ROWS - 1, 0, -1):
            for c in range(COLS):
                if board[r][c] is None and board[r-1][c] is not None:
                    board[r][c] = board[r-1][c]
                    board[r-1][c] = None
                    falling = True

        draw(board, None)
        pygame.time.delay(150)  # 掉落速度（越大越慢）

    # 最后补齐顶部的 None
    for c in range(COLS):
        for r in range(ROWS):
            if board[r][c] is None:
                board[r][c] = random.randint(0, 5)

# -----------------------
# 绘制
# -----------------------
def draw(board, selected):
    screen.fill((30, 30, 30))

    # 绘制方块
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] is None:
                continue
            color = colors[board[r][c]]
            rect = pygame.Rect(c*TILE, r*TILE, TILE, TILE)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0,0,0), rect, 2)

    # 选中框
    if selected:
        r, c = selected
        pygame.draw.rect(screen, (255,255,255), (c*TILE, r*TILE, TILE, TILE), 3)

    # 分数显示
    font = pygame.font.SysFont(None, 36)
    text = font.render(f"Score: {score}", True, (255,255,255))
    screen.blit(text, (10, 10))

    # 最高分显示
    best_text = font.render(f"Best: {best_score}", True, (255,255,255))
    screen.blit(best_text, (10, 50))

    # 时间显示
    elapsed = int(time.time() - start_time)
    remaining = max(0, GAME_DURATION - elapsed)
    time_text = font.render(f"Time: {remaining}s", True, (255,255,255))
    screen.blit(time_text, (10, 90))

    pygame.display.update()

# -----------------------
# 主循环
# -----------------------
running = True
selected = None

while running:
    elapsed = time.time() - start_time
    if elapsed >= GAME_DURATION:
        running = False
        break

    draw(board, selected)

    matched, groups = find_matches(board)
    if groups:
        flash_animation(board, matched)
        collapse(board, matched, groups)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if y > HEIGHT - TILE:
                continue

            r, c = y // TILE, x // TILE

            if selected is None:
                selected = (r, c)
            else:
                r2, c2 = selected
                if abs(r - r2) + abs(c - c2) == 1:
                    swap_animation(board, r, c, r2, c2)
                    board[r][c], board[r2][c2] = board[r2][c2], board[r][c]

                    matched, groups = find_matches(board)
                    if not groups:
                        swap_animation(board, r, c, r2, c2)
                        board[r][c], board[r2][c2] = board[r2][c2], board[r][c]

                selected = None

# -----------------------
# 游戏结束，保存最高分
# -----------------------
best_score = max(best_score, score)
save_best_score(best_score)

# 显示结束画面
screen.fill((0, 0, 0))
font = pygame.font.SysFont(None, 48)
end_text = font.render("Time's up!", True, (255,255,255))
score_text = font.render(f"Your Score: {score}", True, (255,255,255))
best_text = font.render(f"Best Score: {best_score}", True, (255,255,255))

screen.blit(end_text, (120, 150))
screen.blit(score_text, (120, 220))
screen.blit(best_text, (120, 290))
pygame.display.update()

pygame.time.delay(4000)
pygame.quit()
