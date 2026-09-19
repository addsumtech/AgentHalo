#!/usr/bin/env python3
"""Generate pixel "Q版" character themes for Clawd on Desk: Trump, Musk, Jensen.

Shared chibi body rig + per-character hair / skin / outfit / props / catchphrases.
Every state is an SVG with CSS @keyframes; no scripts (external themes are sanitized).
Usage: gen_themes.py [trump|musk|jensen ...]   (default: all)
"""
import os, sys, json
from portraits import PEOPLE, head as portrait_head

THEMES_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "themes")
VIEWBOX = "-15 -25 45 45"

WHITE, INK, RED, BLUE_TXT = "#FFFFFF", "#1E2A47", "#D62828", "#1F3C88"
PUPIL, MOUTH, MOUTH_DK, TEETH = "#1E2A47", "#B9483A", "#7A2A22", "#FFFFFF"
GRAY, GRAY_DK, SCREEN, SHOE = "#8A93A6", "#4A5468", "#BFE3FF", "#111111"
NV_GREEN = "#76B900"
BUBBLE_BG, BUBBLE_STROKE = "#FFFFFF", "#1E2A47"

# ---------------------------------------------------------------- characters
CHARACTERS = {
    "trump": dict(
        name="Trump", desc="Q版特朗普：任务完成时高呼 Make America Great Again",
        hair="#F2C233", hair_hi="#FFE27A", hair_sh="#D19A1F", brow="#C9921B",
        skin="#F0A868", skin_sh="#D98A4E", blush="#E88E62",
        top="#1B2B4E", top_dk="#122040", pants="#122040",
        outfit="suit", hairstyle="swoop", glasses=False,
        accent=RED, accent2=BLUE_TXT, confetti=[RED, WHITE, BLUE_TXT],
        done_lines=["MAKE AMERICA", "GREAT AGAIN!"], done_colors=[RED, BLUE_TXT], done_prop="cap",
        rally="HUGE!", tier2="phone-bird", error="WRONG!", notify="SIGN HERE!",
        delegate="YOU!", poke="FAKE NEWS!", double="TREMENDOUS!", idle_special="golf",
        voice="en-US-GuyNeural", complete_tts="Make America Great Again!", confirm_tts="Huge.",
        tts_rate="+8%", tts_pitch="-6Hz",
    ),
    "musk": dict(
        name="Musk", desc="Q版马斯克：任务完成时抱着水槽说 Let that sink in",
        hair="#3B2A1F", hair_hi="#55402F", hair_sh="#2A1D14", brow="#3B2A1F",
        skin="#F2D3B8", skin_sh="#D9B394", blush="#E9B9A0",
        top="#0E0E13", top_dk="#050508", pants="#1C1C24",
        outfit="tee-jacket", hairstyle="short", glasses=False,
        accent="#E11D48", accent2=INK, confetti=["#E5E7EB", "#A3A3A3", "#E11D48"],
        done_lines=["LET THAT", "SINK IN"], done_colors=[INK, "#E11D48"], done_prop="sink",
        rally="HARDCORE!", tier2="phone-x", error="CONCERNING.", notify="LOOKING INTO IT",
        delegate="SHIP IT!", poke="LOL", double="TO MARS!", idle_special="dance",
        voice="en-US-ChristopherNeural", complete_tts="Let that sink in.", confirm_tts="Looking into it.",
        tts_rate="+0%", tts_pitch="-2Hz",
    ),
    "jensen": dict(
        name="Jensen", desc="Q版黄仁勋：任务完成时举起显卡说 The more you buy, the more you save",
        hair="#1A1A1A", hair_hi="#333333", hair_sh="#0A0A0A", brow="#222222", hair_gray="#9A9A9A",
        skin="#E8BC8E", skin_sh="#C99A6C", blush="#DDA07A",
        top="#141414", top_dk="#0A0A0A", pants="#1E1E1E",
        outfit="leather", hairstyle="neat", glasses=True,
        accent=NV_GREEN, accent2=INK, confetti=[NV_GREEN, WHITE, "#3F9E00"],
        done_lines=["THE MORE YOU BUY", "THE MORE YOU SAVE!"], done_colors=[INK, NV_GREEN], done_prop="gpu",
        rally="ACCELERATE!", tier2="gpu-inspect", error="NEEDS MORE GPUS", notify="RUN, DON'T WALK!",
        delegate="BUILD!", poke="OUCH!", double="IPHONE MOMENT!", idle_special="sign",
        voice="en-US-AndrewNeural", complete_tts="The more you buy, the more you save!", confirm_tts="Run, don't walk!",
        tts_rate="+12%", tts_pitch="+0Hz",
    ),
}

# ---------------------------------------------------------------- 3x5 pixel font
FONT = {
 "A": ["010","101","111","101","101"], "B": ["110","101","110","101","110"],
 "C": ["011","100","100","100","011"], "D": ["110","101","101","101","110"],
 "E": ["111","100","110","100","111"], "F": ["111","100","110","100","100"],
 "G": ["011","100","101","101","011"], "H": ["101","101","111","101","101"],
 "I": ["111","010","010","010","111"], "J": ["011","001","001","101","010"],
 "K": ["101","101","110","101","101"], "L": ["100","100","100","100","111"],
 "M": ["101","111","111","101","101"], "N": ["110","101","101","101","101"],
 "O": ["010","101","101","101","010"], "P": ["110","101","110","100","100"],
 "Q": ["010","101","101","110","011"], "R": ["110","101","110","101","101"],
 "S": ["011","100","010","001","110"], "T": ["111","010","010","010","010"],
 "U": ["101","101","101","101","111"], "V": ["101","101","101","101","010"],
 "W": ["101","101","111","111","101"], "X": ["101","101","010","101","101"],
 "Y": ["101","101","010","010","010"], "Z": ["111","001","010","100","111"],
 "!": ["010","010","010","000","010"], "?": ["110","001","010","000","010"],
 ".": ["000","000","000","000","010"], ",": ["000","000","000","010","100"],
 "'": ["010","010","000","000","000"], " ": ["000","000","000","000","000"],
}

def R(x, y, w, h, fill, extra=""):
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}"{(" " + extra) if extra else ""}/>'

def run_rects(cells, fill, extra=""):
    rows = {}
    for x, y in cells:
        rows.setdefault(y, set()).add(x)
    out = []
    for y in sorted(rows):
        xs = sorted(rows[y])
        start = prev = xs[0]
        for x in xs[1:] + [None]:
            if x is None or x != prev + 1:
                out.append(R(start, y, prev - start + 1, 1, fill, extra))
                if x is not None:
                    start = x
            if x is not None:
                prev = x
    return "\n".join(out)

def text_width(s, scale):
    return (len(s) * 4 - 1) * scale

def pixel_text(s, x, y, scale, fill):
    rects = []
    cx = 0
    for ch in s.upper():
        g = FONT.get(ch, FONT[" "])
        for row, bits in enumerate(g):
            for col, b in enumerate(bits):
                if b == "1":
                    rects.append(f'<rect x="{x + (cx+col)*scale:.3f}" y="{y + row*scale:.3f}" width="{scale:.3f}" height="{scale:.3f}" fill="{fill}"/>')
        cx += 4
    return "\n".join(rects)

