"""Refine pinned Giants portraits into shaded braille using local source snapshots."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

from common import ROOT, prepare


def braille(gray, width, height, black, white):
    # Remove parchment highlights, retain face midtones, then diffuse quantization
    # error in alternating directions so shading has no preferred diagonal.
    levels=[max(0,min(1,(white-v)/max(1,white-black)))**1.35 for v in gray]
    pixels=bytearray(width*height)
    for y in range(height):
        direction=1 if y%2==0 else -1
        xs=range(width) if direction==1 else range(width-1,-1,-1)
        for x in xs:
            i=y*width+x
            value=levels[i]
            pixel=1 if value>=.5 else 0
            pixels[i]=pixel
            error=value-pixel
            for dx,dy,weight in [(direction,0,7/16),(-direction,1,3/16),(0,1,5/16),(direction,1,1/16)]:
                xx,yy=x+dx,y+dy
                if 0<=xx<width and yy<height:
                    levels[yy*width+xx]+=error*weight
    bits=[(0,0,1),(0,1,2),(0,2,4),(1,0,8),(1,1,16),(1,2,32),(0,3,64),(1,3,128)]
    rows=[]
    for y in range(0,height,4):
        row=''
        for x in range(0,width,2):
            code=sum(bit for dx,dy,bit in bits if pixels[(y+dy)*width+x+dx])
            row+=chr(0x2800+code) if code else ' '
        rows.append(row.rstrip())
    return '\n'.join(rows)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'collections/giants-refined')
    args=parser.parse_args()
    dest=args.output.expanduser().absolute()
    if dest.exists(): parser.error('output must not exist')
    baseline=ROOT/'examples/giants'
    manifest=json.loads((baseline/'manifest.json').read_text())
    source_dir=os.open(args.checkout.expanduser()/'backgrounds',os.O_RDONLY|os.O_DIRECTORY)
    artworks=[]
    try:
        with tempfile.TemporaryDirectory(prefix='ascii-save-giants-refine-') as temporary:
            work=Path(temporary)
            output=work/'output'; output.mkdir()
            for art in manifest['artworks']:
                name=Path(art['source']).name
                fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=source_dir)
                with os.fdopen(fd,'rb') as source:
                    before=os.fstat(source.fileno())
                    if not stat.S_ISREG(before.st_mode) or before.st_size>16_000_000:
                        raise ValueError('expected a bounded regular image: '+name)
                    data=source.read(16_000_001)
                    after=os.fstat(source.fileno())
                if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):
                    raise ValueError('source changed: '+name)
                if hashlib.sha256(data).hexdigest()!=art['source_sha256']:
                    raise ValueError('source differs from pinned Giants image: '+name)
                snapshot=work/name; snapshot.write_bytes(data)
                # 9×20 terminal cells: 186×56 cells physically preserve 3:2 art.
                # The 16:9 wordmark uses 208×52 instead, without cropping.
                width,height=(416,208) if name=='omarchy.png' else (372,224)
                gray=subprocess.check_output(['magick','-limit','memory','256MiB','-limit','map','512MiB',str(snapshot),
                    '-background','white','-alpha','remove','-alpha','off','-colorspace','Gray',
                    '-filter','Lanczos','-resize',f'{width}x{height}!','-depth','8','gray:-'],
                    timeout=60,env=dict(os.environ,MAGICK_THREAD_LIMIT='2'))
                if len(gray)!=width*height: raise ValueError('unexpected decoded dimensions')
                values=sorted(gray)
                black=values[len(values)*2//100]
                white=values[len(values)*75//100]
                text=braille(gray,width,height,black,white)
                # Blank wallpaper margins become asymmetric after rstrip and
                # shift the wordmark when the renderer centers the text bounds.
                if name == 'omarchy.png':
                    rows = text.splitlines()
                    while rows and not rows[0].strip(): rows.pop(0)
                    while rows and not rows[-1].strip(): rows.pop()
                    left = min(len(row) - len(row.lstrip()) for row in rows if row.strip())
                    text = '\n'.join(row[left:] for row in rows) + '\n'
                encoded=text.encode('utf-8'); (output/art['output']).write_bytes(encoded)
                artworks.append(dict(source=art['source'],source_sha256=art['source_sha256'],output=art['output'],
                    output_sha256=hashlib.sha256(encoded).hexdigest(),
                    width=max(map(len,text.splitlines())),height=len(text.splitlines()),
                    black_point=black,white_point=white))
            with prepare(output) as files:
                if len(files)!=18: raise ValueError('not all portraits passed preparation')
            dest.mkdir(parents=True)
            for p in output.iterdir(): (dest/p.name).write_bytes(p.read_bytes())
    finally:
        os.close(source_dir)
    result=dict(source_repository=manifest['source_repository'],source_commit=manifest['source_commit'],
        format='braille',conversion=dict(method='serpentine Floyd-Steinberg',black_percentile=2,white_percentile=75,
        darkness_gamma=1.35,crop=False,trim_wordmark_blank_margins=True,terminal_cell_aspect='9:20'),artworks=artworks,
        generator='scripts/refine-giants.py',generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        imagemagick_version=subprocess.check_output(['magick','-version'],text=True).splitlines()[0])
    (dest/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    for name in ['SOURCE-CREDITS.md','ARTWORK-NOTICE.md']:
        (dest/name).write_bytes((baseline/name).read_bytes())
    print(f'Refined and validated {len(artworks)} artworks at {dest}')


if __name__=='__main__':
    main()
