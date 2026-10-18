"""Crea una sesión local de navegador sin mostrar contraseña ni cookies."""
from pathlib import Path
import json
import requests

ROOT=Path(__file__).resolve().parents[1]
session=requests.Session()
base='http://127.0.0.1:18086'
session.get(base+'/wp-login.php', timeout=10).raise_for_status()
response=session.post(base+'/wp-login.php', data={
    'log':'facuso-admin', 'pwd':(ROOT/'docker/.secrets/admin_password').read_text().strip(),
    'wp-submit':'Log In','redirect_to':base+'/wp-admin/','testcookie':'1',
},timeout=20)
response.raise_for_status()
assert any('wordpress_logged_in' in c.name for c in session.cookies), 'Fallo de autenticación local'
state={'cookies':[{'name':c.name,'value':c.value,'domain':c.domain,'path':c.path,'expires':c.expires or -1,'httpOnly':True,'secure':c.secure,'sameSite':'Lax'} for c in session.cookies], 'origins':[]}
path=ROOT/'docker/.secrets/browser-state.json'
path.write_text(json.dumps(state));path.chmod(0o600)
print('Sesión de pruebas creada; credenciales omitidas.')