def speech_bubble(lines, cx, bottom_y, scale=0.55, colors=None, tail=True, cls="bubble", pad=1.2, tail_x=None):
    colors = colors or [INK] * len(lines)
    w = max(text_width(l, scale) for l in lines) + pad * 2
    line_h, gap = 5 * scale, 1.5 * scale
    h = len(lines) * line_h + (len(lines) - 1) * gap + pad * 2
    x0 = cx - w / 2
    # keep the box inside the viewBox (x -15..30) with a little margin; the tail stays put
    if tail_x is None:
        tail_x = cx
    x0 = min(max(x0, -14.2), 29.2 - w)
    cx = x0 + w / 2
    tail_h = 2.2 if tail else 0
    y0 = bottom_y - tail_h - h
    parts = [f'<g class="{cls}">',
             f'<rect x="{x0:.3f}" y="{y0:.3f}" width="{w:.3f}" height="{h:.3f}" rx="1" ry="1" fill="{BUBBLE_BG}" stroke="{BUBBLE_STROKE}" stroke-width="0.5"/>']
    if tail:
        tx = cx if tail_x is None else tail_x
        parts.append(f'<polygon points="{tx-1.3:.3f},{y0+h-0.3:.3f} {tx+1.3:.3f},{y0+h-0.3:.3f} {tx:.3f},{bottom_y:.3f}" fill="{BUBBLE_BG}" stroke="{BUBBLE_STROKE}" stroke-width="0.5" stroke-linejoin="round"/>')
        parts.append(f'<rect x="{tx-1.2:.3f}" y="{y0+h-0.7:.3f}" width="2.4" height="0.8" fill="{BUBBLE_BG}"/>')
    ty = y0 + pad
    for line, col in zip(lines, colors):
        parts.append(pixel_text(line, cx - text_width(line, scale) / 2, ty, scale, col))
        ty += line_h + gap
    parts.append("</g>")
    return "\n".join(parts)

# ---------------------------------------------------------------- shared rig
STATIC_CSS = []
BASE_CSS = "#arm-L { transform-origin: 2.25px 9.5px; } #arm-R { transform-origin: 13.75px 9.5px; }"

