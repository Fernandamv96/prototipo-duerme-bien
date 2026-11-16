"""Procesadores de contexto - módulo cuentas."""
import hashlib
from pathlib import Path

from hotel.reglas import PRECIO_POR_PASAJERO

_ESTATICOS = Path(__file__).resolve().parent / "static" / "hotel"
# Huella del contenido de ui.css, ui.js y tema.js: cambia con cada versión, así el navegador no usa una copia vieja en caché.
_VERSION = hashlib.sha256(
    b"".join((_ESTATICOS / nombre).read_bytes() for nombre in ("ui.css", "ui.js", "tema.js"))
).hexdigest()[:10]


def version_estaticos(request):
    # La tarifa única (RN-07) se muestra en todas las pantallas desde un solo lugar
    tarifa_clp = "$" + f"{PRECIO_POR_PASAJERO:,}".replace(",", ".")
    return {"static_v": _VERSION, "tarifa": PRECIO_POR_PASAJERO, "tarifa_clp": tarifa_clp}
