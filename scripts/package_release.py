"""Empaqueta fuentes e instaladores sin incluir secretos ni archivos de ejecución."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
OUTPUT=DIST/'facuso-entrega-completa.zip'
SKIP={'.secrets','__pycache__','.git','.playwright-cli','vendor','node_modules','.runtime'}
PRIVATE_EXT={'.pem','.key','.phar','.pyc','.pyo'}

def allowed(path):
    return (path.is_file() and not any(p in SKIP for p in path.relative_to(ROOT).parts)
            and path.suffix not in PRIVATE_EXT and path.name not in {'.env','browser-state.json'}
            and not path.name.startswith('.env.'))

files=[]
for name in ['README.md','AGENTS.md','NOTICE.md','SECURITY.md','.gitignore']:
    path=ROOT/name
    if path.exists():files.append(path)
for directory in ['bot','data','docs','scripts','package','docker','imagenes']:
    files += [p for p in (ROOT/directory).rglob('*') if allowed(p)]
files += [p for p in (ROOT/'video').glob('*') if allowed(p) and p.suffix in {'.md', '.txt'}]
for directory in ['research/bop-malaga','research/bop-scout']:
    files += [p for p in (ROOT/directory).glob('*') if allowed(p) and p.suffix in {'.md','.py','.json'}]
files += [DIST/name for name in ['facuso-arranque.zip','facuso-andalucia-tema.zip','facuso-andalucia.xml','contenido-fuentes.json']]
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.parent==DIST}
with zipfile.ZipFile(OUTPUT,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(set(files)):
        if not allowed(path):raise ValueError('Archivo excluido en la entrega: '+str(path))
        entry=zipfile.ZipInfo(str(Path('FAC-USO')/path.relative_to(ROOT)),date_time=(2026,10,18,0,0,0))
        entry.compress_type=zipfile.ZIP_DEFLATED
        entry.external_attr=0o100644 << 16
        archive.writestr(entry,path.read_bytes())
with zipfile.ZipFile(OUTPUT) as archive:
    if archive.testzip() is not None:raise ValueError('ZIP dañado')
    if any('/.secrets/' in name or name.endswith(('.pem','.key','.phar','.pyc')) for name in archive.namelist()):
        raise ValueError('La entrega contiene un fichero privado o de ejecución')
hashes[OUTPUT.name]=hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
(DIST/'SHA256SUMS.txt').write_text(''.join(f'{digest}  {name}\n' for name,digest in sorted(hashes.items())))
print(json.dumps({'bundle':str(OUTPUT.relative_to(ROOT)),'files':len(files),'bytes':OUTPUT.stat().st_size,'sha256':hashes[OUTPUT.name]},ensure_ascii=False))
