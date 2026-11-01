"""Interpretación local de una descripción de PC.

Usa reglas, expresiones regulares y sinónimos. No consulta el catálogo,
no arma configuraciones y no llama servicios externos.
"""

import re

from core.recomendador_pc import Preferencias


MAX_CARACTERES = 2000

_RAM_VALIDA = (8, 16, 32, 64)
_DISCO_VALIDO = (500, 1000, 2000)
_SOCKETS = ('AM4', 'AM5', 'LGA1200', 'LGA1700')
_USO_ETIQUETA = {
    'gaming': 'Gaming',
    'trabajo': 'Trabajo',
    'edicion': 'Edición',
    'general': 'General',
}
_ORDEN = (
    'presupuesto', 'uso', 'resolucion', 'ram_gb',
    'disco_tipo', 'disco_gb', 'socket', 'gpu',
)
_ETIQUETA_CAMPO = {
    'presupuesto': 'Presupuesto',
    'uso': 'Uso principal',
    'resolucion': 'Resolución',
    'ram_gb': 'RAM mínima',
    'disco_tipo': 'Almacenamiento',
    'disco_gb': 'Capacidad mínima',
    'socket': 'Plataforma',
    'gpu': 'Tarjeta gráfica',
}
_TIPO_ETIQUETA = {
    'detectado': 'Detectado',
    'obligatorio': 'Obligatorio',
    'preferencia': 'Preferencia',
    'pendiente': 'Hay que confirmarlo',
}
_MARCADORES = (
    ('como minimo', 'obligatorio'),
    ('al menos', 'obligatorio'),
    ('es obligatorio', 'obligatorio'),
    ('debe tener', 'obligatorio'),
    ('deben tener', 'obligatorio'),
    ('me gustaria', 'preferencia'),
    ('si es posible', 'preferencia'),
    ('de ser posible', 'preferencia'),
    ('preferiria', 'preferencia'),
    ('prefiero', 'preferencia'),
    ('necesitamos', 'obligatorio'),
    ('necesito', 'obligatorio'),
    ('obligatorio', 'obligatorio'),
    ('idealmente', 'preferencia'),
    ('ojala', 'preferencia'),
    ('quisiera', 'pendiente'),
    ('quiero', 'pendiente'),
    ('busco', 'pendiente'),
    ('minimo', 'obligatorio'),
    ('con', 'pendiente'),
)
_FRASES_USO = (
    ('produccion audiovisual', 'edicion'),
    ('edicion de videos', 'edicion'),
    ('edicion de video', 'edicion'),
    ('editar videos', 'edicion'),
    ('editar video', 'edicion'),
    ('renderizado', 'edicion'),
    ('renderizar', 'edicion'),
    ('videojuegos', 'gaming'),
    ('juegos de pc', 'gaming'),
    ('desarrollo de software', 'trabajo'),
    ('desarrollo web', 'trabajo'),
    ('desarrollar software', 'trabajo'),
    ('tareas basicas', 'general'),
    ('uso domestico', 'general'),
    ('navegar por internet', 'general'),
    ('programacion', 'trabajo'),
    ('productividad', 'trabajo'),
    ('ofimatica', 'trabajo'),
    ('programar', 'trabajo'),
    ('estudiar', 'general'),
    ('estudio', 'general'),
    ('trabajar', 'trabajo'),
    ('render', 'edicion'),
    ('oficina', 'trabajo'),
    ('trabajo', 'trabajo'),
    ('edicion', 'edicion'),
    ('editar', 'edicion'),
    ('gaming', 'gaming'),
    ('gamer', 'gaming'),
    ('juegos', 'gaming'),
    ('jugar', 'gaming'),
    ('desarrollar', 'trabajo'),
    ('desarrollo', 'trabajo'),
    ('software', 'trabajo'),
    ('navegar', 'general'),
    ('internet', 'general'),
    ('domestico', 'general'),
)
_SOCKETS_AJENOS = {
    'LGA1151': 'LGA1151',
    'LGA1150': 'LGA1150',
    'LGA1851': 'LGA1851',
    'AM3': 'AM3',
    'TR4': 'TR4',
    'STR5': 'STR5',
    'SP5': 'SP5',
}
_ACENTOS = str.maketrans(
    'áéíóúüñàèìòùÁÉÍÓÚÜÑÀÈÌÒÙ',
    'aeiouunaeiouaeiouunaeiou',
)
_SEPARADORES = re.compile(r'(?<!\d)\s*(?:\.+|;|\n|\bpero\b|,)\s*(?!\d)')
_SIN_GPU = re.compile(
    r'\b(?:'
    r'no\s+quiero\s+(?:una\s+|la\s+)?(?:tarjeta\s+grafica|grafica|gpu)(?:\s+dedicada)?'
    r'|no\s+necesito\s+(?:una\s+|la\s+)?(?:tarjeta\s+grafica|grafica|gpu)(?:\s+dedicada)?'
    r'|no\s+necesite\s+(?:una\s+|la\s+)?(?:tarjeta\s+grafica|grafica|gpu)(?:\s+dedicada)?'
    r'|no\s+tener\s+(?:una\s+|la\s+)?(?:tarjeta\s+grafica|grafica|gpu)(?:\s+dedicada)?'
    r'|sin\s+(?:una\s+|la\s+)?(?:tarjeta\s+grafica|grafica|gpu)(?:\s+dedicada)?'
    r'|sin\s+dedicada'
    r')\b'
)
_CON_GPU = re.compile(
    r'\b(?:necesito|quiero|exijo|busco)\s+(?:una\s+|la\s+)?'
    r'(?:tarjeta\s+grafica|gpu|grafica)\s+dedicada\b'
)
_VRAM = (
    re.compile(
        r'\b(?:gpu|tarjeta\s+grafica|grafica|vram)\s+(?:de\s+)?'
        r'(\d{1,3})\s*(?:gb|gigas?|gigabytes?)\b'
    ),
    re.compile(r'\b(\d{1,3})\s*(?:gb|gigas?|gigabytes?)\s+de\s+(?:vram|video)\b'),
    re.compile(
        r'\b(\d{1,3})\s*(?:gb|gigas?|gigabytes?)\s+de\s+memoria\s+de\s+video\b'
    ),
    re.compile(
        r'\bmemoria\s+de\s+video\s+(?:de\s+)?(\d{1,3})\s*(?:gb|gigas?|gigabytes?)?\b'
    ),
)
_RAM = (
    re.compile(
        r'\b(\d{1,3})\s*(?:gb|gigas?|gigabytes?)\s+o\s+'
        r'(\d{1,3})\s*(?:gb|gigas?|gigabytes?)\s*(?:de\s+)?'
        r'(?:memoria\s+ram|ram|memoria)\b'
    ),
    re.compile(
        r'\b(\d{1,3})\s*(?:gb|gigas?|gigabytes?)\s*(?:de\s+)?'
        r'(?:memoria\s+ram|ram|memoria)\b'
    ),
    re.compile(
        r'\b(?:memoria\s+ram|ram|memoria)\s*(?:de\s+)?'
        r'(\d{1,3})\s*(?:gb|gigas?|gigabytes?)?\b'
    ),
)
_TIPO_Y_CAPACIDAD = re.compile(
    r'\b(ssd|hdd|nvme|disco\s+duro|discos\s+duros|disco|almacenamiento)\b'
    r'(?:\s+\w+){0,5}\s+(\d+(?:[.,]\d+)?)\s*(tb|gb)\b'
)
_CAPACIDAD_Y_TIPO = re.compile(
    r'\b(\d+(?:[.,]\d+)?)\s*(tb|gb)\s+de\s+'
    r'(ssd|hdd|nvme|disco\s+duro|disco|almacenamiento)\b'
)
_SOLO_TB = re.compile(r'\b(\d+(?:[.,]\d+)?)\s*tb\b')
_NEGAR_HDD = re.compile(
    r'\b(?:sin|no\s+quiero|no\s+necesito)\s+(?:un\s+|el\s+|los\s+)?'
    r'(?:hdd|disco\s+duro|discos\s+duros)\b'
)
_NEGAR_SSD = re.compile(
    r'\b(?:sin|no\s+quiero|no\s+necesito)\s+(?:un\s+|el\s+)?ssd\b'
)
_RESOLUCION = re.compile(r'\b(?:(1080|1440|2160)\s*p|4k)\b')
_ECONOMICO = re.compile(
    r'\b(?:economico|barato|barata|lo\s+mas\s+barato(?:\s+posible)?|mas\s+barato|gastar\s+menos)\b'
)
_RANGO_PESOS = re.compile(
    r'\bentre\s+\$?\s*(\d{1,3}(?:\.\d{3})+|\d{5,9})\s+y\s+'
    r'\$?\s*(\d{1,3}(?:\.\d{3})+|\d{5,9})\b'
)
_RANGO_UNIDAD = re.compile(
    r'\bentre\s+(\d+(?:[.,]\d+)?)\s*(lucas?|mil|millones?)?\s+y\s+'
    r'(\d+(?:[.,]\d+)?)\s*(lucas?|mil|millones?)\b'
)
_RANGO_DE_A = re.compile(
    r'\bde\s+(\d+(?:[.,]\d+)?)\s+a\s+(\d+(?:[.,]\d+)?)\s+(lucas?|mil|millones?)\b'
)
_RANGO_K = re.compile(r'\bentre\s+(\d{2,4})k\s+y\s+(\d{2,4})k\b')
_MONTO_K = re.compile(r'(?<![\d.])(\d{2,4})k\b')
_PALO = re.compile(
    r'\b(?:(?P<n>\d+)|un|una)\s+palo(?P<medio>\s+y\s+medio)?\b(?!\s+de\b)'
)
_MEDIO_MILLON = re.compile(
    r'\bmedio\s+millon(?:es)?(?:\s+de\s+pesos)?\b(?!\s+de\s+(?!pesos\b))'
)
_CONTEXTO_DINERO = re.compile(
    r'\b(?:tengo|presupuesto|maximo|hasta|alrededor|cerca|aproximadamente|aprox|'
    r'unas|unos|como|entre|gastar|pesos|lucas|luca|dispongo|cuento|poseo|'
    r'no\s+mas\s+de)\b'
)
_MOD_PRINCIPAL = re.compile(r'\b(?:principalmente|sobre todo)\b')
_MOD_OCASIONAL = re.compile(r'\b(?:ocasionalmente|a veces|de vez en cuando|a ratos)\b')
_NECESIDADES = (
    (
        re.compile(r'\b(?:maquinas?\s+virtuales|maquina\s+virtual|virtualizacion)\b'),
        'Máquinas virtuales',
        'Detectamos que utilizarás máquinas virtuales. Puedes indicar cuánta RAM necesitas; '
        'no se asignará una cantidad automáticamente.',
    ),
    (
        re.compile(r'\bvalorant\b'),
        'Valorant',
        'Detectamos que quieres jugar Valorant. El sistema puede recomendar un PC para Gaming, '
        'pero no garantiza FPS específicos para ese juego.',
    ),
    (
        re.compile(r'\bminecraft\b'),
        'Minecraft',
        'Detectamos que quieres jugar Minecraft. El sistema puede recomendar un PC para Gaming, '
        'pero no garantiza FPS específicos para ese juego.',
    ),
    (
        re.compile(r'\b(?:duradero|vida\s+util|varios\s+anos|dure(?:\s+varios\s+anos)?)\b'),
        'Durabilidad',
        'Quieres que el PC dure varios años. No podemos garantizar una vida útil '
        'determinada a partir de los datos disponibles.',
    ),
    (
        re.compile(
            r'\b(?:actualizar(?:lo|la|los|las|me)?|actualizaciones?(?:\s+futuras)?|'
            r'mas\s+adelante|pueda\s+mejorar|mejorar(?:\s+sus|\s+los)?\s+componentes)\b'
        ),
        'Actualizaciones futuras',
        'Quieres actualizar componentes más adelante. La compatibilidad actual no garantiza '
        'futuras posibilidades de actualización.',
    ),
    (
        re.compile(r'\brapid[oa]s?\b'),
        'Rapidez',
        'Mencionas que lo necesitas rápido. No se asigna una velocidad ni un rendimiento concreto.',
    ),
)
_TECHO_FINAL = re.compile(
    r'(?:hasta|maximo|no\s+mas\s+de|mas\s+de|como\s+maximo|como\s+mucho|tope)\s*$'
)
_APROX_FINAL = re.compile(
    r'(?:alrededor\s+de|cerca\s+de|aproximadamente|aprox|unas|unos|como)\s*$'
)
_APROX_SIGUIENTE = re.compile(r'^\s*(?:aproximadamente|aprox)\b')
_COMO_MINIMO = re.compile(r'\bcomo\s+minimo\s*$')
_MONTO_NEGADO = re.compile(
    r'\bno\s+(?:tengo|dispongo(?:\s+de)?|cuento(?:\s+con)?|poseo)'
    r'(?:\s+(?:unos|unas|alrededor\s+de|cerca\s+de))?\s*$'
)
_AVISO_NEGADO = (
    'No usé un monto que está negado. '
    'Indica el presupuesto máximo que sí quieres gastar.'
)
_AVISO_MINIMO = (
    '«Como mínimo» no indica el presupuesto máximo. Escribe el tope en pesos.'
)
_AVISO_RANGO = (
    'Hay más de un monto. Elige el presupuesto máximo que quieres usar. '
    'Ninguno se aplicó todavía.'
)
_AVISO_APROXIMADO = (
    'El monto es aproximado. Confírmalo antes de usarlo como presupuesto máximo. '
    'La cifra no se cambió.'
)
_MARCA = re.compile(r'\b(amd|ryzen|intel|nvidia)\b')
_SOCKET = re.compile(
    r'\b(lga\s*1851|lga\s*1700|lga\s*1200|lga\s*1151|lga\s*1150|am4|am5|am3|tr4|str5|sp5)\b'
)