class Gen:
    def __init__(self, cid):
        self.C = CHARACTERS[cid]
        self.cid = cid
        self.dir = os.path.join(THEMES_ROOT, cid)
        self.assets = os.path.join(self.dir, "assets")
        os.makedirs(self.assets, exist_ok=True)
        os.makedirs(os.path.join(self.dir, "sounds"), exist_ok=True)

    # ---- head
    def hair(self, cap=False):
        C = self.C
        cells = []
        def row(y, a, b): cells.extend((x, y) for x in range(a, b + 1))
        out = []
        if C["hairstyle"] == "swoop":
            if not cap:
                row(-3, 5, 10)
            row(-2, 3, 12); row(-1, 2, 13); row(0, 1, 13)
            row(1, 1, 6); row(1, 12, 13)
            row(2, 1, 3); row(2, 13, 13)
            row(3, 2, 2); row(3, 13, 13); row(4, 2, 2); row(4, 13, 13)
            out.append(run_rects(cells, C["hair"]))
            hi = [(x, 0) for x in range(2, 5)] + [(x, -1) for x in range(9, 12)]
            if not cap:
                hi += [(x, -2) for x in range(4, 7)]
            out.append(run_rects(hi, C["hair_hi"]))
            out.append(run_rects([(5, 1), (6, 1), (2, 2), (3, 2), (12, 1)], C["hair_sh"]))
        elif C["hairstyle"] == "short":      # Musk: short dark hair, slight widow's peak
            row(-2, 4, 11); row(-1, 3, 12); row(0, 2, 13)
            row(1, 2, 3); row(1, 7, 8); row(1, 12, 13)
            row(2, 2, 2); row(2, 13, 13); row(3, 2, 2); row(3, 13, 13)
            out.append(run_rects(cells, C["hair"]))
            out.append(run_rects([(x, -2) for x in range(5, 8)] + [(2, 0), (3, 0)], C["hair_hi"]))
            out.append(run_rects([(7, 1), (8, 1), (2, 1), (13, 1)], C["hair_sh"]))
        elif C["hairstyle"] == "neat":       # Jensen: neat black hair, gray temples
            row(-2, 4, 11); row(-1, 3, 12); row(0, 2, 13)
            row(1, 2, 3); row(1, 12, 13); row(2, 2, 2); row(2, 13, 13); row(3, 2, 2); row(3, 13, 13)
            out.append(run_rects(cells, C["hair"]))
            out.append(run_rects([(x, -2) for x in range(5, 9)] + [(3, -1), (4, -1)], C["hair_hi"]))
            out.append(run_rects([(2, 1), (13, 1), (2, 2), (13, 2), (2, 3), (13, 3)], C["hair_gray"]))
        if cap:
            out.append(R(3, -4.6, 10, 3.1, "#C8102E"))
            out.append(R(1.4, -1.7, 13.2, 0.9, "#8E0B21"))
            out.append(R(3, -4.6, 10, 0.6, "#8E0B21", 'opacity="0.35"'))
            out.append(pixel_text("MAGA", 8 - text_width("MAGA", 0.42) / 2, -3.9, 0.42, WHITE))
        return "\n".join(out)

    def face_skin(self):
        C = self.C
        cells = []
        def row(y, a, b): cells.extend((x, y) for x in range(a, b + 1))
        row(1, 4, 11); row(2, 3, 12); row(3, 3, 12); row(4, 3, 12)
        row(5, 3, 12); row(6, 3, 12); row(7, 4, 11); row(8, 5, 10)
        return "\n".join([run_rects(cells, C["skin"]), R(5, 8, 6, 0.6, C["skin_sh"]),
                          R(3.4, 5.9, 1.1, 0.7, C["blush"]), R(11.5, 5.9, 1.1, 0.7, C["blush"]),
                          R(7.5, 5.7, 1, 0.6, C["skin_sh"])])

    def features(self, eyes="open", mouth="pursed", pupil_dx=0.0, pupil_dy=0.0, brows="normal", eyes_id=True):
        C = self.C
        B = C["brow"]
        out = []
        if brows == "normal":
            out.append(R(5, 3.1, 2, 0.6, B)); out.append(R(9, 3.1, 2, 0.6, B))
        elif brows == "raised":
            out.append(R(5, 2.4, 2, 0.6, B)); out.append(R(9, 2.4, 2, 0.6, B))
        elif brows == "angry":
            out.append(f'<rect x="5" y="3" width="2" height="0.6" fill="{B}" transform="rotate(14 6 3.3)"/>')
            out.append(f'<rect x="9" y="3" width="2" height="0.6" fill="{B}" transform="rotate(-14 10 3.3)"/>')
        if eyes in ("open", "wide", "squint", "down", "wink"):
            eh = {"open": 1.6, "wide": 2.0, "squint": 0.9, "down": 1.6, "wink": 1.6}[eyes]
            ey = 4.0 if eyes != "squint" else 4.5
            out.append('<defs><clipPath id="eyeclip">'
                       f'<rect x="5" y="{ey}" width="2" height="{eh}"/><rect x="9" y="{ey}" width="2" height="{eh}"/>'
                       '</clipPath></defs>')
            out.append(R(5, ey, 2, eh, WHITE))
            if eyes == "wink":
                out.append(R(9, 4.7, 2, 0.6, PUPIL))
            else:
                out.append(R(9, ey, 2, eh, WHITE))
            pw, ph = (0.9, 0.95) if eyes != "wide" else (1.0, 1.1)
            py = ey + (eh - ph) / 2 + pupil_dy
            gid = ' id="eyes-js"' if eyes_id else ""
            out.append(f'<g{gid} clip-path="url(#eyeclip)"><g class="pupils">')
            out.append(R(5.55 + pupil_dx, py, pw, ph, PUPIL))
            if eyes != "wink":
                out.append(R(9.55 + pupil_dx, py, pw, ph, PUPIL))
            out.append('</g></g>')
            if eyes == "squint":
                out.append(R(5, 4.2, 2, 0.5, C["skin"])); out.append(R(9, 4.2, 2, 0.5, C["skin"]))
        elif eyes == "closed":
            out.append(R(5, 4.9, 2, 0.55, PUPIL)); out.append(R(9, 4.9, 2, 0.55, PUPIL))
        elif eyes == "happy":
            for bx in (5, 9):
                out.append(R(bx, 4.6, 0.7, 0.5, PUPIL)); out.append(R(bx + 0.65, 4.2, 0.7, 0.5, PUPIL)); out.append(R(bx + 1.3, 4.6, 0.7, 0.5, PUPIL))
        if C["glasses"]:
            fr = 'fill="none" stroke="#1C1C1C" stroke-width="0.38"'
            out.append(f'<rect x="4.55" y="3.6" width="2.9" height="2.4" rx="0.3" {fr}/>')
            out.append(f'<rect x="8.55" y="3.6" width="2.9" height="2.4" rx="0.3" {fr}/>')
            out.append(R(7.45, 4.5, 1.1, 0.38, "#1C1C1C"))
            out.append(R(3.0, 4.4, 1.55, 0.38, "#1C1C1C")); out.append(R(11.45, 4.4, 1.55, 0.38, "#1C1C1C"))
        if mouth == "pursed":
            out.append(R(7, 7, 2, 0.8, MOUTH))
        elif mouth == "grin":
            out.append(R(6, 6.7, 4, 1.4, MOUTH_DK)); out.append(R(6.3, 6.9, 3.4, 0.5, TEETH))
        elif mouth == "smile":
            out.append(R(6.3, 7.1, 3.4, 0.6, MOUTH)); out.append(R(6, 6.6, 0.5, 0.6, MOUTH)); out.append(R(9.5, 6.6, 0.5, 0.6, MOUTH))
        elif mouth == "frown":
            out.append(R(6.5, 6.8, 3, 0.6, MOUTH)); out.append(R(6.2, 7.3, 0.5, 0.6, MOUTH)); out.append(R(9.3, 7.3, 0.5, 0.6, MOUTH))
        elif mouth == "o":
            out.append(R(7.3, 6.8, 1.4, 1.2, MOUTH_DK))
        elif mouth == "shout":
            out.append(R(6.4, 6.5, 3.2, 2, MOUTH_DK)); out.append(R(6.7, 6.7, 2.6, 0.5, TEETH))
        elif mouth == "flat":
            out.append(R(6.6, 7.1, 2.8, 0.6, MOUTH))
        return "\n".join(out)

    def head(self, cap=False, **kw):
        if self.cid in PEOPLE:
            return portrait_head(self.cid, cap=cap, **kw)
        return f'<g id="head">\n{self.face_skin()}\n{self.hair(cap)}\n{self.features(**kw)}\n</g>'

    # ---- body
    def torso(self):
        C = self.C
        out = [R(3, 9, 10, 4.6, C["top"])]
        if C["outfit"] == "suit":
            out.append(f'<polygon points="6,9 10,9 8,11.6" fill="{WHITE}"/>')
            out.append(f'<polygon points="5.2,9 6.2,9 7.6,11.8 7.1,12.6" fill="{C["top_dk"]}"/>')
            out.append(f'<polygon points="9.8,9 10.8,9 8.9,12.6 8.4,11.8" fill="{C["top_dk"]}"/>')
            out.append(f'<g><rect x="7.55" y="9.3" width="0.9" height="0.7" fill="{RED}"/>'
                       f'<polygon points="7.5,10 8.5,10 8.65,14.4 8,15.1 7.35,14.4" fill="{RED}"/></g>')
        elif C["outfit"] == "tee-jacket":
            out.append(R(5.6, 9, 4.8, 4.6, "#26262F"))                  # black tee under open jacket
            out.append(f'<polygon points="5.6,9 6.6,9 6.6,13.6 5.6,13.6" fill="{C["top_dk"]}"/>')
            out.append(f'<polygon points="9.4,9 10.4,9 10.4,13.6 9.4,13.6" fill="{C["top_dk"]}"/>')
            # tiny X logo on the tee
            out.append(f'<rect x="7.75" y="10.4" width="0.45" height="1.8" fill="{WHITE}" transform="rotate(45 7.975 11.3)"/>')
            out.append(f'<rect x="7.75" y="10.4" width="0.45" height="1.8" fill="{WHITE}" transform="rotate(-45 7.975 11.3)"/>')
        elif C["outfit"] == "leather":
            out.append(R(3, 9, 10, 0.7, "#2B2B2B"))                     # shoulder sheen
            out.append(R(7.75, 9, 0.5, 4.6, "#A6A6A6"))                 # zipper
            out.append(f'<polygon points="5.5,9 7.6,9 7.6,11.2" fill="#2E2E2E"/>')
            out.append(f'<polygon points="8.4,9 10.5,9 8.4,11.2" fill="#2E2E2E"/>')
            out.append(R(6.9, 9, 0.8, 0.9, "#050505")); out.append(R(8.3, 9, 0.8, 0.9, "#050505"))
        return "\n".join(out)

    def arm(self, side, rotate=0.0, hand=True):
        x = 1.5 if side == "L" else 13.0
        if rotate:
            STATIC_CSS.append(f"#arm-{side} {{ transform: rotate({rotate:g}deg); }}")
        parts = [f'<g id="arm-{side}">', R(x, 9.3, 1.5, 4.0, self.C["top"])]
        if hand:
            parts.append(R(x + 0.1, 13.1, 1.3, 1.1, self.C["skin"]))
        parts.append("</g>")
        return "\n".join(parts)

    def legs(self):
        p = self.C["pants"]
        return (f'<g id="leg-L">{R(4, 13.4, 3, 1.4, p)}{R(3.6, 14.6, 3.6, 0.8, SHOE)}</g>'
                f'<g id="leg-R">{R(9, 13.4, 3, 1.4, p)}{R(8.8, 14.6, 3.6, 0.8, SHOE)}</g>')

    def shadow(self):
        sh = R(2.5, 15.3, 11, 0.9, "#000000", 'opacity="0.35"')
        return f'<g id="shadow-js">{sh}</g>'

    def figure(self, head_svg, arm_l, arm_r, body_cls="breathe", extra_in_body="", extra_after="", extra_front=""):
        return (f'{self.shadow()}\n{self.legs()}\n<g id="body-js"><g class="{body_cls}">\n{arm_l}\n{arm_r}\n{self.torso()}\n'
                f'{extra_in_body}\n{head_svg}\n{extra_front}\n</g></g>\n{extra_after}')

    def svg(self, style, body):
        static = "\n".join(STATIC_CSS); STATIC_CSS.clear()
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VIEWBOX}" width="500" height="500" shape-rendering="crispEdges">\n'
                f'<defs><style>\n{BASE_CSS}\n{static}\n{style}\n</style></defs>\n{body}\n</svg>\n')

    def write(self, name, content):
        with open(os.path.join(self.assets, name), "w") as f:
            f.write(content)

    # ---- props
    def prop_phone(self, kind):
        if kind == "phone-bird":
            extra = f'<g class="fly">{R(13.5, 2.5, 1.2, 0.8, "#1DA1F2")}{R(14.7, 2.1, 0.6, 0.6, "#1DA1F2")}{R(12.9, 2.9, 0.6, 0.5, "#1DA1F2")}</g>'
            screen = SCREEN
        else:  # phone-x
            extra = (f'<g class="fly"><rect x="13.6" y="1.6" width="0.5" height="2.2" fill="{INK}" transform="rotate(45 13.85 2.7)"/>'
                     f'<rect x="13.6" y="1.6" width="0.5" height="2.2" fill="{INK}" transform="rotate(-45 13.85 2.7)"/></g>')
            screen = "#111111"
        dots = INK if kind == "phone-bird" else WHITE
        return (f'<g id="phone">{R(10.4, 4.3, 2.0, 3.4, "#222")}{R(10.7, 4.6, 1.4, 2.6, screen)}'
                f'<g class="dots">{R(10.85, 5.6, 0.35, 0.35, dots)}{R(11.35, 5.6, 0.35, 0.35, dots)}{R(11.85, 5.6, 0.35, 0.35, dots)}</g>'
                f'<g class="thumb">{R(11.9, 7.2, 0.9, 0.7, self.C["skin"])}</g></g>{extra}')

    def prop_gpu(self, x, y, cls=""):
        c = f' class="{cls}"' if cls else ""
        return (f'<g{c}>{R(x, y, 6.4, 2.8, NV_GREEN)}{R(x, y + 2.8, 6.4, 0.5, "#2E4A00")}{R(x + 0.4, y + 3.3, 3.2, 0.5, "#D4AF37")}'
                f'<circle cx="{x+1.8:.2f}" cy="{y+1.4:.2f}" r="0.95" fill="#111"/><circle cx="{x+4.6:.2f}" cy="{y+1.4:.2f}" r="0.95" fill="#111"/>'
                f'<circle cx="{x+1.8:.2f}" cy="{y+1.4:.2f}" r="0.35" fill="#555"/><circle cx="{x+4.6:.2f}" cy="{y+1.4:.2f}" r="0.35" fill="#555"/></g>')

    def prop_sink(self):
        return (f'<g id="sink">{R(4.6, 10.6, 6.8, 2.4, "#F1F1F1")}{R(5.0, 11.0, 6.0, 1.2, "#CFD5DD")}'
                f'{R(7.6, 8.9, 0.6, 1.8, "#9AA3AE")}{R(7.6, 8.9, 1.6, 0.5, "#9AA3AE")}{R(4.6, 13.0, 6.8, 0.5, "#B9C0C8")}</g>')

    def prop_rocket(self):
        return (f'<g class="rocket">{R(17.0, 4.0, 1.8, 4.5, "#EDEDED")}<polygon points="17,4 18.8,4 17.9,2.2" fill="#D62828"/>'
                f'{R(16.4, 7.6, 0.6, 1.2, "#D62828")}{R(18.8, 7.6, 0.6, 1.2, "#D62828")}'
                f'<g class="flame">{R(17.3, 8.5, 1.2, 1.4, "#FF8A00")}{R(17.6, 9.9, 0.6, 0.9, "#FFD166")}</g></g>')

    # ---- states
    BREATHE = """
.breathe { transform-origin: 7.5px 15px; animation: breathe 3.4s infinite ease-in-out; }
@keyframes breathe { 0%,100% { transform: scale(1,1); } 50% { transform: scale(1.015,0.985); } }
.pupils { transform-origin: 7.5px 4.8px; animation: blink 4.6s infinite ease-in-out; }
@keyframes blink { 0%,8%,100% { transform: scaleY(1); } 4% { transform: scaleY(0.1); } }
#eyes-js, #body-js, #shadow-js { transition: transform 0.2s ease-out; }
#shadow-js { transform-origin: 7.5px 15px; }
"""
    POP = """
.bubble { transform-origin: 7.5px -6px; animation: pop 0.45s ease-out both; }
@keyframes pop { 0% { transform: scale(0); opacity: 0; } 70% { transform: scale(1.08); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
"""

    def gen_all(self):
        C = self.C
        B = self.BREATHE
        # idle
        self.write("idle-follow.svg", self.svg(B, self.figure(self.head(), self.arm("L"), self.arm("R"))))
        # thinking
        style = B + """
.tilt { transform-origin: 7.5px 15px; animation: tilt 2.6s infinite ease-in-out; }
@keyframes tilt { 0%,100% { transform: rotate(-2deg); } 50% { transform: rotate(2deg); } }
.dot1 { animation: dot 1.5s infinite; } .dot2 { animation: dot 1.5s 0.25s infinite both; } .dot3 { animation: dot 1.5s 0.5s infinite both; }
@keyframes dot { 0%,100% { opacity: 0.25; } 50% { opacity: 1; } }
.cloud { animation: float 3s infinite ease-in-out; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-0.6px); } }
"""
        cloud = (f'<g class="cloud"><circle cx="14.5" cy="-1.5" r="0.8" fill="{WHITE}" stroke="{INK}" stroke-width="0.35"/>'
                 f'<circle cx="16.6" cy="-4.2" r="1.2" fill="{WHITE}" stroke="{INK}" stroke-width="0.35"/>'
                 f'<rect x="15.2" y="-11.5" width="10" height="5.8" rx="2.6" fill="{WHITE}" stroke="{INK}" stroke-width="0.4"/>'
                 f'<rect class="dot1" x="17.2" y="-9.2" width="1.3" height="1.3" fill="{INK}"/><rect class="dot2" x="19.5" y="-9.2" width="1.3" height="1.3" fill="{INK}"/>'
                 f'<rect class="dot3" x="21.8" y="-9.2" width="1.3" height="1.3" fill="{INK}"/></g>')
        self.write("thinking.svg", self.svg(style, self.figure(
            self.head(pupil_dx=0.55, pupil_dy=-0.4, brows="raised", eyes_id=False), self.arm("L"), self.arm("R", rotate=135),
            body_cls="tilt", extra_after=cloud)))
        # typing (1 session)
        style = B + """
.hand-l { animation: tap 0.28s infinite alternate ease-in-out; } .hand-r { animation: tap 0.28s 0.14s infinite alternate ease-in-out both; }
@keyframes tap { from { transform: translateY(0); } to { transform: translateY(-0.6px); } }
.code1 { animation: code 1.6s infinite step-end; } .code2 { animation: code 1.6s 0.4s infinite step-end both; } .code3 { animation: code 1.6s 0.8s infinite step-end both; }
@keyframes code { 0% { opacity: 0; } 30%,100% { opacity: 1; } }
"""
        scr = SCREEN if C["outfit"] == "suit" else ("#101010" if C["outfit"] == "tee-jacket" else "#0B1F00")
        c1, c2, c3 = (BLUE_TXT, RED, INK) if C["outfit"] == "suit" else ((WHITE, "#E11D48", "#9CA3AF") if C["outfit"] == "tee-jacket" else (NV_GREEN, WHITE, "#A3E635"))
        code_rects = R(5.0, 9.4, 2.6, 0.5, c1, 'class="code1"') + R(5.0, 10.2, 4.0, 0.5, c2, 'class="code2"') + R(5.0, 11.0, 3.2, 0.5, c3, 'class="code3"')
        laptop = (f'<g id="laptop">{R(3.6, 12.2, 8.8, 1.2, GRAY_DK)}{R(4.2, 8.6, 7.6, 3.7, GRAY)}{R(4.6, 9.0, 6.8, 2.9, scr)}{code_rects}'
                  f'<g class="hand-l">{R(5.0, 11.4, 1.4, 0.9, C["skin"])}</g><g class="hand-r">{R(9.6, 11.4, 1.4, 0.9, C["skin"])}</g></g>')
        self.write("typing.svg", self.svg(style, self.figure(
            self.head(eyes="down", pupil_dy=0.45, eyes_id=False), self.arm("L", rotate=-25, hand=False), self.arm("R", rotate=25, hand=False),
            extra_in_body=laptop)))
        # tier 2
        style = B + """
.thumb { animation: tap 0.3s infinite alternate ease-in-out; }
@keyframes tap { from { transform: translateY(0); } to { transform: translateY(-0.4px); } }
.dots rect { animation: dot 1.2s infinite both; } .dots rect:nth-child(2) { animation-delay: 0.2s; } .dots rect:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot { 0%,100% { opacity: 0.2; } 50% { opacity: 1; } }
.fly { animation: fly 4s infinite linear both; }
@keyframes fly { 0% { transform: translate(0,0); opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { transform: translate(6px,-9px); opacity: 0; } }
.inspect { transform-origin: 12px 5px; animation: inspect 2.4s infinite ease-in-out; }
@keyframes inspect { 0%,100% { transform: rotate(-6deg); } 50% { transform: rotate(6deg); } }
"""
        if C["tier2"] == "gpu-inspect":
            prop = self.prop_gpu(9.6, 3.4, cls="inspect")
            hd = self.head(eyes="down", pupil_dx=0.6, pupil_dy=0.2, mouth="smile", eyes_id=False)
        else:
            prop = self.prop_phone(C["tier2"])
            hd = self.head(eyes="down", pupil_dx=0.6, pupil_dy=0.3, eyes_id=False)
        self.write("tier2.svg", self.svg(style, self.figure(hd, self.arm("L"), self.arm("R", rotate=150), extra_front=prop)))
        # rally (3+)
        style = """
.bounce { transform-origin: 7.5px 15px; animation: bounce 0.6s infinite ease-in-out; }
@keyframes bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-1px); } }
#arm-L { animation: pumpL 0.6s infinite ease-in-out; } #arm-R { animation: pumpR 0.6s 0.3s infinite ease-in-out both; }
@keyframes pumpL { 0%,100% { transform: rotate(160deg); } 50% { transform: rotate(120deg); } }
@keyframes pumpR { 0%,100% { transform: rotate(-160deg); } 50% { transform: rotate(-120deg); } }
.bubble { transform-origin: 7.5px -3px; animation: pop 2.4s infinite; }
@keyframes pop { 0%,15% { transform: scale(0); opacity: 0; } 25%,75% { transform: scale(1); opacity: 1; } 85%,100% { transform: scale(0); opacity: 0; } }
.confetti rect { animation: fall 1.8s infinite linear both; }
.confetti rect:nth-child(2n) { animation-duration: 2.3s; animation-delay: 0.5s; } .confetti rect:nth-child(3n) { animation-delay: 1.1s; }
@keyframes fall { 0% { transform: translateY(-6px); opacity: 0; } 15% { opacity: 1; } 100% { transform: translateY(14px); opacity: 0; } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
        cf = C["confetti"]
        confetti = '<g class="confetti">' + "".join(R(x, -8, 0.8, 0.8, cf[i % 3]) for i, x in enumerate([-3, 0, 3, 12, 15, 18, -6, 21])) + '</g>'
        self.write("rally.svg", self.svg(style, self.figure(
            self.head(mouth="shout", brows="raised", eyes_id=False), self.arm("L"), self.arm("R"), body_cls="bounce",
            extra_after=confetti + speech_bubble([C["rally"]], 7.5, -4.2, scale=0.75, colors=[C["accent"]]))))
        # delegating (subagents)
        style = B + """
