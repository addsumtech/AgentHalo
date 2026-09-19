#!/usr/bin/env python3
"""Generate the "Trump" pixel theme for Clawd on Desk.

One character spec (pixel grid in Clawd's viewBox units), many states.
Every state is an SVG with CSS @keyframes animation; no scripts (external
themes are sanitized by Clawd). Output goes to the Clawd user themes dir.
"""
import os, json, math

THEME_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "themes", "trump")
ASSETS = os.path.join(THEME_DIR, "assets")
os.makedirs(ASSETS, exist_ok=True)
os.makedirs(os.path.join(THEME_DIR, "sounds"), exist_ok=True)

VIEWBOX = "-15 -25 45 45"

# ---------------------------------------------------------------- palette
HAIR, HAIR_HI, HAIR_SH = "#F2C233", "#FFE27A", "#D19A1F"
SKIN, SKIN_SH, BLUSH = "#F0A868", "#D98A4E", "#E88E62"
WHITE, PUPIL, BROW = "#FFFFFF", "#1E2A47", "#C9921B"
MOUTH, MOUTH_DK, TEETH = "#B9483A", "#7A2A22", "#FFFFFF"
SUIT, SUIT_DK, TIE, SHOE = "#1B2B4E", "#122040", "#D62828", "#111111"
CAP, CAP_DK = "#C8102E", "#8E0B21"
GRAY, GRAY_DK, SCREEN = "#8A93A6", "#4A5468", "#BFE3FF"
RED, BLUE_TXT, INK = "#D62828", "#1F3C88", "#1E2A47"
BUBBLE_BG, BUBBLE_STROKE = "#FFFFFF", "#1E2A47"

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
 ".": ["000","000","000","000","010"], "'": ["010","010","000","000","000"],
 " ": ["000","000","000","000","000"],
}

def R(x, y, w, h, fill, extra=""):
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}"{(" " + extra) if extra else ""}/>'

def run_rects(cells, fill, extra=""):
    """cells: iterable of (x, y) unit cells -> merged horizontal run rects."""
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
    """Render uppercase text with the 3x5 font. (x,y) = top-left, returns svg."""
    cells = []
    cx = 0
    for ch in s.upper():
        g = FONT.get(ch, FONT[" "])
        for row, bits in enumerate(g):
            for col, b in enumerate(bits):
                if b == "1":
                    cells.append((cx + col, row))
        cx += 4
    rects = []
    for (px, py) in cells:
        rects.append(f'<rect x="{x + px*scale:.3f}" y="{y + py*scale:.3f}" width="{scale:.3f}" height="{scale:.3f}" fill="{fill}"/>')
    return "\n".join(rects)

def speech_bubble(lines, cx, bottom_y, scale=0.55, colors=None, tail=True, cls="bubble", pad=1.2, tail_x=None):
    """Pixel speech bubble centered at cx with its bottom (tail tip) at bottom_y."""
    colors = colors or [INK] * len(lines)
    w = max(text_width(l, scale) for l in lines) + pad * 2
    line_h = 5 * scale
    gap = 1.5 * scale
    h = len(lines) * line_h + (len(lines) - 1) * gap + pad * 2
    x0 = cx - w / 2
    tail_h = 2.2 if tail else 0
    y0 = bottom_y - tail_h - h
    parts = [f'<g class="{cls}">']
    parts.append(f'<rect x="{x0:.3f}" y="{y0:.3f}" width="{w:.3f}" height="{h:.3f}" rx="1" ry="1" fill="{BUBBLE_BG}" stroke="{BUBBLE_STROKE}" stroke-width="0.5"/>')
    if tail:
        tx = cx if tail_x is None else tail_x
        parts.append(f'<polygon points="{tx-1.3:.3f},{y0+h-0.3:.3f} {tx+1.3:.3f},{y0+h-0.3:.3f} {tx:.3f},{bottom_y:.3f}" fill="{BUBBLE_BG}" stroke="{BUBBLE_STROKE}" stroke-width="0.5" stroke-linejoin="round"/>')
        parts.append(f'<rect x="{tx-1.2:.3f}" y="{y0+h-0.7:.3f}" width="{2.4:.3f}" height="{0.8:.3f}" fill="{BUBBLE_BG}"/>')
    ty = y0 + pad
    for line, col in zip(lines, colors):
        tw = text_width(line, scale)
        parts.append(pixel_text(line, cx - tw / 2, ty, scale, col))
        ty += line_h + gap
    parts.append("</g>")
    return "\n".join(parts)

