"""Sensor patch sobre uma camada de polímero apoiada em metal.

Sistema de coordenadas (mm):

    z = 0                  superfície do metal (tubo de aço), condutor perfeito
    0 < z < espessura      camada de polímero (revestimento)
    z = espessura + gap    face do patch, voltada para baixo
    acima do patch         substrato da antena e plano de terra

Sem amostra, o patch fica em z = 0 e há ar em todos os lados.
"""

import os
import time
from dataclasses import dataclass, field

import numpy as np
from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import C0, EPS0

from .ambiente import pasta_simulacao, ver_geometria


@dataclass
class Defeito:
    """Caixa de outro material dentro da camada de polímero, em mm.

    O padrão é um vazio (ar) de 2 mm na interface com o metal, como uma
    delaminação. Para simular umidade, use er=78 e tand=0.1, por exemplo.
    """

    largura_x: float = 20.0
    largura_y: float = 20.0
    altura: float = 2.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0  # altura da base do defeito, a partir do metal
    er: float = 1.0
    tand: float = 0.0


@dataclass
class Resultado:
    """Resultado de uma simulação: frequência em GHz, S11 e impedância de entrada."""

    nome: str
    f: np.ndarray
    s11: np.ndarray
    zin: np.ndarray
    duracao: float = 0.0
    parametros: dict = field(default_factory=dict)

    @property
    def s11_db(self):
        return 20 * np.log10(np.abs(self.s11))

    def ressonancia(self, f1=None, f2=None):
        """Frequência (GHz) e |S11| (dB) da ressonância entre f1 e f2 (GHz).

        Usa o mínimo local mais profundo; um mínimo na borda da faixa não é ressonância.
        Uma parábola pelos três pontos em volta dá a frequência com resolução melhor
        que o passo da varredura.
        """
        y = self.s11_db
        f1 = self.f[0] if f1 is None else f1
        f2 = self.f[-1] if f2 is None else f2
        dentro = np.flatnonzero((self.f >= f1) & (self.f <= f2))
        locais = [i for i in dentro[1:-1] if 0 < i < len(y) - 1 and y[i] < y[i - 1] and y[i] <= y[i + 1]]
        i = min(locais, key=lambda k: y[k]) if locais else int(dentro[np.argmin(y[dentro])])
        if i == 0 or i == len(y) - 1:
            return float(self.f[i]), float(y[i])
        a, b, c = y[i - 1], y[i], y[i + 1]
        curvatura = a - 2 * b + c
        if curvatura <= 0:
            return float(self.f[i]), float(b)
        deslocamento = 0.5 * (a - c) / curvatura  # em passos, entre -0.5 e 0.5
        passo = self.f[i + 1] - self.f[i]
        return float(self.f[i] + deslocamento * passo), float(b - 0.25 * (a - c) * deslocamento)

    @property
    def f_ressonancia(self):
        """Frequência (GHz) da ressonância mais profunda."""
        return self.ressonancia()[0]

    @property
    def s11_minimo(self):
        """|S11| (dB) na ressonância mais profunda."""
        return self.ressonancia()[1]

    def __str__(self):
        return (f"{self.nome}: ressonância em {self.f_ressonancia:.4f} GHz, "
                f"|S11| mínimo = {self.s11_minimo:.1f} dB (simulação de {self.duracao:.0f} s)")


