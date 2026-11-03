#!/usr/bin/env python
"""Prueba local de la integración Django + Ollama Cloud.

Ejecútala en la misma sesión de PowerShell donde ya están las variables de
Ollama. Hace como máximo tres llamadas reales, sin reintentos.

No imprime la clave y no deja escrituras en la base de datos.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LIMITE_LLAMADAS = 3
_HOSTS_LOCALES = frozenset({"127.0.0.1", "localhost", "::1"})
_PRESUPUESTO = None

CASOS = (
    {"id": "saludo", "mensaje": "Hola"},
    {"id": "producto", "mensaje": "busco un procesador disponible"},
    {"id": "armado", "mensaje": "armame un PC gamer con presupuesto 700000"},
    {
        "id": "ambiguo",
        "mensaje": "quizá algo intermedio para jugar, pero no tengo claro por dónde partir",
    },
)


class _Presupuesto:
    def __init__(self) -> None:
        self.llamadas: list[dict] = []

    def instalar(self, clave: str) -> None:
        import core.chatbot.llm.ollama as ollama_mod

        if ollama_mod.requests is None:
            raise RuntimeError("El paquete requests no está disponible.")
        sesion = ollama_mod.requests
        real_post = sesion.post
        real_get = sesion.get
        presupuesto = self

        def _registrar(metodo, url, args, kwargs):
            if len(presupuesto.llamadas) >= LIMITE_LLAMADAS:
                raise sesion.RequestException("limite de llamadas")
            enviado = kwargs.get("json") if isinstance(kwargs.get("json"), dict) else {}
            mensajes = enviado.get("messages") or []
            texto = "\n".join(
                str(item.get("content") or "")
                for item in mensajes
                if isinstance(item, dict)
            )
            sensible = ("@" in texto) or ("pedido #" in texto.lower()) or bool(clave and clave in texto)
            inicio = time.perf_counter()
            registro = {
                "segundos": 0.0,
                "status": None,
                "error": None,
                "contenido": None,
                "sensible": sensible,
                "modelo": enviado.get("model") or "-",
            }
            try:
                respuesta = metodo(url, *args, **kwargs)
            except Exception as exc:
                registro["segundos"] = time.perf_counter() - inicio
                registro["error"] = type(exc).__name__
                presupuesto.llamadas.append(registro)
                raise
            registro["segundos"] = time.perf_counter() - inicio
            registro["status"] = respuesta.status_code
            try:
                data = respuesta.json()
            except ValueError:
                data = None
            if isinstance(data, dict):
                mensaje = data.get("message") or {}
                if isinstance(mensaje, dict) and isinstance(mensaje.get("content"), str):
                    registro["contenido"] = mensaje.get("content")
            presupuesto.llamadas.append(registro)
            return respuesta

        def post(url, *args, **kwargs):
            return _registrar(real_post, url, args, kwargs)

        def get(url, *args, **kwargs):
            return _registrar(real_get, url, args, kwargs)

        sesion.post = post
        sesion.get = get


def _configurar_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HardWareHouse.settings")
    import django

    django.setup()


def _host_publico(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not parsed.scheme or not host:
        return ""
    return f"{parsed.scheme}://{host}"


def _es_https_remoto(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and bool(host) and host not in _HOSTS_LOCALES


def _imprimir(texto: str, clave: str) -> None:
    if clave and clave in texto:
        texto = texto.replace(clave, "[clave]")
    print(texto, flush=True)


def _filtrar_logs(clave: str) -> None:
    class _Filtro(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if clave and clave in record.getMessage():
                record.msg = "registro omitido"
                record.args = ()
            return True

    logging.getLogger().addFilter(_Filtro())


def _preve_nube(texto: str) -> bool:
    from django.conf import settings

    from core.chatbot.armado_optimizar import detectar_optimizacion
    from core.chatbot.llm.intent_extractor import intent_llm_activo
    from core.chatbot.policy import solicita_datos_sensibles
    from core.knowledge.service import responder_conocimiento

    if not intent_llm_activo():
        return False
    if not _es_https_remoto(getattr(settings, "OLLAMA_BASE_URL", "") or ""):
        return False
    if solicita_datos_sensibles(texto):
        return False
    if responder_conocimiento(texto):
        return False
    if detectar_optimizacion(texto):
        return False
    return True


def _clasificar_cuerpo(contenido) -> dict:
    from core.chatbot.llm.intent_schema import validar_intento_llm

    vacio = {
        "json_valido": "no",
        "intent": "-",
        "confianza": "-",
        "umbral": "no",
        "budget_clp": "-",
        "category": "-",
    }
    if not isinstance(contenido, str) or not contenido.strip():
        return vacio
    try:
        data = json.loads(contenido)
    except json.JSONDecodeError:
        return vacio
    intento = validar_intento_llm(data if isinstance(data, dict) else None)
    if intento is None:
        return vacio
    return {
        "json_valido": "si",
        "intent": intento.intent,
        "confianza": f"{intento.confidence:.2f}",
        "umbral": "si" if intento.confiable() else "no",
        "budget_clp": "-" if intento.budget_clp is None else str(intento.budget_clp),
        "category": intento.category or "-",
    }


def _comparar_producto(item: dict) -> str:
    from core.catalogo.registry import MODEL_BY_API_NAME
    from core.chatbot.serializers import precio_a_entero

    modelo = item.get("modelo")
    pk = item.get("producto_pk")
    clase = MODEL_BY_API_NAME.get(modelo or "")
    if clase is None or pk is None:
        return "producto sin identificador ORM"
    fila = clase.objects.filter(pk=pk).only("precio", "stock").first()
    if fila is None:
        return f"{modelo}:{pk} no está en el catálogo"
    precio_ok = precio_a_entero(fila.precio) == int(item.get("precio_clp") or -1)
    stock_ok = int(fila.stock) == int(item.get("stock") if item.get("stock") is not None else -1)
    if precio_ok and stock_ok:
        return f"{modelo}:{pk} precio y stock iguales al ORM"
    return f"{modelo}:{pk} difiere del ORM"


def _hechos_django(resultado: dict, caso_id: str) -> str:
    notas = []
    resultados = ((resultado.get("catalogo") or {}).get("results")) or []
    for item in resultados[:5]:
        if isinstance(item, dict):
            notas.append(_comparar_producto(item))
    armado = resultado.get("armado") if isinstance(resultado.get("armado"), dict) else {}
    productos = armado.get("productos") or []
    for item in productos:
        if isinstance(item, dict):
            notas.append(_comparar_producto(item))
    if productos:
        try:
            total = sum(
                int(item.get("precio_clp") or 0) * int(item.get("cantidad") or 1)
                for item in productos
            )
        except (TypeError, ValueError):
            total = None
        if total is not None and int(armado.get("total_clp") or -1) == total:
            notas.append("total igual a la suma ORM")
        elif total is not None:
            notas.append("total distinto de la suma ORM")
        notas.append(f"evaluacion={armado.get('evaluacion') or '-'}")
        notas.append(f"presupuesto_django={armado.get('presupuesto_clp') or '-'}")
        if caso_id == "armado" and armado.get("presupuesto_clp") != 700_000:
            notas.append("presupuesto distinto de 700000")
    if not notas:
        return "sin filas de catálogo que contrastar"
    return " | ".join(notas)


def _escrituras(consultas) -> int:
    verbos = ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "ALTER", "DROP", "CREATE")
    return sum(
        1
        for consulta in consultas
        if consulta["sql"].lstrip().upper().startswith(verbos)
    )


def _ejecutar_caso(caso: dict, clave: str) -> bool:
    """Ejecuta un caso. Devuelve True si la nube respondió 401."""
    from django.db import connection, transaction
    from django.test.utils import CaptureQueriesContext

    from core.chatbot.conversation import generar_respuesta

    assert _PRESUPUESTO is not None
    antes = len(_PRESUPUESTO.llamadas)
    inicio = time.perf_counter()
    resultado: dict = {}
    error = None
    escrituras = 0
    with transaction.atomic():
        try:
            with CaptureQueriesContext(connection) as ctx:
                resultado = generar_respuesta(caso["mensaje"])
            escrituras = _escrituras(ctx.captured_queries)
        except Exception as exc:
            error = type(exc).__name__
        finally:
            transaction.set_rollback(True)
    total_ms = (time.perf_counter() - inicio) * 1000
    hechas = _PRESUPUESTO.llamadas[antes:]
    nube_ms = sum(item["segundos"] for item in hechas) * 1000
    clasificacion = _clasificar_cuerpo(hechas[-1]["contenido"] if hechas else None)
    motor = resultado.get("motor") or "-"
    # "reglas" aquí es el relevo después de una llamada. Una ruta de FAQ o de
    # saludo que nunca sale del servidor no es un fallo de la nube.
    cayo_en_reglas = bool(hechas) and (
        motor == "reglas" or resultado.get("fallback") == "reglas"
    )
    if not hechas:
        origen = "django_sin_nube"
    elif cayo_en_reglas:
        origen = "reglas_tras_nube"
    else:
        origen = "nube_y_django"
    estado = "-"
    error_red = "-"
    modelo_enviado = "-"
    sensible = "no"
    if hechas:
        ultima = hechas[-1]
        estado = "-" if ultima["status"] is None else str(ultima["status"])
        error_red = ultima["error"] or "-"
        modelo_enviado = ultima["modelo"]
        sensible = "si" if any(item["sensible"] for item in hechas) else "no"
    reply = " ".join((resultado.get("reply") or "").split())
    if len(reply) > 180:
        reply = reply[:180] + "…"
    lineas = [
        f"caso={caso['id']}",
        "ejecutado=si",
        f"llamada_nube={'si' if hechas else 'no'}",
        f"llamadas_en_el_caso={len(hechas)}",
        f"estado_http={estado}",
        f"error_red={error_red}",
        f"modelo_enviado={modelo_enviado}",
        f"payload_sensible={sensible}",
        f"latencia_nube_ms={nube_ms:.0f}",
        f"latencia_total_ms={total_ms:.0f}",
        f"json_valido={clasificacion['json_valido']}",
        f"intent_nube={clasificacion['intent']}",
        f"confianza={clasificacion['confianza']}",
        f"umbral_aceptado={clasificacion['umbral']}",
        f"categoria_nube={clasificacion['category']}",
        f"budget_nube={clasificacion['budget_clp']}",
        f"motor={motor}",
        f"origen={origen}",
        f"fallback_reglas={'si' if cayo_en_reglas else 'no'}",
        f"intent_django={resultado.get('intent') or '-'}",
        f"tipo={resultado.get('response_type') or '-'}",
        f"error_caso={error or '-'}",
        f"escrituras_sql={escrituras}",
        f"hechos={_hechos_django(resultado, caso['id'])}",
        f"respuesta={reply or '-'}",
    ]
    for linea in lineas:
        _imprimir(linea, clave)
    _imprimir("---", clave)
    return bool(hechas and hechas[-1]["status"] == 401)


def main() -> int:
    global _PRESUPUESTO
    _configurar_django()
    from django.conf import settings

    from core.chatbot.llm.intent_extractor import intent_llm_activo
    from core.chatbot.llm.response_composer import response_llm_activo

    clave = (getattr(settings, "OLLAMA_API_KEY", "") or "").strip()
    url = (getattr(settings, "OLLAMA_BASE_URL", "") or "").strip()
    modelo = (getattr(settings, "OLLAMA_MODEL", "") or "").strip()
    _filtrar_logs(clave)
    _imprimir("HardWareHouse prueba local Ollama Cloud", clave)
    _imprimir(f"host={_host_publico(url) or '-'}", clave)
    _imprimir(f"modelo={modelo or '-'}", clave)
    _imprimir(f"timeout_s={getattr(settings, 'OLLAMA_TIMEOUT', '-')}", clave)
    _imprimir(f"intent_llm={'si' if intent_llm_activo() else 'no'}", clave)
    _imprimir(f"response_llm={'si' if response_llm_activo() else 'no'}", clave)
    _imprimir(f"clave={'configurada' if clave else 'ausente'}", clave)
    _imprimir(f"limite_llamadas={LIMITE_LLAMADAS}", clave)
    _imprimir("---", clave)

    if response_llm_activo():
        _imprimir(
            "detenido: HARDWAREHOUSE_CHAT_RESPONSE_LLM está activo. "
            "La redacción sería otra llamada y podría reescribir precios. "
            "Déjalo en False en esta sesión y vuelve a ejecutar. No se envió ninguna solicitud.",
            clave,
        )
        return 2

    if intent_llm_activo() and (not _es_https_remoto(url) or not modelo or not clave):
        _imprimir(
            "detenido: para llamar a la nube hacen falta URL https remota, modelo y clave. "
            "No se envió ninguna solicitud.",
            clave,
        )
        return 2

    _PRESUPUESTO = _Presupuesto()
    import core.chatbot.llm.ollama as ollama_mod

    if ollama_mod.requests is not None:
        _PRESUPUESTO.instalar(clave)

    for caso in CASOS:
        prevista = "si" if _preve_nube(caso["mensaje"]) else "no"
        _imprimir(f"plan caso={caso['id']} llamada_prevista={prevista}", clave)
    _imprimir("---", clave)

    auth_fallo = False
    for caso in CASOS:
        if caso["id"] == "ambiguo" and not intent_llm_activo():
            _imprimir("caso=ambiguo", clave)
            _imprimir("ejecutado=no", clave)
            _imprimir("motivo=la clasificación por nube está apagada", clave)
            _imprimir("---", clave)
            continue
        if len(_PRESUPUESTO.llamadas) >= LIMITE_LLAMADAS:
            _imprimir(f"caso={caso['id']}", clave)
            _imprimir("ejecutado=no", clave)
            _imprimir(
                "motivo=las pruebas anteriores ya usaron 3 llamadas; no se envía otra",
                clave,
            )
            _imprimir("---", clave)
            continue
        if _ejecutar_caso(caso, clave):
            auth_fallo = True
            break

    _imprimir(f"llamadas_realizadas={len(_PRESUPUESTO.llamadas)}", clave)
    if auth_fallo:
        _imprimir("fin=autenticacion_rechazada", clave)
        return 2
    _imprimir("fin=ok", clave)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"error={type(exc).__name__}", flush=True)
        raise SystemExit(1) from None
