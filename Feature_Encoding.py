"""
FEATURE ENCODING MOTION LAB
A continuously animated 3-minute visual explainer for:
    1. Label Encoding
    2. One-Hot Encoding
    3. Ordinal Encoding

No third-party libraries required. Uses Python's built-in tkinter Canvas.

Run:
    python feature_encoding_motion_lab.py

Controls:
    SPACE  Pause / resume
    RIGHT  Skip forward
    LEFT   Restart current chapter
    R      Restart all 3 minutes
    ESC    Close

This is designed as a motion graphic, not a slide deck:
- Categories move through an animated processing pipeline.
- Cards, particles, scanner beams, bit columns, bars, and paths animate continuously.
- Scene transitions slide/fade rather than simply swapping static screens.
- The app targets a 60 FPS update cadence; actual FPS depends on the PC/display.
"""

import tkinter as tk
import math
import random
import time

# ------------------------------ DESIGN -------------------------------------

W, H = 1280, 720
FPS = 60
FRAME_MS = round(1000 / FPS)
TOTAL_TIME = 180.0

BG = "#F7F9FE"
WHITE = "#FFFFFF"  # Used by animation color blends and highlights.
INK = "#1D2942"
MUTED = "#71809B"
FAINT = "#E7ECF5"
PANEL = "#FFFFFF"
CYAN = "#00A3C7"
BLUE = "#5378E8"
PURPLE = "#9566D7"
PINK = "#E75A9B"
GREEN = "#22A77C"
YELLOW = "#D99B18"
ORANGE = "#E17A47"
RED = "#D95061"
PALE_CYAN = "#E1F7FB"
PALE_BLUE = "#E8EEFF"
PALE_PURPLE = "#F1E9FF"
PALE_PINK = "#FFE9F2"
PALE_GREEN = "#E4F8F0"
PALE_YELLOW = "#FFF5D8"
PALE_RED = "#FFEBED"
SHADOW = "#E7ECF5"

# 10 chapters fill exactly 180 seconds.
CHAPTERS = [
    ("OPENING", 12.0, CYAN),
    ("THE PROBLEM", 16.0, PINK),
    ("LABEL ENCODING", 22.0, BLUE),
    ("LABEL ENCODING IN MOTION", 18.0, CYAN),
    ("ONE-HOT ENCODING", 22.0, GREEN),
    ("ONE-HOT IN MOTION", 18.0, GREEN),
    ("ORDINAL ENCODING", 22.0, YELLOW),
    ("COMPARE THE METHODS", 18.0, PURPLE),
    ("PITFALLS + CHALLENGE", 18.0, RED),
    ("RECAP", 14.0, CYAN),
]
assert abs(sum(x[1] for x in CHAPTERS) - TOTAL_TIME) < 0.01

random.seed(8)


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * clamp(t)


def smooth_color(a, b, t):
    """Blend two #RRGGBB colors."""
    t = clamp(t)
    aa = tuple(int(a[i:i+2], 16) for i in (1, 3, 5))
    bb = tuple(int(b[i:i+2], 16) for i in (1, 3, 5))
    cc = tuple(int(aa[k] + (bb[k] - aa[k]) * t) for k in range(3))
    return "#%02x%02x%02x" % cc


def hex_rgb(h):
    return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))


def rounded(canvas, x1, y1, x2, y2, fill, outline="", radius=16, width=1):
    """Rounded rectangle drawn as a smooth polygon."""
    r = min(radius, (x2-x1)/2, (y2-y1)/2)
    points = [
        x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
        x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
        x1, y2, x1, y2-r, x1, y1+r, x1, y1
    ]
    return canvas.create_polygon(
        points, smooth=True, splinesteps=16, fill=fill,
        outline=outline or fill, width=width
    )


def text(canvas, x, y, value, size=18, fill=INK, weight="normal",
         anchor="center", font="Segoe UI"):
    return canvas.create_text(
        x, y, text=value, fill=fill, font=(font, size, weight), anchor=anchor
    )


