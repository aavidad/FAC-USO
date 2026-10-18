#!/usr/bin/env python3
"""Alineación visual del WebM y voz por frase, sin acelerar las acciones."""
from pathlib import Path
import hashlib
import json
import math
import os
import subprocess
import sys
import wave
from PIL import Image, ImageDraw, ImageFont

BASE = Path(os.environ.get('FACUSO_VIDEO_OUTPUT', '/home/alberto/Vídeos/FAC-USO')).resolve()
folder = Path(sys.argv[1]).resolve()
if BASE not in folder.parents:
    raise ValueError('Carpeta fuera de la salida de vídeos')
plan = json.loads((folder / 'plan.json').read_text())
W, H = plan['viewport']['width'], plan['viewport']['height']

def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)

def length(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
        'format=duration', '-of', 'csv=p=0', str(path)]))

def stamp(value, separator=','):
    milliseconds = round(value * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02}{separator}{milliseconds:03}'

clips, phases, chapters = [], [], []
cursor = 0.0
for index, chapter in enumerate(plan['chapters'], 1):
    ident = f'{index:02}'
    data = json.loads((folder / f'chapter-{ident}.json').read_text())
    raw = folder / f'chapter-{ident}.webm'
    # El rectángulo magenta visible al principio establece el desfase real
    # entre performance.now() y los PTS del archivo, como en el método ETF.
    samples = subprocess.check_output(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(raw),
        '-t', '20', '-vf', 'fps=25,crop=100:30:10:10,scale=1:1,format=rgb24', '-f', 'rawvideo', '-'])
    anchor = next((i / 25 for i in range(len(samples)//3)
                   if samples[i*3] > 210 and samples[i*3+1] < 60 and samples[i*3+2] > 210), None)
    if anchor is None:
        raise ValueError('No se encuentra el ancla visual del capítulo '+ident)
    offset = anchor - data['anchor_clock']
    chapters.append({'start': cursor, 'title': chapter['title']})
    for phase in data['phases']:
        start = phase['start'] + offset
        source_seconds = phase['end'] - phase['start']
        action_seconds = phase['action_end'] - phase['start']
        voice_delay = action_seconds + .3
        target = math.ceil(max(plan['min_scene_seconds'], source_seconds,
            action_seconds + plan['min_stable_seconds'],
            voice_delay + phase['voice_seconds'] + .9) * 25) / 25
        clip = folder / f"phase-{phase['id']}.mp4"
        label = folder / f"label-{phase['id']}.txt"
        label.write_text(phase['title'])
        mobile = ('crop=390:844:0:0,scale=-2:1000,pad=1440:1000:(ow-iw)/2:0:color=0xe9f4ed,'
                  if phase['mobile'] else '')
        filters = (mobile + 'fps=25,setsar=1,format=yuv420p,'
            f'drawbox=x=0:y=ih-64:w=iw:h=64:color=0x00482bff:t=fill,'
            'drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:'
            f'textfile={label}:expansion=none:fontcolor=white:fontsize=23:x=38:y=h-46,'
            f'tpad=stop_mode=clone:stop_duration={target:.3f}')
        if not clip.exists():
            run(['ffmpeg', '-v', 'error', '-y', '-threads', '2', '-filter_threads', '2',
                '-ss', f'{start:.5f}', '-t', f'{source_seconds:.5f}', '-i', raw,
                '-vf', filters, '-t', f'{target:.3f}', '-an', '-c:v', 'libx264',
                '-preset', 'veryfast', '-crf', '21', '-threads', '2', clip])
        actual = length(clip)
        if abs(actual-target) > .08:
            raise ValueError(f"Duración no válida en {phase['id']}: {actual} != {target}")
        voice_start = cursor + voice_delay
        phases.append({**phase, 'output_start': cursor, 'output_end': cursor+actual,
            'voice_start': voice_start, 'voice_end': voice_start+phase['voice_seconds'],
            'stable_seconds': actual-action_seconds, 'source_seek': start,
            'chapter_alignment_offset': offset})
        clips.append(clip)
        cursor += actual
        print(f"{phase['id']}: {actual:.2f}s; lectura {actual-action_seconds:.2f}s", flush=True)

track = bytearray(math.ceil(cursor*24000)*2)
for phase in phases:
    with wave.open(str(folder / phase['audio']), 'rb') as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (1, 2, 24000):
            raise ValueError('Formato de voz inesperado')
        voice = w.readframes(w.getnframes())
    begin = round(phase['voice_start']*24000)*2
    track[begin:begin+len(voice)] = voice
with wave.open(str(folder / 'voz.wav'), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(track)

metadata = [';FFMETADATA1']
for i, chapter in enumerate(chapters):
    end = chapters[i+1]['start'] if i+1 < len(chapters) else cursor
    title = chapter['title'].replace('=', '\\=').replace(';', '\\;').replace('#', '\\#')
    metadata += ['[CHAPTER]', 'TIMEBASE=1/1000', f"START={round(chapter['start']*1000)}",
                 f'END={round(end*1000)}', 'title='+title]
(folder/'metadata.txt').write_text('\n'.join(metadata)+'\n')
(folder/'capitulos.txt').write_text('\n'.join(f"{int(c['start']//60):02}:{int(c['start']%60):02} {c['title']}" for c in chapters)+'\n')
(folder/'partes.txt').write_text(''.join(f"file '{p.name}'\n" for p in clips))
run(['ffmpeg','-v','error','-y','-f','concat','-safe','1','-i',folder/'partes.txt','-c','copy',folder/'sin-voz.mp4'])
temporary = folder/'video.part.mp4'
run(['ffmpeg','-v','error','-y','-threads','2','-filter_threads','2',
     '-i',folder/'sin-voz.mp4','-i',folder/'voz.wav','-f','ffmetadata','-i',folder/'metadata.txt',
     '-map','0:v','-map','1:a','-map_metadata','2','-map_chapters','2','-c:v','copy',
     '-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','160k',
     '-movflags','+faststart',temporary])
temporary.replace(folder/'video.mp4')
(folder/'subtitulos.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(
    f"{i}\n{stamp(p['voice_start'],'.')} --> {stamp(p['voice_end'],'.')}\n{p['text']}"
    for i,p in enumerate(phases,1))+'\n')
(folder/'plan-alineado.json').write_text(json.dumps({'seconds':cursor,'phases':phases,'chapters':chapters},ensure_ascii=False,indent=2)+'\n')

preview = Image.new('RGB',(1440,math.ceil(len(chapters)/3)*360),'#f1f5f2')
draw = ImageDraw.Draw(preview)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for i, chapter in enumerate(chapters):
    phase = next(p for p in phases if p['chapter']==i+1)
    point = phase['voice_start'] + min(2, phase['voice_seconds']/2)
    image_path = folder/f'final-{i+1:02}.jpg'
    run(['ffmpeg','-v','error','-threads','2','-ss',str(point),'-i',folder/'video.mp4',
         '-frames:v','1','-vf','scale=480:-2','-q:v','3','-y',image_path])
    frame = Image.open(image_path).convert('RGB')
    x,y=(i%3)*480,(i//3)*360
    preview.paste(frame,(x,y))
    draw.text((x+8,y+338),f"{i+1:02} · {chapter['title'][:42]}",font=font,fill='#00482b')
preview.save(folder/'hoja-control.jpg',quality=90)
report={'video':str(folder/'video.mp4'),'duration_seconds':round(cursor,2),'phases':len(phases),
        'chapters':len(chapters),'minimum_stable_seconds':round(min(p['stable_seconds'] for p in phases),2),
        'sha256':hashlib.sha256((folder/'video.mp4').read_bytes()).hexdigest()}
(folder/'qa-tecnica.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