#arm-L { animation: pointL 1.6s infinite ease-in-out; } #arm-R { animation: pointR 1.6s infinite ease-in-out; }
@keyframes pointL { 0%,40%,100% { transform: rotate(0deg); } 15%,30% { transform: rotate(95deg); } }
@keyframes pointR { 0%,50%,100% { transform: rotate(0deg); } 65%,80% { transform: rotate(-95deg); } }
.pupils { animation: look 1.6s infinite ease-in-out; }
@keyframes look { 0%,40%,100% { transform: translateX(-0.5px); } 50%,90% { transform: translateX(0.5px); } }
.tag { animation: tagpop 1.6s infinite; } .tag2 { animation: tagpop 1.6s 0.8s infinite both; }
@keyframes tagpop { 0%,10%,45%,100% { opacity: 0; } 15%,35% { opacity: 1; } }
"""
        tw = text_width(C["delegate"], 0.5)
        tags = (f'<g class="tag">{pixel_text(C["delegate"], -4 - tw, 2.5, 0.5, INK)}</g>'
                f'<g class="tag2">{pixel_text(C["delegate"], 19, 2.5, 0.5, INK)}</g>')
        self.write("delegating.svg", self.svg(style, self.figure(self.head(mouth="smile", eyes_id=False), self.arm("L"), self.arm("R"), extra_after=tags)))
        # done / attention
        style = """