def line(canvas, *coords, fill=FAINT, width=2, dash=None, smooth=False):
    kw = {"fill": fill, "width": width}
    if dash:
        kw["dash"] = dash
    if smooth:
        kw["smooth"] = True
    return canvas.create_line(*coords, **kw)


def circle(canvas, x, y, r, fill, outline="", width=1):
    return canvas.create_oval(x-r, y-r, x+r, y+r, fill=fill,
                              outline=outline or fill, width=width)


def arrow(canvas, x1, y1, x2, y2, color=CYAN, width=3):
    line(canvas, x1, y1, x2, y2, fill=color, width=width)
    ang = math.atan2(y2-y1, x2-x1)
    size = 11
    p1 = (x2-size*math.cos(ang-0.55), y2-size*math.sin(ang-0.55))
    p2 = (x2-size*math.cos(ang+0.55), y2-size*math.sin(ang+0.55))
    canvas.create_polygon((x2, y2, *p1, *p2), fill=color, outline=color)


def pill(canvas, x, y, label, color, bg=None, size=12):
    width = max(78, len(label) * size * 0.67 + 26)
    rounded(canvas, x, y, x+width, y+30, bg or smooth_color(BG, color, .12),
            outline=smooth_color(FAINT, color, .5), radius=14)
    text(canvas, x+width/2, y+15, label, size, color, "bold")
    return width


def panel(canvas, x, y, w, h, accent=CYAN, fill=PANEL, shadow=True):
    if shadow:
        rounded(canvas, x+3, y+5, x+w+3, y+h+5, SHADOW, SHADOW, 18)
    rounded(canvas, x, y, x+w, y+h, fill, smooth_color(FAINT, accent, .55), 18, 1)


def label_chip(canvas, cx, cy, label, color, width=150, height=54, glow=0):
    """A token chip. glow pulsates by drawing a soft coloured halo."""
    if glow > 0:
        for k in range(3, 0, -1):
            pad = k * (2 + glow * 2)
            halo = smooth_color(WHITE, color, .15 / k)
            canvas.create_oval(cx-width/2-pad, cy-height/2-pad,
                               cx+width/2+pad, cy+height/2+pad,
                               outline=halo, width=1)
    rounded(canvas, cx-width/2, cy-height/2, cx+width/2, cy+height/2,
            smooth_color(WHITE, color, .09),
            smooth_color(FAINT, color, .65), 15, 2)
    circle(canvas, cx-width/2+17, cy, 5, color)
    text(canvas, cx+5, cy, label, 17, INK, "bold")


def bit_box(canvas, cx, cy, value, color, active=False, size=58):
    fill = smooth_color(WHITE, color, .20) if active else "#F1F4FA"
    edge = color if active else "#DDE4F0"
    rounded(canvas, cx-size/2, cy-size/2, cx+size/2, cy+size/2,
            fill, edge, 12, 2 if active else 1)
    text(canvas, cx, cy, str(value), 22, color if active else "#A5AFC2", "bold")
    if active:
        circle(canvas, cx+size/2-7, cy-size/2+7, 4, color)


def draw_background(canvas, t):
    canvas.configure(bg=BG)
    # Subtle moving dots/lines are always in motion.
    for i in range(22):
        x = (i * 61 + (t * (10 + i % 4 * 5))) % (W + 20) - 10
        y = 220 + (i * 43) % 420
        col = [PALE_CYAN, PALE_PURPLE, PALE_PINK, PALE_GREEN][i % 4]
        circle(canvas, x, y, 2 + (i % 2), col)
    # Fine vertical drafting guides.
    for x in range(40, W, 120):
        line(canvas, x, 220, x, 645, fill="#F0F3F9", width=1)


