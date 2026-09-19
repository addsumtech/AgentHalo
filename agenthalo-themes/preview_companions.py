#!/usr/bin/env python3
"""Render a static overview and an animated local gallery for new companions.

Requires Pillow and rsvg-convert. SVGs remain the editable source of truth.
"""
import io
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from gen_companions import COMPANIONS, ROOT

CHARACTERS = {}
for cid in ("trump", "musk", "jensen", *COMPANIONS):
    meta = json.loads((ROOT / "themes" / cid / "theme.json").read_text())
    CHARACTERS[cid] = meta["name"]

OUT = ROOT / "docs" / "previews"
OUT.mkdir(parents=True, exist_ok=True)
font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
title_font = ImageFont.truetype(font_path, 24)
name_font = ImageFont.truetype(font_path, 18)
small_font = ImageFont.truetype(font_path, 14)
sheet = Image.new("RGB", (1200, 140 + ((len(CHARACTERS)+3)//4)*300), "#F1F2F5")
draw = ImageDraw.Draw(sheet)
draw.text((42, 27), f"AgentHalo · {len(CHARACTERS)} 位桌面伙伴", font=title_font, fill="#202B41")
draw.text((42, 66), "17 套状态动画 / 透明背景 / 随时切换", font=small_font, fill="#677086")
cards = []
for i, (cid, label) in enumerate(CHARACTERS.items()):
    png = subprocess.check_output(["rsvg-convert", "-w", "500", "-h", "500", str(ROOT / "themes" / cid / "assets" / "idle-follow.svg")])
    sprite = Image.open(io.BytesIO(png)).convert("RGBA")
    sprite = sprite.crop(sprite.getbbox())
    sprite.thumbnail((188, 176), Image.Resampling.NEAREST)
    x, y = 30 + (i % 4)*294, 110 + (i//4)*300
    draw.rounded_rectangle((x,y,x+278,y+284), radius=20, fill="white")
    sheet.paste(sprite,(x+(278-sprite.width)//2,y+25+(180-sprite.height)//2),sprite)
    parts = label.split(" · ")
    name = parts[0]
    english = parts[1] if len(parts) > 1 else cid.title()
    draw.text((x+22,y+220),name,font=name_font,fill="#202B41")
    draw.text((x+22,y+250),english,font=small_font,fill="#7E8798")
    cards.append(f'<article><div class="stage"><object type="image/svg+xml" data="../../themes/{cid}/assets/idle-follow.svg" data-character="{cid}"></object></div><h2>{name}</h2><p>{english}</p></article>')
sheet.save(OUT / "companions.png")
states = {"idle-follow":"待机","thinking":"思考","typing":"工作","tier2":"双任务","rally":"多任务","delegating":"协作","done":"完成","error":"错误","notification":"提醒","sleeping":"睡眠","waking":"唤醒","walk":"走动","idle-wave":"招手","idle-special":"专属道具","react-poke":"点击","react-double":"双击","react-drag":"拖动"}
options = "".join(f'<option value="{key}">{label}</option>' for key,label in states.items())
html = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AgentHalo 角色预览</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f1f2f5;color:#202b41;font-family:system-ui,sans-serif}}header{{padding:32px 4vw 20px;position:sticky;top:0;background:#f1f2f5ee;backdrop-filter:blur(16px);z-index:2}}h1{{font-size:26px;margin:0 0 18px}}.controls{{display:flex;align-items:center;gap:16px;flex-wrap:wrap}}select{{padding:8px 16px;border:1px solid #ccd1db;border-radius:9px;background:#fff}}main{{padding:8px 4vw 40px;display:grid;grid-template-columns:repeat(auto-fit,minmax(235px,1fr));gap:20px}}article{{background:white;border-radius:18px;padding:10px 24px 22px;overflow:hidden}}.stage{{height:270px;display:grid;place-items:center;background:radial-gradient(ellipse at 50% 78%,#e8ebf2 0,transparent 55%)}}object{{height:var(--size,260px);width:var(--size,260px);pointer-events:none;max-width:none}}h2{{font-size:19px;margin:5px 0}}p{{font-size:14px;color:#7e8798;margin:0}}input{{accent-color:#446dcc}}
</style><header><h1>AgentHalo · {len(CHARACTERS)} 位桌面伙伴</h1><div class="controls"><label>状态 <select id="state">{options}</select></label><label>预览大小 <input id="size" type="range" min="140" max="390" value="260"></label><span>桌宠设置 → Theme 切换角色；右键 → 大小调整</span></div></header><main>{''.join(cards)}</main><script>
document.querySelector('#state').onchange=e=>document.querySelectorAll('object').forEach(o=>o.data=`../../themes/${{o.dataset.character}}/assets/${{e.target.value}}.svg`);
document.querySelector('#size').oninput=e=>document.documentElement.style.setProperty('--size',e.target.value+'px');
</script></html>'''
(OUT / "companions.html").write_text(html)
print(OUT / "companions.png")
print(OUT / "companions.html")
