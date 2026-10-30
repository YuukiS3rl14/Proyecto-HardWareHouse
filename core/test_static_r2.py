import os
import subprocess
import sys

from django.test import SimpleTestCase

from HardWareHouse.settings import middleware_estaticos

BASE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
]
WHITENOISE = 'whitenoise.middleware.WhiteNoiseMiddleware'


class MiddlewareEstaticosTests(SimpleTestCase):
    def test_sin_r2_white_noise_queda_despues_de_seguridad(self):
        cadena = middleware_estaticos(BASE, False)

        self.assertEqual(cadena[0], BASE[0])
        self.assertEqual(cadena[1], WHITENOISE)
        self.assertEqual(cadena[2:], BASE[1:])

    def test_con_r2_no_hay_white_noise(self):
        con_white_noise = [BASE[0], WHITENOISE, *BASE[1:]]

        cadena = middleware_estaticos(con_white_noise, True)

        self.assertNotIn(WHITENOISE, cadena)
        self.assertEqual(cadena, BASE)

    def test_el_proceso_de_django_arma_las_dos_configuraciones(self):
        falso = _proceso('False')
        verdadero = _proceso('True')

        self.assertIn('whitenoise=yes', falso)
        self.assertIn('backend=whitenoise.storage.CompressedStaticFilesStorage', falso)
        self.assertIn('static_url=/static/', falso)
        self.assertIn('static_root=staticfiles', falso)

        self.assertIn('whitenoise=no', verdadero)
        self.assertIn('backend=storages.backends.s3.S3Storage', verdadero)
        self.assertIn('location=static', verdadero)
        self.assertIn('static_root=staticfiles', verdadero)
        self.assertIn('static_url=https-cdn', verdadero)
        self.assertIn('directory_warnings=0', verdadero)
        self.assertIn('check=0', falso)
        self.assertIn('check=0', verdadero)


def _proceso(usar_r2):
    env = os.environ.copy()
    env['USE_R2'] = usar_r2
    env['OLLAMA_BASE_URL'] = ''
    env['HARDWAREHOUSE_CHAT_INTENT_LLM'] = 'False'
    if usar_r2 == 'True':
        env['R2_BUCKET_NAME'] = 'audit-bucket'
        env['R2_ENDPOINT_URL'] = 'https://example.r2.cloudflarestorage.com'
        env['R2_ACCESS_KEY_ID'] = 'audit-access-key'
        env['R2_SECRET_ACCESS_KEY'] = 'audit-secret-key'
        env['R2_PUBLIC_DOMAIN'] = 'cdn.example.com'
    comando = [
        sys.executable,
        '-c',
        (
            'import warnings\n'
            'warnings.simplefilter("always")\n'
            'from django.core.management import execute_from_command_line\n'
            'from django.conf import settings\n'
            'with warnings.catch_warnings(record=True) as caught:\n'
            '    warnings.simplefilter("always")\n'
            '    execute_from_command_line(["manage.py", "check"])\n'
            '    from django.core.wsgi import get_wsgi_application\n'
            '    get_wsgi_application()\n'
            'aviso = sum("No directory at" in str(item.message) for item in caught)\n'
            'white = "whitenoise.middleware.WhiteNoiseMiddleware" in settings.MIDDLEWARE\n'
            'backend = settings.STORAGES["staticfiles"]["BACKEND"]\n'
            'location = settings.STORAGES["staticfiles"].get("OPTIONS", {}).get("location", "")\n'
            'url = settings.STATIC_URL\n'
            'marca = "https-cdn" if url.startswith("https://") and url.endswith("/static/") else url\n'
            'raiz = getattr(settings.STATIC_ROOT, "name", "")\n'
            'print(f"whitenoise={\'yes\' if white else \'no\'}")\n'
            'print(f"backend={backend}")\n'
            'print(f"location={location}")\n'
            'print(f"static_url={marca}")\n'
            'print(f"static_root={raiz}")\n'
            'print(f"directory_warnings={aviso}")\n'
            'print("check=0")\n'
        ),
    ]
    resultado = subprocess.run(
        comando,
        cwd=str(settings_base()),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    self_output = (resultado.stdout or '') + (resultado.stderr or '')
    if resultado.returncode != 0:
        raise AssertionError(self_output[-2000:])
    return self_output


def settings_base():
    from pathlib import Path

    return Path(__file__).resolve().parents[1]