def draw_header(canvas, chapter_idx, elapsed, local_t, paused):
    title, _, accent = CHAPTERS[chapter_idx]
    enter = out_cubic(local_t / .45)
    dx = int((1-enter) * -35)
    pill(canvas, 48+dx, 35, f"CHAPTER {chapter_idx+1:02d}", accent, size=11)
    text(canvas, 48+dx, 91, title, 31, INK, "bold", "w")
    # Moving accent underline.
    underline = 35 + 280 * ease(local_t / .7)
    line(canvas, 48+dx, 127, 48+dx+underline, 127, fill=accent, width=4)
    mins, secs = int(elapsed)//60, int(elapsed)%60
    text(canvas, 1228, 42, f"{mins:02d}:{secs:02d} / 03:00", 13, MUTED, "bold", "e")
    # Overall progress.
    rounded(canvas, 48, 15, 1232, 21, "#E5EAF4", radius=3)
    rounded(canvas, 48, 15, 48+1184*clamp(elapsed/TOTAL_TIME), 21,
            accent, radius=3)
    if paused:
        rounded(canvas, 520, 286, 760, 390, "#FFFFFF", accent, 22, 2)
        text(canvas, 640, 325, "PAUSED", 30, accent, "bold")
        text(canvas, 640, 366, "Press SPACE to continue", 14, MUTED)


def draw_footer(canvas, idx, paused):
    line(canvas, 48, 674, 1232, 674, fill="#E5EAF3", width=1)
    text(canvas, 48, 695, "FEATURE ENCODING MOTION LAB", 11, MUTED, "bold", "w")
    text(canvas, 1232, 695, "SPACE pause   ← restart chapter   → skip   R replay", 11, MUTED, "normal", "e")


# ---------------------------- ANIMATED SCENES -------------------------------

def scene_open(canvas, t):
    """Opening scene: tokens orbit, converge, and transform."""
    cx, cy = 640, 400
    pulse = (math.sin(t*3.5)+1)/2
    # Rotating rings
    for j, r in enumerate((118, 151, 185)):
        col = [CYAN, PURPLE, PINK][j]
        points = []
        start = t*(.25 + .08*j) * (-1 if j % 2 else 1)
        for k in range(49):
            a = start + k*math.tau/48
            points.extend((cx+math.cos(a)*r, cy+math.sin(a)*r*.66))
        line(canvas, *points, fill=smooth_color(BG, col, .62), width=2, smooth=True)
    labels = [("Delhi", CYAN), ("Mumbai", PURPLE), ("Jaipur", PINK),
              ("Small", GREEN), ("High", YELLOW)]
    for i, (lab, col) in enumerate(labels):
        a = t*.72 + i*math.tau/len(labels)
        x = cx + math.cos(a)*220
        y = cy + math.sin(a)*124
        label_chip(canvas, x, y, lab, col, 110, 43, pulse*.6)
    # Core title changes scale gently.
    text(canvas, cx, cy-24, "CATEGORIES", 23+int(pulse*2), INK, "bold")
    text(canvas, cx, cy+18, "↓ encode ↓", 18, CYAN, "bold")
    text(canvas, cx, cy+56, "MODEL-READY DATA", 16, GREEN, "bold")
    text(canvas, 640, 590, "Watch real data tokens transform—not just appear on a slide.", 17, MUTED)


def scene_problem(canvas, t):
    """Categories travel along a conveyor toward a model which cannot read them."""
    y = 380
    # Conveyor rail with moving dashes.
    line(canvas, 68, y+56, 930, y+56, fill="#DCE5F3", width=5)
    for i in range(18):
        x = (i*58 + t*140) % 920 + 40
        line(canvas, x, y+48, x+20, y+48, fill="#C6D4EA", width=3)
    text(canvas, 180, 280, "RAW CATEGORICAL FEATURE", 15, MUTED, "bold")
    text(canvas, 1050, 280, "MODEL", 15, MUTED, "bold")
    words = [("Delhi", CYAN), ("Mumbai", PURPLE), ("Jaipur", PINK), ("Delhi", CYAN)]
    for i, (word, col) in enumerate(words):
        x = 130 + ((t*95 + i*210) % 700)
        label_chip(canvas, x, y, word, col, 130, 54, .4)
    # Model block subtly shakes as unencoded text reaches it.
    shake = math.sin(t*13)*3
    panel(canvas, 962+shake, 315, 230, 160, RED, PALE_RED)
    text(canvas, 1077+shake, 350, "ML MODEL", 22, RED, "bold")
    circle(canvas, 1040+shake, 403, 15, RED)
    circle(canvas, 1077+shake, 403, 15, RED)
    circle(canvas, 1114+shake, 403, 15, RED)
    text(canvas, 1077+shake, 445, "TEXT?  ERROR!", 15, RED, "bold")
    for i in range(3):
        xx = 965 + (t*120 + i*90) % 245
        circle(canvas, xx, 525, 4, RED)
    text(canvas, 640, 600, "Encoding provides a numeric representation while preserving the useful meaning.", 17, INK, "bold")


