"""Render a bowl of mie ayam whose noodles get lifted by floating chopsticks, as a looping,
theme-aware animated ASCII SVG (asset/mieayam.svg). Usage: python mieayam.py <out.svg>
"""

import math
import sys

COLS, ROWS, FRAMES, SECONDS = 48, 26, 40, 4.0
CHAR_W, LINE_H = 7.2, 12  # 12px monospace
CX, RIM, RX, RY, DEPTH = 22, 15, 19, 2, 8  # bowl centre column, rim row, rim radii, bowl depth in rows
SHADES = ".:-=+*#%@"


class Grid:
    def __init__(self):
        self.cells = [[" "] * COLS for _ in range(ROWS)]

    def put(self, x, y, ch, over=True):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < COLS and 0 <= y < ROWS and (over or self.cells[y][x] == " "):
            self.cells[y][x] = ch

    def lines(self):
        return ["".join(r).rstrip() for r in self.cells]


def bowl(g):
    for y in range(RIM + 1, RIM + DEPTH):  # body: half ellipse, lit from the upper left
        half = RX * math.sqrt(max(0.0, 1 - ((y - RIM) / DEPTH) ** 2))
        for x in range(int(CX - half), int(CX + half) + 1):
            u = (x - CX) / RX
            lum = 0.75 - 0.55 * u - 0.35 * (y - RIM) / DEPTH
            g.put(x, y, SHADES[max(0, min(len(SHADES) - 1, int(lum * len(SHADES))))])
    g.put(CX - 4, RIM + DEPTH, "\\")  # foot ring
    g.put(CX + 4, RIM + DEPTH, "/")
    for x in range(CX - 3, CX + 4):
        g.put(x, RIM + DEPTH, "_")
    for x in range(CX - RX + 2, CX + RX - 1):  # back rim; the front lip is the broth's edge
        g.put(x, RIM - RY * math.sqrt(max(0.0, 1 - ((x - CX) / RX) ** 2)) * 0.95, "_")
    g.put(CX - RX, RIM, "(")
    g.put(CX + RX, RIM, ")")


def broth(g, t):
    toppings = {(-11, 0): "#", (-9, 0): "#", (-6, 1): "%", (8, -1): "#", (10, 0): "%", (12, 1): "#",
                (-13, 1): "v", (5, 1): "v", (14, -1): "v", (-3, -1): "o", (2, 1): "o"}  # chicken, greens, onion
    for y in range(RIM - RY + 1, RIM + 1):
        half = (RX - 2) * math.sqrt(max(0.0, 1 - ((y - RIM) / RY) ** 2))
        for x in range(int(CX - half), int(CX + half) + 1):
            ch = toppings.get((x - CX, y - RIM)) or ("~" if (x + y + int(t * 8)) % 3 else "-")
            g.put(x, y, ch)


def noodles_and_chopsticks(g, t):
    lift = 0.5 - 0.5 * math.cos(2 * math.pi * t)  # 0 (resting) .. 1 (fully lifted)
    px, py = CX + 2, RIM - 3 - lift * 8  # where the chopsticks pinch the noodles
    for i in range(5):  # strands hanging from the pinch down into the broth
        top = px + (i - 2) * 0.6
        bottom = CX - 4 + i * 2.5
        rows = RIM - 1 - py
        for k in range(1, int(rows) + 1):
            f = k / rows
            sway = math.sin(k * 0.9 + 2 * math.pi * t * 2 + i) * 0.9 * f
            x = top + (bottom - top) * f + sway
            slope = math.cos(k * 0.9 + 2 * math.pi * t * 2 + i)
            g.put(x, py + k, "(" if slope > 0.4 else ")" if slope < -0.4 else "|")
    for dy, slope in ((0, 0.5), (1, 0.38)):  # two chopsticks, slightly apart, reaching up to the right
        for c in range(1, 24):
            g.put(px + c, py + dy - c * slope, "/")


def steam(g, t):
    for i, x0 in enumerate((CX - 12, CX - 7, CX - 2)):
        for k in range(4):
            phase = (t * 2 + i * 0.33 + k * 0.25) % 1
            y = RIM - 3 - phase * 9
            x = x0 + math.sin((phase * 2 + i) * math.pi) * 1.5
            g.put(x, y, "(" if math.cos((phase * 2 + i) * math.pi) > 0 else ")", over=False)


def frame(n):
    t = n / FRAMES
    g = Grid()
    bowl(g)
    broth(g, t)
    noodles_and_chopsticks(g, t)
    steam(g, t)
    return g.lines()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render():
    w, h = int(COLS * CHAR_W) + 8, ROWS * LINE_H + 8
    step = 100 / FRAMES
    css = f"""
text {{ font: 12px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; fill: #59636e; white-space: pre; }}
@media (prefers-color-scheme: dark) {{ text {{ fill: #9198a1; }} }}
g {{ visibility: hidden; animation: f {SECONDS}s steps(1) infinite; }}
@keyframes f {{ 0% {{ visibility: visible; }} {step:.4f}% {{ visibility: hidden; }} }}
"""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           f"<style>{css}</style>"]
    for n in range(FRAMES):
        out.append(f'<g style="animation-delay:{SECONDS * n / FRAMES - SECONDS:.3f}s">')
        for r, line in enumerate(frame(n)):
            if line:
                out.append(f'<text x="4" y="{4 + (r + 1) * LINE_H - 2}" xml:space="preserve">{esc(line)}</text>')
        out.append("</g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    svg = render()
    assert svg.count("<g ") == FRAMES, "frames missing"
    with open(sys.argv[1], "w") as f:
        f.write(svg)