# ---------------------------------------------------------------- character parts
def hair(cap=False):
    cells = []
    def row(y, a, b): cells.extend((x, y) for x in range(a, b + 1))
    if not cap:
        row(-3, 5, 10)
    row(-2, 3, 12); row(-1, 2, 13); row(0, 1, 13)
    row(1, 1, 6); row(1, 12, 13)
    row(2, 1, 3); row(2, 13, 13)
    row(3, 2, 2); row(3, 13, 13)
    row(4, 2, 2); row(4, 13, 13)
    out = [run_rects(cells, HAIR)]
    hi = [(x, -2) for x in range(4, 7)] + [(x, 0) for x in range(2, 5)] + [(x, -1) for x in range(9, 12)]
    if cap:
        hi = [(x, 0) for x in range(2, 5)] + [(x, -1) for x in range(9, 12)]
    out.append(run_rects(hi, HAIR_HI))
    out.append(run_rects([(5, 1), (6, 1), (2, 2), (3, 2), (12, 1)], HAIR_SH))
    if cap:
        out.append(R(3, -4.6, 10, 3.1, CAP))
        out.append(R(1.4, -1.7, 13.2, 0.9, CAP_DK))
        out.append(R(3, -4.6, 10, 0.6, CAP_DK, 'opacity="0.35"'))
        s = 0.42
        out.append(pixel_text("MAGA", 8 - text_width("MAGA", s) / 2, -3.9, s, WHITE))
    return "\n".join(out)

def face(eyes="open", mouth="pursed", pupil_dx=0.0, pupil_dy=0.0, brows="normal", eyes_id=True):
    cells = []
    def row(y, a, b): cells.extend((x, y) for x in range(a, b + 1))
    row(1, 7, 11); row(2, 4, 12); row(3, 3, 12); row(4, 3, 12)
    row(5, 3, 12); row(6, 3, 12); row(7, 4, 11); row(8, 5, 10)
    out = [run_rects(cells, SKIN)]
    out.append(R(5, 8, 6, 0.6, SKIN_SH))            # chin shade
    out.append(R(3.4, 5.9, 1.1, 0.7, BLUSH)); out.append(R(11.5, 5.9, 1.1, 0.7, BLUSH))
    out.append(R(7.5, 5.7, 1, 0.6, SKIN_SH))         # nose
    # brows
    if brows == "normal":
        out.append(R(5, 3.1, 2, 0.6, BROW)); out.append(R(9, 3.1, 2, 0.6, BROW))
    elif brows == "raised":
        out.append(R(5, 2.4, 2, 0.6, BROW)); out.append(R(9, 2.4, 2, 0.6, BROW))
    elif brows == "angry":
        out.append(f'<rect x="5" y="3" width="2" height="0.6" fill="{BROW}" transform="rotate(14 6 3.3)"/>')
        out.append(f'<rect x="9" y="3" width="2" height="0.6" fill="{BROW}" transform="rotate(-14 10 3.3)"/>')
    elif brows == "sad":
        out.append(f'<rect x="5" y="3" width="2" height="0.6" fill="{BROW}" transform="rotate(-12 6 3.3)"/>')
        out.append(f'<rect x="9" y="3" width="2" height="0.6" fill="{BROW}" transform="rotate(12 10 3.3)"/>')
    # eyes
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
            out.append(R(5, 4.2, 2, 0.5, SKIN)); out.append(R(9, 4.2, 2, 0.5, SKIN))
    elif eyes == "closed":
        out.append(R(5, 4.9, 2, 0.55, PUPIL)); out.append(R(9, 4.9, 2, 0.55, PUPIL))
    elif eyes == "happy":  # ^ ^ closed happy arcs
        out.append(R(5, 4.6, 0.7, 0.5, PUPIL)); out.append(R(5.65, 4.2, 0.7, 0.5, PUPIL)); out.append(R(6.3, 4.6, 0.7, 0.5, PUPIL))
        out.append(R(9, 4.6, 0.7, 0.5, PUPIL)); out.append(R(9.65, 4.2, 0.7, 0.5, PUPIL)); out.append(R(10.3, 4.6, 0.7, 0.5, PUPIL))
    # mouth
    if mouth == "pursed":
        out.append(R(7, 7, 2, 0.8, MOUTH))
    elif mouth == "grin":
        out.append(R(6, 6.7, 4, 1.4, MOUTH_DK)); out.append(R(6.3, 6.9, 3.4, 0.5, TEETH))
    elif mouth == "smile":
        out.append(R(6.3, 7.1, 3.4, 0.6, MOUTH)); out.append(R(6, 6.6, 0.5, 0.6, MOUTH)); out.append(R(9.5, 6.6, 0.5, 0.6, MOUTH))
    elif mouth == "frown":
        out.append(R(6.5, 6.8, 3, 0.6, MOUTH)); out.append(R(6.2, 7.3, 0.5, 0.6, MOUTH)); out.append(R(9.3, 7.3, 0.5, 0.6, MOUTH))
    elif mouth == "open":
        out.append(R(7, 6.7, 2.2, 1.6, MOUTH_DK)); out.append(R(7.2, 6.9, 1.8, 0.4, TEETH))
    elif mouth == "o":
        out.append(R(7.3, 6.8, 1.4, 1.2, MOUTH_DK))
    elif mouth == "shout":
        out.append(R(6.4, 6.5, 3.2, 2, MOUTH_DK)); out.append(R(6.7, 6.7, 2.6, 0.5, TEETH))
    return "\n".join(out)

