"""Regua de furos para o botao de pressao da porta do armario (28/10/2026).

O Josh mediu o botao com 10 mm de diametro. O laser abre o furo um pouco maior
que o desenho (kerf), entao a regua vai de 9,7 a 10,4 mm de 0,1 em 0,1, cada
furo com a medida gravada embaixo. O que segurar o botao sem folga e sem forcar
vira o diametro da porta.

Por fora, cada furo tem rebaixo concentrico de 12,7 mm com 1 mm de
profundidade para a aba do botao assentar. A face de fora vai pra cima na mesa.

Usa o pacote `laser` da branch da interface (rotulo em traco, UTF-8):
    PYTHONPATH=~/Projetos/dispensario-modulos python3 gera.py
"""
import os

from laser import fonte, geom, perfil
from laser.geom import circle_pts

AQUI = os.path.dirname(os.path.abspath(__file__))
DIAMETROS = [9.7, 9.8, 9.9, 10.0, 10.1, 10.2, 10.3, 10.4]
PASSO, MARGEM, ALT_TEXTO = 16.0, 8.0, 2.5
REBAIXO = 12.7


def main():
    w = MARGEM * 2 + PASSO * (len(DIAMETROS) - 1)
    h = MARGEM + REBAIXO + 2.0 + ALT_TEXTO + MARGEM
    cy = h - MARGEM - REBAIXO / 2.0
    cortes, rebaixos, rotulos = [], [], []
    for i, d in enumerate(DIAMETROS):
        cx = MARGEM + PASSO * i
        cortes.append(circle_pts(cx, cy, d))
        rebaixos.append(circle_pts(cx, cy, REBAIXO))
        texto = ("%.1f" % d).replace(".", ",")
        tw = fonte.largura_texto(texto, ALT_TEXTO)
        rotulos.extend(fonte.rotulo(texto, cx - tw / 2.0, cy - REBAIXO / 2.0 - 2.0 - ALT_TEXTO, ALT_TEXTO))
    cortes.append(geom.rrect(0.0, 0.0, w, h, 2.0))
    nome = os.path.join(AQUI, "teste-botao.dxf")
    perfil.escreve(nome, cortes, rebaixos=rebaixos, rotulos=rotulos)
    print("%s | %.1f x %.1f mm | %d furos" % (nome, w, h, len(DIAMETROS)))


if __name__ == "__main__":
    main()
