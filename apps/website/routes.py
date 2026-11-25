"""Una pàgina no pot tenir l'adreça d'una ruta que ja existeix (CA-M07-19)."""

from django.urls import get_resolver


def _first_segments(patterns, prefix=""):
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if hasattr(pattern, "url_patterns"):
            yield from _first_segments(pattern.url_patterns, route)
        else:
            yield route.lstrip("^").split("/")[0]


def route_taken(slug: str) -> bool:
    """El primer tram d'alguna ruta de la plataforma és `slug` (també `gestio`, `en-construccio`
    o l'entrada de l'administració). Les rutes amb paràmetre (`<slug>/`) no compten."""
    return slug in set(_first_segments(get_resolver().url_patterns))


def _names(patterns, namespace=""):
    for pattern in patterns:
        if hasattr(pattern, "url_patterns"):
            child = f"{namespace}{pattern.namespace}:" if pattern.namespace else namespace
            yield from _names(pattern.url_patterns, child)
        elif pattern.name:
            yield namespace + pattern.name


def route_exists(name: str) -> bool:
    """Hi ha una ruta amb aquest nom (`espai:nom`), amb paràmetres o sense (T-M07-10)."""
    return name in set(_names(get_resolver().url_patterns))
