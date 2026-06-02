"""
Módulo para la normalización de expresiones horarias en un texto.

Este módulo proporciona la función `normalizaHoras` que lee un fichero
de texto, busca todas las expresiones horarias (correctas e incorrectas)
y las convierte al formato normalizado HH:MM, donde las horas y los minutos
se representan con dos dígitos y se separan por dos puntos (ej. 08:27).

Las expresiones horarias que no pueden interpretarse de manera razonable
se mantienen sin cambios.

Formatos reconocidos y su normalización:

- Horas con dos puntos (H:MM o HH:MM): los minutos con un solo dígito se
  completan con un cero a la izquierda (17:5 → 17:05).
- Horas con 'h' y minutos opcionales (Hh, HhMM, HhMMm), con o sin periodo
  del día: se convierten al formato 24 horas si se especifica
  'de la mañana/tarde/noche'.
- Expresiones "y media" y "menos cuarto", que se interpretan como :30 y :45
  respectivamente, también con posibilidad de periodo.
- "H en punto": se trata como hora exacta (:00).
- Periodos del día ('mañana', 'tarde', 'noche'): se convierten al sistema
  de 24 horas de forma flexible, corrigiendo incluso combinaciones
  habituales pero incorrectas como "11 de la tarde" (→ 23:00)
  o "17 de la tarde" (→ 17:00).
- Horas superiores a 23 o minutos superiores a 59 se corrigen realizando
  acarreo o reducción módulo 24 (ej. 32h31m → 08:31, 1h78m → 02:18).

La función principal, `normalizaHoras`, lee el fichero de entrada,
aplica todas las transformaciones y escribe el resultado en el fichero
de salida.
"""

import re
import doctest