def scene_label(canvas, t):
    """Animated label-encoding pipeline with category tokens entering and IDs exiting."""
    y0 = 320
    # Pipeline framing.
    panel(canvas, 55, 260, 1170, 305, BLUE, WHITE)
    text(canvas, 120, 292, "CATEGORY INPUT", 13, MUTED, "bold", "w")
    text(canvas, 585, 292, "ENCODER", 13, BLUE, "bold")
    text(canvas, 1080, 292, "INTEGER OUTPUT", 13, MUTED, "bold", "w")
    # Scanner in the central conversion chamber.
    rounded(canvas, 475, 322, 705, 512, PALE_BLUE, "#D1DCFB", 22, 1)
    scan_x = 495 + ((t*175) % 190)
    line(canvas, scan_x, 333, scan_x, 502, fill=BLUE, width=3)
    # conveyor belt.
    line(canvas, 170, 418, 1085, 418, fill="#DCE5F3", width=6)
    for i in range(24):
        x = 170 + ((i*42 + t*120) % 900)
        line(canvas, x, 410, x+14, 410, fill="#B8C8E1", width=2)
    vals = [("Delhi", 0, CYAN), ("Mumbai", 1, PURPLE), ("Jaipur", 2, PINK)]
    for i, (word, val, col) in enumerate(vals):
        # Each token continuously cycles through the pipeline.
        p = (t*0.52 + i/3) % 1
        x = 160 + p*860
        if x < 475:
            label_chip(canvas, x, y0 + i*2, word, col, 132, 55, .3)
        elif x < 710:
            # Token enters conversion scanner; brief flash.
            b = (math.sin(t*12+i)+1)/2
            circle(canvas, x, y0, 29, smooth_color(WHITE, col, .18+b*.2),
                   outline=col, width=2)
            text(canvas, x, y0, "↻", 24, col, "bold")
        else:
            rounded(canvas, x-44, y0-26, x+44, y0+26,
                    smooth_color(WHITE, col, .16), col, 14, 2)
            text(canvas, x, y0, str(val), 24, col, "bold")
    # Stable mapping shown below as an ever-visible key.
    mappings = [("Delhi", "0", CYAN), ("Mumbai", "1", PURPLE), ("Jaipur", "2", PINK)]
    for i, (word, n, col) in enumerate(mappings):
        xx = 150 + i*360
        label_chip(canvas, xx, 515, word, col, 128, 43)
        arrow(canvas, xx+80, 515, xx+130, 515, col, 2)
        rounded(canvas, xx+145, 493, xx+197, 537, smooth_color(WHITE, col, .12), col, 10, 1)
        text(canvas, xx+171, 515, n, 18, col, "bold")
    text(canvas, 640, 605, "Compact and consistent: the same category always maps to the same ID.", 16, INK, "bold")


