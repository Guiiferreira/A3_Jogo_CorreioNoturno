"""
Monta a versão para celular (web/index.html) a partir de web/jogo_fonte.html,
embutindo os sprites de assets/img e os sons de assets/sons no próprio arquivo.

Assim a versão web é um arquivo só, que abre em qualquer navegador (Safari do
iPhone inclusive) sem precisar de servidor.

    python tools/gerar_web.py

Se o ffmpeg estiver instalado, os sons são convertidos para MP3 (arquivo bem
menor). Sem ffmpeg, os WAV são embutidos como estão.
"""
import base64
import json
import os
import shutil
import subprocess
import tempfile

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMG = os.path.join(RAIZ, "assets", "img")
SONS = os.path.join(RAIZ, "assets", "sons")
FONTE = os.path.join(RAIZ, "web", "jogo_fonte.html")
SAIDA = os.path.join(RAIZ, "web", "index.html")


def data_uri(caminho, mime):
    with open(caminho, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def main():
    assets = {"img": {}, "snd": {}}
    for nome in sorted(os.listdir(IMG)):
        if nome.endswith(".png"):
            assets["img"][nome[:-4]] = data_uri(os.path.join(IMG, nome), "image/png")

    ffmpeg = shutil.which("ffmpeg")
    with tempfile.TemporaryDirectory() as tmp:
        for nome in sorted(os.listdir(SONS)):
            if not nome.endswith(".wav"):
                continue
            origem = os.path.join(SONS, nome)
            chave = nome[:-4]
            if ffmpeg:
                destino = os.path.join(tmp, chave + ".mp3")
                taxa = "64k" if chave.startswith("musica") else "56k"
                subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", origem,
                                "-ac", "1", "-b:a", taxa, destino], check=True)
                assets["snd"][chave] = data_uri(destino, "audio/mpeg")
            else:
                assets["snd"][chave] = data_uri(origem, "audio/wav")

    with open(FONTE, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("__ASSETS__", json.dumps(assets))
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"web/index.html gerado ({os.path.getsize(SAIDA) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
