#!/usr/bin/env python3
"""news-image-20261120: "The World Today" — the world news of Friday
20 November 2026, summed up in one image.

A pure-standard-library Python program. It draws a newspaper front page
(masthead, lead story, the day in numbers, a markets chart, three-column
news rows and an around-the-world briefs band) with its own vector stroke
font, and writes the result as a PNG to /output/entry.png (or to
$MAKEFUN_OUTPUT_DIR/entry.png outside the grader). No network, no files
read, fully deterministic: two runs write the same bytes.
"""

import os
import struct
import zlib
from math import ceil, hypot

W = H = 1024

# ---------------------------------------------------------------- PNG out

def png_bytes(w, h, rgb):
    """Encode an RGB bytearray (w*h*3) as a PNG, filter 0 per row."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))

# ---------------------------------------------------------------- canvas

PAPER = (247, 243, 233)
INK = (26, 23, 18)
RED = (178, 40, 30)
BLUE = (30, 74, 118)
GREEN = (30, 116, 66)
SLATE = (96, 92, 84)
BOXBG = (238, 232, 218)
HAIR = (196, 189, 172)


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def blend(self, x, y, color, a):
        if a <= 0.0 or x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        i = (y * self.w + x) * 3
        if a >= 1.0:
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]
        else:
            ia = 1.0 - a
            self.px[i] = int(self.px[i] * ia + color[0] * a + 0.5)
            self.px[i + 1] = int(self.px[i + 1] * ia + color[1] * a + 0.5)
            self.px[i + 2] = int(self.px[i + 2] * ia + color[2] * a + 0.5)

    def fill_rect(self, x0, y0, x1, y1, color):
        x0, y0 = max(0, int(round(x0))), max(0, int(round(y0)))
        x1, y1 = min(self.w, int(round(x1))), min(self.h, int(round(y1)))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        n = len(row)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + n] = row

    def seg(self, x1, y1, x2, y2, color, width):
        """Anti-aliased thick line segment."""
        hw = width / 2.0
        pad = hw + 1.0
        xa = int(min(x1, x2) - pad)
        xb = int(max(x1, x2) + pad)
        ya = int(min(y1, y2) - pad)
        yb = int(max(y1, y2) + pad)
        dx, dy = x2 - x1, y2 - y1
        len2 = dx * dx + dy * dy
        for y in range(ya, yb + 1):
            for x in range(xa, xb + 1):
                if len2 == 0.0:
                    d = hypot(x - x1, y - y1)
                else:
                    t = ((x - x1) * dx + (y - y1) * dy) / len2
                    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
                    d = hypot(x - (x1 + t * dx), y - (y1 + t * dy))
                cov = hw + 0.6 - d
                if cov > 0.0:
                    self.blend(x, y, color, 1.0 if cov >= 1.0 else cov)

    def circle(self, cx, cy, r, color, width=None):
        """Filled disc if width is None, else an outline ring."""
        pad = (width / 2.0 if width else 0.0) + 1.0
        xa, xb = int(cx - r - pad), int(cx + r + pad)
        ya, yb = int(cy - r - pad), int(cy + r + pad)
        for y in range(ya, yb + 1):
            for x in range(xa, xb + 1):
                d = hypot(x - cx, y - cy)
                if width is None:
                    cov = r + 0.6 - d
                else:
                    cov = width / 2.0 + 0.6 - abs(d - r)
                if cov > 0.0:
                    self.blend(x, y, color, 1.0 if cov >= 1.0 else cov)

    def polyline(self, pts, color, width, close=False):
        n = len(pts)
        rng = range(n) if close else range(n - 1)
        for i in rng:
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            self.seg(x1, y1, x2, y2, color, width)

# ---------------------------------------------------------------- font
# A single-stroke vector font drawn by this program. Glyphs live on a grid
# where cap height is 7 units, x-height 5, descenders reach -2.5. Each glyph
# is (advance, path); a path is M/L/Q commands (move / line / quadratic).

GLYPHS = {
    ' ': (2.6, ''),
    'A': (5.6, 'M0,0 L2.8,7 L5.6,0 M1.05,2.5 L4.55,2.5'),
    'B': (5.2, 'M0,0 L0,7 M0,7 L2.7,7 Q4.6,7 4.6,5.3 Q4.6,3.7 2.7,3.7 L0,3.7 '
               'M2.7,3.7 Q4.9,3.7 4.9,1.9 Q4.9,0 2.9,0 L0,0'),
    'C': (5.4, 'M4.9,5.6 Q4,7 2.7,7 Q0.5,7 0.5,3.5 Q0.5,0 2.7,0 Q4,0 4.9,1.4'),
    'D': (5.4, 'M0,0 L0,7 M0,7 L2.5,7 Q5.2,7 5.2,3.5 Q5.2,0 2.5,0 L0,0'),
    'E': (4.8, 'M4.6,7 L0,7 L0,0 L4.6,0 M0,3.7 L3.6,3.7'),
    'F': (4.6, 'M4.6,7 L0,7 L0,0 M0,3.7 L3.4,3.7'),
    'G': (5.6, 'M5,5.6 Q4.1,7 2.8,7 Q0.5,7 0.5,3.5 Q0.5,0 2.8,0 Q4.6,0 5.3,1.6 '
               'L5.3,3.2 L3.2,3.2'),
    'H': (5.6, 'M0,0 L0,7 M5.6,0 L5.6,7 M0,3.7 L5.6,3.7'),
    'I': (2.4, 'M0.2,0 L2.2,0 M1.2,0 L1.2,7 M0.2,7 L2.2,7'),
    'J': (4.4, 'M4.2,7 L4.2,1.6 Q4.2,0 2.6,0 Q1.2,0 0.6,1.2'),
    'K': (5.4, 'M0,0 L0,7 M4.9,7 L0.9,3.4 M1.8,2.8 L5.2,0'),
    'L': (4.6, 'M0,7 L0,0 L4.6,0'),
    'M': (6.6, 'M0,0 L0,7 L3.3,2.6 L6.6,7 L6.6,0'),
    'N': (5.8, 'M0,0 L0,7 L5.8,0 L5.8,7'),
    'O': (5.8, 'M2.9,0 Q0.4,0 0.4,3.5 Q0.4,7 2.9,7 Q5.4,7 5.4,3.5 Q5.4,0 2.9,0'),
    'P': (5.0, 'M0,0 L0,7 M0,7 L2.8,7 Q4.9,7 4.9,5.2 Q4.9,3.5 2.8,3.5 L0,3.5'),
    'Q': (5.8, 'M2.9,0 Q0.4,0 0.4,3.5 Q0.4,7 2.9,7 Q5.4,7 5.4,3.5 Q5.4,0 2.9,0 '
               'M3.4,1.6 L5.6,-0.6'),
    'R': (5.2, 'M0,0 L0,7 M0,7 L2.8,7 Q4.9,7 4.9,5.2 Q4.9,3.5 2.8,3.5 L0,3.5 '
               'M2.9,3.5 L5.1,0'),
    'S': (5.0, 'M4.6,6.2 Q3.9,7 2.7,7 Q0.8,7 0.7,5.6 Q0.6,4.4 2.6,3.8 Q4.5,3.2 '
               '4.5,1.7 Q4.5,0 2.5,0 Q1.2,0 0.4,0.9'),
    'T': (5.4, 'M0,7 L5.4,7 M2.7,7 L2.7,0'),
    'U': (5.6, 'M0,7 L0,1.8 Q0,0 2.8,0 Q5.6,0 5.6,1.8 L5.6,7'),
    'V': (5.6, 'M0,7 L2.8,0 L5.6,7'),
    'W': (7.4, 'M0,7 L1.7,0 L3.7,5.4 L5.7,0 L7.4,7'),
    'X': (5.4, 'M0,0 L5.4,7 M0,7 L5.4,0'),
    'Y': (5.4, 'M0,7 L2.7,3.6 L5.4,7 M2.7,3.6 L2.7,0'),
    'Z': (5.2, 'M0.3,7 L4.9,7 L0.3,0 L4.9,0'),
    'a': (4.6, 'M4.2,5 L4.2,0 M4.2,2.5 Q4.2,5 2.3,5 Q0.5,5 0.5,2.5 Q0.5,0 2.3,0 '
               'Q4.2,0 4.2,2.5'),
    'b': (4.8, 'M0.4,7 L0.4,0 M0.4,2.5 Q0.4,5 2.5,5 Q4.5,5 4.5,2.5 Q4.5,0 2.5,0 '
               'Q0.4,0 0.4,2.5'),
    'c': (4.4, 'M4.1,4 Q3.5,5 2.3,5 Q0.5,5 0.5,2.5 Q0.5,0 2.3,0 Q3.5,0 4.1,1'),
    'd': (4.8, 'M4.4,7 L4.4,0 M4.4,2.5 Q4.4,5 2.4,5 Q0.4,5 0.4,2.5 Q0.4,0 2.4,0 '
               'Q4.4,0 4.4,2.5'),
    'e': (4.6, 'M0.6,2.9 L4.4,2.9 Q4.4,5 2.4,5 Q0.5,5 0.5,2.5 Q0.5,0 2.5,0 '
               'Q3.6,0 4.2,0.9'),
    'f': (3.0, 'M2.9,6.9 Q1.8,7.3 1.4,6.4 Q1.2,5.9 1.2,5 L1.2,0 M0.2,5 L2.8,5'),
    'g': (4.8, 'M4.4,5 L4.4,-1 Q4.4,-2.4 2.6,-2.4 Q1.4,-2.4 0.9,-1.6 M4.4,2.5 '
               'Q4.4,5 2.4,5 Q0.4,5 0.4,2.5 Q0.4,0 2.4,0 Q4.4,0 4.4,2.5'),
    'h': (4.8, 'M0.4,7 L0.4,0 M0.4,2.6 Q0.6,5 2.6,5 Q4.5,5 4.5,2.8 L4.5,0'),
    'i': (2.0, 'M1,0 L1,5 M1,6.5 L1,6.62'),
    'j': (2.4, 'M1.9,5 L1.9,-0.9 Q1.9,-2.4 0.7,-2.4 M1.9,6.5 L1.9,6.62'),
    'k': (4.6, 'M0.4,7 L0.4,0 M4.2,5 L1.2,2.2 M2,1.7 L4.5,0'),
    'l': (2.0, 'M1,7 L1,0'),
    'm': (8.2, 'M0.4,0 L0.4,5 M0.4,2.7 Q0.6,5 2.4,5 Q4.1,5 4.1,2.8 L4.1,0 '
               'M4.1,2.7 Q4.3,5 6,5 Q7.6,5 7.6,2.8 L7.6,0'),
    'n': (4.8, 'M0.4,0 L0.4,5 M0.4,2.6 Q0.6,5 2.6,5 Q4.5,5 4.5,2.8 L4.5,0'),
    'o': (4.8, 'M2.4,0 Q0.4,0 0.4,2.5 Q0.4,5 2.4,5 Q4.4,5 4.4,2.5 Q4.4,0 2.4,0'),
    'p': (4.8, 'M0.4,5 L0.4,-2.4 M0.4,2.5 Q0.4,5 2.5,5 Q4.5,5 4.5,2.5 Q4.5,0 2.5,0 '
               'Q0.4,0 0.4,2.5'),
    'q': (4.8, 'M4.4,5 L4.4,-2.4 M4.4,2.5 Q4.4,5 2.4,5 Q0.4,5 0.4,2.5 Q0.4,0 2.4,0 '
               'Q4.4,0 4.4,2.5'),
    'r': (3.4, 'M0.4,0 L0.4,5 M0.4,2.8 Q0.7,5 2.6,5 Q3.2,5 3.6,4.7'),
    's': (4.2, 'M3.9,4.2 Q3.4,5 2.2,5 Q0.7,5 0.7,3.9 Q0.7,3 2.2,2.6 Q3.8,2.2 '
               '3.8,1.1 Q3.8,0 2.1,0 Q1,0 0.4,0.8'),
    't': (3.2, 'M1.6,7 L1.6,1.2 Q1.6,0 2.9,0 M0.3,5 L3.1,5'),
    'u': (4.8, 'M0.4,5 L0.4,1.6 Q0.4,0 2.4,0 Q4.4,0 4.4,1.8 M4.4,5 L4.4,0'),
    'v': (4.6, 'M0.2,5 L2.3,0 L4.4,5'),
    'w': (6.6, 'M0.2,5 L1.5,0 L3.3,4.2 L5.1,0 L6.4,5'),
    'x': (4.4, 'M0.3,0 L4.1,5 M0.3,5 L4.1,0'),
    'y': (4.6, 'M0.2,5 L2.3,0.6 L4.4,5 M2.3,0.6 L1.9,-1.4 Q1.7,-2.4 0.6,-2.4'),
    'z': (4.4, 'M0.4,5 L4,5 L0.4,0 L4,0'),
    '0': (5.0, 'M2.5,0 Q0.4,0 0.4,3.5 Q0.4,7 2.5,7 Q4.6,7 4.6,3.5 Q4.6,0 2.5,0'),
    '1': (4.6, 'M1.2,5.2 L2.9,7 L2.9,0 M1.2,0 L4.4,0'),
    '2': (5.0, 'M0.5,5.4 Q0.5,7 2.5,7 Q4.5,7 4.5,5.2 Q4.5,3.4 0.5,0 L4.7,0'),
    '3': (5.0, 'M0.6,6.5 Q3,7.4 4.1,6 Q4.9,5 3.6,4 Q5,3.2 4.5,1.6 Q4,0 2.3,0 '
               'Q1.2,0 0.5,0.6'),
    '4': (5.2, 'M3.4,0 L3.4,7 L0.4,2.6 L5,2.6'),
    '5': (5.0, 'M4.4,7 L1,7 L0.8,4.3 Q2.2,4.9 3.4,4.3 Q4.7,3.7 4.4,1.8 Q4.1,0.1 '
               '2.4,0 Q1.2,0 0.5,0.7'),
    '6': (5.0, 'M4.3,6.3 Q3,7.2 1.9,6.2 Q0.4,4.8 0.5,2.4 Q0.6,0.3 2.5,0 Q4.4,0.3 '
               '4.5,2.1 Q4.5,3.9 2.7,4 Q1.4,4 0.6,2.9'),
    '7': (5.0, 'M0.5,7 L4.7,7 L2.2,0'),
    '8': (5.0, 'M2.5,3.9 Q0.8,3.6 0.9,1.9 Q1,0.2 2.5,0 Q4,0.2 4.1,1.9 Q4.2,3.6 '
               '2.5,3.9 Q1.1,4.2 1.2,5.5 Q1.3,6.8 2.5,7 Q3.7,6.8 3.8,5.5 Q3.9,4.2 '
               '2.5,3.9'),
    '9': (5.0, 'M0.7,0.7 Q2,0 3.1,0.8 Q4.6,2.2 4.5,4.6 Q4.4,6.7 2.5,7 Q0.6,6.7 '
               '0.5,4.9 Q0.5,3.1 2.3,3 Q3.6,3 4.4,4.1'),
    '.': (2.0, 'M1,0.1 L1,0.22'),
    ',': (2.0, 'M1.1,0.4 L0.7,-0.9'),
    '!': (2.0, 'M1,5 L1,1.4 M1,0.1 L1,0.22'),
    '?': (4.6, 'M0.6,4 Q0.8,5 2.3,5 Q3.9,5 3.9,3.8 Q3.9,2.7 2.4,2.2 Q1.9,2 1.9,1.2 '
               'M1.9,0.1 L1.9,0.22'),
    ':': (2.0, 'M1,3.4 L1,3.52 M1,0.1 L1,0.22'),
    ';': (2.0, 'M1,3.4 L1,3.52 M1.1,0.4 L0.7,-0.9'),
    '-': (3.4, 'M0.3,2.5 L3.1,2.5'),
    '–': (4.4, 'M0.3,2.5 L4.1,2.5'),
    '—': (6.0, 'M0.2,2.5 L5.8,2.5'),
    "'": (1.8, 'M0.9,7 L0.7,5.6'),
    '"': (2.8, 'M0.7,7 L0.5,5.6 M2.1,7 L1.9,5.6'),
    '(': (3.0, 'M2.3,7.2 Q0.7,5 0.7,3.6 Q0.7,2.2 2.3,-0.2'),
    ')': (3.0, 'M0.6,7.2 Q2.2,5 2.2,3.6 Q2.2,2.2 0.6,-0.2'),
    '/': (3.0, 'M0.2,0 L2.8,7'),
    '%': (6.6, 'M0.4,0 L6.2,7 M1.4,4.9 Q0.3,4.9 0.3,6 Q0.3,7.1 1.4,7.1 Q2.5,7.1 '
               '2.5,6 Q2.5,4.9 1.4,4.9 M5.2,-0.1 Q4.1,-0.1 4.1,1 Q4.1,2.1 5.2,2.1 '
               'Q6.3,2.1 6.3,1 Q6.3,-0.1 5.2,-0.1'),
    '$': (5.0, 'M2.5,7.6 L2.5,-0.6 M4.4,6.2 Q3.8,7 2.6,7 Q0.9,7 0.8,5.7 Q0.7,4.7 '
               '2.6,4.1 Q4.4,3.5 4.4,2 Q4.4,0.3 2.5,0.3 Q1.3,0.3 0.5,1.1'),
    '+': (4.6, 'M0.5,2.5 L4.1,2.5 M2.3,0.7 L2.3,4.3'),
    '=': (4.6, 'M0.5,3.4 L4.1,3.4 M0.5,1.6 L4.1,1.6'),
    '·': (2.0, 'M1,2.5 L1,2.62'),
    '#': (5.2, 'M1.6,0 L2.2,7 M3.6,0 L4.2,7 M0.4,2.4 L5.2,2.4 M0.6,4.6 L5.4,4.6'),
    '&': (5.8, 'M4.9,6.6 Q4.2,7.2 3.2,6.9 Q2,6.5 2.2,5.3 Q2.4,4.3 3.6,3.9 '
               'Q4.9,3.4 4.7,2.1 Q4.5,0.7 3,0.2 Q1.3,-0.3 0.8,1 Q0.3,2.4 1.8,4 '
               'Q3.2,5.4 4.9,6.6 M1.8,4 L5.3,0.3'),
    '°': (2.6, 'M1.3,5.6 Q0.5,5.6 0.5,6.4 Q0.5,7.2 1.3,7.2 Q2.1,7.2 2.1,6.4 '
               'Q2.1,5.6 1.3,5.6'),
}

import re
_TOKEN = re.compile(r'[MLQ]|-?\d+(?:\.\d+)?')


def _parse(path):
    """Parse a glyph path into a list of polylines (tuples of points)."""
    toks = _TOKEN.findall(path)
    strokes = []
    cur = None
    i = 0
    while i < len(toks):
        cmd = toks[i]
        if cmd == 'M':
            cur = [(float(toks[i + 1]), float(toks[i + 2]))]
            strokes.append(cur)
            i += 3
        elif cmd == 'L':
            cur.append((float(toks[i + 1]), float(toks[i + 2])))
            i += 3
        elif cmd == 'Q':
            cx, cy = float(toks[i + 1]), float(toks[i + 2])
            ex, ey = float(toks[i + 3]), float(toks[i + 4])
            x0, y0 = cur[-1]
            for k in range(1, 8):
                t = k / 7.0
                mt = 1.0 - t
                cur.append((mt * mt * x0 + 2 * mt * t * cx + t * t * ex,
                            mt * mt * y0 + 2 * mt * t * cy + t * t * ey))
            i += 5
        else:  # bare numbers continue the current command as lines
            cur.append((float(toks[i]), float(toks[i + 1])))
            i += 2
    return strokes


_PARSED = {ch: (adv, _parse(p)) for ch, (adv, p) in GLYPHS.items()}

_SANITIZE = {
    '−': '-', '–': '–', '—': '—', '‘': "'", '’': "'",
    '“': '"', '”': '"', '…': '...', ' ': ' ',
}


def sanitize(text):
    return ''.join(_SANITIZE.get(c, c) for c in text)


def _seg_cover(mask, mw, mh, x1, y1, x2, y2, hw):
    pad = hw + 1.0
    xa = max(0, int(min(x1, x2) - pad))
    xb = min(mw - 1, int(max(x1, x2) + pad))
    ya = max(0, int(min(y1, y2) - pad))
    yb = min(mh - 1, int(max(y1, y2) + pad))
    dx, dy = x2 - x1, y2 - y1
    len2 = dx * dx + dy * dy
    for y in range(ya, yb + 1):
        row = y * mw
        for x in range(xa, xb + 1):
            if len2 == 0.0:
                d = hypot(x - x1, y - y1)
            else:
                t = ((x - x1) * dx + (y - y1) * dy) / len2
                t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
                d = hypot(x - (x1 + t * dx), y - (y1 + t * dy))
            cov = hw + 0.6 - d
            if cov > 0.0:
                idx = row + x
                v = 255 if cov >= 1.0 else int(cov * 255)
                if v > mask[idx]:
                    mask[idx] = v


_mask_cache = {}


def glyph_mask(ch, size, weight):
    """Coverage mask for one glyph: (pixels, mw, mh, ox, oy) where pixels is
    a list of (index, alpha) and (ox, oy) is the glyph origin in mask px."""
    key = (ch, round(size * 2), round(weight * 4))
    hit = _mask_cache.get(key)
    if hit is not None:
        return hit
    adv, strokes = _PARSED.get(ch, _PARSED[' '])
    s = size / 7.0
    hw = weight / 2.0
    pad = hw + 1.5
    mw = int(ceil((adv + 0.9) * s + 2 * pad))
    mh = int(ceil(10.9 * s + 2 * pad))
    ox = pad + 0.45 * s
    oy = pad + 7.9 * s
    mask = bytearray(mw * mh)
    for stroke in strokes:
        for i in range(len(stroke) - 1):
            x1, y1 = stroke[i]
            x2, y2 = stroke[i + 1]
            _seg_cover(mask, mw, mh, ox + x1 * s, oy - y1 * s,
                       ox + x2 * s, oy - y2 * s, hw)
    pixels = [(i, a) for i, a in enumerate(mask) if a]
    out = (pixels, mw, mh, ox, oy)
    _mask_cache[key] = out
    return out


def text_width(text, size, bold=False, tracking=0.0):
    s = size / 7.0
    w = 0.0
    for c in text:
        adv = _PARSED.get(c, _PARSED[' '])[0]
        w += adv * s + tracking
    return w - (tracking if text else 0.0)


def draw_text(cv, x, ybase, text, size, color, bold=False, tracking=0.0):
    """Draw one line; (x, ybase) is the pen start on the baseline."""
    text = sanitize(text)
    weight = size * (0.175 if bold else 0.115)
    s = size / 7.0
    pen = float(x)
    for c in text:
        adv = _PARSED.get(c, _PARSED[' '])[0]
        if c != ' ':
            pixels, mw, mh, ox, oy = glyph_mask(c, size, weight)
            bx = int(round(pen - ox))
            by = int(round(ybase - oy))
            for idx, a in pixels:
                px = bx + idx % mw
                py = by + idx // mw
                cv.blend(px, py, color, a / 255.0)
        pen += adv * s + tracking
    return pen - x


def draw_centered(cv, cx, ybase, text, size, color, bold=False, tracking=0.0):
    w = text_width(sanitize(text), size, bold, tracking)
    return draw_text(cv, cx - w / 2.0, ybase, text, size, color, bold, tracking)


def wrap_lines(text, size, bold, max_w, tracking=0.0):
    """Greedy word wrap; returns the list of lines."""
    text = sanitize(text)
    words = text.split(' ')
    lines = []
    cur = ''
    for wd in words:
        trial = wd if not cur else cur + ' ' + wd
        if text_width(trial, size, bold, tracking) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, ybase, text, size, color, max_w, bold=False,
              leading=1.35, tracking=0.0):
    """Wrapped paragraph; ybase is the first line's baseline.
    Returns the baseline of the last line drawn."""
    lines = wrap_lines(text, size, bold, max_w, tracking)
    lh = size * leading
    for i, ln in enumerate(lines):
        draw_text(cv, x, ybase + i * lh, ln, size, color, bold, tracking)
    return ybase + (len(lines) - 1) * lh if lines else ybase


def draw_runs(cv, x, ybase, runs, size, max_w, leading=1.35):
    """Wrapped rich text: runs is a list of (text, bold, color) tuples.
    Returns the baseline of the last line."""
    tokens = []  # (word, bold, color)
    for text, bold, color in runs:
        for wd in sanitize(text).split(' '):
            if wd:
                tokens.append((wd, bold, color))
    space_w = text_width(' ', size)
    lines = []
    cur = []
    cur_w = 0.0
    for tok in tokens:
        ww = text_width(tok[0], size, tok[1])
        add = ww if not cur else ww + space_w
        if cur and cur_w + add > max_w:
            lines.append(cur)
            cur, cur_w = [tok], ww
        else:
            cur.append(tok)
            cur_w += add
    if cur:
        lines.append(cur)
    lh = size * leading
    for li, line in enumerate(lines):
        pen = float(x)
        for wd, bold, color in line:
            draw_text(cv, pen, ybase + li * lh, wd, size, color, bold)
            pen += text_width(wd, size, bold) + space_w
    return ybase + (len(lines) - 1) * lh if lines else ybase

# ---------------------------------------------------------------- the page

def kicker(cv, x, ybase, text, color=RED):
    cv.fill_rect(x, ybase - 8, x + 7, ybase - 1, RED)
    draw_text(cv, x + 13, ybase, text, 11.5, color, bold=True, tracking=1.4)


def globe(cv, cx, cy, r):
    cv.circle(cx, cy, r, INK, width=2.2)
    for f in (0.42, 0.78):
        pts = []
        for i in range(41):
            t = 3.14159265 * 2 * i / 40
            from math import sin, cos
            pts.append((cx + r * f * sin(t), cy - r * cos(t)))
        cv.polyline(pts, INK, 1.1, close=True)
    for f in (-0.48, 0.0, 0.48):
        from math import sqrt
        hw = r * sqrt(1 - f * f)
        cv.seg(cx - hw, cy + f * r, cx + hw, cy + f * r, INK, 1.1)


def build():
    cv = Canvas(W, H, PAPER)
    M = 40            # margin
    R = W - M         # right edge (984)

    # --- top strip
    draw_text(cv, M, 32, "ONE DAY · ONE PAGE · THE WHOLE WORLD", 10.5,
              SLATE, bold=True, tracking=2.0)
    t = "FRIDAY EDITION"
    draw_text(cv, R - text_width(t, 10.5, True, 2.0), 32, t, 10.5,
              RED, bold=True, tracking=2.0)
    cv.fill_rect(M, 43, R, 45.5, INK)
    cv.fill_rect(M, 49, R, 50, HAIR)

    # --- masthead
    globe(cv, 76, 80, 27)
    draw_centered(cv, W / 2 + 18, 110, "THE WORLD TODAY", 57, INK,
                  bold=True, tracking=1.0)
    draw_text(cv, R - text_width("ALL THE NEWS", 11, True, 1.6), 76,
              "ALL THE NEWS", 11, SLATE, bold=True, tracking=1.6)
    draw_text(cv, R - text_width("OF ONE DAY", 11, True, 1.6), 94,
              "OF ONE DAY", 11, SLATE, bold=True, tracking=1.6)
    cv.fill_rect(M, 124, R, 127, INK)
    cv.fill_rect(M, 131, R, 132, INK)

    # --- date band
    cv.fill_rect(M, 140, R, 182, INK)
    draw_centered(cv, W / 2, 171, "FRIDAY · 20 NOVEMBER 2026", 24,
                  (247, 243, 233), bold=True, tracking=3.0)
    cv.fill_rect(M, 182, R, 185, RED)

    # --- ticker
    draw_text(cv, M, 205, "LATEST", 12, RED, bold=True, tracking=1.0)
    draw_text(cv, M + 62, 205,
              "Genocide ruling in The Hague · Missiles fall in Poland · "
              "Trump-Xi-Putin summit · Markets slide · COP31 drops fossil "
              "pledge", 11.5, INK)
    cv.fill_rect(M, 215, R, 216, HAIR)

    # --- lead story (left) and the day in numbers (right)
    cv.fill_rect(M, 226, M + 46, 229, RED)
    draw_text(cv, M, 248, "THE HAGUE · WORLD COURT JUDGMENT", 12, RED,
              bold=True, tracking=1.4)
    last = draw_para(cv, M, 290,
                     "Myanmar Committed Genocide Against Rohingya, "
                     "World Court Rules", 36, INK, 592, bold=True,
                     leading=1.39, tracking=0.3)
    draw_para(cv, M, last + 38,
              "The International Court of Justice ruled that Myanmar's "
              "security forces committed genocide against the Rohingya — "
              "the first time the world's court has held a state "
              "responsible for genocide. Judges ordered Myanmar to let "
              "the refugees return. Myanmar called the ruling unfair; "
              "rights groups urged sanctions, though the court cannot "
              "enforce its judgment.", 15, INK, 592, leading=1.45)

    bx0, bx1, by0, by1 = 660, R, 224, 540
    cv.fill_rect(bx0, by0, bx1, by1, BOXBG)
    cv.fill_rect(bx0, by0, bx1, by0 + 30, INK)
    draw_centered(cv, (bx0 + bx1) / 2, by0 + 21, "THE DAY IN NUMBERS",
                  13, (247, 243, 233), bold=True, tracking=1.8)
    stats = [
        ("-3.7%", "S&P 500: fifth straight fall, into correction", RED),
        ("-5.1%", "Nikkei 225 slide in Tokyo's AI sell-off", RED),
        ("6.7", "magnitude earthquake in central Peru", INK),
        ("34", "suspected gang members killed in Haiti", INK),
        ("$48.3bn", "US cost of the Iran war, Pentagon says", INK),
        ("8 yrs", "BepiColombo's voyage to Mercury", BLUE),
    ]
    ry = by0 + 30
    for i, (num, label, ncol) in enumerate(stats):
        if i:
            cv.fill_rect(bx0 + 12, ry, bx1 - 12, ry + 0.75, HAIR)
        nw = text_width(num, 19, True)
        draw_text(cv, bx0 + 112 - nw, ry + 31, num, 19, ncol, bold=True)
        draw_para(cv, bx0 + 124, ry + 19, label, 11.5, INK, bx1 - bx0 - 136,
                  leading=1.28)
        ry += 47.5
    for x in (bx0, bx1 - 1.5):
        cv.fill_rect(x, by0, x + 1.5, by1, INK)
    cv.fill_rect(bx0, by1 - 1.5, bx1, by1, INK)

    # --- row 2: three columns
    cv.fill_rect(M, 556, R, 557.5, INK)
    cols = [(M, 298), (362, 298), (684, 300)]
    for vx in (350, 672):
        cv.fill_rect(vx, 570, vx + 0.75, 770, HAIR)

    x, w = cols[0]
    kicker(cv, x, 580, "WAR IN EUROPE")
    last = draw_para(cv, x, 604, "Missiles From Russia Land in Poland",
                     20, INK, w, bold=True, leading=1.4)
    draw_para(cv, x, last + 24,
              "Two missiles and a suspected drone fell in Poland, which "
              "called it a deliberate provocation; NATO called it a grave "
              "violation of its airspace. That night, strikes on Kyiv "
              "killed eight, and France sought an urgent UN Security "
              "Council meeting.", 13, INK, w, leading=1.45)

    x, w = cols[1]
    kicker(cv, x, 580, "SHENZHEN SUMMIT")
    last = draw_para(cv, x, 604, "Trump, Xi, Putin: A First Three-Way "
                     "Summit", 20, INK, w, bold=True, leading=1.4)
    draw_para(cv, x, last + 24,
              "The three presidents signed a four-point peace declaration "
              "in Shenzhen. Europe's Chancellor Merz warned against a "
              "'new Yalta' settled without Europe, and the talks ended "
              "with few concrete results.", 13, INK, w, leading=1.45)

    x, w = cols[2]
    kicker(cv, x, 580, "MARKETS")
    last = draw_para(cv, x, 604, "AI Sell-Off Pushes Wall Street Into "
                     "Correction", 20, INK, w, bold=True, leading=1.4)
    chart = [("S&P 500", -3.7), ("Nikkei 225", -5.1), ("FTSE 100", -1.0),
             ("Sensex", 2.3), ("Gold", -3.9)]
    zero_x = x + 196
    top = last + 16
    cv.fill_rect(zero_x, top - 8, zero_x + 0.75, top + 5 * 15.5 - 4, HAIR)
    for i, (name, val) in enumerate(chart):
        by = top + i * 15.5
        draw_text(cv, x, by + 4, name, 11, INK, bold=True)
        bw = abs(val) * 11.0
        col = RED if val < 0 else GREEN
        if val < 0:
            cv.fill_rect(zero_x - bw, by - 3.5, zero_x, by + 5.5, col)
            vt = "-%s%%" % ("%.1f" % abs(val))
            draw_text(cv, zero_x - bw - 6 - text_width(vt, 11, True),
                      by + 4, vt, 11, col, bold=True)
        else:
            cv.fill_rect(zero_x, by - 3.5, zero_x + bw, by + 5.5, col)
            vt = "+%s%%" % ("%.1f" % val)
            draw_text(cv, zero_x + bw + 6, by + 4, vt, 11, col, bold=True)
    draw_para(cv, x, top + 5 * 15.5 + 14,
              "Gold fell nearly 4%; Bitcoin is down 24% in a month. "
              "Brent crude held near $90.", 12.5, INK, w, leading=1.35)

    # --- row 3: three columns
    cv.fill_rect(M, 780, R, 781.5, INK)
    for vx in (350, 672):
        cv.fill_rect(vx, 794, vx + 0.75, 924, HAIR)

    x, w = cols[0]
    kicker(cv, x, 802, "MIDDLE EAST")
    last = draw_para(cv, x, 826, "Houthi Missiles Damage Riyadh Tower",
                     18, INK, w, bold=True, leading=1.42)
    draw_para(cv, x, last + 22,
              "Missiles damaged the sovereign fund's tower in the "
              "financial district; Saudi defences downed more. Hormuz "
              "tanker attacks grew.", 12, INK, w, leading=1.4)

    x, w = cols[1]
    kicker(cv, x, 802, "CLIMATE · COP31")
    last = draw_para(cv, x, 826, "Climate Draft Drops Fossil-Fuel "
                     "Phase-Out", 18, INK, w, bold=True, leading=1.42)
    draw_para(cv, x, last + 22,
              "Negotiators in Antalya cut any call to end fossil fuels "
              "from the draft deal, angering island states. A 6.7 quake "
              "struck central Peru.", 12, INK, w, leading=1.4)

    x, w = cols[2]
    kicker(cv, x, 802, "SCIENCE & HEALTH")
    last = draw_para(cv, x, 826, "Mercury Reached After Eight-Year "
                     "Voyage", 18, INK, w, bold=True, leading=1.42)
    draw_para(cv, x, last + 22,
              "Europe and Japan's BepiColombo probe reached Mercury "
              "after eight years. The US lost measles elimination "
              "status; a cancer pill breakthrough.", 12, INK, w,
              leading=1.4)

    # --- around the world
    cv.fill_rect(M, 936, R, 937, HAIR)
    draw_text(cv, M, 958, "AROUND THE WORLD", 11.5, RED, bold=True,
              tracking=1.6)
    src = "SOURCES: REUTERS · PBS NEWSHOUR · SKY NEWS · AGENCIES"
    draw_text(cv, R - text_width(src, 9.5, True, 1.2), 958, src, 9.5,
              SLATE, bold=True, tracking=1.2)
    runs = [
        ("EUROPE  ", True, RED),
        ("UK-EU food, carbon and youth deals; Estonia shuts Russia "
         "crossings.  ", False, INK),
        ("AMERICAS  ", True, RED),
        ("Palisades arsonist convicted; Bolsonaro hospitalised.  ",
         False, INK),
        ("AFRICA  ", True, RED),
        ("Kenya Ebola over; Senegal capsize: dozens missing.  ",
         False, INK),
        ("ASIA  ", True, RED),
        ("Bangladesh violence; N. Korea enrichment grows.  ",
         False, INK),
        ("SPORT  ", True, RED),
        ("Price undisputed welterweight champion; Alcaraz unbeaten; "
         "Nicholls 113 not out.", False, INK),
    ]
    draw_runs(cv, M, 978, runs, 11, R - M, leading=1.41)
    return cv


def main():
    cv = build()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png_bytes(W, H, cv.px))


if __name__ == "__main__":
    main()
