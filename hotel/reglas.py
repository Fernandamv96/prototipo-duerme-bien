"""Reglas de negocio puras (RN-01 a RN-10), sin dependencias de Django.

Se mantienen separadas de los modelos para que puedan probarse de forma aislada
(pruebas unitarias, Tabla 21 del informe).
"""
import re
from datetime import date

PRECIO_POR_PASAJERO = 40000          # RN-07: precio por defecto (por pasajero y por noche) de una habitación nueva
MAX_NOCHES = 90                      # tope razonable de estadía para evitar errores de digitación
MIN_PASSWORD = 8

RUT_RE = re.compile(r"^(\d{7,8})-?([0-9K])$")   # el guion es opcional
TELEFONO_RE = re.compile(r"^\+?\d{8,15}$")
# Correo: parte local con letras, números y . _ % + - ; dominio con etiquetas separadas por puntos y extensión de 2+ letras
CORREO_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*\.[A-Za-z]{2,}$")
MAX_CORREO = 254
FECHA_RE = re.compile(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$")   # DD-MM-AAAA o DD/MM/AAAA


class ReglaError(Exception):
    """Violación de una regla de negocio o de validación; su mensaje se muestra al usuario."""


def normalizar_rut(rut):
    """Devuelve el RUT como '12345678-K' si el dígito verificador es válido; si no, None (RF-13)."""
    m = RUT_RE.match(_limpiar_rut(rut))
    if not m:
        return None
    cuerpo, dv = m.groups()
    return f"{int(cuerpo)}-{dv}" if dv == digito_verificador(cuerpo) else None


def _limpiar_rut(rut):
    return (rut or "").replace(".", "").replace(" ", "").upper()


def digito_verificador(cuerpo):
    """Dígito verificador (módulo 11) del cuerpo numérico de un RUT."""
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - suma % 11
    return {11: "0", 10: "K"}.get(resto, str(resto))


def motivo_rut_invalido(rut):
    """Explica por qué un RUT no es válido, para que el usuario pueda corregirlo."""
    m = RUT_RE.match(_limpiar_rut(rut))
    if not m:
        return "use el formato 12345678-5"
    return f"el dígito verificador debería ser {digito_verificador(m.group(1))}"


def normalizar_telefono(telefono):
    """Teléfono de contacto: 8 a 15 dígitos, con '+' inicial opcional; se ignoran espacios, guiones y paréntesis.
    Devuelve el número limpio (p. ej. '+56912345678') o None si no es válido."""
    limpio = re.sub(r"[\s\-()]", "", telefono or "")
    return limpio if TELEFONO_RE.match(limpio) else None


def correo_valido(correo):
    correo = correo or ""
    return len(correo) <= MAX_CORREO and ".." not in correo and bool(CORREO_RE.match(correo))


def parsear_pasajeros(nombres, ruts, telefonos, correos=None):
    """Un pasajero por fila del formulario (nombre, RUT, teléfono y correo opcional), en listas paralelas.
    Las filas completamente vacías se ignoran. Devuelve una lista de dicts con los datos ya normalizados."""
    correos = list(correos or [])
    filas = zip(nombres or [], ruts or [], telefonos or [], correos + [""] * (len(nombres or []) - len(correos)))
    pasajeros = []
    for i, (nombre, rut, telefono, correo) in enumerate(filas, start=1):
        nombre, rut, telefono, correo = (str(v or "").strip() for v in (nombre, rut, telefono, correo))
        if not (nombre or rut or telefono or correo):
            continue
        faltan = [campo for campo, valor in (("nombre", nombre), ("RUT", rut), ("teléfono", telefono)) if not valor]
        if faltan:
            raise ReglaError(f"Pasajero {i}: falta {' y '.join(faltan)} (RF-13).")
        rut_n = normalizar_rut(rut)
        if rut_n is None:
            raise ReglaError(f"Pasajero {i}: RUT inválido {rut} ({motivo_rut_invalido(rut)}).")
        if any(p["rut"] == rut_n for p in pasajeros):
            raise ReglaError(f"El RUT {rut_n} está repetido en la lista de pasajeros.")
        tel_n = normalizar_telefono(telefono)
        if tel_n is None:
            raise ReglaError(f"Pasajero {i}: teléfono inválido {telefono} (use solo números, p. ej. +56 9 1234 5678).")
        if correo and not correo_valido(correo):
            raise ReglaError(f"Pasajero {i}: correo inválido {correo}.")
        pasajeros.append({"nombre": nombre[:150], "rut": rut_n, "telefono": tel_n, "correo": correo.lower()})
    if not pasajeros:
        raise ReglaError("Debe ingresar al menos un pasajero.")
    return pasajeros


def validar_numero_habitacion(numero):
    """El número de habitación solo admite dígitos (p. ej. 101)."""
    numero = (numero or "").strip()
    if not numero.isdigit() or not numero.isascii():
        raise ReglaError("El número de habitación solo puede contener números (p. ej. 101).")
    return numero


def validar_cantidad(cantidad, pasajeros):
    """La cantidad de pasajeros declarada debe coincidir con los ingresados: cada uno con su propio RUT."""
    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        raise ReglaError("Indique la cantidad de pasajeros.")
    if cantidad < 1:
        raise ReglaError("La cantidad de pasajeros debe ser al menos 1.")
    n = len(pasajeros)
    if n < cantidad:
        raise ReglaError(
            f"Indicó {cantidad} pasajeros pero ingresó {n}: faltan los datos de {cantidad - n}. "
            "Cada pasajero debe tener su propia fila con nombre, RUT y teléfono."
        )
    if n > cantidad:
        raise ReglaError(f"Indicó {cantidad} pasajeros pero ingresó {n}; corrija la cantidad o la lista.")


def parsear_fecha(texto):
    """Fecha escrita a mano como 'DD-MM-AAAA' (también con '/') o en formato ISO 'AAAA-MM-DD'."""
    texto = (texto or "").strip()
    m = FECHA_RE.match(texto)
    if m:
        dia, mes, anio = (int(g) for g in m.groups())
        return date(anio, mes, dia)
    return date.fromisoformat(texto)


def parsear_fechas(inicio, termino, hoy):
    """Fechas de inicio y término de la estadía. Devuelve (inicio, termino, noches)."""
    try:
        f_ini, f_ter = parsear_fecha(inicio), parsear_fecha(termino)
    except ValueError:
        raise ReglaError("Debe indicar fecha de inicio y fecha de término válidas (DD-MM-AAAA).")
    if f_ini < hoy:
        raise ReglaError("La fecha de inicio no puede ser anterior a hoy.")
    noches = (f_ter - f_ini).days
    if noches < 1:
        raise ReglaError("La fecha de término debe ser posterior a la fecha de inicio.")
    if noches > MAX_NOCHES:
        raise ReglaError(f"La estadía no puede superar {MAX_NOCHES} noches.")
    return f_ini, f_ter, noches


def calcular_costo(n_pasajeros, noches, precio):
    """RN-07: pasajeros × noches × precio por pasajero de la habitación."""
    return n_pasajeros * noches * precio


def parsear_precio(precio):
    """Precio por pasajero y por noche: entero positivo en pesos (se aceptan puntos de miles)."""
    try:
        valor = int(str(precio or "").replace(".", "").replace("$", "").strip())
    except ValueError:
        raise ReglaError("El precio debe ser un número entero en pesos.")
    if valor <= 0:
        raise ReglaError("El precio debe ser mayor que 0.")
    return valor
