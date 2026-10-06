"""Prepara a pasta de trabalho do aluno e abre o JupyterLab.

Uso:
    python abrir.py               copia os notebooks novos, cria o atalho e abre o Jupyter
    python abrir.py --preparar    só copia os notebooks e cria o atalho
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOME_ATALHO = "openEMS Lab.lnk"


def pasta_especial(csidl, padrao):
    """Pasta do Windows (Documentos, Área de Trabalho), mesmo se estiver no OneDrive."""
    if os.name != "nt":
        return padrao
    import ctypes
    from ctypes import wintypes

    buffer = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
    if ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buffer) == 0:
        return Path(buffer.value)
    return padrao


def pasta_notebooks():
    return pasta_especial(0x0005, Path.home() / "Documents") / "openEMS-notebooks"


def copiar_notebooks(destino):
    """Copia só os notebooks que ainda não existem: nunca apaga o trabalho do aluno."""
    destino.mkdir(parents=True, exist_ok=True)
    novos = []
    for origem in sorted((RAIZ / "notebooks").glob("*.ipynb")):
        alvo = destino / origem.name
        if not alvo.exists():
            shutil.copy2(origem, alvo)
            novos.append(origem.name)
    return novos


def criar_atalho():
    """Cria o atalho 'openEMS Lab' na Área de Trabalho."""
    if os.name != "nt":
        return None
    area_de_trabalho = pasta_especial(0x0010, Path.home() / "Desktop")
    area_de_trabalho.mkdir(parents=True, exist_ok=True)
    atalho = area_de_trabalho / NOME_ATALHO
    # os caminhos vão por variáveis de ambiente, para não ter problema com espaços e acentos
    ambiente = dict(os.environ,
                    ATALHO=str(atalho),
                    ALVO=str(RAIZ / "ABRIR.bat"),
                    PASTA=str(RAIZ),
                    ICONE=str(RAIZ / "openEMS" / "AppCSXCAD.exe") + ",0")
    ambiente.pop("PSModulePath", None)  # o do PowerShell 7 quebra o PowerShell 5.1
    comando = ("$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:ATALHO); "
               "$s.TargetPath = $env:ALVO; $s.WorkingDirectory = $env:PASTA; "
               "$s.IconLocation = $env:ICONE; $s.Description = 'Abre o Jupyter com o openEMS'; $s.Save()")
    resultado = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", comando],
                               env=ambiente, capture_output=True, text=True)
    if resultado.returncode != 0:
        print("Aviso: não foi possível criar o atalho na Área de Trabalho.")
        print(resultado.stderr.strip())
        return None
    return atalho


def preparar():
    notebooks = pasta_notebooks()
    novos = copiar_notebooks(notebooks)
    if novos:
        print(f"Notebooks novos copiados para {notebooks}:")
        for nome in novos:
            print(f"  - {nome}")
    atalho = criar_atalho()
    if atalho:
        print(f"Atalho na Área de Trabalho: {atalho.name}")
    return notebooks


def main():
    notebooks = preparar()
    if "--preparar" in sys.argv:
        return 0

    print()
    print("O Jupyter vai abrir no navegador em alguns segundos.")
    print("NÃO FECHE ESTA JANELA enquanto usa o Jupyter.")
    print("Para encerrar: salve os notebooks, feche o navegador e depois feche esta janela.")
    print()

    from jupyterlab.labapp import main as jupyter_lab

    sys.argv = ["jupyter-lab", f"--ServerApp.root_dir={notebooks}"]
    return jupyter_lab()


if __name__ == "__main__":
    sys.exit(main())
