"""Seguiment d'errors (checklist E4, part del nivell 1; R11): GlitchTip o Sentry amb el mateix SDK.

Només s'activa a producció i només amb `ERROR_TRACKING_DSN` (config/settings/prod.py): sense, no
s'inicialitza res i no surt res per la xarxa. El host del DSN decideix on van les dades, per
això ha de ser a `ERROR_TRACKING_ALLOWED_HOSTS` (els serveis amb dades a la UE que triï el
propietari; P-294) o l'aplicació no arrenca.

Mai no s'envia: el cos, les galetes, la cadena de consulta ni l'URL de la petició (un enllaç de
convidat porta el testimoni al camí; la ruta es veu igualment a la transacció, sense valors),
cap capçalera fora de `_SAFE_HEADERS`, l'usuari, les variables locals, els `extra` ni els
paràmetres de les consultes SQL. Als missatges d'error i de registre es tapen els IBAN, les
targetes i altres números llargs, els correus, els DNI i NIE, els telèfons i les IP.

Aquest mòdul es carrega des dels settings: no pot importar res de Django que necessiti les apps.
"""

import re
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

MASK = "[tapat]"
_SAFE_HEADERS = {"user-agent", "content-type", "accept", "accept-language"}
# shortcut: patrons amples (tapen també algun identificador que no és personal); si un error
# real queda il·legible, s'afina el patró concret amb una prova.
_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),  # correu
    re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?\b", re.I),  # IBAN
    re.compile(r"\d(?:[ -]?\d){11,}"),  # targeta, compte antic de 20 dígits
    re.compile(r"\b(?:\d{8}|[XYZ]\d{7})[A-Z]\b", re.I),  # DNI, NIE
    re.compile(r"(?:\+\d{2}[ -]?)?\b[6-9](?:[ -]?\d){8}\b"),  # telèfon
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),  # IPv4
    re.compile(r"\b[0-9a-f]{0,4}(?::[0-9a-f]{0,4}){3,7}\b", re.I),  # IPv6
]


def mask(text):
    if not isinstance(text, str):
        return text
    for pattern in _PATTERNS:
        text = pattern.sub(MASK, text)
    return text


def before_send(event, hint):
    if "request" in event:
        request = event["request"] or {}
        headers = request.get("headers") or {}
        event["request"] = {
            "method": request.get("method"),
            "headers": {k: v for k, v in headers.items() if k.lower() in _SAFE_HEADERS},
        }
    for key in ("user", "extra"):
        event.pop(key, None)
    if "message" in event:
        event["message"] = mask(event["message"])
    if event.get("logentry"):
        # Sense `params`: el text ja formatat i tapat n'és prou.
        event["logentry"] = {k: mask(v) for k, v in event["logentry"].items() if k != "params"}
    for exception in (event.get("exception") or {}).get("values") or []:
        exception["value"] = mask(exception.get("value"))
        for frame in (exception.get("stacktrace") or {}).get("frames") or []:
            frame.pop("vars", None)
    return event


def before_breadcrumb(crumb, hint):
    # Les consultes SQL porten els paràmetres (dades de socis): no es guarden.
    if crumb.get("category") == "query":
        return None
    crumb.pop("data", None)
    crumb["message"] = mask(crumb.get("message"))
    return crumb


def dsn_host_allowed(dsn, allowed_hosts):
    host = (urlsplit(dsn).hostname or "").lower()
    return bool(host) and host in {h.strip().lower() for h in allowed_hosts}


def init(dsn, allowed_hosts, environment):
    if not dsn_host_allowed(dsn, allowed_hosts):
        raise ImproperlyConfigured(
            "El host d'ERROR_TRACKING_DSN no és a ERROR_TRACKING_ALLOWED_HOSTS: el seguiment "
            "d'errors només pot enviar dades a un servei de la UE que hagi triat el propietari."
        )
    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        traces_sample_rate=0,
        max_breadcrumbs=10,
        before_send=before_send,
        before_breadcrumb=before_breadcrumb,
    )
