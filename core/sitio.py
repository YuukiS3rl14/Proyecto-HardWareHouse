"""Normaliza la URL pública usada por PayPal y los enlaces absolutos."""
from urllib.parse import urlsplit, urlunsplit

HOST_APEX = 'hardwarehouse.cl'
HOST_WWW = 'www.hardwarehouse.cl'
HOST_RAILWAY = 'proyecto-hardwarehouse-production.up.railway.app'
HOSTS_LOCALES = {'127.0.0.1', 'localhost', 'testserver', '::1'}


def sitio_publico(valor):
    """Devuelve esquema y host, sin ruta ni barra final.

    Un SITE_URL con ruta convertiría return y notify_url en direcciones
    que PayPal no puede alcanzar. El vértice público usa HTTPS.
    """
    texto = (valor or '').strip()
    if not texto:
        return 'http://127.0.0.1:8000'
    if '://' not in texto:
        texto = 'https://' + texto.lstrip('/')
    partes = urlsplit(texto)
    host = (partes.hostname or '').lower()
    if not host:
        return 'http://127.0.0.1:8000'
    esquema = (partes.scheme or 'https').lower()
    if host == HOST_APEX and esquema != 'https':
        esquema = 'https'
    if partes.port and partes.port not in (80, 443):
        netloc = f'{host}:{partes.port}'
    else:
        netloc = host
    return urlunsplit((esquema, netloc, '', '', ''))


def alias_de_navegador(host_railway=''):
    """Hosts que el navegador puede abrir y que deben volver al sitio canónico."""
    alias = {HOST_WWW, HOST_RAILWAY}
    extra = (host_railway or '').split(':')[0].strip().lower()
    if extra and extra not in HOSTS_LOCALES:
        alias.add(extra)
    return alias
