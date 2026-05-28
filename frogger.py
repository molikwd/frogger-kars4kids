import pygame
import random
import sys
import os

ANDROID = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ARGUMENT' in os.environ

# ── Layout ────────────────────────────────────────────────────────────────────
CELL   = 40
COLS   = 12
ROWS   = 14
GW     = COLS * CELL     # 480
GH     = ROWS * CELL     # 560
HEADER = 70
BTN_H  = 120 if ANDROID else 0
VIRT_W = GW
VIRT_H = HEADER + GH + BTN_H
FPS    = 60

# ── Colours ───────────────────────────────────────────────────────────────────
BLACK     = (  0,   0,   0)
WHITE     = (255, 255, 255)
GRASS_C   = ( 34, 120,  34)
SAFE_C    = ( 60, 160,  60)
ROAD_C    = ( 55,  55,  55)
STRIPE_C  = (200, 180,   0)
WATER_C   = ( 20,  80, 170)
LOG_C     = (139,  90,  43)
LOG_D     = (100,  65,  30)
FROG_C    = ( 50, 205,  50)
FROG_D    = ( 30, 150,  30)
PINK      = (230,  80, 160)
DARK_PINK = (200,  60, 130)
LILY_C    = ( 70, 200,  70)
DONE_C    = (230, 200,  30)
GOAL_BG   = (  8,  70,   8)

CAR_PAL = [
    (220,  50,  50),
    ( 50,  50, 220),
    ( 50, 200, 220),
    (220, 180,  30),
    (180,  50, 220),
    (220, 120,  30),
]

SAFE = 0; ROAD = 1; WATER = 2; GOAL_ROW = 3
ROW_TYPES = [
    GOAL_ROW, WATER, WATER, WATER, WATER, WATER,
    SAFE, ROAD, ROAD, ROAD, ROAD, ROAD,
    SAFE, SAFE,
]

GOAL_COLS = [1, 3, 5, 7, 9]

LANE_CFG = {
    1:  ( 55, +1, 'log', 3*CELL, 3),
    2:  ( 70, -1, 'log', 4*CELL, 2),
    3:  ( 45, +1, 'log', 3*CELL, 3),
    4:  ( 80, -1, 'log', 2*CELL, 4),
    5:  ( 60, +1, 'log', 4*CELL, 2),
    7:  ( 65, -1, 'car', CELL+10, 3),
    8:  ( 90, +1, 'car', 2*CELL,  2),
    9:  ( 55, -1, 'car', CELL+10, 3),
    10: (100, +1, 'car', 2*CELL,  2),
    11: ( 75, -1, 'car', CELL+10, 4),
}

_clr_idx = {}

# ── Lane object ───────────────────────────────────────────────────────────────

class Obj:
    def __init__(self, row, x, speed, direction, kind, width):
        self.row       = row
        self.x         = float(x)
        self.speed     = speed
        self.direction = direction
        self.kind      = kind
        self.width     = width
        if kind == 'car':
            ci = _clr_idx.get(row, 0)
            self.color = CAR_PAL[ci % len(CAR_PAL)]
            _clr_idx[row] = ci + 1
        else:
            self.color = LOG_C

    def update(self, dt, mult):
        self.x += self.direction * self.speed * mult * dt / 1000.0
        if self.direction > 0 and self.x > GW + self.width:
            self.x = float(-self.width - 5)
        elif self.direction < 0 and self.x < -self.width - 5:
            self.x = float(GW + 5)

    def rect(self):
        return pygame.Rect(int(self.x), self.row * CELL + 4, self.width, CELL - 8)

    def draw(self, surf):
        r = self.rect()
        if self.kind == 'log':
            pygame.draw.rect(surf, LOG_C, r, border_radius=10)
            pygame.draw.rect(surf, LOG_D, r, 2, border_radius=10)
            seg = r.width // 3
            for i in range(1, 3):
                lx = r.x + i * seg
                if r.left < lx < r.right:
                    pygame.draw.line(surf, LOG_D, (lx, r.y + 4), (lx, r.bottom - 4), 2)
        else:
            pygame.draw.rect(surf, self.color, r, border_radius=6)
            win = pygame.Rect(r.x + 5, r.y + 3, r.width - 10, r.height - 9)
            pygame.draw.rect(surf, (180, 220, 255), win, border_radius=3)
            for wx in [r.x + 6, r.right - 7]:
                pygame.draw.circle(surf, BLACK, (wx, r.bottom + 3), 4)
                pygame.draw.circle(surf, (70, 70, 70), (wx, r.bottom + 3), 2)


