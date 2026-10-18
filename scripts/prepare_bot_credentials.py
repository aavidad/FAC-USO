"""Genera credenciales locales sin exponerlas en salida ni argumentos de procesos."""
from pathlib import Path
import json
import subprocess
ROOT=Path(__file__).resolve().parents[1]
result=subprocess.run(['docker','compose','-f',str(ROOT/'docker/compose.yaml'),'exec','-T','--user','www-data','wordpress','php','/pruebas/bootstrap_bots.php'],capture_output=True,text=True,check=True)
credentials=json.loads(result.stdout)
folder=ROOT/'docker/.secrets/bots'
folder.mkdir(mode=0o700,parents=True,exist_ok=True)
for province,password in credentials.items():
    path=folder/province
    path.write_text(password)
    path.chmod(0o444)
print(f'{len(credentials)} credenciales provinciales guardadas; valores omitidos.')