def head(cap=False, **face_kw):
    return f'<g id="head">\n{hair(cap)}\n{face(**face_kw)}\n</g>'

def torso(tie_swing=False):
    out = [R(3, 9, 10, 4.6, SUIT)]
    out.append(f'<polygon points="6,9 10,9 8,11.6" fill="{WHITE}"/>')
    out.append(f'<polygon points="5.2,9 6.2,9 7.6,11.8 7.1,12.6" fill="{SUIT_DK}"/>')
    out.append(f'<polygon points="9.8,9 10.8,9 8.9,12.6 8.4,11.8" fill="{SUIT_DK}"/>')
    cls = ' class="tie"' if tie_swing else ""
    out.append(f'<g{cls}><rect x="7.55" y="9.3" width="0.9" height="0.7" fill="{TIE}"/>'
               f'<polygon points="7.5,10 8.5,10 8.65,14.4 8,15.1 7.35,14.4" fill="{TIE}"/></g>')
    return "\n".join(out)

STATIC_CSS = []  # per-state CSS rules collected while building parts; consumed by svg()
BASE_CSS = "#arm-L { transform-origin: 2.25px 9.5px; } #arm-R { transform-origin: 13.75px 9.5px; }"

def arm(side, rotate=0.0, cls=None, hand=True):
    """side 'L' shoulder at (2.25,9.5) / 'R' at (13.75,9.5). rotate in deg (SVG clockwise+).
    Static rotation goes through CSS (same origin as animations) — never mix the
    transform attribute with CSS transform-origin, Chrome applies the origin twice."""
    if side == "L":
        x = 1.5
    else:
        x = 13.0
    c = f' class="{cls}"' if cls else ""
    if rotate:
        STATIC_CSS.append(f"#arm-{side} {{ transform: rotate({rotate:g}deg); }}")
    parts = [f'<g id="arm-{side}"{c}>', R(x, 9.3, 1.5, 4.0, SUIT)]
    if hand:
        parts.append(R(x + 0.1, 13.1, 1.3, 1.1, SKIN))
    parts.append("</g>")
    return "\n".join(parts)

def legs(cls_l=None, cls_r=None):
    cl = f' class="{cls_l}"' if cls_l else ""
    cr = f' class="{cls_r}"' if cls_r else ""
    return (f'<g id="leg-L"{cl}>{R(4, 13.4, 3, 1.4, SUIT_DK)}{R(3.6, 14.6, 3.6, 0.8, SHOE)}</g>'
            f'<g id="leg-R"{cr}>{R(9, 13.4, 3, 1.4, SUIT_DK)}{R(8.8, 14.6, 3.6, 0.8, SHOE)}</g>')

def shadow(cls=None):
    c = f' class="{cls}"' if cls else ""
    sh = R(2.5, 15.3, 11, 0.9, "#000000", 'opacity="0.35"')
    return f'<g id="shadow-js"{c}>{sh}</g>'

def svg(style, body):
    static = "\n".join(STATIC_CSS)
    STATIC_CSS.clear()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VIEWBOX}" width="500" height="500" shape-rendering="crispEdges">\n'
            f'<defs><style>\n{BASE_CSS}\n{static}\n{style}\n</style></defs>\n{body}\n</svg>\n')

def write(name, content):
    with open(os.path.join(ASSETS, name), "w") as f:
        f.write(content)
    print("wrote", name)

BREATHE = """
.breathe { transform-origin: 7.5px 15px; animation: breathe 3.4s infinite ease-in-out; }
@keyframes breathe { 0%,100% { transform: scale(1,1); } 50% { transform: scale(1.015,0.985); } }
.pupils { transform-origin: 7.5px 4.8px; animation: blink 4.6s infinite ease-in-out; }
@keyframes blink { 0%,8%,100% { transform: scaleY(1); } 4% { transform: scaleY(0.1); } }
#eyes-js, #body-js, #shadow-js { transition: transform 0.2s ease-out; }
#shadow-js { transform-origin: 7.5px 15px; }
"""