def make_lane(row):
    spd, direction, kind, width, count = LANE_CFG[row]
    spacing = GW // count
    objs = []
    for i in range(count):
        x = float(i * spacing) if direction > 0 else float(GW - width - i * spacing)
        objs.append(Obj(row, x, spd, direction, kind, width))
    return objs


# ── Frog ──────────────────────────────────────────────────────────────────────

class Frog:
    START_COL = COLS // 2
    START_ROW = ROWS - 1

    def __init__(self):
        self.reset()

    def reset(self):
        self.col   = self.START_COL
        self.row   = self.START_ROW
        self.px    = float(self.col * CELL)
        self.alive = True

    def snap_col(self):
        self.col = min(COLS - 1, max(0, round(self.px / CELL)))

    def move(self, dcol, drow):
        self.snap_col()
        nc = self.col + dcol
        nr = self.row + drow
        if 0 <= nc < COLS and 0 <= nr < ROWS:
            self.col = nc
            self.row = nr
            self.px  = float(nc * CELL)
            return True
        return False

    def cx(self):
        return int(self.px) + CELL // 2

    def draw(self, surf):
        x = int(self.px)
        y = self.row * CELL
        pygame.draw.ellipse(surf, FROG_C, pygame.Rect(x+5,  y+10, CELL-10, CELL-16))
        pygame.draw.ellipse(surf, FROG_C, pygame.Rect(x+10, y+3,  CELL-20, 18))
        for ex in [x+13, x+CELL-14]:
            pygame.draw.circle(surf, WHITE, (ex, y+9), 4)
            pygame.draw.circle(surf, BLACK, (ex, y+9), 2)
            pygame.draw.circle(surf, WHITE, (ex-1, y+8), 1)
        pygame.draw.line(surf, FROG_D, (x+7,       y+CELL-14), (x+1,       y+CELL-3), 3)
        pygame.draw.line(surf, FROG_D, (x+CELL-8,  y+CELL-14), (x+CELL-2,  y+CELL-3), 3)
        pygame.draw.line(surf, FROG_D, (x+11,      y+15),      (x+3,       y+21),     2)
        pygame.draw.line(surf, FROG_D, (x+CELL-12, y+15),      (x+CELL-4,  y+21),     2)


# ── High score ────────────────────────────────────────────────────────────────

def _hs_path():
    if ANDROID:
        base = os.environ.get('ANDROID_PRIVATE', os.path.expanduser('~'))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'frogger_high.txt')

def load_high():
    try:
        with open(_hs_path()) as f:
            return int(f.read().strip())
    except Exception:
        return 0

def save_high(score):
    try:
        with open(_hs_path(), 'w') as f:
            f.write(str(score))
    except Exception:
        pass


# ── Game ──────────────────────────────────────────────────────────────────────