def normalizaHoras(ficText, ficNorm):
    """
    Lee un fichero de texto y normaliza sus expresiones horarias.

    Busca en cada línea del fichero `ficText` todas las expresiones horarias
    que sigan alguno de los patrones reconocidos (correctos o con pequeños
    errores) y las convierte al formato estándar HH:MM. El texto resultante
    se guarda en `ficNorm`.

    Args:
        ficText (str): Ruta al fichero de texto de entrada.
        ficNorm (str): Ruta al fichero de texto de salida donde se escribirá
                       el contenido normalizado.

    Returns:
        None: La función no devuelve ningún valor; escribe directamente en
              el fichero `ficNorm`.

    Raises:
        FileNotFoundError: Si el fichero `ficText` no existe.
        PermissionError: Si no se tienen permisos de lectura o escritura.

    Ejemplo de uso:
        >>> normalizaHoras('horas.txt', 'horas_salida.txt')
        >>> with open('horas_salida.txt', encoding='utf-8') as f:
        ...     print(f.read(), end='')
        La llegada del tren está prevista a las 18:30
        Tenía su clase entre las 08:00 y las 10:30
        Se acaba a las 16:30
        Empieza a trabajar a las 07:00
        Es lo mismo 04:45 que 04:45
        Tenemos descanso hasta las 17:05
        Las campanadas son a las 00:00
        <BLANKLINE>
        Son exactamente las 17:05
        Cuando llegó, ya eran las 23:00
        El examen es a las 17:00
        Cenamos en las 7 puertas
        No llegará antes de las 02:18
        Corrió la maratón en 08:31, pero no ganó
        Quedamos a las 23:00

    Nota:
        La función emplea un conjunto de expresiones regulares que se aplican
        en orden, de manera que las transformaciones más específicas se
        realizan antes que las generales. Las partes no horarias del texto
        se mantienen intactas.
    """
    with open(ficText, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
    with open(ficNorm, 'w', encoding='utf-8') as f:
        for linea in lineas:
            linea = normalizarLinea(linea)
            f.write(linea)

def normalizarLinea(linea):
    """Aplica todas las transformaciones de normalización a una línea."""

    # 1. Formato con dos puntos (minutos de 1 o 2 dígitos)
    linea = re.sub(
        r'\b(\d{1,2}):(\d{1,2})\b',
        lambda m: colonRepl(m), linea
    )

    # 2. Formato con 'h', minutos opcionales y periodo opcional
    linea = re.sub(
        r'\b(\d{1,2})h(?:(\d{1,2})m?)?(?:\s*de\s+la\s+(mañana|tarde|noche))?\b',
        lambda m: hRepl(m), linea, flags=re.IGNORECASE
    )

    # 3. "y media"
    linea = re.sub(
        r'\b(\d{1,2})\s+y\s+media(?:\s+de\s+la\s+(mañana|tarde|noche))?\b',
        lambda m: ymediaRepl(m), linea, flags=re.IGNORECASE
    )

    # 4. "menos cuarto"
    linea = re.sub(
        r'\b(\d{1,2})\s+menos\s+cuarto(?:\s+de\s+la\s+(mañana|tarde|noche))?\b',
        lambda m: menoscuartoRepl(m), linea, flags=re.IGNORECASE
    )

    # 5. "de la mañana/tarde/noche" (sin otras partículas)
    linea = re.sub(
        r'\b(\d{1,2})\s+de\s+la\s+(mañana|tarde|noche)\b',
        lambda m: delaRepl(m), linea, flags=re.IGNORECASE
    )

    # 6. "en punto" (con o sin periodo)
    linea = re.sub(
        r'\b(\d{1,2})\s+en\s+punto(?:\s+de\s+la\s+(mañana|tarde|noche))?\b',
        lambda m: enpuntoRepl(m), linea, flags=re.IGNORECASE
    )

    return linea

# ----------------------------------------------------------------------
# Funciones auxiliares de conversión (ahora más permisivas)
# ----------------------------------------------------------------------

def convertirConPeriodo(h, m, periodo):
    """
    Convierte una hora (1-12) y un periodo ('mañana', 'tarde', 'noche')
    a hora en formato 24h.
    Si la hora no encaja en el rango típico del periodo, se aplica una
    corrección flexible:
      - 'mañana': 1-12 -> se deja como está.
      - 'tarde' : suma 12, salvo que h==12 (se deja 12).
      - 'noche' : suma 12 si h != 12; si h==12 se convierte en 0.
    Si h > 12, se ignora el periodo y se devuelve (h, m) directamente.
    Retorna None si el resultado final está fuera de 0-23.
    """
    if h > 12:
        # La hora ya está en formato 24h, ignoramos el periodo
        return (h, m) if h <= 23 else None
    if periodo == 'mañana':
        if 1 <= h <= 12:
            return (h, m)
    elif periodo == 'tarde':
        # En rigor tarde es 1-8, pero si alguien dice "11 de la tarde"
        # lo interpretamos como 23:00 (sumamos 12)
        return ((h + 12) if h != 12 else 12, m)
    elif periodo == 'noche':
        if h == 12:
            return (0, m)
        else:
            return (h + 12, m)
    return None

def ajustarHoraMinutos(h, m):
    """
    Corrige minutos >59 realizando acarreo.
    También reduce la hora módulo 24 si es necesario.
    Retorna (hora, minutos) normalizados.
    """
    horasExtra = m // 60
    m %= 60
    h += horasExtra
    h %= 24
    return h, m

# ----------------------------------------------------------------------
# Reemplazos para cada patrón
# ----------------------------------------------------------------------

def colonRepl(m):
    h = int(m.group(1))
    minutos = int(m.group(2))
    if 0 <= h <= 23 and 0 <= minutos <= 59:
        return f"{h:02d}:{minutos:02d}"
    # Si no, dejamos la expresión original
    return m.group(0)

def hRepl(m):
    h = int(m.group(1))
    minutos = int(m.group(2)) if m.group(2) else 0
    periodo = m.group(3)

    # Si hay periodo, intentamos corregir aunque la hora no esté en el rango original
    if periodo:
        res = convertirConPeriodo(h, 0, periodo)  # primero la hora en punto
        if res is None:
            return m.group(0)
        h24, _ = res
        # Ahora sumamos los minutos (puede haber acarreo)
        hFinal = h24
        mFinal = minutos
        hFinal, mFinal = ajustarHoraMinutos(hFinal, mFinal)
        return f"{hFinal:02d}:{mFinal:02d}"
    else:
        # Sin periodo: aceptamos cualquier hora 0-23, pero si se pasa corregimos
        if h > 23:
            h = h % 24
        h, minutos = ajustarHoraMinutos(h, minutos)
        return f"{h:02d}:{minutos:02d}"

def ymediaRepl(m):
    h = int(m.group(1))
    periodo = m.group(2)
    if periodo:
        res = convertirConPeriodo(h, 0, periodo)
        if res is None:
            return m.group(0)
        h24, _ = res
        # Sumamos 30 minutos, con posible acarreo
        h24, m24 = ajustarHoraMinutos(h24, 30)
        return f"{h24:02d}:{m24:02d}"
    else:
        # Sin periodo, la hora puede ser 1-12 (se asume reloj de 12h) o 0-23
        if 1 <= h <= 12:
            return f"{h:02d}:30"
        elif 0 <= h <= 23:
            # Si es mayor de 12, se asume que ya está en 24h y se le suma 30 min
            h, m = ajustarHoraMinutos(h, 30)
            return f"{h:02d}:{m:02d}"
        return m.group(0)

def menoscuartoRepl(m):
    h = int(m.group(1))
    periodo = m.group(2)
    if periodo:
        res = convertirConPeriodo(h, 0, periodo)
        if res is None:
            return m.group(0)
        h24, _ = res
        totalMinutos = h24 * 60 - 15
        if totalMinutos < 0:
            totalMinutos += 24 * 60
        hNew = totalMinutos // 60
        mNew = totalMinutos % 60
        return f"{hNew:02d}:{mNew:02d}"
    else:
        if 1 <= h <= 12:
            totalMinutos = h * 60 - 15
            if totalMinutos < 0:
                totalMinutos += 24 * 60
            hNew = totalMinutos // 60
            mNew = totalMinutos % 60
            return f"{hNew:02d}:{mNew:02d}"
        elif 0 <= h <= 23:
            totalMinutos = h * 60 - 15
            if totalMinutos < 0:
                totalMinutos += 24 * 60
            hNew = totalMinutos // 60
            mNew = totalMinutos % 60
            return f"{hNew:02d}:{mNew:02d}"
        return m.group(0)

def delaRepl(m):
    h = int(m.group(1))
    periodo = m.group(2)
    res = convertirConPeriodo(h, 0, periodo)
    if res is None:
        return m.group(0)
    h24, m24 = res
    return f"{h24:02d}:{m24:02d}"

def enpuntoRepl(m):
    h = int(m.group(1))
    periodo = m.group(2)
    if periodo:
        res = convertirConPeriodo(h, 0, periodo)
        if res is None:
            return m.group(0)
        h24, m24 = res
        return f"{h24:02d}:{m24:02d}"
    else:
        if 0 <= h <= 23:
            return f"{h:02d}:00"
        return m.group(0)

if __name__ == '__main__':
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE, verbose=True)