class SolicitudInvalida(Exception):
    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


class _Hallazgo:
    def __init__(self, campo, valor, inicio, fin, fragmento, modo_inherente=None, aproximado=False):
        self.campo = campo
        self.valor = valor
        self.inicio = inicio
        self.fin = fin
        self.fragmento = fragmento
        self.modo_inherente = modo_inherente
        self.aproximado = aproximado
        self.tipo = None


def interpretar_solicitud(texto):
    """Devuelve un borrador. No modifica el formulario ni recomienda equipos."""
    if not isinstance(texto, str):
        raise SolicitudInvalida('La descripción no es válida.')
    if len(texto) > MAX_CARACTERES:
        raise SolicitudInvalida(
            f'La descripción supera los {MAX_CARACTERES} caracteres.'
        )
    if not texto.strip():
        raise SolicitudInvalida('Escribe qué computador necesitas antes de interpretarlo.')

    normalizado = _normalizar(texto)
    ocupados = []
    hallazgos = []
    aparte = []
    advertencias = []

    _marcar_vram(normalizado, texto, ocupados, aparte)
    _marcar_resolucion(normalizado, texto, ocupados, hallazgos)
    _marcar_ram(normalizado, texto, ocupados, hallazgos, aparte)
    _marcar_almacenamiento(normalizado, texto, ocupados, hallazgos, aparte)
    _marcar_gb_ambiguo(normalizado, texto, ocupados, aparte)
    _marcar_sockets(normalizado, texto, ocupados, hallazgos, aparte)
    _marcar_gpu(normalizado, texto, ocupados, hallazgos, aparte)
    _marcar_usos(normalizado, texto, hallazgos)
    _marcar_necesidades(normalizado, texto, hallazgos, aparte)
    avisos_monto = []
    _marcar_presupuesto(
        _enmascarar(normalizado, ocupados), texto, hallazgos, avisos_monto,
    )
    advertencias.extend(avisos_monto)
    if _ECONOMICO.search(normalizado):
        advertencias.append(
            '«Económico», «barato» o «gastar menos» no es un presupuesto. '
            'Indica el monto máximo en pesos.'
        )
    for marca in _MARCA.finditer(normalizado):
        aparte.append({
            'dato': marca.group(1).upper(),
            'motivo': (
                'La marca no elige un socket ni una tarjeta gráfica. '
                'El formulario usa AM4, AM5, LGA1200 o LGA1700.'
            ),
            'fragmento': texto[marca.start():marca.end()],
        })

    _asignar_tipos(normalizado, hallazgos)
    campos = _agrupar(hallazgos)
    _anotar_uso_sugerido(normalizado, hallazgos, campos, advertencias)
    contradicciones = _contradicciones(campos)
    for campo in campos:
        if campo['campo'] != 'presupuesto':
            continue
        if campo.get('candidatos'):
            aviso = _AVISO_RANGO
            if campo.get('aproximado'):
                aviso += ' Los montos son aproximados y no se ajustaron.'
            advertencias.append(aviso)
        elif campo.get('aproximado'):
            advertencias.append(_AVISO_APROXIMADO)
    if not campos and not aparte and not advertencias:
        advertencias.append(
            'No reconocí requisitos que el formulario pueda usar. '
            'Puedes indicar presupuesto, uso, RAM, almacenamiento, socket o tarjeta gráfica.'
        )
    elif (
        campos
        and not avisos_monto
        and not any(campo['campo'] == 'presupuesto' for campo in campos)
    ):
        advertencias.append(
            'No reconocí un presupuesto máximo. '
            'Escríbelo en el formulario antes de generar la recomendación.'
        )
    advertencias = list(dict.fromkeys(advertencias))
    vistos = set()
    unicos = []
    for item in aparte:
        firma = (item['dato'], item['motivo'])
        if firma in vistos:
            continue
        vistos.add(firma)
        unicos.append(item)
    aparte = unicos
    pendientes = _pendientes(campos, contradicciones)
    return {
        'campos': campos,
        'advertencias': advertencias,
        'contradicciones': contradicciones,
        'no_representable': aparte,
        'pendientes': pendientes,
        'requiere_confirmacion': bool(pendientes or contradicciones or any(
            campo['tipo'] == 'pendiente' or campo.get('candidatos') for campo in campos
        )),
        'reconocio_requisitos': bool(campos or aparte),
    }


