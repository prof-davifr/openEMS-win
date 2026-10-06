"""Projeto inicial de uma antena patch retangular alimentada por sonda."""

from dataclasses import dataclass

import numpy as np

C0_MM_GHZ = 299.792458  # velocidade da luz em mm·GHz


@dataclass
class Patch:
    """Dimensões de uma antena patch, em mm.

    O comprimento (direção x) define a ressonância. A sonda de alimentação
    fica no eixo x, a uma distância `alimentacao` do centro do patch.
    """

    comprimento: float
    largura: float
    alimentacao: float
    substrato_h: float = 1.6
    substrato_er: float = 4.4
    substrato_tand: float = 0.02
    substrato_lado: float = 60.0
    f_projeto: float = 3.5  # GHz

    def __str__(self):
        return (f"Patch para {self.f_projeto} GHz: comprimento = {self.comprimento:.2f} mm, "
                f"largura = {self.largura:.2f} mm, sonda a {self.alimentacao:.2f} mm do centro, "
                f"substrato {self.substrato_lado:.0f} x {self.substrato_lado:.0f} x "
                f"{self.substrato_h} mm (er = {self.substrato_er})")


def patch_retangular(f_ghz=3.5, er=4.4, h=1.6, tand=0.02, impedancia=50.0):
    """Calcula as dimensões de um patch pelas fórmulas clássicas (Balanis, cap. 14).

    Estas fórmulas dão só um ponto de partida. A simulação mostra a
    frequência real, que normalmente fica alguns por cento abaixo.

    Parâmetros: f_ghz (frequência de projeto, GHz), er e tand (substrato),
    h (espessura do substrato, mm), impedancia (ohm).
    """
    lambda0 = C0_MM_GHZ / f_ghz

    # largura que dá boa eficiência de radiação
    largura = lambda0 / 2 * np.sqrt(2 / (er + 1))

    # permissividade efetiva e extensão do comprimento pelo campo de borda
    er_ef = (er + 1) / 2 + (er - 1) / 2 / np.sqrt(1 + 12 * h / largura)
    dl = 0.412 * h * ((er_ef + 0.3) * (largura / h + 0.264)) / ((er_ef - 0.258) * (largura / h + 0.8))
    comprimento = lambda0 / (2 * np.sqrt(er_ef)) - 2 * dl

    # posição da sonda: R(x0) = R_borda * cos²(pi * x0 / L), x0 medido a partir da borda
    k0h = 2 * np.pi / lambda0 * h
    g1 = largura / (120 * lambda0) * (1 - k0h**2 / 24)
    r_borda = 1 / (2 * g1)

    # a perda do substrato baixa R_borda na razão Q_total / Q_radiação
    # (Q_radiação de Jackson e Alexopoulos, IEEE TAP, 1991)
    n2 = er
    c1 = 1 - 1 / n2 + 0.4 / n2**2
    q_rad = 3 * er * comprimento / (16 * c1 * h) * lambda0 / largura
    q_total = 1 / (1 / q_rad + tand)
    r_borda *= q_total / q_rad
    x0 = comprimento / np.pi * np.arccos(np.sqrt(min(impedancia / r_borda, 1.0)))
    alimentacao = comprimento / 2 - x0

    # substrato com uma margem de lambda0/6 em cada lado
    lado = float(np.ceil(max(comprimento, largura) + lambda0 / 3))

    return Patch(comprimento=round(float(comprimento), 2), largura=round(float(largura), 2),
                 alimentacao=round(float(alimentacao), 2), substrato_h=h, substrato_er=er,
                 substrato_tand=tand, substrato_lado=lado, f_projeto=f_ghz)
