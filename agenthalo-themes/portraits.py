"""Individual facial drawings in the existing SVG animation coordinate system.

Small polygons and fine strokes retain the pixel silhouettes while avoiding a
shared generic face. Reference notes are in docs/character-likeness.md.
"""

PEOPLE = {"trump", "musk", "jensen", "jobs", "buffett", "munger"}


def path(d, fill="none", stroke=None, width=.25):
    line = f' stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"' if stroke else ""
    return f'<path d="{d}" fill="{fill}"{line}/>'


def ellipse(x, y, rx, ry, fill, stroke=None, width=.25):
    line = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}"{line}/>'


def head(cid, cap=False, eyes="open", mouth="pursed", pupil_dx=0, pupil_dy=0,
         brows="normal", eyes_id=True):
    skin = {"musk":"#ECC5AD", "trump":"#E6AA7F", "jensen":"#DEB48E",
            "jobs":"#DDB698", "buffett":"#EBC9B0", "munger":"#DFC3A6"}[cid]
    shade = {"musk":"#CEA58F", "trump":"#C78E68", "jensen":"#BC9474",
             "jobs":"#B9947D", "buffett":"#CEA98F", "munger":"#BDA084"}[cid]
    out = []
    # Distinct cranial outlines: broad Musk jaw, long Jobs face, Munger jowls.
    shapes = {
        "musk":"M3 .1 L4 -1.9 L6 -2.6 L10 -2.6 L12.6 -1 L14 1.5 L13.7 6.3 L12.6 8 L10.3 9.1 L5.8 9.1 L3.4 7.8 L2.3 5.6 L2.3 2 Z",
        "trump":"M3 -.5 L5 -2 L11 -2 L13 -.4 L14 2 L14.5 5 L13.8 7.1 L11.6 8.7 L5.5 9 L3 7.1 L1.9 4 L2 1 Z",
        "jensen":"M3 -.5 L5 -2.4 L11 -2.4 L13 -.6 L13.8 2 L13.8 6 L12 8 L10 8.8 L5.5 8.8 L3.5 7.4 L2.1 5 L2.2 1.5 Z",
        "jobs":"M4 -2 L6 -3.4 L10 -3.4 L12 -1.7 L12.5 1 L12 5.8 L10.8 8.3 L9 9.3 L6.5 9.3 L4.8 7.7 L3.6 5 L3.2 1 Z",
        "buffett":"M2.5 -.6 L5 -2.7 L11 -2.7 L13.5 -.4 L14.6 2.6 L14.8 5.2 L13.6 7.3 L11.2 8.9 L5 8.9 L2.7 7.4 L1.2 5.1 L1.4 2 Z",
        "munger":"M2.3 -1 L4 -3.2 L6.6 -4.1 L10.1 -4 L12.8 -2.8 L14 -1 L14.4 2 L14.5 5.4 L13.7 7.4 L12 8.8 L9.5 9.6 L5.8 9.4 L3.4 8.2 L1.5 6.1 L1.3 2 Z",
    }
    out.append(path(shapes[cid], skin))
    left, right = (2, 13.5) if cid != "jobs" else (3, 12.4)
    out += [ellipse(left-.5,3.8,.8,1.6,skin), ellipse(right+.5,3.8,.8,1.6,skin),
            path(f'M{left-.7} 3 L{left-.4} 4.4 M{right+.6} 3 L{right+.4} 4.4',stroke=shade)]
    if cid == "musk":
        out += [path('M2.3 2 L2 -.1 L2.6 -1.5 L4 -2.8 L5.2 -3.1 L7 -4 L9.6 -3.6 L12 -2.8 L13.5 -1.4 L14 .7 L13.5 2.2 L12.8 .5 L11 -.2 L9.5 -.6 L8.3 -1.1 L6.5 -.6 L5.1 -.8 L3.4 .3 L3.1 2.8 Z','#49362D'),
                path('M3 -1 L5 -2.1 L7 -2.8 L9.4 -2.8 L11.6 -2','#685044',width=.45,stroke='#685044'),
                path('M3.5 5.5 L4.1 7 L6 8 L10.5 8.2 L12.3 7 L13.1 5.5 L12.2 8 L10.2 9 L6 9 L3.8 7.8 Z',shade),
                path('M4 2.5 L5.4 2.1 L6.5 2.4 M9.3 2.4 L10.7 2.1 L12 2.5',stroke='#705547',width=.48),
                path('M7.8 3.1 L7.1 5.7 L8.1 6.1 L9 5.7',stroke=shade,width=.35),
                path('M4.1 5.2 L5.7 5.5 M10.3 5.5 L12 5.1',stroke=shade,width=.2)]
    elif cid == "trump":
        out += [path('M1.5 3.4 L.8 .2 L1.3 -1.6 L2.8 -3 L5 -4 L9.8 -4.2 L13 -3 L14.3 -1 L13.9 2 L13.3 2.5 L12.6 -.6 L10.6 -1 L8.6 -.5 L6 .4 L3.3 .9 L2.8 4 Z','#DAC07B'),
                path('M1.7 -1 L4 -2.5 L7.6 -3.4 L11 -3 L12.7 -2.2 L9.4 -2 L6.6 -1 L3 -.2 Z','#F0D697'),
                path('M2.3 1 L4.4 .1 L8 -1 L11 -1.2 M3.4 -2 L5.4 -2.8',stroke='#B9985D',width=.35),
                ellipse(5.4,3.8,1.7,1.2,'#EED4B5'), ellipse(10.6,3.8,1.7,1.2,'#EED4B5'),
                path('M3.8 2.7 L5.1 2.3 L6.7 2.5 M9.1 2.5 L10.6 2.3 L12.1 2.7',stroke='#AC915F',width=.52),
                path('M7.9 3.2 L7.3 5.5 L8.3 6.1 L9.2 5.7',stroke=shade,width=.4),
                path('M3.7 5.5 L4.4 6.9 M11.7 5.6 L11 7 M5.7 8.1 L10.6 8.1',stroke=shade,width=.25)]
    elif cid == "jensen":
        out += [path('M2.1 2 L1.6 -.3 L2.5 -2 L4.7 -3.4 L7.7 -3.8 L11 -3.3 L13.3 -1.9 L14 0 L13.8 3.2 L12.8 2.2 L12.5 -.3 L3.4 -.5 L3 2.6 Z','#929998'),
                path('M2.3 -1.2 L4.3 -2.8 L7.3 -3.2 L10.3 -3 L12.7 -1.8 L13 -.6 L10.4 -.8 L7.6 -1.4 L4.5 -.9 Z','#C2C7C3'),
                path('M3.5 -1.6 L4 -2.4 M5.2 -1.5 L5.8 -2.8 M7 -1.5 L7.5 -3 M8.8 -1.3 L9.3 -2.8 M11 -.9 L11.2 -2.2',stroke='#E6E7DB',width=.28),
                path('M3.8 2.4 L6.5 2.4 M9.5 2.4 L12 2.4',stroke='#5B5A51',width=.45),
                path('M7.9 4 L7.5 5.8 L8.4 6 L9 5.8',stroke=shade,width=.3)]
    elif cid == "jobs":
        out += [path('M3.3 -.5 L2.8 .3 L3 3.5 L3.7 4.5 L4 1 L4 -.7 Z','#888985'),
                path('M11.9 -.5 L12.7 .4 L12.6 3.8 L11.9 4.7 L11.5 1 Z','#888985'),
                path('M4 5.5 L4.8 6.3 L5.7 7.1 L6.6 7.5 L9.3 7.5 L10.2 6.7 L11.7 5.4 L11 8 L9 9.2 L6.6 9.2 L4.8 7.7 Z','#AC9B8A'),
                path('M5.3 7 L6 8 M6.5 8 L7 8.6 M8.5 8.3 L9 8.8 M10.2 7.3 L10 8.1',stroke='#D5C6B4',width=.3),
                path('M4.3 2 L6.5 1.7 M9.2 1.7 L11.5 2',stroke='#5E554A',width=.42),
                path('M7.8 3.4 L7 5.8 L8 6.3 L9 5.9',stroke=shade,width=.38)]
    elif cid == "buffett":
        out += [path('M1.4 3 L.8 .3 L1.3 -2 L3.5 -3.6 L6 -4 L8.2 -3.7 L10.3 -4 L13 -2.8 L14.3 -1 L15.1 1 L14.5 4 L13.5 3 L13 -.1 L11 -1.4 L8.2 -1.8 L5 -1.1 L3.1 .2 L2.6 3.9 Z','#D6DBD6'),
                path('M1.8 -.5 L2.8 -2.3 L5 -3.4 L7.7 -3.1 L10.5 -3.5 L12.5 -2.5 L13.6 -.5 L12 -.8 L10 -1.6 L7.7 -1.4 L5 -1.2 L3.1 .1 Z','#F4F2E6'),
                path('M3.9 2.1 L6.4 1.9 M9.4 1.9 L12.1 2.2',stroke='#B5AA91',width=.37),
                ellipse(8,5.8,1.2,.65,shade),
                path('M3.6 5.5 L4.8 6.2 L5.1 7.5 M12.5 5.5 L11.3 6.2 L11 7.5',stroke=shade,width=.26)]
    else:
        out += [path('M1.4 2 L1.2 -.8 L2 -2.3 L3.6 -3.7 L6.6 -4.5 L10 -4.4 L12.5 -3.4 L13.7 -1.5 L14.6 .2 L14.2 3.1 L13.4 2.8 L13.2 -.3 L12.3 -1.8 L10.3 -2.9 L7.1 -3.2 L4.8 -2.8 L3.1 -1.4 L2.5 1.9 Z','#D4D8CF'),
                path('M2.2 -1.9 L3.8 -3.1 L6.5 -3.9 L9.9 -3.9 L11.9 -3.3 M3.2 -2.4 L5.9 -3.4 L9.5 -3.5',stroke='#F8F3E3',width=.4),
                path('M4.6 -.1 L6.5 -.4 L9.5 -.3 L11.5 .1 M4.6 .9 L7 .6 L10 .8',stroke=shade,width=.17),
                path('M3 5.2 L3.7 6.9 L5.1 8.2 L7.2 8.9 L10 8.8 L12.4 7.4 L13.2 5.5',stroke=shade,width=.25),
                path('M3.1 2.1 L4.6 1.6 L6.5 1.9 M9.3 1.9 L11.2 1.6 L12.6 2.1',stroke='#ECE8D8',width=.48),
                path('M7.8 3.6 L7.1 5.5 L7.3 6.3 L8.6 6.6 L9.6 6 L9 4',skin,shade,.27),
                ellipse(7.7,6,.28,.18,'#8C7160'), ellipse(9,6,.28,.18,'#8C7160'),
                path('M5.5 6.1 L5 7.3 L5.7 8.2 M10.5 6.2 L11.1 7.4 L10.7 8.1',stroke=shade,width=.22)]

    # Eyelids and pupils are separate, retaining the blink/follow animation.
    closed = eyes in ('closed','happy','squint')
    xpos = (5.4,10.7) if cid != 'jobs' else (5.5,10.4)
    ey = {'musk':3.75,'trump':3.85,'jensen':3.85,'jobs':3.45,'buffett':3.9,'munger':3.65}[cid]
    eh = .63 if cid in ('musk','jensen','munger') else .84
    pupil = []
    for i,x in enumerate(xpos):
        if closed or (eyes == 'wink' and i == 1):
            pupil.append(path(f'M{x-1} {ey+.15} Q{x} {ey-.55 if eyes=="happy" else ey+.4} {x+1} {ey+.15}',stroke='#574B40',width=.25))
        else:
            out.append(ellipse(x,ey,1.05,eh,'#F9EDDE'))
            out.append(path(f'M{x-1.1} {ey-.05} Q{x} {ey-eh-.22} {x+1.1} {ey-.1}',stroke='#846A57',width=.28))
            pupil.append(ellipse(x+pupil_dx*.4,ey+pupil_dy*.35,.38,.52 if eyes!='wide' else .66,'#61767B' if cid in ('musk','trump') else '#4F5047'))
            pupil.append(ellipse(x+pupil_dx*.4,ey+pupil_dy*.35,.18,.36,'#272E30'))
    gid = ' id="eyes-js"' if eyes_id else ''
    out.append(f'<g{gid}><g class="pupils">{"".join(pupil)}</g></g>')
    if cid in ('munger','buffett','jobs','jensen'):
        specs = {'munger':(2.35,1.5,'#777468',.22), 'buffett':(2.2,1.5,'#84847A',.22),
                 'jobs':(2,1.7,'#878C87',.2), 'jensen':(2.3,1.4,'#414746',.3)}
        rx,ry,col,width=specs[cid]
        for x in xpos:
            out.append(ellipse(x,ey+.25,rx,ry,'none',col,width))
        out.append(path(f'M{xpos[0]+rx} {ey-.05} L{xpos[1]-rx} {ey-.05} M{xpos[0]-rx} {ey} L{left-.3} {ey-.4} M{xpos[1]+rx} {ey} L{right+.4} {ey-.4}',stroke=col,width=width))

    lip = '#987360' if cid != 'trump' else '#B27563'
    if mouth in ('o','shout'):
        out.append(ellipse(8,7.35,1 if mouth=='o' else 1.6,.7 if mouth=='o' else .95,'#705144'))
    elif mouth in ('frown','flat'):
        out.append(path('M6 7.5 Q8 6.9 10 7.5',stroke=lip,width=.26))
    elif cid == 'buffett' or mouth in ('grin','smile'):
        out.append(path('M5.5 6.95 Q8 7.8 10.8 6.95 L10 8 Q8 8.7 6.3 8 Z','#A47D66'))
        out.append(path('M5.9 7.17 Q8 7.7 10.4 7.17 L10 7.8 L6.4 7.8 Z','#FFF3DF'))
    elif cid == 'munger':
        out.append(path('M5.9 7.6 Q8.2 8 10.5 7.35 M6.7 8.45 Q8 8.75 9.5 8.35',stroke=lip,width=.23))
    elif cid == 'musk':
        out.append(path('M6.2 7.2 Q8.2 7.7 10.1 7.05 M7.1 7.9 L9.2 7.9',stroke=lip,width=.26))
    else:
        out.append(path('M6.5 7.25 Q8 6.85 9.6 7.25 L9.2 7.7 L7 7.7 Z',lip))
    if cap:
        out += [path('M3 -4.7 L13 -4.7 L13 -1.5 L1.5 -1.5 L1.5 -2.2 L3 -2.2 Z','#C8102E'),
                path('M5 -3.4 H11',stroke='#FFEEDB',width=.45)]
    return '<g id="head">'+''.join(out)+'</g>'
