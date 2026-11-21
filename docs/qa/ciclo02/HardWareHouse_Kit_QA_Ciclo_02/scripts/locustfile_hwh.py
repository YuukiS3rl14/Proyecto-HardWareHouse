"""Carga SOLO LECTURA de HardWareHouse. Recomendado ejecutar en staging.

Requisitos: pip install locust
No accede a carrito, pagos, envío de correos, administración ni APIs generativas.
Seguridad: las URLs de producción exigen opt-in expreso por variable de entorno.
"""
import os
from urllib.parse import urlsplit
from locust import HttpUser, between, task

PROD = {'proyecto-hardwarehouse-production.up.railway.app','hardwarehouse.cl','www.hardwarehouse.cl'}

class HWReadOnlyUser(HttpUser):
    wait_time = between(6, 10)

    def on_start(self):
        hostname = urlsplit(self.host).hostname
        if hostname in PROD and os.getenv('HWH_CARGA_PRODUCCION_AUTORIZADA') != 'SI':
            raise RuntimeError('Producción bloqueada: usar staging. Si existe autorización explícita, definir HWH_CARGA_PRODUCCION_AUTORIZADA=SI.')

    @task(3)
    def home(self):
        with self.client.get('/', name='GET /', catch_response=True, timeout=12) as r:
            if r.status_code >= 500:
                r.failure('Error 5xx en inicio')

    @task(3)
    def tienda(self):
        with self.client.get('/tienda/', name='GET /tienda/', catch_response=True, timeout=12) as r:
            if r.status_code >= 500:
                r.failure('Error 5xx en tienda')

    @task(2)
    def armado(self):
        with self.client.get('/armado/', name='GET /armado/', catch_response=True, timeout=12) as r:
            if r.status_code >= 500:
                r.failure('Error 5xx en armado')

    @task(1)
    def contacto(self):
        with self.client.get('/contacto/', name='GET /contacto/', catch_response=True, timeout=12) as r:
            if r.status_code >= 500:
                r.failure('Error 5xx en contacto')
