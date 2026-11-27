"""Prepara PF-01 a PF-06 y se niega a cargar producción.

Sin --ejecutar no abre conexiones HTTP.
--ejecutar además exige HWH_STAGING_URL fuera de los hosts públicos
y, para PF-03, HWH_PF_LIMITE_AUTORIZADO=SI junto con HWH_PF_USUARIOS_MAX.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

PROD = {
    'proyecto-hardwarehouse-production.up.railway.app',
    'hardwarehouse.cl',
    'www.hardwarehouse.cl',
}
LOCUSTFILE = 'scripts/locustfile_hwh.py'
DURACION = '45s'
ESPERA = 'entre 6 y 10 s por usuario'


def host_de(url):
    return (urlsplit(url).hostname or '').lower()


def es_produccion(url):
    return host_de(url) in PROD


def staging_configurado():
    url = os.getenv('HWH_STAGING_URL', '').strip()
    if not url:
        return None, 'HWH_STAGING_URL no está definida.'
    partes = urlsplit(url)
    if partes.scheme not in {'http', 'https'} or not partes.hostname:
        return None, 'HWH_STAGING_URL no es una URL http(s).'
    if es_produccion(url):
        return None, f'{partes.hostname} es un host de producción. La carga no se inicia.'
    return url, ''


def limite_de_estres():
    if os.getenv('HWH_PF_LIMITE_AUTORIZADO') != 'SI':
        return None, 'No hay un límite de estrés autorizado (HWH_PF_LIMITE_AUTORIZADO=SI).'
    texto = os.getenv('HWH_PF_USUARIOS_MAX', '').strip()
    if not texto.isdigit() or int(texto) < 1 or int(texto) > 25:
        return None, 'HWH_PF_USUARIOS_MAX debe ser un entero entre 1 y 25.'
    return int(texto), ''


def comando(host, usuarios, modo='base', ruta=''):
    env = f'HWH_PF_MODO={modo}'
    if ruta:
        env += f' HWH_PF_RUTA={ruta}'
    return (
        f'{env} locust -f {LOCUSTFILE} --headless --host {host} '
        f'--users {usuarios} --spawn-rate 1 --run-time {DURACION} '
        f'--html evidencias/rendimiento/PF-XX/reporte.html --csv evidencias/rendimiento/PF-XX/locust'
    )


def plan(host='https://STAGING_PENDIENTE'):
    lineas = [
        'Plan preparado. Ninguna de estas líneas se ejecutó en esta corrida.',
        f'Espera entre solicitudes: {ESPERA}. Duración por etapa: {DURACION}.',
        'Parada: el proceso termina al cumplir --run-time. La etapa siguiente no arranca si el CSV previo supera 5 % de errores o si existe el archivo evidencias/rendimiento/DETENER.',
        'PF-03 no arranca sin límite autorizado. El máximo aceptado por el script es 25 usuarios.',
        '',
        'PF-01, un usuario, una ruta por ejecución:',
    ]
    for ruta, _nombre in [
        ('/', 'inicio'),
        ('/tienda/', 'tienda'),
        ('/armado/', 'armado'),
        ('/contacto/', 'contacto'),
    ]:
        lineas.append(comando(host, 1, 'base', ruta))
    lineas.append('')
    lineas.append('PF-02, la misma mezcla de cuatro GET:')
    for usuarios in (1, 5, 10):
        lineas.append(comando(host, usuarios))
    lineas.append('')
    lineas.append('PF-03, solo tras PF-01, PF-02 y el límite autorizado. Incrementos de 5 hasta el máximo, sin superar 25.')
    lineas.append('PF-04, un usuario y 45 s después de detener PF-03, comparado con PF-01.')
    lineas.append('PF-05: HWH_PF_MODO=filtros, un usuario, 45 s. El proveedor exige HWH_PF_PROVEEDOR_ID numérico de staging.')
    lineas.append(comando(host, 1, 'filtros'))
    lineas.append('PF-06: repetir PF-01 sobre dos SHA con el mismo host, duración y datos. Sin CSV previo queda bloqueada.')
    return '\n'.join(lineas)


def _errores_sostenidos(csv_path):
    import csv
    if not csv_path.exists():
        print(f'No apareció {csv_path}. La etapa siguiente no continúa.')
        return True
    with csv_path.open(newline='', encoding='utf-8') as archivo:
        filas = list(csv.DictReader(archivo))
    for fila in filas:
        if fila.get('Name') != 'Aggregated':
            continue
        total = int(fila.get('Request Count') or 0)
        fallos = int(fila.get('Failure Count') or 0)
        return total > 0 and (fallos / total) > 0.05
    return False


def _locust(host, usuarios, destino, modo='base', ruta='', etiqueta=''):
    if es_produccion(host):
        raise RuntimeError('Destino de producción rechazado.')
    if os.path.exists('evidencias/rendimiento/DETENER'):
        print('Detención pedida: existe evidencias/rendimiento/DETENER.')
        return 3
    marca = etiqueta or str(usuarios)
    entorno = os.environ.copy()
    entorno['HWH_PF_MODO'] = modo
    entorno['HWH_CARGA_PRODUCCION_AUTORIZADA'] = ''
    if ruta:
        entorno['HWH_PF_RUTA'] = ruta
        marca = etiqueta or ruta.strip('/').replace('/', '_') or 'inicio'
    else:
        entorno.pop('HWH_PF_RUTA', None)
    comando_locust = [
        'locust', '-f', LOCUSTFILE, '--headless', '--host', host,
        '--users', str(usuarios), '--spawn-rate', '1', '--run-time', DURACION,
        '--html', str(destino / f'reporte_{marca}.html'),
        '--csv', str(destino / f'locust_{marca}'),
        '--only-summary',
    ]
    print(' '.join(comando_locust))
    codigo = subprocess.call(comando_locust, env=entorno)
    if codigo != 0:
        return codigo
    if _errores_sostenidos(destino / f'locust_{marca}_stats.csv'):
        print('Detención: la etapa superó 5 % de errores. No se aumenta la carga.')
        return 3
    return 0


def ejecutar(caso):
    url, motivo = staging_configurado()
    if not url:
        print(motivo)
        return 2
    if caso == 'PF-03':
        _maximo, motivo_limite = limite_de_estres()
        if motivo_limite:
            print(motivo_limite)
            return 2
    if caso == 'PF-04' and not list(Path('evidencias/rendimiento/PF-03').glob('locust_*_stats.csv')):
        print('PF-04 permanece bloqueada: no existe el CSV de PF-03.')
        return 2
    if caso == 'PF-06':
        print('PF-06 permanece bloqueada: no hay dos CSV de la misma carga en releases distintos.')
        return 2
    if shutil.which('locust') is None:
        print('Locust no está instalado. No se envían solicitudes.')
        return 2
    carpeta = Path('evidencias') / 'rendimiento' / caso
    carpeta.mkdir(parents=True, exist_ok=True)
    if caso == 'PF-01':
        codigos = []
        for ruta in ('/', '/tienda/', '/armado/', '/contacto/'):
            codigos.append(_locust(url, 1, carpeta, 'base', ruta))
            if codigos[-1] != 0:
                return codigos[-1]
        return 0
    if caso == 'PF-05':
        return _locust(url, 1, carpeta, 'filtros')
    if caso == 'PF-02':
        for usuarios in (1, 5, 10):
            codigo = _locust(url, usuarios, carpeta, 'base')
            if codigo != 0:
                return codigo
        return 0
    if caso == 'PF-03':
        maximo, _motivo = limite_de_estres()
        for usuarios in range(5, maximo + 1, 5):
            codigo = _locust(url, usuarios, carpeta, 'base')
            if codigo != 0:
                return codigo
        return 0
    return _locust(url, 1, carpeta, 'base')


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ejecutar', choices=['PF-01', 'PF-02', 'PF-03', 'PF-04', 'PF-05', 'PF-06'])
    args = parser.parse_args(argv)
    if args.ejecutar:
        return ejecutar(args.ejecutar)
    url, motivo = staging_configurado()
    print('Comprobación PF sin tráfico HTTP.')
    print(motivo or f'Staging candidato: {host_de(url)}')
    print(f'Locust instalado: {"sí" if shutil.which("locust") else "no"}.')
    print(plan(url or 'https://STAGING_PENDIENTE'))
    if not url:
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