def scene_label_motion(canvas, t):
    """One moving token cycles through input -> conversion -> output."""
    text(canvas, 640, 240, "FOLLOW ONE VALUE THROUGH THE PIPELINE", 17, MUTED, "bold")
    # Process nodes.
    nodes = [(150, "CATEGORY", CYAN), (480, "ENCODE", BLUE), (820, "INTEGER", PURPLE), (1110, "FEATURE", GREEN)]
    for i, (x, name, col) in enumerate(nodes):
        pulse = .5 + .5*math.sin(t*4-i)
        r = 44 + pulse*3
        circle(canvas, x, 395, r, smooth_color(WHITE, col, .10),
               outline=col, width=2)
        text(canvas, x, 395, name, 12, col, "bold")
        if i < len(nodes)-1:
            arrow(canvas, x+55, 395, nodes[i+1][0]-56, 395, col, 3)
    # Token moves around the pipeline.
    u = (t*.34) % 1.0
    x = 150 + u*960
    labels = [("Delhi", CYAN, "0"), ("Mumbai", PURPLE, "1"), ("Jaipur", PINK, "2")]
    step = int(t/2.5) % 3
    label, col, num = labels[step]
    glow = .5 + .5*math.sin(t*7)
    if u < .53:
        label_chip(canvas, x, 395, label, col, 122, 49, glow)
    else:
        rounded(canvas, x-45, 366, x+45, 424, smooth_color(WHITE, col, .15), col, 15, 2)
        text(canvas, x, 395, num, 26, col, "bold")
    # Mapping rail.
    panel(canvas, 290, 500, 700, 95, BLUE, WHITE)
    text(canvas, 640, 522, "MAPPING TABLE", 12, MUTED, "bold")
    for i, (lab, c, n) in enumerate(labels):
        xx = 405+i*225
        text(canvas, xx, 562, f"{lab}  →  {n}", 17, c, "bold")
    text(canvas, 640, 625, "Important: these numbers are identifiers, not measurements or rankings.", 15, RED, "bold")


def scene_onehot(canvas, t):
    """Columns animate into place; active bits illuminate as a token moves."""
    panel(canvas, 70, 250, 1140, 345, GREEN)
    text(canvas, 135, 280, "CATEGORY", 13, MUTED, "bold", "w")
    text(canvas, 785, 280, "ONE-HOT VECTOR", 13, MUTED, "bold")
    categories = [("Delhi", CYAN), ("Mumbai", PURPLE), ("Jaipur", PINK)]
    xs = [690, 820, 950]
    for j, (cat, col) in enumerate(categories):
        # Column headings bob slightly as they enter.
        bob = math.sin(t*2+j)*3
        rounded(canvas, xs[j]-48, 305+bob, xs[j]+48, 349+bob,
                smooth_color(WHITE, col, .12), col, 12, 1)
        text(canvas, xs[j], 327+bob, cat, 12, col, "bold")
    # Input chips move one at a time.
    active_row = int(t*0.65) % 3
    row_names = ["Delhi", "Mumbai", "Jaipur"]
    for i, name in enumerate(row_names):
        y = 390 + i*63
        col = categories[i][1]
        if i == active_row:
            # A bright streak connects the selected category to its bit.
            pulse = (math.sin(t*6)+1)/2
            label_chip(canvas, 220, y, name, col, 135, 44, pulse)
            arrow(canvas, 330, y, 635, y, col, 3)
            for k in range(6):
                u = (t*1.6+k/6) % 1
                circle(canvas, 340+u*280, y, 3, col)
        else:
            label_chip(canvas, 220, y, name, col, 135, 44, .08)
            line(canvas, 330, y, 635, y, fill="#E3EAF4", width=2)
        for j in range(3):
            value = 1 if i == j else 0
            bit_box(canvas, xs[j], y, value, categories[j][1],
                    active=(i == j and i == active_row), size=48)
    text(canvas, 640, 620, "Each row has one active bit. Categories do not get a numeric rank.", 17, GREEN, "bold")


