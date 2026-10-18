"""Prepara secretos desechables solo para el WordPress local de pruebas."""
from pathlib import Path
import secrets

folder = Path(__file__).resolve().parents[1] / "docker/.secrets"
folder.mkdir(mode=0o700, parents=True, exist_ok=True)
for name in ["db_password", "db_root_password", "admin_password"]:
    path = folder / name
    if not path.exists():
        path.write_text(secrets.token_urlsafe(30))
    # Compose monta estos ficheros conservando el propietario del host. El directorio
    # 0700 impide leerlos a otros usuarios del host; PHP necesita leer el secreto montado.
    path.chmod(0o600 if name == 'db_root_password' else 0o444)