def _normalizar(texto):
    return texto.replace('\u00a0', ' ').translate(_ACENTOS).lower()


def _fragmento(original, inicio, fin):
    return ' '.join(original[inicio:fin].split())


def _ocupa(ocupados, inicio, fin):
    return any(not (fin <= a or inicio >= b) for a, b in ocupados)


def _tomar(ocupados, inicio, fin):
    ocupados.append((inicio, fin))


def _enmascarar(texto, ocupados):
    chars = list(texto)
    for inicio, fin in ocupados:
        for indice in range(max(0, inicio), min(len(chars), fin)):
            chars[indice] = ' '
    return ''.join(chars)


def _clausulas(texto):
    limites = [0]
    for coincidencia in _SEPARADORES.finditer(texto):
        limites.append(coincidencia.start())
        limites.append(coincidencia.end())
    limites.append(len(texto))
    pares = []
    for inicio, fin in zip(limites[0::2], limites[1::2]):
        if texto[inicio:fin].strip():
            pares.append((inicio, fin))
    return pares or [(0, len(texto))]


def _marcadores(texto):
    ocupado = [False] * len(texto)
    encontrados = []
    for frase, tipo in sorted(_MARCADORES, key=lambda item: len(item[0]), reverse=True):
        for coincidencia in re.finditer(rf'\b{re.escape(frase)}\b', texto):
            if any(ocupado[coincidencia.start():coincidencia.end()]):
                continue
            for indice in range(coincidencia.start(), coincidencia.end()):
                ocupado[indice] = True
            encontrados.append({
                'inicio': coincidencia.start(),
                'fin': coincidencia.end(),
                'tipo': tipo,
            })
    return encontrados