class Simulacao:
    """Monta e roda uma simulação FDTD de um patch, com ou sem amostra.

    Exemplo:
        sim = Simulacao(f_min=2, f_max=5)
        sim.antena(patch_retangular(3.5))
        sim.amostra(espessura=10, er=4, tand=0.01, gap=3)
        resultado = sim.rodar("patch_sobre_polimero")
    """

    def __init__(self, f_min=2.0, f_max=5.0, celulas_por_lambda=15, max_passos=30000,
                 criterio_fim=1e-4):
        self.f_min = f_min
        self.f_max = f_max
        self.celulas_por_lambda = celulas_por_lambda
        self.max_passos = max_passos
        self.criterio_fim = criterio_fim
        self._patch = None
        self._posicao = (0.0, 0.0)
        self._amostra = None
        self._defeitos = []

    # ------------------------------------------------------------------ descrição

    def antena(self, patch, x=0.0, y=0.0):
        """Define a antena patch e a posição (x, y) do centro dela, em mm."""
        self._patch = patch
        self._posicao = (float(x), float(y))
        return self

    def amostra(self, espessura=10.0, er=4.0, tand=0.01, gap=3.0):
        """Coloca uma camada de polímero sobre metal abaixo da antena.

        espessura: espessura do polímero (mm); er, tand: polímero;
        gap: distância de ar entre o polímero e o patch (mm).
        A camada e o metal ocupam todo o plano xy da simulação.
        """
        self._amostra = dict(espessura=float(espessura), er=float(er), tand=float(tand),
                             gap=float(gap))
        return self

    def defeito(self, defeito=None, **kwargs):
        """Coloca um defeito na camada de polímero. Aceita um Defeito ou os campos dele."""
        if self._amostra is None:
            raise ValueError("Chame sim.amostra(...) antes de sim.defeito(...).")
        self._defeitos.append(defeito or Defeito(**kwargs))
        return self

    # ------------------------------------------------------------------ montagem

    def _kappa(self, er, tand):
        """Condutividade (S/m) equivalente à tangente de perdas no centro da banda."""
        f_centro = (self.f_min + self.f_max) / 2 * 1e9
        return 2 * np.pi * f_centro * EPS0 * er * tand

    def montar(self):
        """Cria a estrutura (CSX), o motor FDTD e a porta. Retorna (fdtd, csx, porta)."""
        if self._patch is None:
            raise ValueError("Chame sim.antena(...) antes de montar a simulação.")
        p = self._patch
        x0, y0 = self._posicao
        h = p.substrato_h

        f_centro = (self.f_min + self.f_max) / 2 * 1e9
        meia_banda = (self.f_max - self.f_min) / 2 * 1e9
        fdtd = openEMS(NrTS=self.max_passos, EndCriteria=self.criterio_fim)
        fdtd.SetGaussExcite(f_centro, meia_banda)

        csx = ContinuousStructure()
        fdtd.SetCSX(csx)
        malha = csx.GetGrid()
        malha.SetDeltaUnit(1e-3)

        # resolução da malha: o meio mais denso define o menor comprimento de onda
        # (defeitos não entram na conta: água, com er = 78, deixaria a malha lenta demais)
        er_max = max(p.substrato_er, self._amostra["er"] if self._amostra else 1.0)
        lambda_min = C0 / (self.f_max * 1e9) / 1e-3
        res_ar = lambda_min / self.celulas_por_lambda
        res = res_ar / np.sqrt(er_max)

        # alturas
        if self._amostra:
            t = self._amostra["espessura"]
            z_patch = t + self._amostra["gap"]
        else:
            z_patch = 0.0
        z_terra = z_patch + h

        # caixa de ar: lambda/4 na menor frequência em volta da antena
        margem = C0 / (self.f_min * 1e9) / 1e-3 / 4
        meio = p.substrato_lado / 2
        x_lim = [x0 - meio - margem, x0 + meio + margem]
        y_lim = [y0 - meio - margem, y0 + meio + margem]
        for d in self._defeitos:
            x_lim = [min(x_lim[0], d.x - d.largura_x / 2 - res), max(x_lim[1], d.x + d.largura_x / 2 + res)]
            y_lim = [min(y_lim[0], d.y - d.largura_y / 2 - res), max(y_lim[1], d.y + d.largura_y / 2 + res)]
        z_lim = [0.0 if self._amostra else z_patch - margem, z_terra + margem]
        malha.AddLine("x", x_lim)
        malha.AddLine("y", y_lim)
        malha.AddLine("z", z_lim)

        # metal da amostra = contorno PEC em z mínimo; nos outros lados, absorção (MUR)
        fundo = "PEC" if self._amostra else "MUR"
        fdtd.SetBoundaryCond(["MUR", "MUR", "MUR", "MUR", fundo, "MUR"])

        # ---- antena: patch embaixo, substrato, plano de terra em cima
        substrato = csx.AddMaterial("substrato", epsilon=p.substrato_er,
                                    kappa=self._kappa(p.substrato_er, p.substrato_tand))
        substrato.AddBox([x0 - meio, y0 - meio, z_patch], [x0 + meio, y0 + meio, z_terra], priority=0)
        malha.AddLine("z", np.linspace(z_patch, z_terra, 5))

        terra = csx.AddMetal("plano_de_terra")
        terra.AddBox([x0 - meio, y0 - meio, z_terra], [x0 + meio, y0 + meio, z_terra], priority=10)
        fdtd.AddEdges2Grid(dirs="xy", properties=terra)

        patch = csx.AddMetal("patch")
        patch.AddBox([x0 - p.comprimento / 2, y0 - p.largura / 2, z_patch],
                     [x0 + p.comprimento / 2, y0 + p.largura / 2, z_patch], priority=10)
        # regra 1/3-2/3 nas bordas do patch; o passo tem de ser menor que "res",
        # senão a suavização põe uma linha na borda e o patch fica eletricamente maior
        fdtd.AddEdges2Grid(dirs="xy", properties=patch, metal_edge_res=res / 2)

        x_sonda = x0 - p.alimentacao
        porta = fdtd.AddLumpedPort(1, 50, [x_sonda, y0, z_patch], [x_sonda, y0, z_terra], "z", 1.0,
                                   priority=5, edges2grid="xy")

        # ---- amostra: polímero sobre o metal (o metal é o contorno PEC em z = 0)
        if self._amostra:
            a = self._amostra
            polimero = csx.AddMaterial("polimero", epsilon=a["er"], kappa=self._kappa(a["er"], a["tand"]))
            polimero.AddBox([x_lim[0], y_lim[0], 0], [x_lim[1], y_lim[1], t], priority=1)
            n = int(np.ceil(t / res)) + 1
            linhas_z = np.linspace(0, t, max(n, 4))
            malha.AddLine("z", linhas_z)

            metal = csx.AddMetal("metal")  # só para aparecer no visualizador
            metal.AddBox([x_lim[0], y_lim[0], 0], [x_lim[1], y_lim[1], 0], priority=10)

            # uma linha do defeito perto da borda do patch estraga a regra 1/3-2/3
            # (o patch fica maior e a ressonância cai); essas linhas ficam de fora
            bordas = {"x": [x0 - p.comprimento / 2, x0 + p.comprimento / 2],
                      "y": [y0 - p.largura / 2, y0 + p.largura / 2],
                      "z": list(linhas_z)}
            distancia = {"x": res, "y": res, "z": res / 4}

            for i, d in enumerate(self._defeitos):
                mat = csx.AddMaterial(f"defeito_{i + 1}", epsilon=d.er, kappa=self._kappa(d.er, d.tand))
                inicio = [d.x - d.largura_x / 2, d.y - d.largura_y / 2, d.z]
                fim = [d.x + d.largura_x / 2, d.y + d.largura_y / 2, min(d.z + d.altura, t)]
                mat.AddBox(inicio, fim, priority=2)
                for k, eixo in enumerate("xyz"):
                    for valor in (inicio[k], fim[k]):
                        if all(abs(valor - b) >= distancia[eixo] for b in bordas[eixo]):
                            malha.AddLine(eixo, valor)

        malha.SmoothMeshLines("all", res, 1.4)
        # a suavização deixa erros de arredondamento (1.6000000000000014 em vez de 1.6);
        # uma folha de metal fora da linha da malha some da simulação
        for eixo in "xyz":
            malha.SetLines(eixo, np.unique(np.round(malha.GetLines(eixo), 6)))
        return fdtd, csx, porta

    # ------------------------------------------------------------------ uso

    def ver(self, nome="geometria"):
        """Abre a geometria no visualizador 3D (AppCSXCAD)."""
        # o objeto openEMS é dono da geometria: se ele for apagado antes, o Python fecha com erro
        fdtd, csx, porta = self.montar()
        arquivo = ver_geometria(csx, nome)
        del porta, fdtd
        return arquivo

    def rodar(self, nome, pontos=401):
        """Roda a simulação e retorna um Resultado com S11 e Zin."""
        fdtd, csx, porta = self.montar()
        pasta = pasta_simulacao(nome)
        malha = csx.GetGrid()
        celulas = malha.GetQtyLines("x") * malha.GetQtyLines("y") * malha.GetQtyLines("z")
        print(f"Simulação '{nome}': {celulas / 1e3:.0f} mil células. Aguarde (normalmente 1 a 5 min)...")

        # o openEMS muda a pasta atual para a pasta da simulação; voltar depois,
        # para que plt.savefig("figura.png") grave ao lado do notebook
        pasta_atual = os.getcwd()
        inicio = time.time()
        try:
            fdtd.Run(str(pasta), cleanup=True)
        finally:
            os.chdir(pasta_atual)
        duracao = time.time() - inicio

        f = np.linspace(self.f_min, self.f_max, pontos)
        porta.CalcPort(str(pasta), f * 1e9)
        s11 = porta.uf_ref / porta.uf_inc
        zin = porta.uf_tot / porta.if_tot

        parametros = dict(amostra=self._amostra, defeitos=list(self._defeitos), posicao=self._posicao)
        resultado = Resultado(nome=nome, f=f, s11=s11, zin=zin, duracao=duracao, parametros=parametros)
        print(resultado)
        return resultado
