"""Regua de furos para o botao de pressao da porta do armario (28/10/2026).

O Josh mediu o botao com 10 mm de diametro. A primeira regua (9,7 a 10,4) ficou
apertada ate o fim, entao esta vai de 10,5 a 12,5 mm de 0,1 em 0,1, cada
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
# 1a regua (9,7 a 10,4) cortada em 28/10: 10,4 ainda ficou apertado
DIAMETROS = [round(10.5 + 0.1 * i, 1) for i in range(21)]   # 10,5 a 12,5
PASSO, MARGEM, ALT_TEXTO = 16.0, 8.0, 2.5
REBAIXO = 12.7


COLUNAS = 7
LINHA = REBAIXO + 2.0 + ALT_TEXTO + 3.0     # altura de cada linha da grade
BORDA = 4.0                                  # da borda da placa ate o rebaixo


def main():
    linhas = -(-len(DIAMETROS) // COLUNAS)
    w = 2 * BORDA + REBAIXO + PASSO * (COLUNAS - 1)
    h = 2 * BORDA + LINHA * linhas - 3.0
    cortes, rebaixos, rotulos = [], [], []
    for i, d in enumerate(DIAMETROS):
        col, lin = i % COLUNAS, i // COLUNAS
        cx = BORDA + REBAIXO / 2.0 + PASSO * col
        cy = h - BORDA - REBAIXO / 2.0 - LINHA * lin      # menor em cima, a esquerda
        cortes.append(circle_pts(cx, cy, d))
        rebaixos.append(circle_pts(cx, cy, REBAIXO))
        texto = ("%.1f" % d).replace(".", ",")
        tw = fonte.largura_texto(texto, ALT_TEXTO)
        rotulos.extend(fonte.rotulo(texto, cx - tw / 2.0, cy - REBAIXO / 2.0 - 2.0 - ALT_TEXTO, ALT_TEXTO))
    cortes.append(geom.rrect(0.0, 0.0, w, h, 2.0))
    nome = os.path.join(AQUI, "teste-botao.dxf")
    perfil.escreve(nome, cortes, rebaixos=rebaixos, rotulos=rotulos)
    print("%s | %.1f x %.1f mm | %d furos em %d x %d" % (nome, w, h, len(DIAMETROS), COLUNAS, linhas))


if __name__ == "__main__":
    main()