.bounce { transform-origin: 7.5px 15px; animation: bounce 0.7s infinite ease-in-out; }
@keyframes bounce { 0%,100% { transform: translateY(0) scale(1,1); } 50% { transform: translateY(-1.4px) scale(1.02,0.98); } }
#shadow-js { transform-origin: 7.5px 15px; animation: sh 0.7s infinite ease-in-out; }
@keyframes sh { 0%,100% { transform: scaleX(1); opacity: 0.35; } 50% { transform: scaleX(0.85); opacity: 0.25; } }
.spark rect { animation: twinkle 1.2s infinite step-end both; } .spark rect:nth-child(2n) { animation-delay: 0.4s; } .spark rect:nth-child(3n) { animation-delay: 0.8s; }
@keyframes twinkle { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
.rocket { animation: launch 2.2s infinite ease-in both; }
@keyframes launch { 0% { transform: translateY(6px); opacity: 0; } 15% { opacity: 1; } 85% { opacity: 1; } 100% { transform: translateY(-22px); opacity: 0; } }
.flame { transform-origin: 17.9px 8.5px; animation: flick 0.12s infinite alternate; }
@keyframes flick { from { transform: scaleY(1); } to { transform: scaleY(1.5); } }
""" + self.POP
        sparks = '<g class="spark">' + "".join(R(x, y, 0.9, 0.9, cf[i % 3]) for i, (x, y) in enumerate([(-4, 2), (-6, 6), (-2, -3), (18, 3), (20, 7), (16, -2), (-5, 11), (19, 12)])) + '</g>'
        bubble = speech_bubble(C["done_lines"], 7.5, -5.6, scale=0.55, colors=C["done_colors"])
        if C["done_prop"] == "cap":
            style += "#arm-L { animation: waveL 0.35s infinite alternate ease-in-out; } #arm-R { animation: waveR 0.35s infinite alternate ease-in-out; }\n" \
                     "@keyframes waveL { from { transform: rotate(150deg); } to { transform: rotate(170deg); } }\n@keyframes waveR { from { transform: rotate(-150deg); } to { transform: rotate(-170deg); } }\n"
            body = self.figure(self.head(cap=True, eyes="happy", mouth="grin"), self.arm("L"), self.arm("R"), body_cls="bounce", extra_after=sparks + bubble)
        elif C["done_prop"] == "sink":
            body = self.figure(self.head(eyes="happy", mouth="grin"), self.arm("L", rotate=-40), self.arm("R", rotate=40), body_cls="bounce",
                               extra_front=self.prop_sink(), extra_after=sparks + self.prop_rocket() + bubble)
        else:  # gpu held high in right hand, left hand waving
            style += "#arm-L { animation: waveL 0.35s infinite alternate ease-in-out; }\n@keyframes waveL { from { transform: rotate(150deg); } to { transform: rotate(170deg); } }\n" \
                     "#arm-R { transform: rotate(-165deg); }\n.gpu-up { transform-origin: 14.5px 4px; animation: tilt 0.7s infinite alternate ease-in-out; }\n@keyframes tilt { from { transform: rotate(-5deg); } to { transform: rotate(5deg); } }\n"
            body = self.figure(self.head(eyes="happy", mouth="grin"), self.arm("L"), self.arm("R"), body_cls="bounce",
                               extra_front=self.prop_gpu(11.6, 1.2, cls="gpu-up"), extra_after=sparks + bubble)
        self.write("done.svg", self.svg(style, body))
        # error
        style = """
.shake { transform-origin: 7.5px 15px; animation: shake 0.5s infinite ease-in-out; }
@keyframes shake { 0%,100% { transform: translateX(0); } 25% { transform: translateX(-0.5px); } 75% { transform: translateX(0.5px); } }
.vein { animation: vein 0.8s infinite step-end; }
@keyframes vein { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
#shadow-js { transform-origin: 7.5px 15px; }
""" + self.POP
        crossed = f'{R(2.8, 10.6, 10.4, 1.9, C["top"])}{R(2.6, 10.9, 1.4, 1.2, C["skin"])}{R(12.0, 10.9, 1.4, 1.2, C["skin"])}'
        vein = f'<g class="vein">{R(12.6, 1.2, 0.5, 1.4, RED)}{R(12.1, 1.7, 1.4, 0.5, RED)}</g>'
        self.write("error.svg", self.svg(style, self.figure(
            self.head(eyes="squint", mouth="frown", brows="angry", eyes_id=False), self.arm("L", rotate=-20, hand=False), self.arm("R", rotate=20, hand=False),
            body_cls="shake", extra_in_body=crossed, extra_after=vein + speech_bubble([C["error"]], 7.5, -4.2, scale=0.7, colors=[C["accent"]]))))
        # notification
        style = B + """
.mark { transform-origin: 7.5px -6px; animation: hop 0.7s infinite ease-in-out; }
@keyframes hop { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-1.2px); } }
#arm-R { animation: raise 1.4s infinite ease-in-out; }
@keyframes raise { 0%,100% { transform: rotate(-165deg); } 50% { transform: rotate(-150deg); } }
"""
        mark = f'<g class="mark">{R(6.6, -12, 1.8, 5, C["accent"])}{R(6.6, -6, 1.8, 1.8, C["accent"])}</g>'
        self.write("notification.svg", self.svg(style, self.figure(
            self.head(eyes="wide", mouth="o", brows="raised", eyes_id=False), self.arm("L"), self.arm("R"),
            extra_after=mark + speech_bubble([C["notify"]], 20, -1.5, scale=0.5, colors=[INK], tail_x=16))))
        # sleeping
        style = """
