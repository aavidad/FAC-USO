#!/usr/bin/env python3
"""Prepara solo la locución pública del recorrido FAC-USO."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
GUION = RAIZ / "docs/recorridos/guion.md"
SALIDA = Path(os.environ.get("FACUSO_VIDEO_OUTPUT", "/home/alberto/Vídeos/FAC-USO")).expanduser().resolve()
PYTHON = Path(os.environ.get("FACUSO_EDGE_PYTHON", "/home/alberto/Vídeos/ETF/.herramientas/voz/bin/python")).expanduser()
COMMIT = "0b1c544d020b01338ae491d7f4547729afdc39d3"
VOZ = "es-ES-AlvaroNeural"
RATE = "+4%"


def ejecutar(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def extraer():
    texto = GUION.read_text(encoding="utf-8")
    secciones = re.split(r"(?m)^## (\d+)\. ([^\n]+)\n", texto)
    tramos = []
    for i in range(1, len(secciones), 3):
        numero, titulo, cuerpo = secciones[i:i+3]
        voces = re.findall(r"\*\*Locución(?: de bienvenida y avance| del recorrido)?:\*\* «([^»]+)»", cuerpo)
        for j, voz in enumerate(voces):
            tramos.append({"id": f"{int(numero):02d}{chr(97+j) if len(voces)>1 else ''}", "titulo": titulo,
                           "texto": voz, "capitulo": int(numero), "tipo": "avance" if numero == "1" and j == 0 else "web"})
    if len(tramos) != 15 or not all(t["texto"] for t in tramos):
        raise ValueError(f"Se esperaban 15 tramos narrados; encontrados {len(tramos)}")
    return tramos


def comprobar_entorno():
    if not PYTHON.is_file():
        raise RuntimeError("Falta el entorno de voz ETF autorizado")
    metadatos = list((PYTHON.parent.parent / "lib").glob("python*/site-packages/edge_tts-*.dist-info/direct_url.json"))
    if len(metadatos) != 1 or json.loads(metadatos[0].read_text())["vcs_info"]["commit_id"] != COMMIT:
        raise RuntimeError("La versión fijada de edge-tts no coincide")


def duracion(path):
    dato = ejecutar("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path,
                   capture_output=True, text=True).stdout.strip()
    return float(dato)


def main():
    comprobar_entorno()
    if SALIDA == RAIZ or RAIZ in SALIDA.parents:
        raise ValueError('La salida del vídeo debe estar fuera del repositorio')
    tramos = extraer()
    marca = hashlib.sha256(GUION.read_bytes()).hexdigest()[:10]
    carpeta = SALIDA / f"recorrido-{marca}"
    carpeta.mkdir(parents=True, exist_ok=True)
    env = {"PATH": os.defpath, "LANG": "C.UTF-8"}
    for tramo in tramos:
        mp3 = carpeta / f"voz-{tramo['id']}.mp3"
        wav = carpeta / f"voz-{tramo['id']}.wav"
        if not wav.is_file():
            temporal = carpeta / f"voz-{tramo['id']}.part.mp3"
            ejecutar(PYTHON, "-m", "edge_tts", "--voice", VOZ, f"--rate={RATE}", "--text", tramo["texto"],
                    "--write-media", temporal, env=env, timeout=120, capture_output=True)
            if temporal.stat().st_size < 1000:
                raise RuntimeError(f"Audio incompleto: {tramo['id']}")
            temporal.replace(mp3)
            ejecutar("ffmpeg", "-v", "error", "-y", "-i", mp3, "-ac", "1", "-ar", "24000", wav)
        tramo["duracion_s"] = duracion(wav)
        tramo["wav"] = wav.name
    (carpeta / "guion.md").write_text(GUION.read_text(encoding="utf-8"), encoding="utf-8")
    (carpeta / "tramos.json").write_text(json.dumps(tramos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"carpeta": str(carpeta), "duracion_voz_s": round(sum(t["duracion_s"] for t in tramos), 1),
                      "tramos": len(tramos)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
