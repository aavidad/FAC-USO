#!/usr/bin/env python3
"""Locución por frase: cada pista tendrá su propia pantalla y pausa de lectura."""
from pathlib import Path
import asyncio
import hashlib
import json
import os
import subprocess
from importlib.metadata import distribution
import edge_tts

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / 'docs/recorridos/plan-v2.json'

async def main():
    provenance = distribution('edge-tts').read_text('direct_url.json')
    if not provenance or json.loads(provenance).get('vcs_info', {}).get('commit_id') != '0b1c544d020b01338ae491d7f4547729afdc39d3':
        raise RuntimeError('Use el entorno de voz fijado de ETF antes de preparar el recorrido')
    plan = json.loads(PLAN.read_text())
    output = Path(os.environ.get('FACUSO_VIDEO_OUTPUT', '/home/alberto/Vídeos/FAC-USO')).resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('El material de trabajo debe quedar fuera del repositorio')
    folder = output / ('corregido-v2-' + hashlib.sha256(PLAN.read_bytes()).hexdigest()[:10])
    folder.mkdir(parents=True, exist_ok=True)
    phases = [p for c in plan['chapters'] for p in c['phases']]
    semaphore = asyncio.Semaphore(3)
    async def prepare(phase):
        async with semaphore:
            mp3 = folder / (phase['id'] + '.mp3')
            wav = folder / (phase['id'] + '.wav')
            if not wav.exists():
                last_error = None
                for attempt in range(3):
                    try:
                        await edge_tts.Communicate(phase['text'], plan['voice'], rate=plan['rate']).save(str(mp3))
                        last_error = None
                        break
                    except Exception as error:
                        last_error = error
                        await asyncio.sleep(1 + attempt)
                if last_error:
                    raise last_error
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-threads', '2', '-i', str(mp3),
                                '-ac', '1', '-ar', '24000', str(wav)], check=True)
            duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                'format=duration', '-of', 'csv=p=0', str(wav)]))
            phase['voice_seconds'] = duration
            phase['audio'] = wav.name
            print(phase['id'], round(duration, 2), flush=True)
    await asyncio.gather(*(prepare(phase) for phase in phases))
    (folder / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    (folder / 'guion.md').write_text('# Recorrido corregido FAC-USO Andalucía\n\n' + '\n\n'.join(
        '## ' + chapter['title'] + '\n\n' + '\n\n'.join(p['text'] for p in chapter['phases'])
        for chapter in plan['chapters']) + '\n')
    print(json.dumps({'folder': str(folder), 'phases': len(phases),
                      'voice_seconds': round(sum(p['voice_seconds'] for p in phases), 2)}, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