def figure(head_svg, arm_l, arm_r, legs_svg=None, body_cls="breathe", extra_in_body="", extra_after="", extra_front=""):
    """Layer order: shadow, legs, [body: arms, torso, extra_in_body, head, extra_front], extra_after."""
    legs_svg = legs_svg if legs_svg is not None else legs()
    return (f'{shadow()}\n{legs_svg}\n<g id="body-js"><g class="{body_cls}">\n{arm_l}\n{arm_r}\n{torso()}\n{extra_in_body}\n{head_svg}\n{extra_front}\n</g></g>\n{extra_after}')

# ---------------------------------------------------------------- states
def gen_idle():
    body = figure(head(eyes="open", mouth="pursed"), arm("L"), arm("R"))
    write("idle-follow.svg", svg(BREATHE, body))

def gen_thinking():
    style = BREATHE + """
.tilt { transform-origin: 7.5px 15px; animation: tilt 2.6s infinite ease-in-out; }
@keyframes tilt { 0%,100% { transform: rotate(-2deg); } 50% { transform: rotate(2deg); } }
.dot1 { animation: dot 1.5s infinite; } .dot2 { animation: dot 1.5s 0.25s infinite both; } .dot3 { animation: dot 1.5s 0.5s infinite both; }
@keyframes dot { 0%,100% { opacity: 0.25; } 50% { opacity: 1; } }
.cloud { animation: float 3s infinite ease-in-out; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-0.6px); } }
"""
    cloud = f'''<g class="cloud">
<circle cx="14.5" cy="-1.5" r="0.8" fill="{WHITE}" stroke="{INK}" stroke-width="0.35"/>
<circle cx="16.6" cy="-4.2" r="1.2" fill="{WHITE}" stroke="{INK}" stroke-width="0.35"/>
<rect x="15.2" y="-11.5" width="10" height="5.8" rx="2.6" fill="{WHITE}" stroke="{INK}" stroke-width="0.4"/>
<rect class="dot1" x="17.2" y="-9.2" width="1.3" height="1.3" fill="{INK}"/>
<rect class="dot2" x="19.5" y="-9.2" width="1.3" height="1.3" fill="{INK}"/>
<rect class="dot3" x="21.8" y="-9.2" width="1.3" height="1.3" fill="{INK}"/>
</g>'''
    body = figure(head(eyes="open", mouth="pursed", pupil_dx=0.55, pupil_dy=-0.4, brows="raised", eyes_id=False),
                  arm("L"), arm("R", rotate=135), body_cls="tilt", extra_after=cloud)
    write("thinking.svg", svg(style, body))

def gen_typing():
    style = BREATHE + """
.hand-l { animation: tap 0.28s infinite alternate ease-in-out; }
.hand-r { animation: tap 0.28s 0.14s infinite alternate ease-in-out both; }
@keyframes tap { from { transform: translateY(0); } to { transform: translateY(-0.6px); } }
.screen { animation: glow 1.2s infinite step-end; }
@keyframes glow { 0%,100% { opacity: 0.85; } 50% { opacity: 1; } }
.code1 { animation: code 1.6s infinite step-end; } .code2 { animation: code 1.6s 0.4s infinite step-end both; } .code3 { animation: code 1.6s 0.8s infinite step-end both; }
@keyframes code { 0% { opacity: 0; } 30%,100% { opacity: 1; } }
"""
    laptop = f'''<g id="laptop">
{R(3.6, 12.2, 8.8, 1.2, GRAY_DK)}{R(4.2, 8.6, 7.6, 3.7, GRAY)}{R(4.6, 9.0, 6.8, 2.9, SCREEN, 'class="screen"')}
{R(5.0, 9.4, 2.6, 0.5, BLUE_TXT, 'class="code1"')}{R(5.0, 10.2, 4.0, 0.5, RED, 'class="code2"')}{R(5.0, 11.0, 3.2, 0.5, INK, 'class="code3"')}
<g class="hand-l">{R(5.0, 11.4, 1.4, 0.9, SKIN)}</g><g class="hand-r">{R(9.6, 11.4, 1.4, 0.9, SKIN)}</g>
</g>'''
    body = figure(head(eyes="down", mouth="pursed", pupil_dy=0.45, eyes_id=False),
                  arm("L", rotate=-25, hand=False), arm("R", rotate=25, hand=False), extra_in_body=laptop)
    write("typing.svg", svg(style, body))

