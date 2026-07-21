"""
El bGeigie original guarda las coordenadas en formato NMEA crudo
(ddmm.mmmm para latitud, dddmm.mmmm para longitud) más una letra de
hemisferio (NorteSur / EsteOeste), tal como sale del GPS. Para pintarlas
en un mapa necesitamos grados decimales.

Si algún registro viejo ya viene en decimal (por una fuente distinta),
lo detectamos por rango y lo dejamos tal cual en vez de convertirlo mal.
"""


def _nmea_to_decimal(raw: str, degree_digits: int) -> float | None:
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None

    degrees = int(value / 100) if degree_digits == 2 else int(value / 100)
    # separar grados y minutos según la cantidad de dígitos de grados
    divisor = 10 ** (2 if degree_digits == 2 else 3)
    degrees = int(value // divisor) if value >= divisor / 100 else int(value // 100)
    minutes = value - degrees * 100
    return degrees + minutes / 60


def parse_latitude(raw: str, hemisphere: str | None) -> float | None:
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None

    # Ya viene en decimal (rango típico de latitud)
    if -90 <= value <= 90 and value < 1000:
        # ambiguo con NMEA pequeño; NMEA de latitud siempre es >= 100 aprox
        # (ddmm.mmmm con dd de 2 dígitos ronda 000-9000+)
        if value < 90:
            decimal = value
        else:
            degrees = int(value // 100)
            minutes = value - degrees * 100
            decimal = degrees + minutes / 60
    else:
        degrees = int(value // 100)
        minutes = value - degrees * 100
        decimal = degrees + minutes / 60

    if hemisphere and hemisphere.upper() == "S":
        decimal = -decimal
    return decimal


def parse_longitude(raw: str, hemisphere: str | None) -> float | None:
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None

    if value < 100:
        decimal = value
    else:
        degrees = int(value // 100)
        minutes = value - degrees * 100
        decimal = degrees + minutes / 60

    if hemisphere and hemisphere.upper() == "W":
        decimal = -decimal
    return decimal
