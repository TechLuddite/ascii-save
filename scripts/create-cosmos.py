"""Original natural-space compositions, drawn directly into deterministic braille text.

Code and generated artwork: MIT, ascii-save contributors, 2026.
No image inputs, downloaded artwork, or external packages are used.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random

from common import ROOT, prepare

PI = math.pi


def clamp(v):
    return max(0.0, min(1.0, v))


def noise(x, y):
    # Smooth deterministic value noise, with no repeating trigonometric grid.
    ix, iy = math.floor(x), math.floor(y)
    u, v = x - ix, y - iy
    u, v = u*u*(3-2*u), v*v*(3-2*v)
    def h(a, b):
        z = ((a * 374761393 + b * 668265263) ^ 1274126177) & 0xffffffff
        z = ((z ^ (z >> 13)) * 1274126177) & 0xffffffff
        return (z ^ (z >> 16)) / 4294967295
    return ((h(ix, iy)*(1-u)+h(ix+1, iy)*u)*(1-v)
            +(h(ix, iy+1)*(1-u)+h(ix+1, iy+1)*u)*v)


def cloud(x, y):
    return sum(noise(x*s+13, y*s-7)*a for s, a in [(2, .52), (5, .26), (13, .14), (31, .08)])


def eclipse(x, y):
    dx, dy = x+.25, y+.03
    r, a = math.hypot(dx, dy), math.atan2(dy, dx)
    radius = .48
    if r < radius:
        return 0, True
    d = r-radius
    rays = (.5+.5*math.sin(a*9 + 2*math.sin(a*3)))**5
    fine = (.5+.5*math.sin(a*83 + math.sin(a*17)))**8
    equator = abs(math.cos(a))**8
    length = .07+.21*rays+.36*equator
    corona = .63*math.exp(-d/length)*(0.35+.65*cloud(dx*9,dy*9))
    rim = 1.4*math.exp(-d/.015)
    stream = .22*fine*math.exp(-d/.28)
    return clamp(corona+rim+stream), False


def galaxy(x, y):
    dx, dy = x-.15, y+.05
    u = dx*.91-dy*.415
    v = (dx*.415+dy*.91)/.48
    r, a = math.hypot(u,v), math.atan2(v,u)
    n = cloud(u*4, v*4)
    phase = a*2-5.8*math.log(r+.14)+n*1.6
    arm = (.5+.5*math.cos(phase))**7
    dust = (.5+.5*math.cos(phase+.72))**12
    disk = math.exp(-r/1.05)*(.025+.90*arm)*(.35+1.3*n)
    core = 1.45*math.exp(-(r/.19)**1.2)+.27*math.exp(-r/.4)
    return clamp((disk+core)*(1-.83*dust*clamp(r*3))), False


def rings(x, y):
    dx, dy = x-.38, y+.03
    u = dx*.94+dy*.342
    v = -dx*.342+dy*.94
    radius = .56
    ring_r = math.hypot(u,v/.28)
    ring = 0
    if .76 < ring_r < 1.52:
        grain = .6+.4*noise(u*110,v*160)
        ring = (.30+.30*math.sin(ring_r*145)**2)*grain
        if 1.22 < ring_r < 1.27 or 1.45 < ring_r < 1.47:
            ring *= .1
        ring *= clamp((ring_r-.76)*24)*clamp((1.52-ring_r)*35)
        # Shadow cast behind the globe, on the far side of the rings.
        if v < 0 and .0 < u < .52:
            ring *= .08
    r = math.hypot(dx,dy)
    if r < radius:
        z = math.sqrt(radius*radius-r*r)/radius
        light = clamp(-dx/radius*.65-dy/radius*.2+z*.72)
        band = .68+.11*math.sin((dy+.025*math.sin(dx*12))*65)+.12*noise(dx*12,dy*35)
        surface = light*band*1.35
        if -.12 < v < -.065:
            surface *= .35
        if v > 0 and ring:
            return ring, True
        return surface, True
    return ring, False


def nebula(x, y):
    n = cloud(x*2,y*2)
    flow = y+.26*math.sin(x*1.7)+.18*math.sin(x*4+n*3)
    veil = math.exp(-((flow+.12)/.54)**2)
    glow = veil*max(0,n-.22)*1.28
    # Three eroded, dark molecular-cloud columns with bright ionized rims.
    for cx, top, width in [(-.58,-.57,.23),(-.03,-.28,.20),(.47,-.04,.16)]:
        bend = cx+.15*math.sin(y*2.8)+.065*math.sin(y*10)
        edge = abs(x-bend)-width*(1+.6*y)-.10*(noise(x*15,y*13)-.5)
        cap = y-top-.10*math.sin(x*15)
        inside = min(-edge,cap)
        if inside > 0:
            glow *= .045+.12*n
        elif cap > -.11:
            glow += .40*math.exp(-abs(edge)/.037)*math.exp(-max(0,-cap)*22)*veil
    return clamp(glow), False


def crescent(x, y):
    dx,dy=x+1.03,y-.38
    radius=1.13
    r=math.hypot(dx,dy)
    if r >= radius:
        band=y+.45*x-.05
        stars=math.exp(-(band/.23)**2)*max(0,cloud(x*3,y*3)-.30)*.26
        return stars,False
    z=math.sqrt(radius*radius-r*r)/radius
    light=clamp(dx/radius*.89-dy/radius*.16-z*.44)
    surface=light*(.42+.48*cloud(dx*9,dy*9))
    for cx,cy,cr in [(.84,-.23,.075),(.92,.06,.11),(.65,-.55,.12),(.75,.43,.09),(.99,.3,.055),(.54,-.71,.055),(.88,-.43,.045)]:
        q=math.hypot(dx-cx,dy-cy)/cr
        if q<1.3:
            surface *= .48 if q<.83 else 1.0
            surface += light*.28*math.exp(-((q-1)/.11)**2)
    return clamp(surface),True


SCENES=[('01-corona','Corona',eclipse),('02-spiral','Spiral',galaxy),
        ('03-ringed-giant','Ringed Giant',rings),('04-pillars','Pillars',nebula),
        ('05-crescent','Crescent',crescent)]


def draw(func, width, height, seed):
    pw,ph=width*2,height*4
    aspect=width*9/(height*20)
    rng=random.Random(seed)
    pixels=[[False]*pw for _ in range(ph)]
    blocked=[[False]*pw for _ in range(ph)]
    for py in range(ph):
        y=(py/(ph-1)*2-1)
        for px in range(pw):
            x=(px/(pw-1)*2-1)*aspect
            val,mask=func(x,y)
            blocked[py][px]=mask
            # Stochastic dot coverage preserves faint gas instead of binary blobs.
            pixels[py][px]=rng.random()<clamp(max(0,val)**.80*1.12)
    # Sparse stars at several scales; bodies occult the background stars.
    for _ in range(width*height//35):
        px,py=rng.randrange(2,pw-2),rng.randrange(2,ph-2)
        if blocked[py][px]:
            continue
        pixels[py][px]=True
        if rng.random()<.16:
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                if not blocked[py+dy][px+dx]: pixels[py+dy][px+dx]=True
    bits=[(0,0,1),(0,1,2),(0,2,4),(1,0,8),(1,1,16),(1,2,32),(0,3,64),(1,3,128)]
    rows=[]
    for y in range(0,ph,4):
        row=''
        for x in range(0,pw,2):
            code=sum(bit for dx,dy,bit in bits if pixels[y+dy][x+dx])
            row+=chr(0x2800+code) if code else ' '
        rows.append(row.rstrip())
    return '\n'.join(rows)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'collections/cosmos-generated')
    parser.add_argument('--width',type=int,default=208)
    parser.add_argument('--height',type=int,default=56)
    args=parser.parse_args()
    if not 40<=args.width<=240 or not 16<=args.height<=80:
        parser.error('use width 40–240 and height 16–80')
    output=args.output.expanduser().absolute()
    if output.exists(): parser.error('output must not exist')
    output.mkdir(parents=True)
    artworks=[]
    for i,(slug,title,func) in enumerate(SCENES):
        seed=20260913+i
        data=draw(func,args.width,args.height,seed).encode('utf-8')
        (output/(slug+'.txt')).write_bytes(data)
        artworks.append(dict(title=title,output=slug+'.txt',seed=seed,output_sha256=hashlib.sha256(data).hexdigest()))
    with prepare(output) as files:
        if len(files)!=len(SCENES): raise RuntimeError('not every artwork passed playback limits')
    manifest=dict(title='Cosmos — original natural space',license='MIT',width=args.width,height=args.height,
                  author='ascii-save contributors; created with Codex',source='scripts/create-cosmos.py',
                  generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),artworks=artworks)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Created {len(artworks)} validated artworks in {output}')


if __name__=='__main__':
    main()