def _asignar_tipos(texto, hallazgos):
    marcadores = _marcadores(texto)
    clausulas = _clausulas(texto)
    sensibles = [
        item for item in hallazgos
        if item.campo not in ('presupuesto', 'uso', 'resolucion')
    ]
    for hallazgo in hallazgos:
        if hallazgo.campo in ('presupuesto', 'uso', 'resolucion'):
            hallazgo.tipo = 'pendiente' if hallazgo.aproximado else 'detectado'
            continue
        elegido = _elegir_marcador(texto, hallazgo, marcadores, clausulas)
        if elegido and elegido['tipo'] == 'preferencia' and _hay_requisito_antes(elegido, hallazgo, sensibles):
            elegido = None
        if elegido is None:
            elegido = _preferencia_colgante(hallazgo, marcadores, clausulas, sensibles)
        if hallazgo.modo_inherente == 'obligatorio':
            hallazgo.tipo = 'preferencia' if elegido and elegido['tipo'] == 'preferencia' else 'obligatorio'
        elif elegido:
            hallazgo.tipo = elegido['tipo']
        else:
            hallazgo.tipo = 'pendiente'


def _elegir_marcador(texto, hallazgo, marcadores, clausulas):
    clausula = next(
        (par for par in clausulas if par[0] <= hallazgo.inicio < par[1]),
        (0, len(texto)),
    )
    previos = [
        marca for marca in marcadores
        if clausula[0] <= marca['inicio'] and marca['fin'] <= hallazgo.inicio
    ]
    siguientes = [
        marca for marca in marcadores
        if hallazgo.fin <= marca['inicio'] <= min(hallazgo.fin + 30, clausula[1])
    ]
    if previos:
        return max(previos, key=lambda marca: marca['inicio'])
    if siguientes:
        return min(siguientes, key=lambda marca: marca['inicio'])
    return None


def _hay_requisito_antes(marca, hallazgo, sensibles):
    return any(marca['fin'] <= otro.inicio < hallazgo.inicio for otro in sensibles)


def _preferencia_colgante(hallazgo, marcadores, clausulas, sensibles):
    indice = next(
        (posicion for posicion, par in enumerate(clausulas) if par[0] <= hallazgo.inicio < par[1]),
        None,
    )
    if indice is None or indice == 0:
        return None
    actual = clausulas[indice]
    if any(actual[0] <= otro.inicio < hallazgo.inicio for otro in sensibles):
        return None
    anterior = clausulas[indice - 1]
    if any(anterior[0] <= otro.inicio < anterior[1] for otro in sensibles):
        return None
    preferencias = [
        marca for marca in marcadores
        if anterior[0] <= marca['inicio'] < anterior[1] and marca['tipo'] == 'preferencia'
    ]
    if not preferencias:
        return None
    marca = max(preferencias, key=lambda item: item['inicio'])
    if _hay_requisito_antes(marca, hallazgo, sensibles):
        return None
    return marca


def _marcar_vram(texto, original, ocupados, aparte):
    for patron in _VRAM:
        for coincidencia in patron.finditer(texto):
            if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
                continue
            _tomar(ocupados, coincidencia.start(), coincidencia.end())
            numero = next(grupo for grupo in coincidencia.groups() if grupo)
            aparte.append({
                'dato': f'{numero} GB de la tarjeta gráfica',
                'motivo': (
                    'Esa cantidad es memoria de video, no RAM del computador. '
                    'El formulario no pide la VRAM.'
                ),
                'fragmento': _fragmento(original, coincidencia.start(), coincidencia.end()),
            })


def _marcar_resolucion(texto, original, ocupados, hallazgos):
    for coincidencia in _RESOLUCION.finditer(texto):
        if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
            continue
        _tomar(ocupados, coincidencia.start(), coincidencia.end())
        valor = '4k' if coincidencia.group(0).replace(' ', '') in ('2160p', '4k') else coincidencia.group(1) + 'p'
        hallazgos.append(_Hallazgo(
            'resolucion', valor, coincidencia.start(), coincidencia.end(),
            _fragmento(original, coincidencia.start(), coincidencia.end()),
        ))


def _marcar_ram(texto, original, ocupados, hallazgos, aparte):
    for patron in _RAM:
        for coincidencia in patron.finditer(texto):
            if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
                continue
            if re.search(r'memoria\s+de\s+video', coincidencia.group(0)):
                continue
            _tomar(ocupados, coincidencia.start(), coincidencia.end())
            fragmento = _fragmento(original, coincidencia.start(), coincidencia.end())
            for grupo in coincidencia.groups():
                if not grupo:
                    continue
                numero = int(grupo)
                if numero in _RAM_VALIDA:
                    hallazgos.append(_Hallazgo(
                        'ram_gb', numero, coincidencia.start(), coincidencia.end(), fragmento,
                    ))
                else:
                    aparte.append({
                        'dato': f'{numero} GB de RAM',
                        'motivo': 'El formulario solo admite 8, 16, 32 o 64 GB de RAM mínima.',
                        'fragmento': fragmento,
                    })