def scene_onehot_motion(canvas, t):
    """A bit moves across the vector as the input category changes."""
    text(canvas, 640, 240, "THE ACTIVE BIT FOLLOWS THE CATEGORY", 18, MUTED, "bold")
    cats = [("Delhi", CYAN), ("Mumbai", PURPLE), ("Jaipur", PINK)]
    active = int(t*0.85) % 3
    label, col = cats[active]
    # Category token approaches a one-hot encoder.
    token_x = 115 + (t*100 % 235)
    label_chip(canvas, token_x, 400, label, col, 122, 50, .7)
    # Encoder gate with animated scanning lights.
    rounded(canvas, 410, 318, 590, 480, PALE_GREEN, GREEN, 22, 2)
    text(canvas, 500, 350, "ONE-HOT", 14, GREEN, "bold")
    for i in range(5):
        yy = 375+i*18
        x = 430 + ((t*120+i*28) % 140)
        circle(canvas, x, yy, 3, GREEN)
    arrow(canvas, 350, 400, 400, 400, GREEN, 3)
    arrow(canvas, 600, 400, 655, 400, GREEN, 3)
    # Vector outputs animate with active bit travelling to chosen position.
    for j, (name, c) in enumerate(cats):
        x = 720+j*135
        value = 1 if j == active else 0
        bit_box(canvas, x, 400, value, c, active=(j == active), size=75)
        text(canvas, x, 455, name, 13, c, "bold")
    # Active-bit travelling glow.
    glow_x = 720+active*135
    for r in (34, 43, 51):
        circle(canvas, glow_x, 400, r, "", outline=smooth_color(WHITE, col, .55), width=1)
    text(canvas, 640, 550, f"{label}  →  [{1 if active==0 else 0}, {1 if active==1 else 0}, {1 if active==2 else 0}]",
         24, col, "bold")
    text(canvas, 640, 602, "The binary vector tells the model which category is present.", 16, MUTED)


def scene_ordinal(canvas, t):
    """Ordinal categories rise like an animated staircase."""
    text(canvas, 640, 237, "THE ORDER COMES FROM DOMAIN MEANING", 17, MUTED, "bold")
    levels = [("SMALL", 1, GREEN), ("MEDIUM", 2, YELLOW), ("LARGE", 3, ORANGE)]
    base_y = 575
    for i, (name, value, col) in enumerate(levels):
        x = 180+i*350
        target_h = 115+i*78
        growth = ease((t-i*.4)/1.0)
        h = target_h*growth
        y = base_y-h
        rounded(canvas, x, y, x+220, base_y, smooth_color(WHITE, col, .16),
                col, 18, 2)
        text(canvas, x+110, y+31, name, 18, col, "bold")
        text(canvas, x+110, y+77, str(value), 35, INK, "bold")
        if i < 2:
            arrow(canvas, x+235, y+target_h*.45, x+330, y+target_h*.45, YELLOW, 3)
    # Animated rank marker slides across staircase.
    marker_x = 285 + (t*115 % 680)
    marker_y = 548 - ((marker_x-285)/680)*160
    circle(canvas, marker_x, marker_y, 10, WHITE, outline=PURPLE, width=3)
    circle(canvas, marker_x, marker_y, 3, PURPLE)
    text(canvas, 640, 620, "SMALL < MEDIUM < LARGE     •     Ranking is meaningful; equal gaps are not guaranteed.",
         15, YELLOW, "bold")


def scene_compare(canvas, t):
    """Three encodings actively transform the same moving categories side by side."""
    categories = [("low", CYAN), ("medium", PURPLE), ("high", PINK)]
    row_i = int(t*.8) % 3
    label, col = categories[row_i]
    # Three side-by-side live processors.
    specs = [
        (55, "LABEL", CYAN),
        (455, "ONE-HOT", GREEN),
        (855, "ORDINAL", YELLOW),
    ]
    for x, title, accent in specs:
        panel(canvas, x, 265, 360, 300, accent)
        text(canvas, x+180, 300, title, 19, accent, "bold")
        # Circular encoder chamber rotates its orbiting dots.
        cx, cy = x+180, 390
        for j in range(8):
            a = t*1.1+j*math.tau/8
            circle(canvas, cx+math.cos(a)*48, cy+math.sin(a)*34, 3, accent)
        circle(canvas, cx, cy, 33, smooth_color(WHITE, accent, .10), outline=accent, width=2)
    # Label representation
    value = row_i
    text(canvas, 235, 458, f"{label}  →  {value}", 20, CYAN, "bold")
    # One-hot representation
    bits = [1 if j == row_i else 0 for j in range(3)]
    for j, bit in enumerate(bits):
        bit_box(canvas, 535+j*82, 460, bit, categories[j][1], bit == 1, size=48)
    # Ordinal mapping
    text(canvas, 1035, 458, f"{label}  →  {row_i+1}", 20, YELLOW, "bold")
    text(canvas, 640, 610, "Same category, different representation. Choose based on feature semantics.", 16, INK, "bold")