def gen_tweeting():
    style = BREATHE + """
.thumb { animation: tap 0.3s infinite alternate ease-in-out; }
@keyframes tap { from { transform: translateY(0); } to { transform: translateY(-0.4px); } }
.dots rect { animation: dot 1.2s infinite; } .dots rect:nth-child(2) { animation-delay: 0.2s; } .dots rect:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot { 0%,100% { opacity: 0.2; } 50% { opacity: 1; } }
.bird { animation: fly 4s infinite linear; }
@keyframes fly { 0% { transform: translate(0,0); opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { transform: translate(6px,-9px); opacity: 0; } }
"""
    phone = f'''<g id="phone">{R(10.4, 4.3, 2.0, 3.4, "#222")}{R(10.7, 4.6, 1.4, 2.6, SCREEN)}
<g class="dots">{R(10.85, 5.6, 0.35, 0.35, INK)}{R(11.35, 5.6, 0.35, 0.35, INK)}{R(11.85, 5.6, 0.35, 0.35, INK)}</g>
<g class="thumb">{R(11.9, 7.2, 0.9, 0.7, SKIN)}</g></g>
<g class="bird">{R(13.5, 2.5, 1.2, 0.8, "#1DA1F2")}{R(14.7, 2.1, 0.6, 0.6, "#1DA1F2")}{R(12.9, 2.9, 0.6, 0.5, "#1DA1F2")}</g>'''
    body = figure(head(eyes="down", mouth="pursed", pupil_dx=0.6, pupil_dy=0.3, eyes_id=False),
                  arm("L"), arm("R", rotate=150), extra_front=phone)
    write("tweeting.svg", svg(style, body))

def gen_rally():
    style = """
.bounce { transform-origin: 7.5px 15px; animation: bounce 0.6s infinite ease-in-out; }
@keyframes bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-1px); } }
#arm-L { animation: pumpL 0.6s infinite ease-in-out; } #arm-R { animation: pumpR 0.6s 0.3s infinite ease-in-out both; }
@keyframes pumpL { 0%,100% { transform: rotate(160deg); } 50% { transform: rotate(120deg); } }
@keyframes pumpR { 0%,100% { transform: rotate(-160deg); } 50% { transform: rotate(-120deg); } }
.bubble { transform-origin: 7.5px -3px; animation: pop 2.4s infinite; }
@keyframes pop { 0%,15% { transform: scale(0); opacity: 0; } 25%,75% { transform: scale(1); opacity: 1; } 85%,100% { transform: scale(0); opacity: 0; } }
.confetti rect { animation: fall 1.8s infinite linear; }
.confetti rect:nth-child(2n) { animation-duration: 2.3s; animation-delay: 0.5s; } .confetti rect:nth-child(3n) { animation-delay: 1.1s; }
@keyframes fall { 0% { transform: translateY(-6px); opacity: 0; } 15% { opacity: 1; } 100% { transform: translateY(14px); opacity: 0; } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
    confetti = '<g class="confetti">' + "".join(
        R(x, -8, 0.8, 0.8, c) for x, c in [(-3, RED), (0, WHITE), (3, BLUE_TXT), (12, RED), (15, WHITE), (18, BLUE_TXT), (-6, BLUE_TXT), (21, RED)]) + '</g>'
    bubble = speech_bubble(["HUGE!"], 7.5, -4.2, scale=0.75, colors=[RED])
    body = figure(head(eyes="open", mouth="shout", brows="raised", eyes_id=False), arm("L"), arm("R"),
                  body_cls="bounce", extra_after=confetti + bubble)
    write("rally.svg", svg(style, body))

def gen_delegating():
    style = BREATHE + """
#arm-L { animation: pointL 1.6s infinite ease-in-out; } #arm-R { animation: pointR 1.6s infinite ease-in-out; }
@keyframes pointL { 0%,40%,100% { transform: rotate(0deg); } 15%,30% { transform: rotate(95deg); } }
@keyframes pointR { 0%,50%,100% { transform: rotate(0deg); } 65%,80% { transform: rotate(-95deg); } }
.pupils { animation: look 1.6s infinite ease-in-out; }
@keyframes look { 0%,40%,100% { transform: translateX(-0.5px); } 50%,90% { transform: translateX(0.5px); } }
.tag { animation: tagpop 1.6s infinite; } .tag2 { animation: tagpop 1.6s 0.8s infinite both; }
@keyframes tagpop { 0%,10%,45%,100% { opacity: 0; } 15%,35% { opacity: 1; } }
"""
    tags = (f'<g class="tag">{pixel_text("YOU!", -7.5, 2.5, 0.5, INK)}</g>'
            f'<g class="tag2">{pixel_text("YOU!", 15.5, 2.5, 0.5, INK)}</g>')
    body = figure(head(eyes="open", mouth="smile", eyes_id=False), arm("L"), arm("R"), extra_after=tags)
    write("delegating.svg", svg(style, body))

def gen_maga():
    style = """