def _marcar_almacenamiento(texto, original, ocupados, hallazgos, aparte):
    def agregar_tipo(token, inicio, fin, inherente=None):
        if token in ('disco', 'disco duro', 'discos duros', 'almacenamiento'):
            return
        if token == 'nvme':
            aparte.append({
                'dato': 'NVMe',
                'motivo': (
                    'El formulario distingue SSD y HDD. '
                    'No asume que un SSD sea NVMe ni comprueba esa interfaz.'
                ),
                'fragmento': _fragmento(original, inicio, fin),
            })
            return
        hallazgos.append(_Hallazgo(
            'disco_tipo', token, inicio, fin,
            _fragmento(original, inicio, fin), inherente,
        ))

    def agregar_capacidad(numero, unidad, inicio, fin):
        cantidad = _a_gb(numero, unidad)
        fragmento = _fragmento(original, inicio, fin)
        if cantidad in _DISCO_VALIDO:
            hallazgos.append(_Hallazgo('disco_gb', cantidad, inicio, fin, fragmento))
            return
        if cantidad is None:
            return
        aparte.append({
            'dato': _etiqueta_capacidad(cantidad, unidad, numero),
            'motivo': 'El formulario solo admite 500 GB, 1 TB o 2 TB de capacidad mínima.',
            'fragmento': fragmento,
        })

    for coincidencia in _NEGAR_HDD.finditer(texto):
        if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
            continue
        _tomar(ocupados, coincidencia.start(), coincidencia.end())
        agregar_tipo('ssd', coincidencia.start(), coincidencia.end(), 'obligatorio')
    for coincidencia in _NEGAR_SSD.finditer(texto):
        if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
            continue
        _tomar(ocupados, coincidencia.start(), coincidencia.end())
        agregar_tipo('hdd', coincidencia.start(), coincidencia.end(), 'obligatorio')

    for patron in (_CAPACIDAD_Y_TIPO, _TIPO_Y_CAPACIDAD):
        for coincidencia in patron.finditer(texto):
            if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
                continue
            _tomar(ocupados, coincidencia.start(), coincidencia.end())
            if patron is _CAPACIDAD_Y_TIPO:
                numero, unidad, token = coincidencia.group(1), coincidencia.group(2), coincidencia.group(3)
            else:
                token, numero, unidad = coincidencia.group(1), coincidencia.group(2), coincidencia.group(3)
            token = ' '.join(token.split())
            if token != 'nvme' and 'nvme' in coincidencia.group(0):
                agregar_tipo('nvme', coincidencia.start(), coincidencia.end())
            agregar_tipo(token, coincidencia.start(), coincidencia.end())
            agregar_capacidad(numero, unidad, coincidencia.start(), coincidencia.end())
    for coincidencia in _SOLO_TB.finditer(texto):
        if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
            continue
        _tomar(ocupados, coincidencia.start(), coincidencia.end())
        agregar_capacidad(coincidencia.group(1), 'tb', coincidencia.start(), coincidencia.end())
    for coincidencia in re.finditer(r'\b(ssd|hdd)\b', texto):
        if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
            continue
        _tomar(ocupados, coincidencia.start(), coincidencia.end())
        agregar_tipo(coincidencia.group(1), coincidencia.start(), coincidencia.end())
    for coincidencia in re.finditer(r'\bnvme\b', texto):
        if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
            continue
        _tomar(ocupados, coincidencia.start(), coincidencia.end())
        agregar_tipo('nvme', coincidencia.start(), coincidencia.end())


def _marcar_gb_ambiguo(texto, original, ocupados, aparte):
    for coincidencia in re.finditer(r'\b(\d{1,4})\s*(?:gb|gigas?|gigabytes?)\b', texto):
        if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
            continue
        _tomar(ocupados, coincidencia.start(), coincidencia.end())
        aparte.append({
            'dato': f'{coincidencia.group(1)} GB',
            'motivo': (
                'No queda claro si es RAM, almacenamiento o memoria de video, '
                'así que no se aplicó.'
            ),
            'fragmento': _fragmento(original, coincidencia.start(), coincidencia.end()),
        })


def _marcar_sockets(texto, original, ocupados, hallazgos, aparte):
    for coincidencia in _SOCKET.finditer(texto):
        if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
            continue
        _tomar(ocupados, coincidencia.start(), coincidencia.end())
        token = re.sub(r'\s+', '', coincidencia.group(1)).upper()
        fragmento = _fragmento(original, coincidencia.start(), coincidencia.end())
        if token in _SOCKETS:
            hallazgos.append(_Hallazgo(
                'socket', token, coincidencia.start(), coincidencia.end(), fragmento,
            ))
        else:
            aparte.append({
                'dato': _SOCKETS_AJENOS.get(token, token),
                'motivo': 'Ese socket no está entre AM4, AM5, LGA1200 y LGA1700.',
                'fragmento': fragmento,
            })


def _marcar_gpu(texto, original, ocupados, hallazgos, aparte):
    for coincidencia in _SIN_GPU.finditer(texto):
        if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
            continue
        _tomar(ocupados, coincidencia.start(), coincidencia.end())
        hallazgos.append(_Hallazgo(
            'gpu', 'sin_dedicada', coincidencia.start(), coincidencia.end(),
            _fragmento(original, coincidencia.start(), coincidencia.end()),
            'obligatorio',
        ))
    enmascarado = _enmascarar(texto, ocupados)
    for coincidencia in _CON_GPU.finditer(enmascarado):
        if _ocupa(ocupados, coincidencia.start(), coincidencia.end()):
            continue
        _tomar(ocupados, coincidencia.start(), coincidencia.end())
        aparte.append({
            'dato': 'GPU dedicada',
            'motivo': (
                'El formulario puede dejar la tarjeta en Automática o pedir un equipo '
                'sin GPU dedicada. No tiene una opción para exigir una GPU dedicada.'
            ),
            'fragmento': _fragmento(original, coincidencia.start(), coincidencia.end()),
        })


def _marcar_necesidades(texto, original, hallazgos, aparte):
    hay_capacidad = any(item.campo == 'disco_gb' for item in hallazgos)
    for patron, dato, motivo in _NECESIDADES:
        for coincidencia in patron.finditer(texto):
            aparte.append({
                'dato': dato,
                'motivo': motivo,
                'fragmento': _fragmento(original, coincidencia.start(), coincidencia.end()),
            })
            break
    if hay_capacidad:
        return
    for coincidencia in re.finditer(r'\bmas\s+almacenamiento\b|\bmas\s+disco\b', texto):
        aparte.append({
            'dato': 'Almacenamiento',
            'motivo': (
                'Quieres más almacenamiento. Indica una capacidad mínima '
                'para que podamos considerarla.'
            ),
            'fragmento': _fragmento(original, coincidencia.start(), coincidencia.end()),
        })
        break


def _habla_de_dinero(texto, coincidencia):
    return _CONTEXTO_DINERO.search(_clausula_de(texto, coincidencia.start())) is not None


def _clausula_de(texto, posicion):
    for izquierda, derecha in _clausulas(texto):
        if izquierda <= posicion < derecha:
            return texto[izquierda:derecha]
    return texto


def _monto_palo(coincidencia):
    base = int(coincidencia.group('n') or 1)
    if coincidencia.group('medio'):
        return base * 1_000_000 + 500_000
    return base * 1_000_000


def _anotar_uso_sugerido(texto, hallazgos, campos, advertencias):
    sugerido = _sugerir_uso_principal(texto, hallazgos)
    if not sugerido:
        return
    campo = next((item for item in campos if item['campo'] == 'uso' and item.get('candidatos')), None)
    if not campo:
        return
    campo['sugerido'] = sugerido
    secundarios = []
    for candidato in campo['candidatos']:
        if candidato['valor'] == sugerido:
            candidato['etiqueta'] += ', sugerido'
            candidato['sugerido'] = True
        else:
            secundarios.append(candidato['valor'])
    advertencias.append(_aviso_uso_sugerido(sugerido, secundarios))


