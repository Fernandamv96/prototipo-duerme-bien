"""Reglas de negocio puras (RN-01 a RN-10), sin dependencias de Django.

Se mantienen separadas de los modelos para que puedan probarse de forma aislada
(pruebas unitarias, Tabla 21 del informe) y para conservar el mismo diseño que el
prototipo original (hotel/reglas.py en la versión Flask).
"""
import re

PRECIO_POR_PASAJERO = 40000          # RN-07: valor fijo, definido una sola vez
MIN_PASSWORD = 8

RUT_RE = re.compile(r"^(\d{7,8})-([0-9K])$")


class ReglaError(Exception):
    """Violación de una regla de negocio o de validación; su mensaje se muestra al usuario."""


def normalizar_rut(rut):
    """Devuelve el RUT como '12345678-K' si el dígito verificador es válido; si no, None (RF-13)."""
    limpio = (rut or "").replace(".", "").replace(" ", "").upper()
    m = RUT_RE.match(limpio)
    if not m:
        return None
    cuerpo, dv = m.groups()
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - suma % 11
    esperado = {11: "0", 10: "K"}.get(resto, str(resto))
    return f"{int(cuerpo)}-{dv}" if dv == esperado else None


def parsear_pasajeros(texto):
    """Una línea por pasajero con el formato 'Nombre;RUT'. Devuelve lista de (nombre, rut)."""
    pasajeros = []
    for linea in (texto or "").splitlines():
        if not linea.strip():
            continue
        if ";" not in linea:
            raise ReglaError("Cada pasajero debe escribirse como 'Nombre;RUT'.")
        nombre, rut = (p.strip() for p in linea.split(";", 1))
        if not nombre or not rut:
            raise ReglaError("Nombre y RUT del pasajero son obligatorios (RF-13).")
        rut_n = normalizar_rut(rut)
        if rut_n is None:
            raise ReglaError(f"RUT inválido: {rut}.")
        pasajeros.append((nombre[:150], rut_n))
    if not pasajeros:
        raise ReglaError("Debe ingresar al menos un pasajero.")
    return pasajeros
