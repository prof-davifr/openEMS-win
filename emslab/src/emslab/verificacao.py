"""Verificação da instalação, com mensagens para quem está começando."""

import os
import platform
import sys
import time
import traceback

OK = "[ OK ]"
ERRO = "[ERRO]"
AVISO = "[AVISO]"


def _linha(estado, texto):
    print(f"{estado} {texto}", flush=True)


def verificar(simular=True):
    """Confere a instalação passo a passo. Retorna True se tudo funcionou."""
    tudo_certo = True
    _linha(OK, f"Python {platform.python_version()} ({sys.executable})")

    instalacao = os.environ.get("CSXCAD_INSTALL_PATH")
    if os.name == "nt":
        if not instalacao:
            _linha(ERRO, "A variável CSXCAD_INSTALL_PATH não existe. Abra o Jupyter pelo atalho "
                         "'openEMS - Simulações' na área de trabalho.")
            return False
        if not os.path.isfile(os.path.join(instalacao, "openEMS.exe")):
            _linha(ERRO, f"openEMS.exe não está em {instalacao}. Rode INSTALAR.bat de novo.")
            return False
        _linha(OK, f"openEMS em {instalacao}")

    try:
        import CSXCAD
        import openEMS  # noqa: F401
        from openEMS import openEMS as _motor  # noqa: F401
    except ImportError as erro:
        _linha(ERRO, f"Não foi possível carregar o openEMS no Python: {erro}")
        _linha(ERRO, "Rode INSTALAR.bat de novo. Se o erro continuar, mande o arquivo "
                     "instalacao.log ao orientador.")
        return False
    _linha(OK, f"Módulos CSXCAD {CSXCAD.__version__} e openEMS carregados")

    from .ambiente import _appcsxcad, pasta_base, pasta_simulacao

    if _appcsxcad():
        _linha(OK, "Visualizador 3D (AppCSXCAD) encontrado")
    else:
        _linha(AVISO, "Visualizador 3D (AppCSXCAD) não encontrado; as simulações funcionam sem ele")

    try:
        pasta = pasta_simulacao("verificacao")
        (pasta / "teste.txt").write_text("ok")
        _linha(OK, f"Pasta das simulações: {pasta_base()}")
    except OSError as erro:
        _linha(ERRO, f"Não foi possível gravar na pasta das simulações: {erro}")
        return False

    if simular:
        from .antena import patch_retangular
        from .simulacao import Simulacao

        try:
            inicio = time.time()
            sim = Simulacao(celulas_por_lambda=8, max_passos=2000)
            sim.antena(patch_retangular(3.5))
            resultado = sim.rodar("verificacao")
            if not all(abs(v) < 10 for v in resultado.s11):
                raise RuntimeError("S11 com valores sem sentido")
            _linha(OK, f"Simulação de teste em {time.time() - inicio:.0f} s")
        except Exception:
            traceback.print_exc()
            _linha(ERRO, "A simulação de teste falhou. Mande esta mensagem ao orientador.")
            tudo_certo = False

    if tudo_certo:
        print("\nTudo certo! O openEMS está pronto para uso.")
    return tudo_certo