class Game:
    def __init__(self):
        self.score  = 0
        self.level  = 1
        self.lives  = 3
        self.over   = False
        self.paused = False
        self.flash  = 0
        self._new_level()

    def _new_level(self):
        _clr_idx.clear()
        self.frog  = Frog()
        self.lanes = {r: make_lane(r) for r in LANE_CFG}
        self.goals = [False] * 5

    def _mult(self):
        return 1.0 + (self.level - 1) * 0.15

    def _die(self):
        self.lives -= 1
        if self.lives <= 0:
            self.over = True
        else:
            self.frog.reset()

    def move(self, dcol, drow):
        if self.over or self.paused or self.flash > 0:
            return
        if self.frog.move(dcol, drow) and drow < 0:
            self.score += 10

    def update(self, dt):
        if self.over or self.paused:
            return
        if self.flash > 0:
            self.flash -= dt
            return

        mult = self._mult()
        frog = self.frog

        for objs in self.lanes.values():
            for obj in objs:
                obj.update(dt, mult)

        rt = ROW_TYPES[frog.row]

        if rt == WATER:
            cx  = frog.cx()
            log = next((o for o in self.lanes[frog.row]
                        if o.rect().left <= cx <= o.rect().right), None)
            if log:
                dx = log.direction * log.speed * mult * dt / 1000.0
                frog.px += dx
                if frog.px < 0 or frog.px + CELL > GW:
                    frog.alive = False
            else:
                frog.alive = False

        elif rt == ROAD:
            fr = pygame.Rect(int(frog.px)+4, frog.row*CELL+4, CELL-8, CELL-8)
            for obj in self.lanes[frog.row]:
                if fr.colliderect(obj.rect()):
                    frog.alive = False
                    break

        elif rt == GOAL_ROW:
            frog.snap_col()
            hit = False
            for i, gc in enumerate(GOAL_COLS):
                if frog.col == gc and not self.goals[i]:
                    self.goals[i] = True
                    self.score += 200 + self.level * 50
                    self.flash = 600
                    frog.reset()
                    hit = True
                    if all(self.goals):
                        self.level += 1
                        self._new_level()
                    break
            if not hit:
                frog.alive = False

        if not frog.alive:
            self._die()

    def draw_game(self, surf):
        for r in range(ROWS):
            ry = r * CELL
            rt = ROW_TYPES[r]
            if rt == GOAL_ROW:
                pygame.draw.rect(surf, GOAL_BG, (0, ry, GW, CELL))
                for i, gc in enumerate(GOAL_COLS):
                    col = DONE_C if self.goals[i] else LILY_C
                    pygame.draw.ellipse(surf, col,       (gc*CELL+4, ry+4, CELL-8, CELL-8))
                    pygame.draw.ellipse(surf, (0,100,0), (gc*CELL+4, ry+4, CELL-8, CELL-8), 1)
            elif rt == WATER:
                pygame.draw.rect(surf, WATER_C, (0, ry, GW, CELL))
                for wx in range(4, GW, 20):
                    pygame.draw.arc(surf, (35,100,190),
                                    pygame.Rect(wx, ry+10, 12, 5), 0, 3.14, 1)
            elif rt == ROAD:
                pygame.draw.rect(surf, ROAD_C, (0, ry, GW, CELL))
                for dx in range(10, GW, 40):
                    pygame.draw.rect(surf, STRIPE_C, (dx, ry+CELL//2-2, 20, 3))
            else:
                col = SAFE_C if r in (6, 12) else GRASS_C
                pygame.draw.rect(surf, col, (0, ry, GW, CELL))

        for objs in self.lanes.values():
            for obj in objs:
                obj.draw(surf)

        if self.frog.alive:
            self.frog.draw(surf)

        if self.flash > 0:
            alpha = min(200, int(220 * self.flash / 600))
            fs = pygame.Surface((GW, GH), pygame.SRCALPHA)
            fs.fill((255, 240, 50, alpha))
            surf.blit(fs, (0, 0))


# ── HUD ───────────────────────────────────────────────────────────────────────

def draw_header(surf, game, font, small, high, pause_btn):
    pygame.draw.rect(surf, (15, 15, 30), (0, 0, VIRT_W, HEADER))
    pygame.draw.line(surf, (60, 60, 80), (0, HEADER-1), (VIRT_W, HEADER-1), 2)

    surf.blit(small.render("SCORE", True, (160,160,160)), (10, 8))
    surf.blit(font.render(str(game.score), True, WHITE),  (10, 24))

    surf.blit(small.render("BEST",  True, (160,160,160)), (120, 8))
    surf.blit(font.render(str(high), True, PINK),         (120, 24))

    surf.blit(small.render("LEVEL", True, (160,160,160)), (240, 8))
    surf.blit(font.render(str(game.level), True, (100,220,255)), (240, 24))

    surf.blit(small.render("LIVES", True, (160,160,160)), (330, 8))
    for i in range(game.lives):
        lx = 330 + i * 32
        pygame.draw.ellipse(surf, FROG_C, (lx, 26, 24, 14))
        pygame.draw.circle(surf, BLACK, (lx+7,  31), 2)
        pygame.draw.circle(surf, BLACK, (lx+17, 31), 2)

    if not game.over:
        col = DARK_PINK if game.paused else PINK
        pygame.draw.rect(surf, col, pause_btn, border_radius=5)
        pygame.draw.rect(surf, WHITE, pause_btn, 1, border_radius=5)
        lbl = small.render("II" if not game.paused else ">", True, WHITE)
        surf.blit(lbl, (pause_btn.centerx - lbl.get_width()//2,
                        pause_btn.centery - lbl.get_height()//2))




def draw_overlay(surf, title, sub, font, small):
    ov = pygame.Surface((GW, GH), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 160))
    surf.blit(ov, (0, HEADER))
    tw = font.size(title)[0]
    surf.blit(font.render(title, True, WHITE),
              (VIRT_W//2 - tw//2, HEADER + GH//2 - 30))
    sw = small.size(sub)[0]
    surf.blit(small.render(sub, True, (200, 200, 200)),
              (VIRT_W//2 - sw//2, HEADER + GH//2 + 10))


# ── D-pad (Android only) ─────────────────────────────────────────────────────

def draw_dpad(surf, rects):
    for name, rect in rects.items():
        pygame.draw.rect(surf, PINK, rect, border_radius=10)
        pygame.draw.rect(surf, WHITE, rect, 2, border_radius=10)
        cx, cy = rect.centerx, rect.centery
        s = 11
        if name == 'up':
            pts = [(cx, cy-s), (cx-s, cy+s), (cx+s, cy+s)]
        elif name == 'down':
            pts = [(cx, cy+s), (cx-s, cy-s), (cx+s, cy-s)]
        elif name == 'left':
            pts = [(cx-s, cy), (cx+s, cy-s), (cx+s, cy+s)]
        else:
            pts = [(cx+s, cy), (cx-s, cy-s), (cx-s, cy+s)]
        pygame.draw.polygon(surf, WHITE, pts)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    pygame.init()

    if ANDROID:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        SW = screen.get_width()
        SH = screen.get_height()
        if SW > SH:
            SW, SH = SH, SW
        _scale   = min(SW / VIRT_W, SH / VIRT_H)
        SCALED_W = int(VIRT_W * _scale)
        SCALED_H = int(VIRT_H * _scale)
        OFF_X    = (SW - SCALED_W) // 2
        OFF_Y    = (SH - SCALED_H) // 2
    else:
        screen = pygame.display.set_mode((VIRT_W, VIRT_H))
        SW, SH   = VIRT_W, VIRT_H
        _scale   = 1.0
        SCALED_W = VIRT_W
        SCALED_H = VIRT_H
        OFF_X    = OFF_Y = 0

    def to_virt(pos):
        return (int((pos[0] - OFF_X) / _scale), int((pos[1] - OFF_Y) / _scale))

    pygame.display.set_caption("Frogger Kars4Kids")
    clock = pygame.time.Clock()
    font  = pygame.font.SysFont("consolas", 22, bold=True)
    small = pygame.font.SysFont("consolas", 14)

    virt      = pygame.Surface((VIRT_W, VIRT_H))
    game_surf = pygame.Surface((GW, GH))
    game      = Game()
    high      = load_high()

    pause_btn = pygame.Rect(VIRT_W - 55, 18, 48, 28)

    # D-pad button rects (only used on Android, positioned below game area)
    _by = HEADER + GH   # y=630 — top of button strip
    dpad = {
        'up':    pygame.Rect(VIRT_W//2 - 45, _by +  5, 90, 40),
        'down':  pygame.Rect(VIRT_W//2 - 45, _by + 75, 90, 40),
        'left':  pygame.Rect(VIRT_W//2 - 145, _by + 40, 90, 40),
        'right': pygame.Rect(VIRT_W//2 + 55,  _by + 40, 90, 40),
    }
    DPAD_MOVE = {'up': (0,-1), 'down': (0,+1), 'left': (-1,0), 'right': (+1,0)}

    while True:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_r, pygame.K_RETURN) and game.over:
                    game = Game()
                if event.key == pygame.K_p and not game.over:
                    game.paused = not game.paused
                if not game.over and not game.paused:
                    if event.key in (pygame.K_UP,    pygame.K_w): game.move( 0, -1)
                    if event.key in (pygame.K_DOWN,  pygame.K_s): game.move( 0, +1)
                    if event.key in (pygame.K_LEFT,  pygame.K_a): game.move(-1,  0)
                    if event.key in (pygame.K_RIGHT, pygame.K_d): game.move(+1,  0)

            if ANDROID and event.type == pygame.FINGERDOWN:
                vpos = to_virt((int(event.x * SW), int(event.y * SH)))
                if game.over:
                    game = Game()
                elif pause_btn.collidepoint(vpos):
                    if not game.over:
                        game.paused = not game.paused
                elif not game.paused:
                    for name, rect in dpad.items():
                        if rect.collidepoint(vpos):
                            dc, dr = DPAD_MOVE[name]
                            game.move(dc, dr)
                            break

        game.update(dt)

        if game.score > high:
            high = game.score
            save_high(high)

        # ── Draw ──────────────────────────────────────────────────────────────
        game_surf.fill(BLACK)
        game.draw_game(game_surf)

        virt.fill(BLACK)
        draw_header(virt, game, font, small, high, pause_btn)
        virt.blit(game_surf, (0, HEADER))

        if ANDROID:
            draw_dpad(virt, dpad)

        if game.paused and not game.over:
            sub = "Tap II to resume" if ANDROID else "Press P to resume"
            draw_overlay(virt, "PAUSED", sub, font, small)
        if game.over:
            sub = "Tap to restart" if ANDROID else "Press R to restart"
            draw_overlay(virt, "GAME OVER", sub, font, small)

        if ANDROID:
            scaled = pygame.transform.scale(virt, (SCALED_W, SCALED_H))
            screen.fill(BLACK)
            screen.blit(scaled, (OFF_X, OFF_Y))
        else:
            screen.blit(virt, (0, 0))

        pygame.display.flip()


if __name__ == "__main__":
    main()
