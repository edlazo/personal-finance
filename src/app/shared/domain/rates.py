"""Tipos de cotización del dólar."""

from enum import StrEnum


class RateType(StrEnum):
    MEP = "MEP"
    OFICIAL = "OFICIAL"
    BLUE = "BLUE"
    CCL = "CCL"
    CRIPTO = "CRIPTO"
