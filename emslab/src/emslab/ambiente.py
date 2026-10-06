"""Pastas de trabalho e visualização da geometria."""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def pasta_base():
    """Pasta onde ficam os resultados de todas as simulações.

    No Windows, o openEMS não abre caminhos com acento. Se a pasta do usuário
    tiver acento (por exemplo, C:\\Users\\João), usa C:\\Users\\Public.
    A variável de ambiente EMSLAB_SIMULACOES troca a pasta, se for preciso.
    """
    escolhida = os.environ.get("EMSLAB_SIMULACOES")
    if escolhida:
        return Path(escolhida)
    base = Path.home() / "openEMS-simulacoes"
    if not str(base).isascii():
        publica = os.environ.get("PUBLIC") or tempfile.gettempdir()
        base = Path(publica) / "openEMS-simulacoes"
    return base


def pasta_simulacao(nome):
    """Caminho da pasta de uma simulação. Troca espaços e acentos por '_'."""
    seguro = re.sub(r"[^A-Za-z0-9_.-]", "_", str(nome)) or "simulacao"
    pasta = pasta_base() / seguro
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _appcsxcad():
    """Caminho do AppCSXCAD (visualizador 3D que vem com o openEMS)."""
    from CSXCAD import AppCSXCAD_BIN

    candidatos = [AppCSXCAD_BIN + ".exe", AppCSXCAD_BIN]
    for variavel in ("CSXCAD_INSTALL_PATH", "OPENEMS_INSTALL_PATH"):
        raiz = os.environ.get(variavel)
        if raiz:
            candidatos += [os.path.join(raiz, "AppCSXCAD.exe"),
                           os.path.join(raiz, "bin", "AppCSXCAD.sh"),
                           os.path.join(raiz, "bin", "AppCSXCAD")]
    for caminho in candidatos:
        if os.path.isfile(caminho):
            return caminho
    return shutil.which("AppCSXCAD") or shutil.which("AppCSXCAD.sh")


def ver_geometria(csx, nome="geometria"):
    """Grava a geometria em XML e abre o AppCSXCAD numa janela separada."""
    arquivo = pasta_simulacao(nome) / "geometria.xml"
    csx.Write2XML(str(arquivo))
    if os.environ.get("EMSLAB_SEM_JANELA"):  # testes automáticos
        print(f"Geometria gravada em: {arquivo}")
        return arquivo
    programa = _appcsxcad()
    if programa is None:
        print(f"AppCSXCAD não encontrado. A geometria está em: {arquivo}")
        return arquivo
    subprocess.Popen([programa, str(arquivo)])
    print("A geometria abriu numa janela nova. Feche a janela para continuar a trabalhar nela.")
    return arquivo
