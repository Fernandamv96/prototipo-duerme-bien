"""Procesadores de contexto - módulo cuentas."""
import hashlib
from pathlib import Path

_ESTATICOS = Path(__file__).resolve().parent / "static" / "hotel"
# Huella del contenido de ui.css y ui.js: cambia con cada versión, así el navegador no usa una copia vieja en caché.
_VERSION = hashlib.sha256(
    b"".join((_ESTATICOS / nombre).read_bytes() for nombre in ("ui.css", "ui.js"))
).hexdigest()[:10]


def version_estaticos(request):
    return {"static_v": _VERSION}
