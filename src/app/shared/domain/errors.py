"""Errores de dominio. No saben de HTTP: la capa api los traduce a problem+json."""


class DomainError(Exception):
    """Regla de negocio violada (por defecto, 422 en la API)."""


class NotFoundError(DomainError):
    """El recurso no existe o no pertenece al usuario."""


class ConflictError(DomainError):
    """La operación choca con el estado actual (por ejemplo, un email ya registrado)."""
