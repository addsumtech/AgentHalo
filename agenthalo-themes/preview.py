#!/usr/bin/env python3
"""Render all SVGs of a theme inline (ids prefixed per file), fast-forward CSS animations,
and screenshot with headless Chrome.
Usage: preview.py <theme-id> [seek_seconds] [out.png]
"""
import os, re, sys, subprocess

theme = sys.argv[1] if len(sys.argv) > 1 else "trump"
seek = float(sys.argv[2]) if len(sys.argv) > 2 else 2.7
out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), f"preview-{theme}.png")
A = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "themes", theme, "assets")
files = sorted(f for f in os.listdir(A) if f.endswith(".svg"))
order = ["idle-follow.svg", "thinking.svg", "typing.svg", "tier2.svg", "rally.svg", "delegating.svg", "done.svg", "error.svg",
         "notification.svg", "sleeping.svg", "react-poke.svg", "react-double.svg", "react-drag.svg", "idle-wave.svg",
         "idle-special.svg", "walk.svg", "waking.svg"]
files = [f for f in order if f in files] + [f for f in files if f not in order]
cells = []
for i, f in enumerate(files):
    s = open(os.path.join(A, f)).read()
    p = f"f{i}-"
    for _id in set(re.findall(r'id="([^"]+)"', s)):
        s = (s.replace(f'id="{_id}"', f'id="{p}{_id}"').replace(f'url(#{_id})', f'url(#{p}{_id})')
              .replace(f'#{_id} ', f'#{p}{_id} ').replace(f'#{_id},', f'#{p}{_id},').replace(f'#{_id}{{', f'#{p}{_id}{{'))
    s = re.sub(r'width="500" height="500"', 'width="100%" height="100%"', s)
    cells.append(f'<div class="c"><div class="t">{f}</div><div class="box">{s}</div></div>')
html = f'''<html><body style="margin:0;background:#2b2f3a;font-family:monospace">
<style>
.g{{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;padding:8px}}
.c{{background:#3a3f4d;border-radius:6px;padding:4px}}.t{{color:#cfd3dc;font-size:11px;margin-bottom:2px}}
.box{{background:#fff;border-radius:4px;aspect-ratio:1}} .box svg{{display:block}}
svg * {{ animation-delay: -{seek}s !important; animation-play-state: paused !important; }}
</style><div class="g">{"".join(cells)}</div></body></html>'''
htmlp = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"preview-{theme}.html")
open(htmlp, "w").write(html)
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless=new", "--disable-gpu",
                "--hide-scrollbars", "--window-size=1500,900", "--virtual-time-budget=500",
                f"--screenshot={out}", f"file://{htmlp}"], stderr=subprocess.DEVNULL)
print("wrote", out, "seek", seek)
