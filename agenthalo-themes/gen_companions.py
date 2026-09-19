#!/usr/bin/env python3
"""Generate character companions with the existing 17-state animation rig.

Usage: python3 gen_companions.py [character-id ...]
Existing notification sounds are preserved when regenerating visual assets.
"""
import json
import shutil
import sys
from pathlib import Path

from gen_themes import Gen, CHARACTERS, R, WHITE, INK, STATIC_CSS, pixel_text

ROOT = Path(__file__).resolve().parent.parent


def P(points, fill, extra=""):
    return f'<polygon points="{points}" fill="{fill}" {extra}/>'


def G(body, extra=""):
    return f'<g {extra}>{body}</g>'


COMPANIONS = {
    "jobs": ("乔布斯 · Jobs", "黑色高领、圆眼镜、牛仔裤", "#171923", "#577591", "#9DADC0", "ONE MORE THING", "phone"),
    "buffett": ("巴菲特 · Buffett", "蓬松白发、圆脸笑容、细框眼镜与汽水罐", "#426B98", "#294A71", "#C83A45", "STAY PATIENT", "cola"),
    "munger": ("芒格 · Munger", "宽脸与下颌、稀疏白发、椭圆金属眼镜、西装领带与书本", "#414957", "#343C46", "#456957", "KEEP LEARNING", "book"),
    "luffy": ("路飞 · Luffy", "草帽、红马甲、蓝短裤和肉棒", "#DF3444", "#3C75BE", "#EDB849", "ADVENTURE!", "meat"),
    "zoro": ("索隆 · Zoro", "绿色短发、绿腰封、三把刀", "#255644", "#24332C", "#70BA56", "ALL CLEAR!", "sword"),
    "chopper": ("乔巴 · Chopper", "鹿角、粉色十字帽、蓝鼻子", "#C98E58", "#AF644B", "#ED81AE", "ALL BETTER!", "medical"),
    "doraemon": ("哆啦 A 梦 · Doraemon", "蓝色圆身体、红鼻子、铃铛与口袋", "#1596D0", "#FFFFFF", "#F3C44B", "HERE YOU GO!", "dorayaki"),
    "conan": ("柯南 · Conan", "翘发、大眼镜、蓝西装与红领结", "#2B63A5", "#7F94BA", "#D83B42", "CASE CLOSED!", "glass"),
    "shinchan": ("蜡笔小新 · Shinchan", "粗眉、圆脸、红衣黄裤", "#ED3D43", "#FFD349", "#F3C735", "YAY!", "snack"),
    "pikachu": ("皮卡丘 · Pikachu", "黑尖长耳、红脸颊、黄色身体与闪电尾巴", "#F3CB3C", "#F3CB3C", "#EC6544", "PIKA!", "bolt"),
    "mario": ("马里奥 · Mario", "红色 M 帽、圆鼻胡子、蓝背带裤与白手套", "#D83B40", "#3072B1", "#E9BF43", "LET'S GO!", "mushroom"),
    "sonic": ("索尼克 · Sonic", "蓝色刺猬轮廓、白手套与红白跑鞋", "#256EBB", "#256EBB", "#E6BB3C", "GOTTA GO!", "ring"),
    "spongebob": ("海绵宝宝 · SpongeBob", "方形黄色海绵、大蓝眼、门牙和棕色短裤", "#F4D34D", "#95613D", "#E78354", "I'M READY!", "spatula"),
    "totoro": ("龙猫 · Totoro", "灰色圆身体、长耳、奶油色肚皮与胡须", "#8A969C", "#8A969C", "#70A36D", "HELLO!", "leaf"),
    "batman": ("蝙蝠侠 · Batman", "尖耳黑面罩、蝙蝠披风、黄色腰带", "#39414C", "#222C39", "#E2BE46", "ALL CLEAR!", "batsignal"),
    "ironman": ("钢铁侠 · Iron Man", "红金装甲、金色面甲与蓝色胸口反应堆", "#A93639", "#9C3038", "#70D0E4", "SYSTEM READY", "energy"),
    "sunwukong": ("孙悟空 · Sun Wukong", "猴脸、金箍、红围巾、虎皮裙与金箍棒", "#E8BE4C", "#DEA64C", "#CE4641", "HERE WE GO!", "peach"),
}


def config(cid):
    name, desc, top, pants, accent, phrase, prop = COMPANIONS[cid]
    skin = "#F0CBAB" if cid in ("jobs", "buffett", "munger") else "#F3C69B"
    skin = {"pikachu":"#F3CB3C", "sonic":"#EDD0A4", "spongebob":"#F4D34D", "totoro":"#8A969C", "batman":"#D8AC85", "ironman":"#C44A43", "sunwukong":"#EBC49A"}.get(cid,skin)
    return dict(name=name, desc=desc, top=top, top_dk="#18263A", pants=pants,
                skin=skin, skin_sh="#D4A07A", blush="#E9A18C", hair="#202737",
                hair_hi="#3C4759", hair_sh="#111827", hair_gray="#DCE1E9", brow="#283047",
                hairstyle="short", glasses=cid in ("jobs", "buffett", "munger", "conan"),
                outfit="suit" if cid == "buffett" else "plain",
                accent=accent, accent2=INK, confetti=[accent, WHITE, top],
                done_lines=[phrase], done_colors=[INK], done_prop="custom", prop=prop,
                rally="GO!", tier2="custom", error="OOPS!", notify="READY!",
                delegate="GO!", poke="HEY!", double=phrase, idle_special="sign")


