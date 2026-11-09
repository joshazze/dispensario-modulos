#!/usr/bin/env python3
"""Monta as paginas do site a partir dos fragmentos desta pasta.

Cada fragmento <nome>.html traz o hero e as <section id=...><h2>...</h2>. Este script poe a barra
de paginas, o sumario (tirado dos h2), os links de anterior/proxima e o rodape, e grava docs/<nome>.html.

    python3 docs/_fonte/gera.py
"""
import html
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DOCS = AQUI.parent
GRUPO = "Beatriz Samaha, Bruna Bento, Joshua Azze e Marcelo Reis"
ATUALIZADO = "08/11/2026"

# (arquivo, nome na barra, titulo da aba, descricao)
PAGINAS = [
    ("index", "Visão geral", "Dispensário Eletrônico",
     "Protótipo de farmácia satélite com acesso por digital ou senha e registro de cada abertura, para o Instituto Mário Penna."),
    ("requisitos", "Requisitos", "Requisitos · Dispensário Eletrônico",
     "Problema, requisitos funcionais e não funcionais, contrato entre hardware e software, máquina de estados e critérios de aceite."),
    ("eletronica", "Eletrônica", "Eletrônica · Dispensário Eletrônico",
     "Componentes, alimentação, pinagem do Arduino Mega e da ESP32-CAM e os 13 esquemas da bancada."),
    ("firmware", "Firmware", "Firmware · Dispensário Eletrônico",
     "Como o Mega decide o acesso, como a ESP32-CAM entrega eventos e fotos, credenciais, porta, sinais e testes."),
    ("servidor", "Servidor e nuvem", "Servidor e nuvem · Dispensário Eletrônico",
     "API do servidor, banco, segurança e a hospedagem com HTTPS na AWS."),
    ("gabinete", "Gabinete", "Gabinete · Dispensário Eletrônico",
     "Chassi modular em MDF, módulo biométrico, armário, porta, gaveteiro por letra e placa do projeto."),
    ("fabricacao", "Fabricação", "Fabricação · Dispensário Eletrônico",
     "Corte a laser na eCNC L-1210: gerador paramétrico, parâmetros medidos, cupons de teste e rota de corte."),
    ("linha-do-tempo", "Linha do tempo", "Linha do tempo · Dispensário Eletrônico",
     "O projeto dia a dia, de 20 de agosto a 9 de novembro de 2026."),
    ("fontes", "Fontes e glossário", "Fontes e glossário · Dispensário Eletrônico",
     "Repositórios, fontes de cada medida e decisão e glossário dos termos usados."),
]

MODELO = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<meta name="description" content="{descricao}">
<link rel="stylesheet" href="site/estilo.css">
</head>
<body>
<nav class="topo" aria-label="Páginas"><div class="wrap">
  <a class="marca" href="index.html">Dispensário Eletrônico</a>
  <ul class="paginas">{barra}</ul>
</div></nav>
{hero}
<main class="wrap">
{toc}
{corpo}
<div class="proxima">{ant}{prox}</div>
</main>
<footer><div class="wrap">
  Dispensário Eletrônico · Projeto de Sistemas Embarcados · Ibmec · 2026.2 · cliente Instituto Mário Penna (Hospital Luxemburgo).<br>
  Grupo: {grupo}. Professor: Osmar Ventura Gomes. Atualizado em {atualizado}.<br>
  Código e arquivos: <a href="https://github.com/joshazze/dispensario-modulos">dispensario-modulos</a> ·
  <a href="https://github.com/joshazze/dispensario-design-system">dispensario-design-system</a> ·
  <a href="https://github.com/marceloxreis/sistema-embarcados">sistema-embarcados</a>
</div></footer>
</body>
</html>
"""


def main():
    for i, (nome, barra_nome, titulo, descricao) in enumerate(PAGINAS):
        fonte = (AQUI / (nome + ".html")).read_text(encoding="utf-8")
        hero, corpo = fonte.split("<!-- corpo -->", 1)
        barra = "".join('<li><a href="%s.html"%s>%s</a></li>' % (n, ' aria-current="page"' if n == nome else "", b)
                        for n, b, _, _ in PAGINAS)
        secoes = re.findall(r'<section id="([^"]+)">\s*<h2>(.*?)</h2>', corpo)
        toc = ""
        if len(secoes) > 2:
            toc = '<nav class="toc" aria-label="Nesta página"><b>Nesta página</b><ol>%s</ol></nav>' % "".join(
                '<li><a href="#%s">%s</a></li>' % (sid, re.sub(r"<[^>]+>", "", t)) for sid, t in secoes)
        ant = prox = "<span></span>"
        if i > 0:
            n, b = PAGINAS[i - 1][:2]
            ant = '<a href="%s.html"><small>Anterior</small>%s</a>' % (n, b)
        if i < len(PAGINAS) - 1:
            n, b = PAGINAS[i + 1][:2]
            prox = '<a href="%s.html"><small>Próxima</small>%s</a>' % (n, b)
        saida = MODELO.format(titulo=titulo, descricao=html.escape(descricao, quote=True), barra=barra, hero=hero.strip(),
                              toc=toc, corpo=corpo.strip(), ant=ant, prox=prox, grupo=GRUPO, atualizado=ATUALIZADO)
        assert "PSE" not in re.sub(r'(href|src)="[^"]*"', "", saida), (nome, "a sigla PSE apareceu no texto")
        (DOCS / (nome + ".html")).write_text(saida, encoding="utf-8")
        print("ok", nome + ".html", len(saida), "bytes,", len(secoes), "secoes")


if __name__ == "__main__":
    main()