def scene_pitfalls(canvas, t):
    """Wrong mapping gets visually caught by an animated warning scanner."""
    text(canvas, 640, 237, "A CONVENIENT NUMBER IS NOT ALWAYS A MEANINGFUL NUMBER", 17, MUTED, "bold")
    # Fake city rank meter.
    panel(canvas, 72, 275, 520, 260, RED, PALE_RED)
    text(canvas, 112, 307, "BAD IDEA: CITIES AS RANKS", 16, RED, "bold", "w")
    cities = [("Delhi", 0, CYAN), ("Mumbai", 1, PURPLE), ("Jaipur", 2, PINK)]
    for i, (city, n, col) in enumerate(cities):
        y = 360+i*52
        label_chip(canvas, 180, y, city, col, 125, 40)
        rounded(canvas, 300, y-18, 354+n*70, y+18, smooth_color(WHITE, RED, .10), RED, 8, 1)
        text(canvas, 329+n*35, y, str(n), 15, RED, "bold")
    scan_y = 340+(t*90 % 155)
    line(canvas, 105, scan_y, 550, scan_y, fill=RED, width=3)
    text(canvas, 330, 500, "There is no city order!", 16, RED, "bold")
    # Correct practices
    panel(canvas, 650, 275, 558, 260, GREEN, PALE_GREEN)
    text(canvas, 690, 307, "BETTER PRACTICE", 16, GREEN, "bold", "w")
    practices = [
        "Use one-hot for nominal input categories",
        "Use ordinal only when ranking is real",
        "Fit preprocessing on training data only",
        "Plan for unseen categories at inference",
    ]
    for i, item in enumerate(practices):
        y = 360+i*43
        # checks animate one by one
        done = t > i*1.3
        circle(canvas, 690, y, 11, GREEN if done else "#DAE4EE")
        if done:
            line(canvas, 684, y, 689, y+5, fill=WHITE, width=2)
            line(canvas, 689, y+5, 698, y-6, fill=WHITE, width=2)
        text(canvas, 715, y, item, 14, INK, "normal", "w")


def scene_recap(canvas, t):
    """Closing sequence: streams converge to the three final encoding examples."""
    # Three glowing streams flow into their representations.
    center_y = [330, 435, 540]
    info = [
        ("LABEL", "Delhi → 0", CYAN),
        ("ONE-HOT", "Delhi → [1, 0, 0]", GREEN),
        ("ORDINAL", "Small < Medium < Large", YELLOW),
    ]
    for i, (name, example, col) in enumerate(info):
        y = center_y[i]
        # Flowing small dots from the left into final mapping.
        for k in range(12):
            u = (t*1.4+k/12) % 1
            x = 80+u*570
            yy = y+math.sin(u*math.tau+t*1.7+i)*8
            circle(canvas, x, yy, 3+(k%2), col)
        arrow(canvas, 655, y, 735, y, col, 3)
        panel(canvas, 755, y-34, 420, 68, col)
        pill(canvas, 775, y-15, name, col, size=11)
        text(canvas, 1015, y, example, 17, INK, "bold")
    text(canvas, 640, 615, "Nominal has no rank  •  Ordinal has a real rank  •  Keep preprocessing consistent",
         15, GREEN, "bold")


SCENE_DRAWERS = [
    scene_open,
    scene_problem,
    scene_label,
    scene_label_motion,
    scene_onehot,
    scene_onehot_motion,
    scene_ordinal,
    scene_compare,
    scene_pitfalls,
    scene_recap,
]