.bounce { transform-origin: 7.5px 15px; animation: bounce 0.7s infinite ease-in-out; }
@keyframes bounce { 0%,100% { transform: translateY(0) scale(1,1); } 50% { transform: translateY(-1.4px) scale(1.02,0.98); } }
#shadow-js { transform-origin: 7.5px 15px; animation: sh 0.7s infinite ease-in-out; }
@keyframes sh { 0%,100% { transform: scaleX(1); opacity: 0.35; } 50% { transform: scaleX(0.85); opacity: 0.25; } }
#arm-L { animation: waveL 0.35s infinite alternate ease-in-out; } #arm-R { animation: waveR 0.35s infinite alternate ease-in-out; }
@keyframes waveL { from { transform: rotate(150deg); } to { transform: rotate(170deg); } }
@keyframes waveR { from { transform: rotate(-150deg); } to { transform: rotate(-170deg); } }
.bubble { transform-origin: 7.5px -6px; animation: pop 0.5s ease-out both; }
@keyframes pop { 0% { transform: scale(0); opacity: 0; } 70% { transform: scale(1.08); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
.spark rect { animation: twinkle 1.2s infinite step-end; } .spark rect:nth-child(2n) { animation-delay: 0.4s; } .spark rect:nth-child(3n) { animation-delay: 0.8s; }
@keyframes twinkle { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
"""
    sparks = '<g class="spark">' + "".join(
        R(x, y, 0.9, 0.9, c) for x, y, c in [(-4, 2, RED), (-6, 6, WHITE), (-2, -3, BLUE_TXT), (18, 3, RED), (20, 7, WHITE), (16, -2, BLUE_TXT), (-5, 11, BLUE_TXT), (19, 12, RED)]) + '</g>'
    bubble = speech_bubble(["MAKE AMERICA", "GREAT AGAIN!"], 7.5, -5.6, scale=0.55, colors=[RED, BLUE_TXT])
    body = figure(head(cap=True, eyes="happy", mouth="grin"), arm("L"), arm("R"),
                  body_cls="bounce", extra_after=sparks + bubble)
    write("maga.svg", svg(style, body))

def gen_error():
    style = """
.shake { transform-origin: 7.5px 15px; animation: shake 0.5s infinite ease-in-out; }
@keyframes shake { 0%,100% { transform: translateX(0); } 25% { transform: translateX(-0.5px); } 75% { transform: translateX(0.5px); } }
.bubble { transform-origin: 7.5px -4px; animation: pop 0.4s ease-out both; }
@keyframes pop { 0% { transform: scale(0); } 100% { transform: scale(1); } }
.vein { animation: vein 0.8s infinite step-end; }
@keyframes vein { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
    crossed = f'{R(2.8, 10.6, 10.4, 1.9, SUIT)}{R(2.6, 10.9, 1.4, 1.2, SKIN)}{R(12.0, 10.9, 1.4, 1.2, SKIN)}'
    vein = f'<g class="vein">{R(12.6, 1.2, 0.5, 1.4, RED)}{R(12.1, 1.7, 1.4, 0.5, RED)}</g>'
    bubble = speech_bubble(["WRONG!"], 7.5, -4.2, scale=0.75, colors=[RED])
    body = figure(head(eyes="squint", mouth="frown", brows="angry", eyes_id=False),
                  arm("L", rotate=-20, hand=False), arm("R", rotate=20, hand=False),
                  body_cls="shake", extra_in_body=crossed, extra_after=vein + bubble)
    write("error.svg", svg(style, body))

def gen_notification():
    style = BREATHE + """
.mark { transform-origin: 7.5px -6px; animation: hop 0.7s infinite ease-in-out; }
@keyframes hop { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-1.2px); } }
#arm-R { animation: raise 1.4s infinite ease-in-out; }
@keyframes raise { 0%,100% { transform: rotate(-165deg); } 50% { transform: rotate(-150deg); } }
"""
    mark = f'<g class="mark">{R(6.6, -12, 1.8, 5, RED)}{R(6.6, -6, 1.8, 1.8, RED)}</g>'
    bubble = speech_bubble(["SIGN HERE!"], 19, -1.5, scale=0.5, colors=[INK], tail_x=16)
    body = figure(head(eyes="wide", mouth="o", brows="raised", eyes_id=False), arm("L"), arm("R"),
                  extra_after=mark + bubble)
    write("notification.svg", svg(style, body))

def gen_sleeping():
    style = """
.nod { transform-origin: 7.5px 8.5px; animation: nod 4s infinite ease-in-out; }
@keyframes nod { 0%,100% { transform: rotate(-4deg); } 50% { transform: rotate(3deg); } }
.breathe { transform-origin: 7.5px 15px; animation: breathe 4s infinite ease-in-out; }
@keyframes breathe { 0%,100% { transform: scale(1,1); } 50% { transform: scale(1.02,0.98); } }
.z1 { animation: zz 3.6s infinite linear; } .z2 { animation: zz 3.6s 1.2s infinite linear both; } .z3 { animation: zz 3.6s 2.4s infinite linear both; }
@keyframes zz { 0% { transform: translate(0,0) scale(0.6); opacity: 0; } 15% { opacity: 1; } 100% { transform: translate(4px,-9px) scale(1.3); opacity: 0; } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
    zs = "".join(f'<g class="z{i}" style="transform-origin:14px 0px">{pixel_text("Z", 13.5, -1.5, 0.6, INK)}</g>' for i in (1, 2, 3))
    hd = head(eyes="closed", mouth="o")
    body = figure(f'<g class="nod">{hd}</g>', arm("L"), arm("R"), extra_after=zs)
    write("sleeping.svg", svg(style, body))

def gen_react_poke():
    style = """
.recoil { transform-origin: 7.5px 15px; animation: recoil 2.5s ease-out both; }
@keyframes recoil { 0% { transform: translateX(0); } 8% { transform: translateX(-1.2px) rotate(-3deg); } 30%,100% { transform: translateX(0) rotate(0); } }
.bubble { transform-origin: 7.5px -4px; animation: pop 0.35s ease-out both; }
@keyframes pop { 0% { transform: scale(0); } 100% { transform: scale(1); } }
#arm-R { animation: wag 0.5s infinite alternate ease-in-out; }
@keyframes wag { from { transform: rotate(-95deg); } to { transform: rotate(-120deg); } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
    bubble = speech_bubble(["FAKE NEWS!"], 7.5, -4.2, scale=0.6, colors=[RED])
    body = figure(head(eyes="squint", mouth="frown", brows="angry", eyes_id=False), arm("L"), arm("R"),
                  body_cls="recoil", extra_after=bubble)
    write("react-poke.svg", svg(style, body))

def gen_react_double():
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
    bubble = speech_bubble(["TREMENDOUS!"], 7.5, -5.2, scale=0.6, colors=[BLUE_TXT])
    body = figure(head(eyes="happy", mouth="grin", eyes_id=False), arm("L"), arm("R"), body_cls="jump", extra_after=bubble)
    write("react-double.svg", svg(style, body))

def gen_react_drag():
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
    body = figure(head(eyes="wide", mouth="o", brows="raised", eyes_id=False), arm("L"), arm("R"), body_cls="sway")
    write("react-drag.svg", svg(style, body))

def gen_idle_wave():
    style = BREATHE + """
#arm-R { animation: wave 0.5s infinite alternate ease-in-out; }
@keyframes wave { from { transform: rotate(-150deg); } to { transform: rotate(-175deg); } }
"""
    body = figure(head(eyes="wink", mouth="smile", eyes_id=False), arm("L"), arm("R"))
    write("idle-wave.svg", svg(style, body))

def gen_idle_golf():
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
    club = f'<g class="club">{R(7.6, 8.5, 0.6, 6.2, GRAY)}{R(6.4, 14.4, 2.4, 0.9, GRAY_DK)}</g>'
    ball_rect = R(9.2, 14.5, 0.9, 0.9, WHITE, f'stroke="{INK}" stroke-width="0.15"')
    ball = f'<g class="ball">{ball_rect}</g>'
    hands = f'{R(7.0, 12.6, 1.3, 1.1, SKIN)}{R(8.0, 12.9, 1.3, 1.1, SKIN)}'
    body = figure(head(eyes="down", mouth="pursed", pupil_dy=0.45, eyes_id=False),
                  arm("L", hand=False), arm("R", hand=False), extra_front=club + hands, extra_after=ball)
    write("idle-golf.svg", svg(style, body))

def gen_walk():
    style = """
.bob { transform-origin: 7.5px 15px; animation: bob 0.5s infinite ease-in-out; }
@keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-0.6px); } }
#leg-L { transform-origin: 5.5px 13.4px; animation: stepL 0.5s infinite ease-in-out; }
#leg-R { transform-origin: 10.5px 13.4px; animation: stepR 0.5s infinite ease-in-out; }
@keyframes stepL { 0%,100% { transform: rotate(18deg); } 50% { transform: rotate(-18deg); } }
@keyframes stepR { 0%,100% { transform: rotate(-18deg); } 50% { transform: rotate(18deg); } }
#arm-L { animation: swingL 0.5s infinite ease-in-out; } #arm-R { animation: swingR 0.5s infinite ease-in-out; }
@keyframes swingL { 0%,100% { transform: rotate(-25deg); } 50% { transform: rotate(25deg); } }
@keyframes swingR { 0%,100% { transform: rotate(25deg); } 50% { transform: rotate(-25deg); } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
    body = figure(head(eyes="open", mouth="smile", pupil_dx=0.5, eyes_id=False), arm("L"), arm("R"), body_cls="bob")
    write("walk.svg", svg(style, body))

def gen_waking():
    style = """
.stretch { transform-origin: 7.5px 15px; animation: stretch 1.5s ease-in-out both; }
@keyframes stretch { 0% { transform: scale(1,0.97); } 50% { transform: scale(1,1.03); } 100% { transform: scale(1,1); } }
#arm-L { animation: sL 1.5s both; } #arm-R { animation: sR 1.5s both; }
@keyframes sL { 0% { transform: rotate(0); } 50% { transform: rotate(150deg); } 100% { transform: rotate(0); } }
@keyframes sR { 0% { transform: rotate(0); } 50% { transform: rotate(-150deg); } 100% { transform: rotate(0); } }
#shadow-js { transform-origin: 7.5px 15px; }
"""
    body = figure(head(eyes="squint", mouth="o", eyes_id=False), arm("L"), arm("R"), body_cls="stretch")
    write("waking.svg", svg(style, body))

# ---------------------------------------------------------------- theme.json
def gen_theme_json():
    cfg = {
        "schemaVersion": 1,
        "name": "Trump",
        "author": "Martin",
        "version": "1.0.0",
        "description": "Q版特朗普：任务完成时高呼 Make America Great Again",
        "customization": {"petTint": False},
        "viewBox": {"x": -15, "y": -25, "width": 45, "height": 45},
        "layout": {
            "contentBox": {"x": -1, "y": -5, "width": 18, "height": 22},
            "centerX": 7.5,
            "baselineY": 17,
            "visibleHeightRatio": 0.58,
            "baselineBottomRatio": 0.05,
        },
        "eyeTracking": {
            "enabled": True,
            "states": ["idle"],
            "eyeRatioX": 0.5, "eyeRatioY": 0.5,
            "maxOffset": 0.6, "bodyScale": 0.25,
            "shadowStretch": 0.15, "shadowShift": 0.3,
            "ids": {"eyes": "eyes-js", "body": "body-js", "shadow": "shadow-js"},
            "shadowOrigin": "7.5px 15px",
        },
        "states": {
            "idle": ["idle-follow.svg"],
            "thinking": ["thinking.svg"],
            "working": ["typing.svg"],
            "juggling": ["delegating.svg"],
            "error": ["error.svg"],
            "attention": ["maga.svg"],
            "notification": ["notification.svg"],
            "sweeping": {"fallbackTo": "attention"},
            "carrying": {"fallbackTo": "attention"},
            "sleeping": ["sleeping.svg"],
            "waking": ["waking.svg"],
            "roam": ["walk.svg"],
        },
        "sleepSequence": {"mode": "direct"},
        "workingTiers": [
            {"minSessions": 3, "file": "rally.svg"},
            {"minSessions": 2, "file": "tweeting.svg"},
            {"minSessions": 1, "file": "typing.svg"},
        ],
        "jugglingTiers": [
            {"minSessions": 1, "file": "delegating.svg"},
        ],
        "idleAnimations": [
            {"file": "idle-wave.svg", "duration": 4000},
            {"file": "idle-golf.svg", "duration": 10000},
        ],
        "timings": {"mouseIdleTimeout": 20000, "mouseSleepTimeout": 60000},
        "hitBoxes": {
            "default": {"x": 0, "y": -5, "w": 16, "h": 21},
            "sleeping": {"x": 0, "y": -5, "w": 16, "h": 21},
        },
        "sleepingHitboxFiles": ["sleeping.svg"],
        "reactions": {
            "drag": {"file": "react-drag.svg"},
            "clickLeft": {"file": "react-poke.svg", "duration": 2500},
            "clickRight": {"file": "react-poke.svg", "duration": 2500},
            "double": {"files": ["react-double.svg"], "duration": 3000},
        },
        "sounds": {"complete": "complete.mp3", "confirm": "confirm.mp3"},
        "miniMode": {"supported": False},
        "objectScale": {"widthRatio": 1.9, "heightRatio": 1.3, "offsetX": -0.45, "offsetY": -0.25},
    }
    with open(os.path.join(THEME_DIR, "theme.json"), "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print("wrote theme.json")

if __name__ == "__main__":
    for fn in [gen_idle, gen_thinking, gen_typing, gen_tweeting, gen_rally, gen_delegating, gen_maga,
               gen_error, gen_notification, gen_sleeping, gen_react_poke, gen_react_double, gen_react_drag,
               gen_idle_wave, gen_idle_golf, gen_walk, gen_waking]:
        fn()
    gen_theme_json()
