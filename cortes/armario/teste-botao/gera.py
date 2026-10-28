"""Teste do rebaixo do botao de pressao da porta do armario (28/10/2026).

O furo do botao ficou definido em 10,1 mm (reguas de furo de 9,7 a 10,4 e 10,5
a 11,4 cortadas antes). Agora o que varia e o rebaixo por fora, onde a aba do
botao assenta. Depois da grade de 10,5 a 12,5 mm, o Josh fechou em furo de
10,1 com rebaixo de 12,8 mm e 1 mm de profundidade: sai uma peca so, com o
diametro do rebaixo gravado embaixo. A face de fora vai pra cima na mesa.

Usa o pacote `laser` da branch da interface (rebaixo, rotulo em traco, UTF-8):
    PYTHONPATH=~/Projetos/dispensario-modulos python3 gera.py
"""
import os

from laser import fonte, geom, perfil
from laser.geom import circle_pts

AQUI = os.path.dirname(os.path.abspath(__file__))
FURO = 10.1
# grade 10,5 a 12,5 cortada em 28/10; o Josh escolheu 12,8: sai uma peca so
REBAIXOS = [12.8]
PASSO, MARGEM, ALT_TEXTO = 16.0, 8.0, 2.5
REBAIXO = max(REBAIXOS)   # maior rebaixo, manda no espacamento


COLUNAS = 7
LINHA = REBAIXO + 2.0 + ALT_TEXTO + 3.0     # altura de cada linha da grade
BORDA = 4.0                                  # da borda da placa ate o rebaixo


def main():
    colunas = min(COLUNAS, len(REBAIXOS))
    linhas = -(-len(REBAIXOS) // colunas)
    w = 2 * BORDA + REBAIXO + PASSO * (colunas - 1)
    h = 2 * BORDA + LINHA * linhas - 3.0
    cortes, rebaixos, rotulos = [], [], []
    for i, d in enumerate(REBAIXOS):
        col, lin = i % colunas, i // colunas
        cx = BORDA + REBAIXO / 2.0 + PASSO * col
        cy = h - BORDA - REBAIXO / 2.0 - LINHA * lin      # menor em cima, a esquerda
        cortes.append(circle_pts(cx, cy, FURO))
        rebaixos.append(circle_pts(cx, cy, d))
        texto = ("%.1f" % d).replace(".", ",")
        tw = fonte.largura_texto(texto, ALT_TEXTO)
        rotulos.extend(fonte.rotulo(texto, cx - tw / 2.0, cy - REBAIXO / 2.0 - 2.0 - ALT_TEXTO, ALT_TEXTO))
    cortes.append(geom.rrect(0.0, 0.0, w, h, 2.0))
    nome = os.path.join(AQUI, "teste-botao.dxf")
    perfil.escreve(nome, cortes, rebaixos=rebaixos, rotulos=rotulos)
    print("%s | %.1f x %.1f mm | %d rebaixos em %d x %d" % (nome, w, h, len(REBAIXOS), colunas, linhas))


if __name__ == "__main__":
    main()