class FeatureEncodingMotionLab:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Feature Encoding Motion Lab | 60 FPS | 3 Minutes")
        self.root.geometry(f"{W}x{H}")
        self.root.minsize(960, 540)
        self.root.configure(bg=BG)

        self.canvas = tk.Canvas(self.root, width=W, height=H, bg=BG,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.elapsed = 0.0
        self.scene_idx = 0
        self.scene_t = 0.0
        self.paused = False
        self.running = True
        self.last_clock = time.perf_counter()
        self.frame_count = 0
        self.fps_clock = time.perf_counter()
        self.measured_fps = 0.0
        self._resize_after = None

        self.root.bind("<space>", self.toggle_pause)
        self.root.bind("<Right>", self.skip_scene)
        self.root.bind("<Left>", self.restart_scene)
        self.root.bind("<r>", self.restart_all)
        self.root.bind("<R>", self.restart_all)
        self.root.bind("<Escape>", self.close)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.tick()

    def locate_scene(self, elapsed):
        cursor = 0.0
        for i, (_, duration, _) in enumerate(CHAPTERS):
            if elapsed < cursor+duration or i == len(CHAPTERS)-1:
                return i, elapsed-cursor
            cursor += duration
        return len(CHAPTERS)-1, 0.0

    def toggle_pause(self, _event=None):
        self.paused = not self.paused
        self.last_clock = time.perf_counter()

    def skip_scene(self, _event=None):
        next_i = (self.scene_idx+1) % len(CHAPTERS)
        self.elapsed = sum(x[1] for x in CHAPTERS[:next_i])
        self.scene_idx, self.scene_t = self.locate_scene(self.elapsed)

    def restart_scene(self, _event=None):
        self.elapsed = sum(x[1] for x in CHAPTERS[:self.scene_idx])
        self.scene_idx, self.scene_t = self.locate_scene(self.elapsed)

    def restart_all(self, _event=None):
        self.elapsed = 0.0
        self.scene_idx = 0
        self.scene_t = 0.0

    def close(self, _event=None):
        self.running = False
        self.root.destroy()

    def render(self):
        # Canvas is recreated every frame, but the number of vector primitives
        # remains modest; no bitmap rendering or heavy framework redraw is used.
        self.canvas.delete("all")
        # Calculate scale so the design remains proportional in a resized window.
        screen_w = max(1, self.canvas.winfo_width())
        screen_h = max(1, self.canvas.winfo_height())
        scale = min(screen_w/W, screen_h/H)
        ox = (screen_w-W*scale)/2
        oy = (screen_h-H*scale)/2

        # Draw to virtual coordinates by temporarily scaling coordinates through
        # a transform wrapper isn't practical for Canvas; create at base size and
        # scale all canvas items after drawing.
        draw_background(self.canvas, self.elapsed)
        SCENE_DRAWERS[self.scene_idx](self.canvas, self.scene_t)
        draw_header(self.canvas, self.scene_idx, self.elapsed, self.scene_t, self.paused)
        draw_footer(self.canvas, self.scene_idx, self.paused)
        if scale != 1.0 or ox or oy:
            self.canvas.scale("all", 0, 0, scale, scale)
            # Canvas items are scaled about origin. Letterboxing is handled by
            # moving all created elements into the centered viewport.
            if ox or oy:
                self.canvas.move("all", ox, oy)

        # Show measured FPS in a small unobtrusive badge.
        pill(self.canvas, max(14, screen_w-135), max(25, 28), f"{self.measured_fps:.0f} FPS",
             GREEN if self.measured_fps >= 52 else YELLOW, size=9)

    def tick(self):
        if not self.running:
            return
        now = time.perf_counter()
        dt = min(now-self.last_clock, 0.05)
        self.last_clock = now
        if not self.paused:
            self.elapsed += dt
            if self.elapsed >= TOTAL_TIME:
                self.elapsed = 0.0
            self.scene_idx, self.scene_t = self.locate_scene(self.elapsed)

        self.frame_count += 1
        span = now-self.fps_clock
        if span >= 0.5:
            self.measured_fps = self.frame_count/span
            self.frame_count = 0
            self.fps_clock = now

        self.render()
        self.root.after(FRAME_MS, self.tick)

    def run(self):
        self.root.mainloop()


def main():
    app = FeatureEncodingMotionLab()
    app.run()


if __name__ == "__main__":
    main()
