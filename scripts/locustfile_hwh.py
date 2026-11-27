"""Carga SOLO LECTURA de HardWareHouse. Solo contra un staging autorizado.

No accede a carrito, pagos, envío de correos, administración ni APIs generativas.
Las URLs de producción se rechazan salvo HWH_CARGA_PRODUCCION_AUTORIZADA=SI.

HWH_PF_MODO=base    endpoints de PF-01.
HWH_PF_MODO=filtros URLs reales de la tienda para PF-05.
HWH_PF_RUTA         si está definida, solo se pide esa ruta.
HWH_PF_PROVEEDOR_ID identificador numérico de un proveedor de staging.
"""
import os
from urllib.parse import urlsplit

from locust import HttpUser, between, task

PROD = {
    'proyecto-hardwarehouse-production.up.railway.app',
    'hardwarehouse.cl',
    'www.hardwarehouse.cl',
}
MODO = os.getenv('HWH_PF_MODO', 'base').strip() or 'base'
RUTA_UNICA = os.getenv('HWH_PF_RUTA', '').strip()
PROVEEDOR = os.getenv('HWH_PF_PROVEEDOR_ID', '').strip()

RUTAS_BASE = [
    ('/', 'GET /'),
    ('/tienda/', 'GET /tienda/'),
    ('/armado/', 'GET /armado/'),
    ('/contacto/', 'GET /contacto/'),
]
RUTAS_CATALOGO = [
    ('/tienda/', 'A sin filtros'),
    ('/tienda/?q=procesador', 'B busqueda'),
    ('/tienda/?categoria=CPU', 'C categoria'),
    ('/tienda/?categoria=CPU&precio=50-100&orden=precio_asc', 'E combinados'),
    ('/tienda/?page=1', 'F pagina 1'),
    ('/tienda/?page=2', 'G pagina 2'),
]
if PROVEEDOR.isdigit():
    RUTAS_CATALOGO.insert(3, (f'/tienda/?proveedor={PROVEEDOR}', 'D proveedor'))


def _bloquear_produccion(host):
    hostname = urlsplit(host or '').hostname
    if hostname in PROD and os.getenv('HWH_CARGA_PRODUCCION_AUTORIZADA') != 'SI':
        raise RuntimeError(
            'Producción bloqueada. Usa un staging aislado. '
            'HWH_CARGA_PRODUCCION_AUTORIZADA=SI solo con autorización explícita.'
        )


def _rutas(plan):
    activas = [item for item in plan if not RUTA_UNICA or item[0] == RUTA_UNICA]
    if not activas:
        raise RuntimeError(f'HWH_PF_RUTA no pertenece a este escenario: {RUTA_UNICA}')
    return activas


class _Base(HttpUser):
    abstract = True
    wait_time = between(6, 10)

    def on_start(self):
        _bloquear_produccion(self.host)
        self._pf_indice = 0

    def _leer(self, plan):
        rutas = _rutas(plan)
        ruta, nombre = rutas[self._pf_indice % len(rutas)]
        self._pf_indice += 1
        with self.client.get(ruta, name=nombre, catch_response=True, timeout=12) as respuesta:
            if respuesta.status_code >= 500:
                respuesta.failure(f'Error {respuesta.status_code} en {nombre}')


class HWReadOnlyUser(_Base):
    """PF-01 a PF-04. Reparte las cuatro rutas o se queda en la indicada."""

    abstract = MODO == 'filtros'

    @task
    def leer(self):
        self._leer(RUTAS_BASE)


class HWCatalogoUser(_Base):
    """PF-05. Parámetros reales de la tienda. Sin escritura."""

    abstract = MODO != 'filtros'

    @task
    def leer(self):
        self._leer(RUTAS_CATALOGO)
