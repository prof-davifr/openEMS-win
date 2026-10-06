"""Gráficos de S11 e de impedância."""

import matplotlib.pyplot as plt


def grafico_s11(*resultados, ax=None, marcar=True, titulo="Coeficiente de reflexão"):
    """Desenha |S11| em dB de um ou mais resultados e marca a ressonância."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4.5), tight_layout=True)
    for r in resultados:
        (linha,) = ax.plot(r.f, r.s11_db, linewidth=2, label=r.nome)
        if marcar:
            ax.plot(r.f_ressonancia, r.s11_minimo, "o", color=linha.get_color())
    ax.axhline(-10, color="gray", linestyle=":", linewidth=1)
    ax.set_xlabel("Frequência (GHz)")
    ax.set_ylabel("|S11| (dB)")
    ax.set_title(titulo)
    ax.set_xmargin(0)
    ax.grid(True)
    ax.legend()
    return ax


def grafico_zin(resultado, ax=None):
    """Desenha a parte real e a parte imaginária da impedância de entrada."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4.5), tight_layout=True)
    ax.plot(resultado.f, resultado.zin.real, "k-", linewidth=2, label="Re{Zin}")
    ax.plot(resultado.f, resultado.zin.imag, "r--", linewidth=2, label="Im{Zin}")
    ax.axhline(50, color="gray", linestyle=":", linewidth=1)
    ax.set_xlabel("Frequência (GHz)")
    ax.set_ylabel("Zin (ohm)")
    ax.set_title(f"Impedância de entrada - {resultado.nome}")
    ax.set_xmargin(0)
    ax.grid(True)
    ax.legend()
    return ax
