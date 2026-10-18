#!/usr/bin/env python3
"""Monta clips públicos reales, voz y capítulos en un MP4 reproducible."""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SALIDA = Path(os.environ.get('FACUSO_VIDEO_OUTPUT','/home/alberto/Vídeos/FAC-USO')).expanduser().resolve()
RAIZ = Path(__file__).resolve().parents[2]


def ejecutar(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def duracion(archivo):
    return float(ejecutar('ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',archivo,
                         capture_output=True,text=True).stdout.strip())


def metadata(caps, largo, path):
    lineas=[';FFMETADATA1']
    for i,(marca,titulo) in enumerate(caps):
        fin=round((caps[i+1][0] if i+1<len(caps) else largo)*1000)
        inicio=round(marca*1000)
        lineas+=['[CHAPTER]','TIMEBASE=1/1000',f'START={inicio}',f'END={fin}',
                 'title='+titulo.replace('\\','\\\\').replace('=','\\=').replace(';','\\;').replace('#','\\#')]
    path.write_text('\n'.join(lineas)+'\n',encoding='utf8')


def hoja(carpeta, tramos, escenas, marcas):
    ancho, alto=1440, 245*len(tramos)+70
    img=Image.new('RGB',(ancho,alto),'#f5f7f5'); d=ImageDraw.Draw(img)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
    bold=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',23)
    d.text((26,17),'FAC-USO Andalucía · hoja de control de escenas',font=bold,fill='#00482b')
    y=70
    for t,e,marca in zip(tramos,escenas,marcas):
        frame=carpeta/f"hoja-{t['id']}.png"
        segundo=marca+min(t['duracion_s']/2+0.65, duracion(carpeta/e['video'])-0.5)
        ejecutar('ffmpeg','-v','error','-y','-ss',f'{segundo:.2f}','-i',carpeta/'video.mp4',
                 '-frames:v','1',frame)
        im=Image.open(frame).convert('RGB');im.thumbnail((368,207))
        d.rounded_rectangle((18,y-5,1420,y+225),radius=8,fill='white',outline='#b8d2bf',width=2)
        img.paste(im,(28,y+4))
        d.text((415,y+10),f"{t['id']} · {t['titulo']}",font=bold,fill='#00482b')
        d.text((415,y+48),f"{int(marca//60):02d}:{int(marca%60):02d}  ·  voz {t['duracion_s']:.1f} s  ·  {e['url']}",font=font,fill='#333')
        texto=t['texto']
        chunks=[texto[i:i+90] for i in range(0,min(len(texto),360),90)]
        for j,linea in enumerate(chunks):d.text((415,y+85+j*29),linea,font=font,fill='#343434')
        y+=245
    img.save(carpeta/'hoja-control.png')


def main():
    carpeta=Path(sys.argv[1]).resolve()
    if SALIDA == RAIZ or RAIZ in SALIDA.parents or SALIDA not in carpeta.parents:
        raise ValueError('Salida fuera del repositorio requerida')
    tramos=json.loads((carpeta/'tramos.json').read_text())
    escenas=json.loads((carpeta/'escenas.json').read_text())
    if [t['id'] for t in tramos]!=[e['id'] for e in escenas]:raise ValueError('Escenas y voz no coinciden')
    archivos=[];offset=0;marcas=[];capitulos=[]
    total_previsto=sum(max(duracion(carpeta/e['video']),t['duracion_s']+1.8) for t,e in zip(tramos,escenas))
    pista=bytearray((math.ceil(total_previsto*24000)+48000)*2)
    for t,e in zip(tramos,escenas):
        origen=carpeta/e['video']; bruto=duracion(origen)
        objetivo=math.ceil(max(bruto,t['duracion_s']+1.8)*25)/25
        clip=carpeta/f"clip-{t['id']}.mp4"
        if not clip.is_file():
            rotulo=carpeta/f"rotulo-{t['id']}.txt"
            rotulo.write_text('Bienvenidas y bienvenidos' if t['id']=='01a' else t['titulo'],encoding='utf8')
            encuadre=('fps=25,crop=390:844:0:0,scale=416:900,pad=1440:900:(ow-iw)/2:0:color=0xe9f4ed'
                      if t['id']=='11' else
                      'fps=25,scale=1440:900:force_original_aspect_ratio=decrease,pad=1440:900:(ow-iw)/2:(oh-ih)/2:color=white')
            ejecutar('ffmpeg','-v','error','-y','-threads','2','-filter_threads','2','-i',origen,'-vf',
                     f'{encuadre},setsar=1,format=yuv420p,'
                     f'drawbox=x=0:y=ih-78:w=iw:h=78:color=0x00482bff:t=fill,'
                     f'drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile={rotulo}:expansion=none:fontcolor=white:fontsize=24:x=45:y=h-56,'
                     f'tpad=stop_mode=clone:stop_duration={objetivo:.2f}',
                     '-t',f'{objetivo:.2f}','-an','-c:v','libx264','-preset','fast','-crf','21','-r','25','-threads','2',clip)
        real=duracion(clip)
        if real+0.05 < objetivo:raise ValueError(f'Clip corto {t["id"]}: {real} < {objetivo}')
        if not capitulos or capitulos[-1][0]!=t['capitulo']:capitulos.append((t['capitulo'],offset,t['titulo']))
        marcas.append(offset)
        with wave.open(str(carpeta/t['wav']),'rb') as w:
            if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,2,24000):raise ValueError('WAV incompatible')
            voz=w.readframes(w.getnframes())
        inicio=round((offset+0.65)*24000)*2
        pista[inicio:inicio+len(voz)]=voz
        archivos.append(clip)
        offset+=real
        print(f"{t['id']}: {real:.2f} s, voz {t['duracion_s']:.2f} s",flush=True)
    with wave.open(str(carpeta/'voz.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000)
        w.writeframes(pista[:round(offset*24000)*2])
    lista=carpeta/'partes.txt'
    lista.write_text(''.join(f"file '{p.name}'\n" for p in archivos))
    metadata([(x[1],x[2]) for x in capitulos],offset,carpeta/'capitulos.txt')
    sin=carpeta/'sin-voz.mp4'
    ejecutar('ffmpeg','-v','error','-y','-threads','2','-f','concat','-safe','1','-i',lista,'-c','copy',sin)
    video=carpeta/'video.mp4'
    ejecutar('ffmpeg','-v','error','-y','-threads','2','-filter_threads','2','-i',sin,'-i',carpeta/'voz.wav','-f','ffmetadata','-i',carpeta/'capitulos.txt',
             '-map','0:v','-map','1:a','-map_metadata','2','-map_chapters','2','-c:v','copy',
             '-af','loudnorm=I=-16:TP=-2:LRA=11','-c:a','aac','-b:a','160k','-ar','48000',
             '-movflags','+faststart',video)
    hoja(carpeta,tramos,escenas,marcas)
    (carpeta/'ficha-tecnica.md').write_text(
        f"# Ficha técnica\n\nVídeo: `video.mp4` · {offset:.2f} s · 1440 × 900 · 25 fps · H.264/AAC.\n\n"
        f"Locución: `voz.wav` · voz española {len(tramos)} tramos · 24 kHz mono. AAC a 48 kHz en el MP4, normalizado cerca de -16 LUFS.\n\n"
        f"Capítulos: {len(capitulos)}. Captura: Chrome del sistema, Playwright, origen local 127.0.0.1:18086 y solo GET.\n\n"
        "La sección de automatización usa cartelas explicativas sobre páginas reales; no representa un panel del producto.\n",
        encoding='utf8')
    print(json.dumps({'video':str(video),'duracion_s':round(duracion(video),2),'capitulos':len(capitulos)},ensure_ascii=False))


if __name__=='__main__':main()