def _sugerir_uso_principal(texto, hallazgos):
    usos = [item for item in hallazgos if item.campo == 'uso']
    distintos = []
    for item in usos:
        if item.valor not in distintos:
            distintos.append(item.valor)
    if len(distintos) < 2:
        return None
    principales = []
    for coincidencia in _MOD_PRINCIPAL.finditer(texto):
        destino = _uso_siguiente(usos, coincidencia.end())
        if destino and destino.valor not in principales:
            principales.append(destino.valor)
    if len(principales) == 1:
        return principales[0]
    if len(principales) > 1:
        return None
    ocasionales = []
    for coincidencia in _MOD_OCASIONAL.finditer(texto):
        if any(coincidencia.start() < item.inicio for item in usos) and coincidencia.start() < min(item.inicio for item in usos):
            continue
        destino = _uso_mas_cercano(usos, coincidencia.start(), coincidencia.end())
        if destino and destino.valor not in ocasionales:
            ocasionales.append(destino.valor)
    if len(ocasionales) != 1:
        return None
    resto = [valor for valor in distintos if valor not in ocasionales]
    if len(resto) == 1:
        return resto[0]
    return None


def _uso_siguiente(usos, desde):
    posteriores = [item for item in usos if desde <= item.inicio <= desde + 40]
    if not posteriores:
        return None
    return min(posteriores, key=lambda item: item.inicio)


def _uso_mas_cercano(usos, inicio, fin):
    previo = None
    distancia_previo = None
    for item in usos:
        if item.fin <= inicio and inicio - item.fin <= 20:
            distancia = inicio - item.fin
            if distancia_previo is None or distancia < distancia_previo:
                previo = item
                distancia_previo = distancia
    posterior = None
    distancia_posterior = None
    for item in usos:
        if item.inicio >= fin and item.inicio - fin <= 35:
            distancia = item.inicio - fin
            if distancia_posterior is None or distancia < distancia_posterior:
                posterior = item
                distancia_posterior = distancia
    if previo and posterior:
        if distancia_previo < distancia_posterior:
            return previo
        if distancia_posterior < distancia_previo:
            return posterior
        return None
    return posterior or previo


def _aviso_uso_sugerido(principal, secundarios):
    nombre = _USO_ETIQUETA[principal]
    if len(secundarios) == 1:
        mencion = (
            f'{_USO_ETIQUETA[secundarios[0]]} queda como mención y no cambia los criterios.'
        )
    else:
        otros = ' y '.join(_USO_ETIQUETA[valor] for valor in secundarios)
        mencion = f'{otros} quedan como mención y no cambian los criterios.'
    return (
        f'La frase sugiere {nombre} como uso principal. No se aplicó todavía. '
        f'Si lo confirmas, la recomendación se optimizará principalmente para {nombre}. '
        f'{mencion}'
    )


def _marcar_usos(texto, original, hallazgos):
    ocupado = [False] * len(texto)
    for frase, uso in sorted(_FRASES_USO, key=lambda item: len(item[0]), reverse=True):
        for coincidencia in re.finditer(rf'\b{re.escape(frase)}\b', texto):
            if any(ocupado[coincidencia.start():coincidencia.end()]):
                continue
            for indice in range(coincidencia.start(), coincidencia.end()):
                ocupado[indice] = True
            hallazgos.append(_Hallazgo(
                'uso', uso, coincidencia.start(), coincidencia.end(),
                _fragmento(original, coincidencia.start(), coincidencia.end()),
            ))


def _marcar_presupuesto(texto, original, hallazgos, avisos):
    ocupados = []

    def libre(inicio, fin):
        return not any(not (fin <= a or inicio >= b) for a, b in ocupados)

    def anotar(inicio, fin, montos, aproximado):
        fragmento = _fragmento(original, inicio, fin)
        unicos = []
        for monto in montos:
            if isinstance(monto, float) and monto.is_integer():
                monto = int(monto)
            if not isinstance(monto, int) or monto < 1 or monto > 2_000_000_000:
                continue
            if monto not in unicos:
                unicos.append(monto)
        for monto in unicos:
            hallazgos.append(_Hallazgo(
                'presupuesto', monto, inicio, fin, fragmento, aproximado=aproximado,
            ))

    def registrar(coincidencia, montos):
        inicio, fin = coincidencia.start(), coincidencia.end()
        if not libre(inicio, fin):
            return
        ocupados.append((inicio, fin))
        decision = _clasificar_prefijo(_prefijo_hasta_cifra(texto, coincidencia))
        if decision == 'minimo':
            avisos.append(_AVISO_MINIMO)
            return
        if decision == 'negado':
            avisos.append(_AVISO_NEGADO)
            return
        despues = texto[fin:fin + 24]
        anotar(inicio, fin, montos, _es_aproximado(_prefijo_hasta_cifra(texto, coincidencia), despues))

    for coincidencia in _RANGO_PESOS.finditer(texto):
        registrar(coincidencia, [_numero(coincidencia.group(1)), _numero(coincidencia.group(2))])
    for coincidencia in _RANGO_UNIDAD.finditer(texto):
        unidad = coincidencia.group(2) or coincidencia.group(4)
        registrar(coincidencia, [
            _aplicar_unidad(coincidencia.group(1), unidad),
            _aplicar_unidad(coincidencia.group(3), coincidencia.group(4)),
        ])
    for coincidencia in _RANGO_DE_A.finditer(texto):
        unidad = coincidencia.group(3)
        registrar(coincidencia, [
            _aplicar_unidad(coincidencia.group(1), unidad),
            _aplicar_unidad(coincidencia.group(2), unidad),
        ])
    for coincidencia in _RANGO_K.finditer(texto):
        if coincidencia.group(0) == '4k' or '4k' in (coincidencia.group(1) + 'k', coincidencia.group(2) + 'k'):
            continue
        registrar(coincidencia, [
            int(coincidencia.group(1)) * 1000,
            int(coincidencia.group(2)) * 1000,
        ])
    for coincidencia in _PALO.finditer(texto):
        if not _habla_de_dinero(texto, coincidencia):
            continue
        registrar(coincidencia, [_monto_palo(coincidencia)])
    for coincidencia in _MEDIO_MILLON.finditer(texto):
        registrar(coincidencia, [500_000])

    patrones = (
        re.compile(r'(?<![\d.])(\d+)\s+lucas?\b'),
        re.compile(r'(?<![\d.])(\d+)\s+mil\b'),
        re.compile(r'\b(?:un|una)\s+millon(?:es)?(?:\s+de\s+pesos)?\b'),
        re.compile(r'\b(\d+(?:[.,]\d+)?)\s+millones?(?:\s+de\s+pesos)?\b'),
        re.compile(r'\$\s*(\d{1,3}(?:\.\d{3})+|\d{4,9})\b'),
        re.compile(r'\b(\d{1,3}(?:\.\d{3})+)\s*(?:pesos|clp)?\b'),
        re.compile(
            r'\b(?:presupuesto|maximo|hasta|tengo|no\s+mas\s+de)\b'
            r'(?:\s+[a-z]+){0,4}\s*\$?\s*(\d{5,9})\b'
        ),
        re.compile(r'(?<![\d.])(\d{5,9})\b'),
    )
    for patron in patrones:
        for coincidencia in patron.finditer(texto):
            monto = _monto_de(patron, coincidencia)
            registrar(coincidencia, [monto])
    for coincidencia in _MONTO_K.finditer(texto):
        if coincidencia.group(0) == '4k':
            continue
        registrar(coincidencia, [int(coincidencia.group(1)) * 1000])


