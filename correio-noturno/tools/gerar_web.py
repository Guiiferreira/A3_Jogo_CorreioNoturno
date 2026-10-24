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
        corpo = f.read().replace("__ASSETS__", json.dumps(assets))
    gerar_icones()
    # Página completa: abre igual no GitHub Pages, em outro site ou direto do arquivo.
    # título, metas e links das fontes (tudo antes do primeiro <style>) vão para o <head>
    i = corpo.index("<style>")
    cabeca, corpo = corpo[:i], corpo[i:]
    html = CABECALHO.replace("</head>", cabeca + "</head>") + corpo + "\n</body>\n</html>\n"
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"web/index.html gerado ({os.path.getsize(SAIDA) / 1e6:.1f} MB)")


CABECALHO = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Correio Noturno: ajude o pombo Bico a entregar as cartas antes do sol nascer.">
<link rel="icon" type="image/png" href="icone-192.png">
<link rel="apple-touch-icon" href="icone-180.png">
<link rel="manifest" href="manifest.webmanifest">
<meta name="apple-mobile-web-app-title" content="Correio Noturno">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);box-sizing:border-box}</style>
</head>
<body>
"""


def gerar_icones():
    """Ícones para a aba do navegador e para a tela de início do celular."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    pygame.init()
    # usa a arte do ícone (web/icone-original.png, 1024x1024); sem ela, o sprite do Bico
    original = os.path.join(RAIZ, "web", "icone-original.png")
    if os.path.exists(original):
        arte = pygame.image.load(original)
        for tamanho in (180, 192, 512):
            img = pygame.transform.smoothscale(arte, (tamanho, tamanho))
            pygame.image.save(img, os.path.join(RAIZ, "web", f"icone-{tamanho}.png"))
    else:
        pombo = pygame.image.load(os.path.join(IMG, "pombo_bico_0.png"))
        for tamanho in (180, 192, 512):
            tela = pygame.Surface((tamanho, tamanho))
            tela.fill((18, 20, 38))
            lado = int(tamanho * 0.78)
            img = pygame.transform.scale(pombo, (lado, lado))
            tela.blit(img, img.get_rect(center=(tamanho // 2, tamanho // 2)))
            pygame.image.save(tela, os.path.join(RAIZ, "web", f"icone-{tamanho}.png"))
    manifesto = {
        "name": "Correio Noturno", "short_name": "Correio Noturno", "lang": "pt-BR",
        "start_url": "./", "display": "fullscreen", "orientation": "portrait",
        "background_color": "#0b0c18", "theme_color": "#121426",
        "icons": [{"src": "icone-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "icone-512.png", "sizes": "512x512", "type": "image/png"}],
    }
    with open(os.path.join(RAIZ, "web", "manifest.webmanifest"), "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