.nod { transform-origin: 7.5px 8.5px; animation: nod 4s infinite ease-in-out; }
@keyframes nod { 0%,100% { transform: rotate(-4deg); } 50% { transform: rotate(3deg); } }
.breathe { transform-origin: 7.5px 15px; animation: breathe 4s infinite ease-in-out; }
@keyframes breathe { 0%,100% { transform: scale(1,1); } 50% { transform: scale(1.02,0.98); } }
.z1 { animation: zz 3.6s infinite linear both; } .z2 { animation: zz 3.6s 1.2s infinite linear both; } .z3 { animation: zz 3.6s 2.4s infinite linear both; }
@keyframes zz { 0% { transform: translate(0,0) scale(0.6); opacity: 0; } 15% { opacity: 1; } 100% { transform: translate(4px,-9px) scale(1.3); opacity: 0; } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
        zs = "".join(f'<g class="z{i}" style="transform-origin:14px 0px">{pixel_text("Z", 13.5, -1.5, 0.6, INK)}</g>' for i in (1, 2, 3))
        self.write("sleeping.svg", self.svg(style, self.figure(f'<g class="nod">{self.head(eyes="closed", mouth="o")}</g>', self.arm("L"), self.arm("R"), extra_after=zs)))
        # react poke
        style = """
.recoil { transform-origin: 7.5px 15px; animation: recoil 2.5s ease-out both; }
@keyframes recoil { 0% { transform: translateX(0); } 8% { transform: translateX(-1.2px) rotate(-3deg); } 30%,100% { transform: translateX(0) rotate(0); } }
#arm-R { animation: wag 0.5s infinite alternate ease-in-out; }
@keyframes wag { from { transform: rotate(-95deg); } to { transform: rotate(-120deg); } }
#shadow-js { transform-origin: 7.5px 15px; }
""" + self.POP
        self.write("react-poke.svg", self.svg(style, self.figure(
            self.head(eyes="squint", mouth="frown", brows="angry", eyes_id=False), self.arm("L"), self.arm("R"), body_cls="recoil",
            extra_after=speech_bubble([C["poke"]], 7.5, -4.2, scale=0.6, colors=[C["accent"]]))))
        # react double
        style = """
.jump { transform-origin: 7.5px 15px; animation: jump 0.8s ease-out both; }
@keyframes jump { 0% { transform: translateY(0); } 40% { transform: translateY(-4px); } 100% { transform: translateY(0); } }
#shadow-js { transform-origin: 7.5px 15px; animation: sh 0.8s ease-out both; }
@keyframes sh { 0%,100% { transform: scaleX(1); } 40% { transform: scaleX(0.6); opacity: 0.2; } }
#arm-L { animation: up 0.8s both; } #arm-R { animation: upR 0.8s both; }
@keyframes up { 0% { transform: rotate(0); } 40%,100% { transform: rotate(160deg); } }
@keyframes upR { 0% { transform: rotate(0); } 40%,100% { transform: rotate(-160deg); } }
.bubble { transform-origin: 7.5px -4px; animation: pop 0.5s 0.3s ease-out both; }
@keyframes pop { 0% { transform: scale(0); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
"""
        self.write("react-double.svg", self.svg(style, self.figure(
            self.head(eyes="happy", mouth="grin", eyes_id=False), self.arm("L"), self.arm("R"), body_cls="jump",
            extra_after=speech_bubble([C["double"]], 7.5, -5.2, scale=0.6, colors=[C["accent2"]]))))
        # react drag
        style = """
#arm-L { animation: flailL 0.3s infinite alternate ease-in-out; } #arm-R { animation: flailR 0.3s infinite alternate ease-in-out; }
@keyframes flailL { from { transform: rotate(120deg); } to { transform: rotate(60deg); } }
@keyframes flailR { from { transform: rotate(-120deg); } to { transform: rotate(-60deg); } }
#leg-L { transform-origin: 5.5px 13.4px; animation: kick 0.35s infinite alternate ease-in-out; }
#leg-R { transform-origin: 10.5px 13.4px; animation: kick 0.35s 0.17s infinite alternate-reverse ease-in-out both; }
@keyframes kick { from { transform: rotate(-12deg); } to { transform: rotate(12deg); } }
.sway { transform-origin: 7.5px 9px; animation: sway 0.9s infinite ease-in-out; }
@keyframes sway { 0%,100% { transform: rotate(-4deg); } 50% { transform: rotate(4deg); } }
#shadow-js { opacity: 0.15; }
"""
        self.write("react-drag.svg", self.svg(style, self.figure(self.head(eyes="wide", mouth="o", brows="raised", eyes_id=False), self.arm("L"), self.arm("R"), body_cls="sway")))
        # idle wave
        style = B + "#arm-R { animation: wave 0.5s infinite alternate ease-in-out; }\n@keyframes wave { from { transform: rotate(-150deg); } to { transform: rotate(-175deg); } }\n"
        self.write("idle-wave.svg", self.svg(style, self.figure(self.head(eyes="wink", mouth="smile", eyes_id=False), self.arm("L"), self.arm("R"))))
        # idle special
        if C["idle_special"] == "golf":
            style = """
.breathe { transform-origin: 7.5px 15px; animation: twist 5s infinite ease-in-out; }
@keyframes twist { 0%,30%,100% { transform: rotate(0); } 45% { transform: rotate(-6deg); } 60% { transform: rotate(6deg); } }
#arm-L { transform: rotate(-35deg); } #arm-R { transform: rotate(35deg); }
.club { transform-origin: 7.9px 14.2px; animation: swing 5s infinite ease-in-out; }
@keyframes swing { 0%,30% { transform: rotate(-70deg); } 50% { transform: rotate(-70deg); } 58% { transform: rotate(80deg); } 80%,100% { transform: rotate(80deg); } }
.ball { animation: ball 5s infinite ease-out; }
@keyframes ball { 0%,57% { transform: translate(0,0); opacity: 1; } 90% { transform: translate(16px,-18px); opacity: 1; } 91%,100% { opacity: 0; } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
            club = f'<g class="club">{R(7.6, 8.5, 0.6, 6.2, GRAY)}{R(6.4, 14.4, 2.4, 0.9, GRAY_DK)}</g>{R(7.0, 12.6, 1.3, 1.1, C["skin"])}{R(8.0, 12.9, 1.3, 1.1, C["skin"])}'
            ball = f'<g class="ball">{R(9.2, 14.5, 0.9, 0.9, WHITE, f"stroke={chr(34)}{INK}{chr(34)} stroke-width={chr(34)}0.15{chr(34)}")}</g>'
            body = self.figure(self.head(eyes="down", pupil_dy=0.45, eyes_id=False), self.arm("L", hand=False), self.arm("R", hand=False), extra_front=club, extra_after=ball)
        elif C["idle_special"] == "dance":  # Musk's awkward dance
            style = """
.groove { transform-origin: 7.5px 15px; animation: groove 0.7s infinite ease-in-out; }
@keyframes groove { 0%,100% { transform: rotate(-5deg) translateY(0); } 50% { transform: rotate(5deg) translateY(-0.8px); } }
#arm-L { animation: dL 0.7s infinite ease-in-out; } #arm-R { animation: dR 0.7s infinite ease-in-out; }
@keyframes dL { 0%,100% { transform: rotate(150deg); } 50% { transform: rotate(80deg); } }
@keyframes dR { 0%,100% { transform: rotate(-80deg); } 50% { transform: rotate(-150deg); } }
#leg-L { transform-origin: 5.5px 13.4px; animation: kick 0.7s infinite ease-in-out; } #leg-R { transform-origin: 10.5px 13.4px; animation: kick 0.7s 0.35s infinite ease-in-out both; }
@keyframes kick { 0%,100% { transform: rotate(0); } 50% { transform: rotate(14deg); } }
.note { animation: note 1.4s infinite linear both; } .note2 { animation: note 1.4s 0.7s infinite linear both; }
@keyframes note { 0% { transform: translate(0,0); opacity: 0; } 20% { opacity: 1; } 100% { transform: translate(3px,-8px); opacity: 0; } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
            notes = (f'<g class="note">{R(16, 1, 0.7, 2.6, INK)}{R(15, 3.0, 1.6, 1.0, INK)}{R(16.7, 1, 1.2, 0.6, INK)}</g>'
                     f'<g class="note2">{R(-3, 3, 0.7, 2.6, INK)}{R(-4, 5.0, 1.6, 1.0, INK)}{R(-2.3, 3, 1.2, 0.6, INK)}</g>')
            body = self.figure(self.head(eyes="happy", mouth="grin", eyes_id=False), self.arm("L"), self.arm("R"), body_cls="groove", extra_after=notes)
        else:  # Jensen signing autographs
            style = self.BREATHE + """
#arm-R { animation: scribble 0.35s infinite alternate ease-in-out; }
@keyframes scribble { from { transform: rotate(-70deg); } to { transform: rotate(-95deg); } }
.ink { stroke-dasharray: 12; animation: draw 3s infinite linear; }
@keyframes draw { 0% { stroke-dashoffset: 12; opacity: 1; } 70% { stroke-dashoffset: 0; opacity: 1; } 90%,100% { opacity: 0; } }
"""
            pad = (f'{R(13.6, 7.2, 6.4, 4.4, WHITE, f"stroke={chr(34)}{INK}{chr(34)} stroke-width={chr(34)}0.35{chr(34)}")}'
                   f'<path class="ink" d="M14.6 10.2 q1.2 -2.4 2.2 0 t2.2 -1.2" fill="none" stroke="{INK}" stroke-width="0.4"/>'
                   f'{R(16.4, 5.2, 0.5, 2.4, "#1C1C1C")}')
            body = self.figure(self.head(eyes="down", pupil_dx=0.6, pupil_dy=0.3, mouth="smile", eyes_id=False), self.arm("L"), self.arm("R"), extra_after=pad)
        self.write("idle-special.svg", self.svg(style, body))
        # walk
        style = """
.bob { transform-origin: 7.5px 15px; animation: bob 0.5s infinite ease-in-out; }
@keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-0.6px); } }
#leg-L { transform-origin: 5.5px 13.4px; animation: stepL 0.5s infinite ease-in-out; } #leg-R { transform-origin: 10.5px 13.4px; animation: stepR 0.5s infinite ease-in-out; }
@keyframes stepL { 0%,100% { transform: rotate(18deg); } 50% { transform: rotate(-18deg); } }
@keyframes stepR { 0%,100% { transform: rotate(-18deg); } 50% { transform: rotate(18deg); } }
#arm-L { animation: swingL 0.5s infinite ease-in-out; } #arm-R { animation: swingR 0.5s infinite ease-in-out; }
@keyframes swingL { 0%,100% { transform: rotate(-25deg); } 50% { transform: rotate(25deg); } }
@keyframes swingR { 0%,100% { transform: rotate(25deg); } 50% { transform: rotate(-25deg); } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
        self.write("walk.svg", self.svg(style, self.figure(self.head(mouth="smile", pupil_dx=0.5, eyes_id=False), self.arm("L"), self.arm("R"), body_cls="bob")))
        # waking
        style = """
.stretch { transform-origin: 7.5px 15px; animation: stretch 1.5s ease-in-out both; }
@keyframes stretch { 0% { transform: scale(1,0.97); } 50% { transform: scale(1,1.03); } 100% { transform: scale(1,1); } }
#arm-L { animation: sL 1.5s both; } #arm-R { animation: sR 1.5s both; }
@keyframes sL { 0% { transform: rotate(0); } 50% { transform: rotate(150deg); } 100% { transform: rotate(0); } }
@keyframes sR { 0% { transform: rotate(0); } 50% { transform: rotate(-150deg); } 100% { transform: rotate(0); } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
        self.write("waking.svg", self.svg(style, self.figure(self.head(eyes="squint", mouth="o", eyes_id=False), self.arm("L"), self.arm("R"), body_cls="stretch")))
        self.theme_json()

    def theme_json(self):
        C = self.C
        cfg = {
            "schemaVersion": 1, "name": C["name"], "author": "Martin", "version": "1.1.0", "description": C["desc"],
            "customization": {"petTint": False},
            "viewBox": {"x": -15, "y": -25, "width": 45, "height": 45},
            "layout": {"contentBox": {"x": -1, "y": -5, "width": 18, "height": 22}, "centerX": 7.5, "baselineY": 17,
                       "visibleHeightRatio": 0.58, "baselineBottomRatio": 0.05},
            "eyeTracking": {"enabled": True, "states": ["idle"], "eyeRatioX": 0.5, "eyeRatioY": 0.5, "maxOffset": 0.6,
                            "bodyScale": 0.25, "shadowStretch": 0.15, "shadowShift": 0.3,
                            "ids": {"eyes": "eyes-js", "body": "body-js", "shadow": "shadow-js"}, "shadowOrigin": "7.5px 15px"},
            "states": {
                "idle": ["idle-follow.svg"], "thinking": ["thinking.svg"], "working": ["typing.svg"], "juggling": ["delegating.svg"],
                "error": ["error.svg"], "attention": ["done.svg"], "notification": ["notification.svg"],
                "sweeping": {"fallbackTo": "attention"}, "carrying": {"fallbackTo": "attention"},
                "sleeping": ["sleeping.svg"], "waking": ["waking.svg"], "roam": ["walk.svg"],
            },
            "sleepSequence": {"mode": "direct"},
            "workingTiers": [{"minSessions": 3, "file": "rally.svg"}, {"minSessions": 2, "file": "tier2.svg"}, {"minSessions": 1, "file": "typing.svg"}],
            "jugglingTiers": [{"minSessions": 1, "file": "delegating.svg"}],
            "idleAnimations": [{"file": "idle-wave.svg", "duration": 4000}, {"file": "idle-special.svg", "duration": 8000}],
            "timings": {"mouseIdleTimeout": 20000, "mouseSleepTimeout": 60000},
            "hitBoxes": {"default": {"x": 0, "y": -5, "w": 16, "h": 21}, "sleeping": {"x": 0, "y": -5, "w": 16, "h": 21}},
            "sleepingHitboxFiles": ["sleeping.svg"],
            "reactions": {"drag": {"file": "react-drag.svg"}, "clickLeft": {"file": "react-poke.svg", "duration": 2500},
                          "clickRight": {"file": "react-poke.svg", "duration": 2500}, "double": {"files": ["react-double.svg"], "duration": 3000}},
            "sounds": {"complete": "complete.mp3", "confirm": "confirm.mp3"},
            "miniMode": {"supported": False},
            "objectScale": {"widthRatio": 1.9, "heightRatio": 1.3, "offsetX": -0.45, "offsetY": -0.25},
        }
        with open(os.path.join(self.dir, "theme.json"), "w") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)

def tts_commands(cid):
    C = CHARACTERS[cid]
    d = os.path.join(THEMES_ROOT, cid, "sounds")
    return [
        ["edge-tts", "--voice", C["voice"], f"--rate={C['tts_rate']}", f"--pitch={C['tts_pitch']}", "--text", C["complete_tts"], "--write-media", os.path.join(d, "complete.mp3")],
        ["edge-tts", "--voice", C["voice"], f"--rate={C['tts_rate']}", f"--pitch={C['tts_pitch']}", "--text", C["confirm_tts"], "--write-media", os.path.join(d, "confirm.mp3")],
    ]

if __name__ == "__main__":
    ids = sys.argv[1:] or list(CHARACTERS)
    for cid in ids:
        Gen(cid).gen_all()
        print("generated", cid, "->", os.path.join(THEMES_ROOT, cid))
    # Placeholder TTS only on request: real-voice clips in sounds/ must not be overwritten.
    if "--tts" in sys.argv:
        ids = [i for i in ids if i != "--tts"]
        import subprocess
        for cid in ids:
            for cmd in tts_commands(cid):
                subprocess.run(cmd, check=False)
            print("tts", cid, CHARACTERS[cid]["complete_tts"])
