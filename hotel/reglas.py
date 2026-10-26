"""Reglas de negocio puras (RN-01 a RN-10), sin dependencias de Django.

Se mantienen separadas de los modelos para que puedan probarse de forma aislada
(pruebas unitarias, Tabla 21 del informe).
"""
import re
from datetime import date

PRECIO_POR_PASAJERO = 40000          # RN-07: valor fijo por pasajero y por noche, definido una sola vez
MAX_NOCHES = 90                      # tope razonable de estadía para evitar errores de digitación
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
        if any(r == rut_n for _n, r in pasajeros):
            raise ReglaError(f"El RUT {rut_n} está repetido en la lista de pasajeros.")
        pasajeros.append((nombre[:150], rut_n))
    if not pasajeros:
        raise ReglaError("Debe ingresar al menos un pasajero.")
    return pasajeros


def parsear_fechas(inicio, termino, hoy):
    """Fechas de inicio y término de la estadía ('AAAA-MM-DD'). Devuelve (inicio, termino, noches)."""
    try:
        f_ini, f_ter = date.fromisoformat(inicio or ""), date.fromisoformat(termino or "")
    except ValueError:
        raise ReglaError("Debe indicar fecha de inicio y fecha de término válidas.")
    if f_ini < hoy:
        raise ReglaError("La fecha de inicio no puede ser anterior a hoy.")
    noches = (f_ter - f_ini).days
    if noches < 1:
        raise ReglaError("La fecha de término debe ser posterior a la fecha de inicio.")
    if noches > MAX_NOCHES:
        raise ReglaError(f"La estadía no puede superar {MAX_NOCHES} noches.")
    return f_ini, f_ter, noches


def calcular_costo(n_pasajeros, noches):
    """RN-07: pasajeros × noches × precio por pasajero."""
    return n_pasajeros * noches * PRECIO_POR_PASAJERO