def _prefijo_hasta_cifra(texto, coincidencia):
    inicio = 0
    for izquierda, derecha in _clausulas(texto):
        if izquierda <= coincidencia.start() < derecha:
            inicio = izquierda
            break
    digitos = re.search(r'\d', coincidencia.group(0))
    fin = coincidencia.start() + (digitos.start() if digitos else 0)
    return texto[inicio:fin]


def _limpiar_prefijo(prefijo):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z\s]+', ' ', prefijo)).strip()


def _clasificar_prefijo(prefijo):
    limpio = _limpiar_prefijo(prefijo)
    if _COMO_MINIMO.search(limpio):
        return 'minimo'
    if re.search(r'\bmas\s+de$', limpio):
        return 'techo'
    if _MONTO_NEGADO.search(limpio):
        return 'negado'
    return 'ok'


def _es_aproximado(prefijo, despues):
    limpio = _limpiar_prefijo(prefijo)
    if _TECHO_FINAL.search(limpio):
        return False
    if _APROX_FINAL.search(limpio):
        return True
    return _APROX_SIGUIENTE.search(despues) is not None


def _aplicar_unidad(numero, unidad):
    base = _numero(str(numero))
    if base is None:
        return None
    if unidad and (unidad.startswith('luca') or unidad == 'mil'):
        return int(round(float(base) * 1000))
    if unidad and unidad.startswith('millon'):
        return int(round(float(base) * 1_000_000))
    if isinstance(base, float) and base.is_integer():
        return int(base)
    return base if isinstance(base, int) else None


def _monto_de(patron, coincidencia):
    texto = coincidencia.group(0)
    if 'millon' in texto and coincidencia.lastindex is None:
        return 1_000_000
    numero = coincidencia.group(1) if coincidencia.lastindex else None
    if numero is None:
        return None
    if 'luca' in texto or re.search(r'\bmil\b', texto):
        base = _entero_simple(numero)
        return None if base is None else base * 1000
    if 'millon' in texto:
        base = _numero(numero)
        if base is None:
            return None
        return int(round(float(base) * 1_000_000))
    return _numero(numero)


def _numero(texto):
    limpio = texto.strip().replace(' ', '')
    if re.fullmatch(r'\d{1,3}(?:\.\d{3})+', limpio):
        return int(limpio.replace('.', ''))
    if re.fullmatch(r'\d+', limpio):
        return int(limpio)
    if re.fullmatch(r'\d+[.,]\d+', limpio):
        return float(limpio.replace(',', '.'))
    return None


def _entero_simple(texto):
    if re.fullmatch(r'\d+', texto):
        return int(texto)
    return None


def _a_gb(numero, unidad):
    valor = _numero(numero)
    if valor is None:
        return None
    if unidad == 'tb':
        return int(round(float(valor) * 1000))
    if isinstance(valor, float):
        return None
    return int(valor)


def _etiqueta_capacidad(cantidad, unidad, numero):
    if unidad == 'tb':
        return f'{numero} TB'
    return f'{cantidad} GB'


def _etiqueta_valor(campo, valor):
    if campo == 'presupuesto':
        return '$' + f'{int(valor):,}'.replace(',', '.')
    if campo == 'uso':
        return _USO_ETIQUETA.get(valor, str(valor))
    if campo == 'resolucion':
        return '4K' if valor == '4k' else str(valor)
    if campo == 'ram_gb':
        return f'{valor} GB'
    if campo == 'disco_tipo':
        return str(valor).upper()
    if campo == 'disco_gb':
        if valor == 1000:
            return '1 TB'
        if valor == 2000:
            return '2 TB'
        return f'{valor} GB'
    if campo == 'gpu':
        return 'Sin GPU dedicada' if valor == 'sin_dedicada' else 'Automática'
    return str(valor)


def _agrupar(hallazgos):
    por_campo = {}
    for hallazgo in hallazgos:
        por_campo.setdefault(hallazgo.campo, []).append(hallazgo)
    campos = []
    for nombre in _ORDEN:
        grupo = por_campo.get(nombre) or []
        if not grupo:
            continue
        valores = []
        for hallazgo in grupo:
            if hallazgo.valor not in valores:
                valores.append(hallazgo.valor)
        fragmentos = []
        for hallazgo in grupo:
            if hallazgo.fragmento and hallazgo.fragmento not in fragmentos:
                fragmentos.append(hallazgo.fragmento)
        tipos = {hallazgo.tipo for hallazgo in grupo}
        aproximado = any(item.aproximado for item in grupo)
        if len(valores) == 1:
            tipo = grupo[0].tipo if len(tipos) == 1 else 'pendiente'
            campo = _campo(nombre, valores[0], tipo, fragmentos)
            if aproximado:
                campo['aproximado'] = True
                campo['tipo'] = 'pendiente'
                campo['tipo_etiqueta'] = _TIPO_ETIQUETA['pendiente']
                if campo['valor_etiqueta']:
                    campo['valor_etiqueta'] += ', aproximado'
            campos.append(campo)
            continue
        candidatos = []
        for valor in valores:
            tipo_valor = next(item.tipo for item in grupo if item.valor == valor)
            etiqueta = _etiqueta_valor(nombre, valor)
            if nombre == 'presupuesto':
                etiqueta += ' como máximo'
            candidatos.append({
                'valor': valor,
                'etiqueta': etiqueta,
                'tipo': tipo_valor,
            })
        campo = _campo(nombre, None, 'pendiente', fragmentos)
        campo['candidatos'] = candidatos
        campo['aproximado'] = aproximado
        campos.append(campo)
    return campos


def _campo(nombre, valor, tipo, fragmentos):
    return {
        'campo': nombre,
        'etiqueta': _ETIQUETA_CAMPO[nombre],
        'valor': valor,
        'valor_etiqueta': None if valor is None else _etiqueta_valor(nombre, valor),
        'tipo': tipo,
        'tipo_etiqueta': _TIPO_ETIQUETA[tipo],
        'fragmento': ' · '.join(fragmentos),
        'bloqueado': False,
        'aproximado': False,
    }


