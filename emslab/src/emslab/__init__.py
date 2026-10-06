"""Funções de apoio para simular sensores de micro-ondas com o openEMS."""

from .ambiente import pasta_base, pasta_simulacao, ver_geometria
from .antena import Patch, patch_retangular
from .graficos import grafico_s11, grafico_zin
from .simulacao import Defeito, Resultado, Simulacao
from .verificacao import verificar

__all__ = [
    "Defeito", "Patch", "Resultado", "Simulacao",
    "grafico_s11", "grafico_zin", "pasta_base", "pasta_simulacao",
    "patch_retangular", "ver_geometria", "verificar",
]
