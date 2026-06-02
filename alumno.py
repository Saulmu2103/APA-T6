class Alumno:
    """
    Clase usada para el tratamiento de las notas de los alumnos. Cada uno
    incluye los atributos siguientes:

    numIden:   Número de identificación. Es un número entero que, en caso
               de no indicarse, toma el valor por defecto 'numIden=-1'.
    nombre:    Nombre completo del alumno.
    notas:     Lista de números reales con las distintas notas de cada alumno.
    """

    def __init__(self, nombre, numIden=-1, notas=[]):
        self.numIden = numIden
        self.nombre = nombre
        self.notas = [nota for nota in notas]

    def __add__(self, other):
        """
        Devuelve un nuevo objeto 'Alumno' con una lista de notas ampliada con
        el valor pasado como argumento. De este modo, añadir una nota a un
        Alumno se realiza con la orden 'alumno += nota'.
        """
        return Alumno(self.nombre, self.numIden, self.notas + [other])

    def media(self):
        """
        Devuelve la nota media del alumno.
        """
        return sum(self.notas) / len(self.notas) if self.notas else 0

    def __repr__(self):
        """
        Devuelve la representación 'oficial' del alumno. A partir de copia
        y pega de la cadena obtenida es posible crear un nuevo Alumno idéntico.
        """
        return f'Alumno("{self.nombre}", {self.numIden!r}, {self.notas!r})'

    def __str__(self):
        """
        Devuelve la representación 'bonita' del alumno. Visualiza en tres
        columnas separas por tabulador el número de identificación, el nombre
        completo y la nota media del alumno con un decimal.
        """
        return f'{self.numIden}\t{self.nombre}\t{self.media():.1f}'

import doctest
import re

def leeAlumnos(ficAlumn):
    """
    Lee un fichero de texto con los datos de los alumnos y devuelve un diccionario 
    en el que la clave es el nombre de cada alumno, el contenido es el objeto Alumno correspondiente.
    ficAlumn: fichero con los objetos Alumno

    Test unitario:

    >>> alumnos = leeAlumnos('alumnos.txt')
    >>> for alumno in alumnos:
    ...     print(alumnos[alumno])
    ...
    171     Blanca Agirrebarrenetse 9.5
    23      Carles Balcell de Lara  4.9
    68      David Garcia Fuster     7.0
    """

    alumnos = {}
    with open(ficAlumn, encoding='utf-8') as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue

            # 1. Capturar el ID (número entero al principio y el espacio que le sigue)
            match_id = re.match(r'(\d+)\s+', linea)
            if not match_id:
                continue
            idAlumno = int(match_id.group(1))
            resto = linea[match_id.end():]   # todo lo que queda después del ID

            # 2. Buscar el primer número (la primera nota) en ese resto
            match_primer_num = re.search(r'\d+(?:\.\d+)?', resto)
            if not match_primer_num:
                continue

            # 3. El nombre es lo que hay antes de ese primer número, quitando espacios al final
            nombre = resto[:match_primer_num.start()].strip()

            # 4. Capturar TODOS los números (notas) desde esa posición en adelante
            notas_str = re.findall(r'\d+(?:\.\d+)?', resto[match_primer_num.start():])
            notas = [float(n) for n in notas_str]

            # 5. Crear el alumno usando argumentos por palabra clave
            alumno = Alumno(nombre=nombre, numIden=idAlumno, notas=notas)
            alumnos[nombre] = alumno

    return alumnos
        


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE, verbose=True)