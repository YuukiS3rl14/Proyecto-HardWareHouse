"""Redirige el navegador al dominio canónico sin tocar el POST de PayPal."""
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.http import HttpResponsePermanentRedirect

from core.sitio import HOSTS_LOCALES, alias_de_navegador


class DominioCanonicoMiddleware:
    """Lleva GET y HEAD al host de SITE_URL.

    PayPal entrega el IPN con POST. Una redirección convertiría ese POST
    en GET y PayPal perdería el cuerpo de la notificación.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ('GET', 'HEAD'):
            destino = self.destino(request)
            if destino:
                return HttpResponsePermanentRedirect(destino)
        return self.get_response(request)

    def destino(self, request):
        canonico = urlsplit(settings.SITE_URL)
        host_canonico = (canonico.hostname or '').lower()
        if canonico.scheme != 'https' or host_canonico in HOSTS_LOCALES:
            return None
        try:
            host = request.get_host().split(':')[0].lower()
        except DisallowedHost:
            return None
        if host == host_canonico or host in HOSTS_LOCALES:
            return None
        alias = alias_de_navegador(getattr(settings, 'RAILWAY_PUBLIC_DOMAIN', ''))
        if host not in alias:
            return None
        return settings.SITE_URL + request.get_full_path()