def _tipo_candidato(campo, valor):
    for candidato in campo.get('candidatos') or []:
        if candidato['valor'] == valor:
            return candidato['tipo']
    return campo['tipo']


def _contradicciones(campos):
    por_nombre = {campo['campo']: campo for campo in campos}
    resultado = []
    gpu = por_nombre.get('gpu')
    uso = por_nombre.get('uso')
    if gpu and gpu.get('valor') == 'sin_dedicada' and uso:
        usos = [uso['valor']] if uso.get('valor') else [
            candidato['valor'] for candidato in uso.get('candidatos') or []
        ]
        conflictivos = [item for item in usos if item in ('gaming', 'edicion')]
        if conflictivos:
            gpu['bloqueado'] = True
            uso['bloqueado'] = True
            resultado.append(_contradiccion_sin_gpu(conflictivos, usos, gpu['tipo']))
    disco = por_nombre.get('disco_tipo')
    if disco and disco.get('candidatos'):
        valores = {candidato['valor'] for candidato in disco['candidatos']}
        if valores == {'ssd', 'hdd'}:
            disco['bloqueado'] = True
            resultado.append({
                'mensaje': (
                    'La solicitud menciona SSD y HDD. '
                    'El formulario admite un solo tipo de almacenamiento.'
                ),
                'campos': ['disco_tipo'],
                'alternativas': [
                    _alternativa(
                        'solo-ssd', 'Usar SSD', 'disco_tipo', 'ssd',
                        _tipo_candidato(disco, 'ssd'),
                    ),
                    _alternativa(
                        'solo-hdd', 'Usar HDD', 'disco_tipo', 'hdd',
                        _tipo_candidato(disco, 'hdd'),
                    ),
                ],
            })
    return resultado


def _contradiccion_sin_gpu(conflictivos, usos, modo_gpu):
    mensajes = []
    for uso in conflictivos:
        mensaje = Preferencias(gpu='sin_dedicada').rechazo_de_uso(uso)
        if mensaje and mensaje not in mensajes:
            mensajes.append(mensaje)
    modo = modo_gpu if modo_gpu in ('obligatorio', 'preferencia') else 'obligatorio'
    alternativas = []
    for uso in conflictivos:
        alternativas.append(_alternativa(
            f'mantener-{uso}',
            f'Mantener {_USO_ETIQUETA[uso]} y dejar la tarjeta gráfica en Automática',
            'uso', uso, 'detectado',
            extra=('gpu', 'automatica', 'detectado'),
        ))
    for uso in usos:
        if uso in ('trabajo', 'general'):
            alternativas.append(_alternativa(
                f'{uso}-sin-gpu',
                f'Mantener {_USO_ETIQUETA[uso]} y el equipo sin GPU dedicada',
                'uso', uso, 'detectado',
                extra=('gpu', 'sin_dedicada', modo),
            ))
    if 'trabajo' not in usos:
        alternativas.append(_alternativa(
            'trabajo-sin-gpu',
            'Cambiar el uso a Trabajo y mantener el equipo sin GPU dedicada',
            'uso', 'trabajo', 'detectado',
            extra=('gpu', 'sin_dedicada', modo),
        ))
    if 'general' not in usos:
        alternativas.append(_alternativa(
            'general-sin-gpu',
            'Cambiar el uso a General y mantener el equipo sin GPU dedicada',
            'uso', 'general', 'detectado',
            extra=('gpu', 'sin_dedicada', modo),
        ))
    return {
        'mensaje': ' '.join(mensajes) + ' Elige una alternativa válida antes de aplicar.',
        'campos': ['uso', 'gpu'],
        'alternativas': alternativas,
    }


def _alternativa(identificador, etiqueta, campo, valor, tipo, extra=None):
    cambios = [_cambio(campo, valor, tipo)]
    if extra:
        cambios.append(_cambio(*extra))
    return {'id': identificador, 'etiqueta': etiqueta, 'campos': cambios}


def _cambio(campo, valor, tipo):
    return {
        'campo': campo,
        'etiqueta': _ETIQUETA_CAMPO[campo],
        'valor': valor,
        'valor_etiqueta': _etiqueta_valor(campo, valor),
        'tipo': tipo,
        'tipo_etiqueta': _TIPO_ETIQUETA.get(tipo, _TIPO_ETIQUETA['detectado']),
    }


_MENSAJE_VALOR = {
    'presupuesto': 'Hay más de un presupuesto. Elige el máximo que quieres usar antes de aplicar.',
    'uso': 'Hay más de un uso. Elige el principal antes de aplicar.',
    'resolucion': 'Hay más de una resolución. Elige una antes de aplicar.',
    'ram_gb': 'Hay más de una cantidad de RAM. Elige una antes de aplicar.',
    'disco_tipo': 'Hay más de un tipo de almacenamiento. Elige uno antes de aplicar.',
    'disco_gb': 'Hay más de una capacidad. Elige una antes de aplicar.',
    'socket': 'Hay más de una plataforma. Elige una antes de aplicar.',
    'gpu': 'Hay más de una opción de tarjeta gráfica. Elige una antes de aplicar.',
}
_MENSAJE_MODO = {
    'ram_gb': 'Confirma si la RAM mínima es obligatoria o una preferencia.',
    'disco_tipo': 'Confirma si el tipo de almacenamiento es obligatorio o una preferencia.',
    'disco_gb': 'Confirma si la capacidad mínima es obligatoria o una preferencia.',
    'socket': 'Confirma si la plataforma es obligatoria o una preferencia.',
    'gpu': 'Confirma si el equipo sin GPU dedicada es obligatorio o una preferencia.',
}


def _pendientes(campos, contradicciones):
    textos = []
    if contradicciones:
        textos.append('Hay una contradicción. Elige una alternativa antes de aplicar.')
    for campo in campos:
        if campo.get('bloqueado'):
            continue
        if campo.get('candidatos'):
            textos.append(_MENSAJE_VALOR[campo['campo']])
            if any(candidato['tipo'] == 'pendiente' for candidato in campo['candidatos']):
                texto = _MENSAJE_MODO.get(campo['campo'])
                if texto:
                    textos.append(texto)
        elif campo.get('aproximado'):
            textos.append(_AVISO_APROXIMADO)
        elif campo['tipo'] == 'pendiente':
            textos.append(_MENSAJE_MODO.get(
                campo['campo'],
                f'Confirma cómo aplicar {campo["etiqueta"]}.',
            ))
    return textos