class Companion(Gen):
    def hair(self, cap=False):
        cid, C = self.cid, self.C
        dark = C["hair"]
        if cid == "buffett":
            return (P("1,4 0,2 0,-1 1,-1 1,-3 3,-3 3,-4 6,-4 6,-5 11,-5 11,-4 14,-4 14,-2 16,-2 16,2 15,4 13,3 13,0 10,0 10,-1 5,-1 5,0 3,1 3,4", "#D5DCE3")
                    + P("1,1 1,-1 2,-1 2,-3 5,-3 5,-4 10,-4 10,-3 13,-3 13,-1 15,-1 15,2 14,2 13,0 10,0 10,-1 5,-1 5,0 3,1", "#F3F4EF")
                    + R(1.2,1.8,1.5,3,"#E9EDEB") + R(13.3,1.8,1.5,3,"#E9EDEB"))
        if cid == "munger":
            return (P("0,4 0,1 1,0 2,0 2,4", "#BCC2C5") + P("14,4 14,0 15,0 16,1 16,4", "#BCC2C5")
                    + R(3,-2.8,2,.4,"#D6CFBF") + R(4,-3.3,2.5,.35,"#D6CFBF"))
        if cid == "jobs":
            return R(2,0,1.8,4.3,"#ADB6C2") + R(12.2,0,1.8,4.3,"#ADB6C2")
        if cid in ("pikachu", "sonic", "spongebob", "totoro", "batman", "ironman"):
            return ""
        if cid == "mario":
            return (P("1,4 1,0 3,-2 13,-2 15,0 15,4 13,5 12,2 4,2 3,5", "#71422D")
                    + P("1,0 1,-2 3,-2 3,-4 6,-5 11,-5 14,-3 14,0", "#D83B40")
                    + R(0,0,16,1.2,"#AE2835") + R(2,-3,3,.7,"#EA6254")
                    + '<ellipse cx="8" cy="-2.2" rx="2.2" ry="1.7" fill="#FFF4DD"/>'
                    + '<path d="M6.8 -1 V-3.2 L8 -1.8 L9.2 -3.2 V-1" fill="none" stroke="#C8333A" stroke-width=".55"/>')
        if cid == "sunwukong":
            return (P("1,4 0,1 1,-2 3,-2 3,-4 6,-3 8,-5 10,-3 13,-4 13,-2 15,-1 16,2 15,5 13,3 12,0 4,0 3,3", "#94623A")
                    + R(1,-.2,14,1,"#F1CB55") + R(1,.8,14,.35,"#B78A2D")
                    + '<path d="M6 .1 C5 -1.5 7 -1.9 8 -.6 C9 -1.9 11 -1.5 10 .1" fill="none" stroke="#F1CB55" stroke-width=".6"/>')
        if cid == "luffy":
            return (P("2,0 3,-3 12,-3 14,0 13,5 12,3 11,4 10,2 8,3 7,1 5,3 4,2 3,5", dark)
                    + P("2,-1 2,-4 4,-4 4,-5 12,-5 12,-4 14,-4 14,-1", "#EFC571")
                    + R(2, -2, 12, 1.3, "#D84540") + R(-1, -0.8, 18, 1.2, "#DCAA58")
                    + R(1, -0.8, 14, .4, "#FFE4A0"))
        if cid == "zoro":
            return (P("2,3 1.5,0 2,-1 2.5,-2.3 3.5,-1.8 4,-3 5,-2.4 6,-3.4 7,-2.5 8,-3.6 9,-2.6 10,-3.3 11,-2.4 12,-3 13,-2 14,-1 14,1 13,4 12.5,1 11,.3 9,.5 7,.2 5,.6 3.5,1.2", "#65A958")
                    + ''.join(P(f'{x},-2.2 {x+.4},-1.1 {x},0 {x-.4},-1',"#99C781") for x in (4,6,8,10,12))
                    + R(13, 5, .4, 2, "#F3D267") + R(13.8, 5, .4, 2, "#F3D267") + R(14.6, 5, .4, 2, "#F3D267"))
        if cid == "conan":
            return P("2,4 1,0 3,-2 3,-4 6,-3 9,-4 12,-3 14,-1 17,-2 15,1 13,1 13,4 11,2 10,4 8,1 6,3 5,1 3,4", dark) + R(5,-2,5,.7,"#3D4B65")
        if cid == "shinchan":
            return P("0,3 0,0 2,-2 5,-3 11,-3 14,-1 15,2 14,3 12,1 3,1 2,3", "#202634")
        if cid == "chopper":
            horns = (P("1,-2 -2,-3 -3,-5 -5,-5 -5,-7 -4,-7 -3,-6 -2,-8 -1,-7 -1,-5 1,-4", "#825138")
                     + P("15,-2 18,-3 19,-5 21,-5 21,-7 20,-7 19,-6 18,-8 17,-7 17,-5 15,-4", "#825138"))
            return (horns + P("1,0 1,-4 3,-5 13,-5 15,-4 15,0", "#E575A6")
                    + R(0,-.5,16,1.5,"#BC4F87") + R(3,-4,10,.7,"#F5A8CB")
                    + P("6,-4 7,-4 8,-3 9,-4 10,-4 10,-3 9,-2 10,-1 9,0 8,-1 7,0 6,-1 7,-2 6,-3", WHITE))
        if cid == "doraemon":
            return ""
        return super().hair()

    def face_skin(self):
        cid, C = self.cid, self.C
        if cid in ("luffy", "zoro", "conan"):
            shape = {
                "luffy":"2.8,.3 12.5,.3 13.8,2.5 13.2,6.5 11,8.7 8,9.2 5,8.7 2.5,6.3 1.8,3",
                "zoro":"3,.2 12.5,.2 13.2,3 13,6.4 10.5,8.7 8,9.1 5.5,8.7 3,6.1 2.3,3",
                "conan":"3,.5 12.5,.5 13.4,3 13,6 10.5,8.3 8,9 5.5,8.3 3,6 2.5,3",
            }[cid]
            return P(shape,C['skin']) + '<ellipse cx="2.1" cy="4.5" rx=".9" ry="1.5" fill="#E7B88F"/><ellipse cx="13.8" cy="4.5" rx=".9" ry="1.5" fill="#E7B88F"/>'
        if cid == "buffett":
            return (P("3,0 12,0 14,2 15,4 15,6 14,7 12,9 5,9 3,8 1,6 1,3", "#EFC5A6")
                    + R(.5,3.6,1.7,2.7,"#E5B395") + R(14,3.6,1.5,2.7,"#E5B395")
                    + R(2.8,6.3,2.2,.75,"#DDA68F") + R(11.2,6.3,2.2,.75,"#DDA68F")
                    + R(5.5,8.8,6,.45,"#D7AA8C"))
        if cid == "munger":
            return (P("2,-2 4,-3.5 12,-3.5 14,-2 15,0 15,7 13.5,9 3,9 1,7 1,0", "#E6C3A1")
                    + R(-.1,3.6,1.5,3,"#D9B18F") + R(14.6,3.6,1.5,3,"#D9B18F")
                    + R(4,-.4,7,.25,"#CAAA8E") + R(4.8,.4,5.5,.2,"#CAAA8E")
                    + R(2.5,6.2,.35,1.7,"#C19C7E") + R(13,6.2,.35,1.7,"#C19C7E"))
        if cid == "pikachu":
            return (P("3,1 0,-6 1,-9 3,-7 6,0",C["top"]) + P("0,-6 1,-9 3,-7 3.7,-4.8 1.4,-3.8",INK)
                    + P("10,0 14,-7 17,-8 16,-4 13,2",C["top"]) + P("14,-7 17,-8 16,-4 13.3,-4.3",INK)
                    + P("3,-1 12,-1 14,1 15,4 14,7 12,9 4,9 1,7 0,4 1,1",C["top"])
                    + R(2.5,5.8,2.2,1.6,"#E96542") + R(11.2,5.8,2.2,1.6,"#E96542"))
        if cid == "mario":
            return (P("4,0 12,0 14,2 14,7 11,9 5,9 2,7 2,2", "#EDBE98")
                    + R(.6,3,2.4,3,"#E2A982") + R(13,3,2.4,3,"#E2A982"))
        if cid == "sonic":
            return (P("3,-1 2,-5 6,-3 10,-5 15,-4 13,-2 18,-1 15,2 19,3 15,5 17,7 13,8 10,9 4,8 1,5 -2,4 1,2 -2,0",C["top"])
                    + P("3,0 3,-3 5,-1", "#DDB68E")
                    + P("3,4 12,3.5 15,5 14,8 11,9 5,9 2,7", "#ECCD9F"))
        if cid == "spongebob":
            return (P("0,-4 4,-4 4,-3.6 8,-4 12,-3.6 16,-4 16,0 15.6,0 16,4 15.6,8.8 0,8.8 .4,5 0,2",C["top"])
                    + ''.join(R(x,y,w,h,"#C6AC3C") for x,y,w,h in [(1,-2,1.2,1),(13,-2.6,1.4,1.3),(.7,5,1.1,1.8),(13.8,6,1.4,1),(2,7.4,1,1),(11.5,-2.7,.6,.7)]))
        if cid == "totoro":
            return (P("3,0 2,-5 3,-8 5,-6 6,-1 10,-1 11,-6 13,-8 14,-5 13,0 16,3 17,8 16,12 14,14 2,14 0,12 -1,8 0,3",C["top"])
                    + P("3,-5 3.5,-6 4.3,-3 4.5,-.8 3.5,-1.5", "#6C7C86")
                    + P("12,-5 12.5,-6 12.8,-2 11.5,-1", "#6C7C86")
                    + P("5,5 11,5 14,7 14.5,11 12.5,13.6 3.5,13.6 1.5,11 2,7", "#E6DDBE")
                    + ''.join(P(f"{x},{y} {x+1},{y-1} {x+2},{y} {x+1},{y-.3}","#77868C") for x,y in [(4,7),(7,7),(10,7),(3.5,9.3),(7,9.3),(10.5,9.3)]))
        if cid == "batman":
            return (P("1,2 1,-7 4,-4 5,-2 11,-2 12,-4 15,-7 15,6 13,7 3,7 1,6", "#222C39")
                    + P("5,5 11,5 12,7 10,9 6,9 4,7", "#D6AC88") + P("2,-2 4,-1 4,3 2,4", "#354251"))
        if cid == "ironman":
            return (P("3,-4 13,-4 15,-2 16,4 14,7 11,9 5,9 2,7 0,4 1,-2", "#A93639")
                    + P("3,-2 6,-3 7,-1 9,-1 10,-3 13,-2 13,1 14,3 12,7 4,7 2,3 3,1", "#E4B657")
                    + R(4,7,8,.7,"#C48C3C") + R(1.2,2,1,3,"#742C35") + R(13.8,2,1,3,"#742C35"))
        if cid == "sunwukong":
            return (P("2,0 13,0 15,2 14,6 12,9 4,9 1,6 0,2", "#BD8954")
                    + P("4,1 7,2 8,3 9,2 12,1 14,3 12,6 11,8 5,8 4,6 2,3", "#ECCC9F")
                    + P("1,2 -1,1 -2,3 0,5 2,5", "#DAAC7A") + P("14,2 17,1 18,3 16,5 14,5", "#DAAC7A"))
        if cid == "doraemon":
            return (P("3,-4 13,-4 13,-3 15,-3 15,-1 17,-1 17,6 15,6 15,8 13,8 13,9 3,9 3,8 1,8 1,6 -1,6 -1,-1 1,-1 1,-3 3,-3", C["top"])
                    + P("3,0 13,0 15,2 15,6 13,8 3,8 1,6 1,2", WHITE))
        if cid == "chopper":
            return (P("0,1 -2,2 -2,4 1,5 3,8 6,9 10,9 13,8 15,5 18,4 18,2 16,1", "#C9925B")
                    + R(0,2,2,1,"#E4B786") + R(14,2,2,1,"#E4B786")
                    + P("4,5 12,5 13,7 11,9 5,9 3,7", "#EFD2AA"))
        if cid == "shinchan":
            return P("3,0 12,0 14,2 14,4 17,5 17,8 14,10 6,10 2,8 0,5 1,2", "#F3C69B") + R(14,6,2,1,"#E7A992")
        base = super().face_skin()
        if cid == "jobs":
            base = P("4,-2 6,-3 10,-3 12,-2 13,0 13,4 3,4 3,0", C["skin"]) + base
        return base

    def features(self, **kw):
        cid, C = self.cid, self.C
        eyes = kw.get("eyes", "open")
        if cid in ("luffy", "zoro", "conan"):
            return self.anime_features(**kw)
        if cid in ("buffett", "munger"):
            return self.investor_features(**kw)
        if cid in ("pikachu", "mario", "sonic", "spongebob", "totoro", "batman", "ironman", "sunwukong"):
            return self.icon_features(**kw)
        if cid not in ("doraemon", "chopper", "shinchan"):
            base = super().features(**kw)
            if cid == "luffy":
                base += R(10.5,6,2,.3,"#9F654C") + R(11.1,5.6,.3,1,"#9F654C")
            if cid == "zoro":
                base += R(10.4,2.2,.3,4,"#9F654C") + R(9,4.4,2,.45,INK)
            if cid == "conan":
                base += '<rect x="3.7" y="3.5" width="4.1" height="3.1" rx=".5" fill="none" stroke="#14243E" stroke-width=".48"/><rect x="8.2" y="3.5" width="4.1" height="3.1" rx=".5" fill="none" stroke="#14243E" stroke-width=".48"/>'
            if cid == "jobs":
                base += R(5,7.8,6,.4,"#A39085") + R(5.5,8.3,5,.35,"#A39085")
            return base
        closed = eyes in ("closed", "happy", "squint")
        if cid == "doraemon":
            base = '<rect x="4.2" y="-1.6" width="3.8" height="4.6" rx="1.5" fill="white" stroke="#24364A" stroke-width=".28"/><rect x="8" y="-1.6" width="3.8" height="4.6" rx="1.5" fill="white" stroke="#24364A" stroke-width=".28"/>'
            y, xs = .6, (6, 9)
        elif cid == "chopper":
            base, y, xs = "", 3.3, (4.5, 10)
        else:
            base = P("3,3 4,2 6,2 7,3 7,4 5,3 3,4", INK) + P("8,3 9,2 11,2 12,3 12,4 10,3 8,4", INK)
            y, xs = 4.7, (4.5, 9.5)
        eye_id = 'id="eyes-js"' if kw.get("eyes_id", True) else ""
        base += G(G("".join(R(x,y+(.5 if closed else 0),1.1,.45 if closed else 1.7,INK) for x in xs), 'class="pupils"'), eye_id)
        if cid == "doraemon":
            base += '<circle cx="8" cy="3" r="1.05" fill="#E13D46"/>' + R(7.5,2.4,.5,.4,WHITE) + R(7.85,4,.3,2.4,INK)
            base += '<path d="M4 6 Q8 9 12 6 M1 3 L4 4 M1 5 L4 5 M1 7 L4 6 M12 4 L15 3 M12 5 L15 5 M12 6 L15 7" fill="none" stroke="#24364A" stroke-width=".32"/>'
        elif cid == "chopper":
            base += R(7,5.7,2,1,"#337CB3") + '<path d="M8 6.7 V7.4 M6.5 7.6 Q8 9 9.5 7.6" stroke="#7A513D" stroke-width=".4" fill="none"/>'
        else:
            base += R(11,8,1.3,.7,"#9E4E43")
        return base

    def anime_features(self, **kw):
        cid = self.cid
        closed = kw.get('eyes') in ('closed', 'happy', 'squint')
        out, pupil = '', ''
        for i,x in enumerate((5.1,10.8)):
            if closed or (cid == 'zoro' and i == 1):
                pupil += f'<path d="M{x-1.5} 4.3 Q{x} 3.8 {x+1.4} 4.1" stroke="#34302B" stroke-width=".35" fill="none"/>'
            elif cid == 'luffy':
                out += f'<ellipse cx="{x}" cy="4.35" rx="1.7" ry="1.65" fill="white" stroke="#4C3C30" stroke-width=".2"/>'
                pupil += f'<ellipse cx="{x}" cy="4.4" rx=".48" ry=".75" fill="#25262D"/>'
            elif cid == 'conan':
                out += f'<path d="M{x-1.7} 3.3 Q{x} 2.7 {x+1.4} 3.6 L{x+1.1} 5.8 Q{x} 6.2 {x-1.2} 5.5 Z" fill="white"/>'
                pupil += f'<ellipse cx="{x+.1}" cy="4.6" rx=".82" ry="1.23" fill="#3B7299"/><ellipse cx="{x+.1}" cy="4.7" rx=".38" ry=".9" fill="#1E344A"/><circle cx="{x-.2}" cy="3.9" r=".32" fill="white"/>'
            else:
                out += f'<path d="M{x-1.5} 3.9 L{x+1.6} 3.4 L{x+1.1} 4.65 L{x-1.1} 4.65 Z" fill="white" stroke="#3D4132" stroke-width=".2"/>'
                pupil += R(x,3.9,.42,.7,'#252C28')
        out += G(G(pupil,'class="pupils"'),'id="eyes-js"' if kw.get('eyes_id',True) else '')
        if cid == 'zoro':
            out += '<path d="M10.6 1.8 L10.9 6.4 M3.8 2.8 L6.7 3.2 M9.3 3 L12.4 2.5 M7.5 5 L7.1 6.1 L8.4 6.1 M6.1 7.4 Q8.4 7.9 10.4 7.2" stroke="#66553D" stroke-width=".3" fill="none"/>'
        elif cid == 'conan':
            out += '<path d="M3.7 2.5 L6.5 2.4 M9.5 2.3 L12 2.8 M7.7 5.5 L7.1 6.3 L8.2 6.3 M6.8 7.5 Q8.3 8.1 9.6 7.3" stroke="#584131" stroke-width=".23" fill="none"/>'
            out += '<rect x="2.9" y="3" width="4.8" height="3.5" rx="1.25" fill="none" stroke="#1C3243" stroke-width=".34"/><rect x="8.25" y="3" width="4.8" height="3.5" rx="1.25" fill="none" stroke="#1C3243" stroke-width=".34"/><path d="M7.7 4.1 H8.25 M1.6 3.8 H2.9 M13 3.8 H14.2" stroke="#1C3243" stroke-width=".3"/>'
        else:
            out += '<path d="M3.7 2.5 Q5 2 6.2 2.5 M9.5 2.5 Q10.8 2 12 2.5 M10.4 6 H12.6 M11 5.6 V6.4 M12 5.6 V6.4 M7.6 5.5 L7.1 6.2 L8 6.2" stroke="#6F4C39" stroke-width=".24" fill="none"/>'
            out += '<path d="M4.9 6.8 Q8 7.7 11.1 6.8 L10.2 8.2 Q8 9.4 5.8 8.2 Z" fill="#FFF5E0" stroke="#6F4C39" stroke-width=".24"/>'
        if kw.get('mouth') in ('frown','o','shout'):
            out += '<ellipse cx="8" cy="7.7" rx="1.1" ry=".8" fill="#804A39"/>'
        return out

    def investor_features(self, **kw):
        buffett = self.cid == "buffett"
        closed = kw.get("eyes") in ("closed", "happy", "squint")
        frames = ((3.5,3.5,4,2.6),(8.5,3.5,4,2.6)) if buffett else ((2.2,3.3,5.1,3.1),(8.7,3.3,5.1,3.1))
        out = ''
        for x,y,w,h in frames:
            if buffett:
                out += f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="#F7E9DC" stroke="#69717A" stroke-width=".28"/>'
            else:
                out += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx=".2" fill="#EEE4D8" stroke="#28323D" stroke-width=".62"/>'
        out += R(7.4 if buffett else 7.2,4.3,1.4 if buffett else 1.6,.28 if buffett else .62,"#69717A" if buffett else "#28323D")
        pupil = ''
        for x in ((5,10) if buffett else (4.4,10.7)):
            if closed:
                pupil += f'<path d="M{x-.55} 4.95 Q{x+.4} 4.05 {x+1.1} 4.95" fill="none" stroke="#324253" stroke-width=".36"/>'
            else:
                pupil += R(x+kw.get("pupil_dx",0)*.45,4.2+kw.get("pupil_dy",0)*.45,.65,1.05,"#394956")
        out += G(G(pupil,'class="pupils"'),'id="eyes-js"' if kw.get('eyes_id',True) else '')
        if buffett:
            out += R(4,2.8,2.2,.35,"#B0A797") + R(9.3,2.8,2.2,.35,"#B0A797")
            out += '<ellipse cx="8" cy="6" rx="1.2" ry=".75" fill="#D5A482"/>'
            if kw.get('mouth') in ('frown','flat'):
                out += R(6,7.5,4,.45,"#9D6553")
            elif kw.get('mouth') == 'o':
                out += R(7.2,7.2,1.5,1,"#95604E")
            else:
                out += P("5.4,7 10.6,7 10,8.1 6,8.1","#A76B58") + R(5.8,7.1,4.4,.55,"#FFF6E5")
        else:
            out += R(3,2.4,3.5,.5,"#9D9E99") + R(9,2.4,3.5,.5,"#9D9E99")
            out += P("7.2,5 8.8,5 9.4,7 7,7","#BD987A") + R(4.3,6.9,1.2,.25,"#BD987A") + R(10.6,6.9,1.2,.25,"#BD987A")
            out += R(6,7.9,4,.38,"#855F4E") + R(6.8,8.6,2.3,.2,"#C0A084")
            if kw.get('mouth') in ('grin','shout'):
                out += R(6.4,8.25,3.2,.35,"#FFF1DA")
        return out

    def icon_features(self, **kw):
        cid = self.cid
        eyes = kw.get('eyes','open')
        closed = eyes in ('closed','happy','squint')
        out = ''
        if cid == 'spongebob':
            out += '<circle cx="5" cy="1.6" r="2.7" fill="white" stroke="#695A32" stroke-width=".25"/><circle cx="11" cy="1.6" r="2.7" fill="white" stroke="#695A32" stroke-width=".25"/>'
            out += ''.join(R(x,-2,.35,1.2,INK) for x in (3.5,5,6.5,9.5,11,12.5))
            xs,y,col = (4.3,10.3),.7,'#46A1BD'
        elif cid == 'sonic':
            out += P("3,3 3,0 5,-1 8,1 10,-1 13,0 13,4 9,5 7,4",WHITE)
            xs,y,col = (5.7,10),1.5,'#3C8D67'
        elif cid in ('batman','ironman'):
            color = '#BAEDFA' if cid == 'ironman' else WHITE
            out += P("3,2 6.5,2.8 6,3.6 3.5,3.2",color) + P("9.5,2.8 13,2 12.5,3.2 10,3.6",color)
            if kw.get('eyes_id',True):out += G('', 'id="eyes-js"')
            if cid == 'ironman':
                out += R(5.5,5.7,5,.4,'#916230') + R(4.5,5,1,.4,'#916230') + R(10.5,5,1,.4,'#916230')
            else:
                out += R(6,6.9,4,.4,'#735A4C')
            return out
        else:
            xs,y,col = {'pikachu':((4,10.6),2.4,INK),'mario':((4.7,10.1),2.3,'#3D82A2'),'totoro':((3,11.5),1.2,INK),'sunwukong':((4.2,10.5),2.4,INK)}[cid]
            if cid in ('mario','totoro'):
                out += ''.join(f'<ellipse cx="{x+.6}" cy="{y+.8}" rx="1.4" ry="1.7" fill="white"/>' for x in xs)
        pupil = ''
        for x in xs:
            if closed:
                pupil += f'<path d="M{x-.2} {y+1.1} Q{x+.6} {y+.2} {x+1.4} {y+1.1}" stroke="{INK}" stroke-width=".4" fill="none"/>'
            else:
                pupil += R(x+kw.get('pupil_dx',0)*.4,y+kw.get('pupil_dy',0)*.4,1.2,1.8,col)
                pupil += R(x+.25,y+.15,.35,.45,WHITE)
        out += G(G(pupil,'class="pupils"'),'id="eyes-js"' if kw.get('eyes_id',True) else '')
        if cid == 'pikachu':
            out += P('7.2,4.4 8.8,4.4 8,5',INK) + '<path d="M6.4 6 Q7.1 7.3 8 6.3 Q8.9 7.3 9.6 6" fill="none" stroke="#795638" stroke-width=".4"/>'
        elif cid == 'mario':
            out += P('3.7,5 5.4,5.4 7.8,5 10,5.4 12.5,5 11.5,7 10,7.5 8,7 6,7.5 4.5,7','#603923')
            out += '<ellipse cx="8" cy="4.7" rx="2" ry="1.4" fill="#DCA781"/>'
            out += R(5,1.4,2,.6,'#603923') + R(9.7,1.4,2,.6,'#603923')
        elif cid == 'sonic':
            out += '<ellipse cx="8" cy="4.8" rx="1.2" ry=".7" fill="#203041"/><path d="M8 7.2 Q10 8 12 6.6" stroke="#81684F" stroke-width=".35" fill="none"/>'
        elif cid == 'spongebob':
            out += R(7,2.4,1.7,3,'#EDD05D') + '<path d="M3 5.1 Q8 9.4 13 5.1" stroke="#A56D36" stroke-width=".4" fill="none"/>'
            out += R(6.4,6.7,1.4,1.6,WHITE) + R(8.3,6.7,1.4,1.6,WHITE)
            out += R(2,4.8,1.5,.7,'#E9915A') + R(12.5,4.8,1.5,.7,'#E9915A')
        elif cid == 'totoro':
            out += P('6.5,3 9.5,3 8,4','#394955')
            out += '<path d="M0 3 L3 3.6 M-.6 4.4 L3 4.2 M0 5.6 L3 4.9 M13 3.6 L16 3 M13 4.2 L16.6 4.4 M13 4.9 L16 5.6" stroke="#394955" stroke-width=".28"/>'
        else:
            out += R(6.8,4.7,2.5,.8,'#AD704C') + '<path d="M5.7 6.5 Q8 8.3 10.3 6.5" fill="none" stroke="#955D3D" stroke-width=".4"/>'
            out += P('3.5,2 6.5,1.5 6.5,2.1 3.5,2.7','#845331') + P('9.5,1.5 12.5,2 12.5,2.7 9.5,2.1','#845331')
        return out

    def torso(self):
        cid, C = self.cid, self.C
        if cid == "buffett":
            return super().torso()
        if cid == "munger":
            return (P('3,9 13,9 14,10 14,14 2,14 2,10',C['top'])
                    + P('5.6,9 10.4,9 8.8,14 7.2,14','#E4E0D3')
                    + P('4.7,9 5.8,9 7.3,13.5 4.5,11.8 5.3,11','#2C3440')
                    + P('10.2,9 11.3,9 10.7,11 11.5,11.8 8.7,13.5','#2C3440')
                    + P('7.5,9.7 8.5,9.7 8.4,10.4 8.8,13.6 8,14.2 7.2,13.6 7.6,10.4','#6C5667')
                    + ''.join(P(f'7.5,{y} 8.4,{y-.3} 8.5,{y+.1} 7.4,{y+.5}','#B3AB79') for y in (10.8,11.8,12.8)))
        if cid == 'pikachu':
            return P('3,8 13,8 14,11 12,14 4,14 2,11',C['top']) + R(4,10.6,1.2,2,'#FFE87B')
        if cid == 'mario':
            return (R(2,9,12,4.7,C['top']) + R(4,9,1.5,5,C['pants']) + R(10.5,9,1.5,5,C['pants'])
                    + R(4,11,8,3,C['pants']) + R(4.5,10.7,.8,.8,'#F7CE51') + R(10.7,10.7,.8,.8,'#F7CE51'))
        if cid == 'sonic':
            return P('5,8 11,8 12,11 10,14 6,14 4,11',C['top']) + '<ellipse cx="8" cy="10.8" rx="2.3" ry="2.8" fill="#EDD0A4"/>'
        if cid == 'spongebob':
            return (R(0,8,16,1.8,WHITE) + R(0,9.8,16,2.4,C['pants']) + P('7,8.5 9,8.5 8.5,9.4 9,10.9 8,11.5 7,10.9 7.5,9.4','#C74039')
                    + R(1,10.4,3,.45,INK) + R(5,10.4,2,.45,INK) + R(9.5,10.4,2,.45,INK) + R(13,10.4,2,.45,INK))
        if cid == 'totoro':
            return ''
        if cid == 'batman':
            return (R(2.4,9,11.2,4.7,C['top']) + '<ellipse cx="8" cy="10.6" rx="3.6" ry="1.4" fill="#DFC44F"/>'
                    + P('4.8,10 6.3,10.6 7,9.8 7.5,10.4 8.5,10.4 9,9.8 9.7,10.6 11.2,10 10.6,11.2 9,11.2 8,12 7,11.2 5.4,11.2',INK)
                    + R(2.4,13,11.2,1,'#D4AD43') + R(7.2,12.8,1.6,1.4,'#F2D466'))
        if cid == 'ironman':
            return (P('2,9 14,9 12,14 4,14',C['top']) + P('3,9 6.2,9 6,10.5 3,10.2','#E4B657')
                    + P('9.8,9 13,9 13,10.2 10,10.5','#E4B657') + '<circle cx="8" cy="10.5" r="1.25" fill="#70D0E4"/><circle cx="8" cy="10.5" r=".65" fill="#EAFCFF"/>'
                    + R(5,12,6,.5,'#742C35') + R(6,13,4,.5,'#742C35'))
        if cid == 'sunwukong':
            return (R(3,9,10,4.8,C['top']) + P('3,8.8 13,8.8 12,10.3 4,10.3','#CE4641') + P('12,9 18,10 19,12 14,11','#CE4641')
                    + R(3,12,10,2.2,'#D69D48') + ''.join(P(f'{x},12 {x+1.2},12 {x+.4},14 {x-.4},13.5','#765232') for x in (4,7,10,12)))
        if cid == "doraemon":
            return (R(2,8.5,12,5.5,C["top"]) + R(2,8.5,12,.8,"#D93642")
                    + '<ellipse cx="8" cy="11.4" rx="4.4" ry="2.9" fill="white"/>'
                    + '<path d="M5 11.2 H11 Q11 14 8 14 Q5 14 5 11.2" fill="white" stroke="#24364A" stroke-width=".3"/>'
                    + '<circle cx="8" cy="9.4" r="1" fill="#F1C847" stroke="#9E7B2F" stroke-width=".2"/>' + R(7.2,9.1,1.6,.25,"#9E7B2F") + R(7.8,9.6,.4,.7,"#9E7B2F"))
        if cid == "luffy":
            return R(3,9,10,4.5,C["skin"]) + R(3,9,3,4.5,C["top"]) + R(10,9,3,4.5,C["top"]) + R(10.8,10, .5,.5,"#F4CE67") + R(10.8,12,.5,.5,"#F4CE67")
        if cid == "zoro":
            swords = "".join(G(R(-1,0,13,.6,col) + R(11,-.3,1,1.2,"#D4B04B") + R(12,0,3,.6,"#282534"),f'transform="translate(0 {12.2+i*.8}) rotate({-12+i*4} 8 0)"') for i,col in enumerate(("#E7DFD7","#403B52","#933D48")))
            return R(3,9,10,4.5,C["top"]) + P("6,9 10,9 8,12",C["skin"]) + R(3,12,10,1.7,"#7A9E4E") + swords
        if cid == "chopper":
            return R(4,9,8,4.5,C["top"]) + R(6,10,4,3,"#E4B786") + R(12,9,1,5,"#48748A")
        base = R(3,9,10,4.6,C["top"])
        if cid == "jobs":
            return base + R(5,8.6,6,1.6,"#171923") + R(4,13,8,.5,"#111827")
        if cid == "conan":
            base += P("5,9 11,9 9,13 7,13",WHITE) + P("5,9 6,9 7,13 5.5,12", "#354D72") + P("10,9 11,9 10.5,12 9,13", "#354D72")
            if cid == "conan":
                base += P("5.7,9.4 8,10 10.3,9.4 10.3,11.3 8,10.6 5.7,11.3", "#CF3542")
        return base

    def arm(self, side, rotate=0, hand=True):
        if self.cid in ('pikachu','mario','sonic','spongebob','totoro','batman','ironman','sunwukong'):
            x = .9 if side == 'L' else 13.3
            if rotate:
                STATIC_CSS.append(f'#arm-{side} {{ transform: rotate({rotate}deg); }}')
            color = '#F4D34D' if self.cid == 'spongebob' else self.C['top']
            body = R(x,9,1.7,3.8,color)
            if hand:
                color = WHITE if self.cid in ('mario','sonic') else ('#202C39' if self.cid == 'batman' else color)
                body += R(x-.3,12,2.3,1.7,color)
            return G(body,f'id="arm-{side}"')
        if self.cid not in ("luffy", "doraemon", "chopper"):
            return super().arm(side, rotate, hand)
        x = 1.5 if side == "L" else 13
        if rotate:
            STATIC_CSS.append(f"#arm-{side} {{ transform: rotate({rotate}deg); }}")
        color = self.C["skin"] if self.cid == "luffy" else self.C["top"]
        body = R(x,9.3,1.5,4,color)
        if hand:
            body += R(x-.2,12.7,1.9,1.6,WHITE if self.cid == "doraemon" else ("#865237" if self.cid == "chopper" else color))
        return G(body, f'id="arm-{side}"')

    def legs(self):
        if self.cid in ('pikachu','mario','sonic','spongebob','totoro','batman','ironman','sunwukong'):
            out = ''
            for side,x in (('L',4),('R',9)):
                color = self.C['pants']
                foot = '#D94343' if self.cid == 'sonic' else ('#734F32' if self.cid == 'mario' else color)
                if self.cid == 'spongebob':
                    body = R(x,12.2,1.3,1.3,'#EDCE4E') + R(x,13.5,1.3,1.1,WHITE) + R(x-.5,14.6,3,.8,INK)
                else:
                    body = R(x,13,2.8,1.8,color) + R(x-.5,14.3,3.8,1.2,foot)
                    if self.cid == 'sonic':body += R(x+.3,14.3,.9,1.2,WHITE)
                out += G(body,f'id="leg-{side}"')
            return out
        if self.cid == "doraemon":
            return G(R(2.5,13.7,5.5,1.7,WHITE), 'id="leg-L"') + G(R(8,13.7,5.5,1.7,WHITE), 'id="leg-R"')
        if self.cid in ("luffy", "conan", "shinchan", "chopper"):
            return "".join(G(R(x,13.2,3,1.1,self.C["pants"]) + R(x+.5,14.2,2,.6,self.C["skin"]) + R(x-.2,14.8,3.4,.6,"#EFD785" if self.cid == "shinchan" else "#684E3E"),f'id="leg-{side}"') for side,x in (("L",4),("R",9)))
        return super().legs()

    def item(self, x=0, y=0, cls=""):
        prop, accent = self.C["prop"], self.C["accent"]
        if prop == "phone":
            body = R(1,0,3.4,5.7,"#172337") + R(1.35,.4,2.7,4.6,accent) + R(2.3,5.2,.8,.25,WHITE)
        elif prop == "chip":
            body = R(0,1,6,4,accent) + R(1,1.8,4,2.4,"#233D48") + "".join(R(i,.3,.5,.8,"#D6DBDF")+R(i,5,.5,.8,"#D6DBDF") for i in (1,2,3,4))
        elif prop in ("book", "parcel", "snack", "medical"):
            body = R(0,1,5.8,4.7,accent) + R(.6,1.5,4.6,3.7,"#FFF1D5")
            if prop == "medical":
                body += R(2.4,2,1,2.7,"#DC485F") + R(1.5,2.9,2.8,.9,"#DC485F")
            elif prop == "snack":
                body += R(1.4,2.4,3,1.9,"#644534") + R(1.7,2.6,.6,.6,"#AC7750")
            else:
                body += R(1,2.2,3.8,.45,accent) + R(1,3.3,2.6,.45,accent)
        elif prop == "cola":
            body = R(1,0,3.7,5.7,"#C83A45") + R(1,.2,3.7,.5,"#CAD1DB") + R(1,5,3.7,.5,"#CAD1DB") + P("1,2 4.7,1.5 4.7,2.5 1,3",WHITE)
        elif prop == "meat":
            body = R(0,2,6.4,1.2,"#F7E2B3") + R(-.5,1.5,1,2.2,"#F7E2B3") + R(6,1.5,1,2.2,"#F7E2B3") + P("1,1 2,0 5,0 6,1 6,4 5,5 2,5 1,4","#A64B35") + R(2,1,3,1,"#D67A4D")
        elif prop == "sword":
            body = P("2,0 3,-2 4,0 4,5 2,5","#E1E8EA") + R(1.2,4.3,3.6,.7,"#D6BA5C") + R(2.5,5,.9,2,"#403B52")
        elif prop == "dorayaki":
            body = '<ellipse cx="3" cy="3" rx="3.3" ry="2.2" fill="#D89441"/>' + R(.2,2.8,5.6,.8,"#713C30") + '<ellipse cx="3" cy="2.5" rx="3.3" ry="1.4" fill="#EBB765"/>'
        elif prop == 'bolt':
            body = P('4,-1 0,3 2.4,3 1,6 6,1.5 3.5,1.5','#F2C13D')
        elif prop == 'mushroom':
            body = R(1.5,3,3,2.4,'#E8CAA7') + P('0,3 0,1 2,-1 4,-1 6,1 6,3','#D94743') + R(1,.5,1.5,1.5,WHITE) + R(3.7,1,1.2,1.2,WHITE)
        elif prop == 'ring':
            body = '<circle cx="3" cy="2.8" r="2.5" fill="none" stroke="#EFCA4F" stroke-width="1.1"/>'
        elif prop == 'leaf':
            body = P('0,3 1,0 4,-1 6,1 5,4 2,5','#6C9D66') + '<path d="M1 5 L4 0" stroke="#416B46" stroke-width=".4"/>'
        elif prop == 'spatula':
            body = R(2.5,2,1,4,'#6C5845') + R(1,-1,4,3.5,'#B2C4CC') + ''.join(R(x,-.5,.3,2,'#637680') for x in (2,3,4))
        elif prop == 'batsignal':
            body = '<circle cx="3" cy="2.5" r="3" fill="#E7CD65"/>' + P('0,1.5 1.5,2 2,1 3,2 4,1 4.5,2 6,1.5 5,3 4,3 3,4 2,3 1,3',INK)
        elif prop == 'energy':
            body = '<circle cx="3" cy="2.5" r="3" fill="#84DCEE"/><circle cx="3" cy="2.5" r="1.5" fill="#E8FBFF"/>'
        elif prop == 'peach':
            body = P('0,2 1,0 3,1 5,0 6,2 5,4 3,5 1,4','#E79784') + P('3,1 3,-1 5,-2 5,-.5','#739753')
        else:
            body = '<circle cx="2.6" cy="2.2" r="2.1" fill="#B8DEF0" stroke="#5A7188" stroke-width=".7"/>' + G(R(2.2,4,.9,3,"#604537"),'transform="rotate(-30 2.6 4)"')
        return G(body, f'class="{cls}" transform="translate({x} {y})"')

    def prop_phone(self, kind):
        return self.item(11,4,"inspect")

    def prop_gpu(self, x, y, cls=""):
        # The inherited celebratory pose holds each character's own accessory.
        return G(self.item(x,y), f'class="{cls}"')

    def gen_all(self):
        super().gen_all()
        style = self.BREATHE + """
.keepsake { transform-origin: 16px 8px; animation: show 3s infinite ease-in-out; }
@keyframes show { 0%,100% { transform: rotate(-7deg); } 50% { transform: rotate(8deg) translateY(-1px); } }
#arm-R { transform: rotate(-105deg); }
"""
        self.write("idle-special.svg",self.svg(style,self.figure(self.head(mouth="smile",eyes_id=False),self.arm("L"),self.arm("R"),extra_after=G(self.item(15,5),'class="keepsake"'))))
        for name in ("complete.mp3", "confirm.mp3"):
            dest = Path(self.dir) / 'sounds' / name
            if not dest.exists():
                shutil.copy2(ROOT / 'agenthalo' / 'assets' / 'sounds' / name, dest)

    def figure(self, head_svg, arm_l, arm_r, **kw):
        rear = ''
        if self.cid == 'pikachu':
            rear = P('12,12 17,9 14,7 19,3 21,5 18,7 20,9 15,13','#EABF39')
        elif self.cid == 'batman':
            rear = P('4,8 12,8 16,15 12,14 10,15 8,14 6,15 4,14 0,15','#1C2836')
        elif self.cid == 'sunwukong':
            rear = R(16,-3,1,18,'#945333') + R(16,-3,1,3,'#EFCB5B') + R(16,12,1,3,'#EFCB5B')
        return rear + super().figure(head_svg,arm_l,arm_r,**kw)

    def theme_json(self):
        super().theme_json()
        path = Path(self.dir) / "theme.json"
        cfg = json.loads(path.read_text())
        cfg["version"] = "2.0.0"
        cfg["layout"]["contentBox"] = {"x": -5, "y": -8, "width": 26, "height": 25}
        cfg["hitBoxes"] = {key: {"x": -3, "y": -6, "w": 22, "h": 22} for key in ("default", "sleeping")}
        path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    ids = sys.argv[1:] or list(COMPANIONS)
    unknown = set(ids) - COMPANIONS.keys()
    if unknown:
        raise SystemExit("Unknown character: " + ", ".join(sorted(unknown)))
    for cid in ids:
        CHARACTERS[cid] = config(cid)
        Companion(cid).gen_all()
        print("generated", cid)
