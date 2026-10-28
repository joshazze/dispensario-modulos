"""Cupons de teste da fechadura eletrica do armario (28/10/2026).

Medidas da fechadura do desenho da DFRobot FIT0620 (73 x 58 x 13,3 mm),
conferidas pelo Josh com regua em 28/10/2026 (base do batente 34,65 x 20 x 1,6,
furos da base de 4,4). Duas pecas num retalho de MDF 3 mm:

- TRANCA: pedaco da lateral da casca. A fechadura fica de pe, com as costas
  encostadas na parede, presa por fora com 3 parafusos M4 nas roscas dela. O
  contorno do corpo sai gravado em linha, com a boca da lingueta para a frente.
  Furos a 6,5 mm da boca, 36,5 entre eles e centrados na altura; o terceiro
  36 mm a direita, a 30 mm da base.
- GANCHO: pedaco da porta. Bolso gravado do tamanho da base do batente em U
  (34,65 x 20 mm, folga de 0,25 por lado), para 1,6 mm de profundidade, a
  espessura da chapa, e a base entrar faceada com a porta, mais os 2 furos a
  25 mm entre centros.

Usa o pacote `laser` da branch da interface (rebaixo, rotulo em traco, UTF-8):
    PYTHONPATH=~/Projetos/dispensario-modulos python3 gera.py
"""
import os

from laser import fonte, geom, perfil
from laser.geom import circle_pts

AQUI = os.path.dirname(os.path.abspath(__file__))
MARGEM, GAP = 10.0, 5.0
FURO_M4 = 4.4

# fechadura, vista pelas costas, boca da lingueta na aresta esquerda
CORPO_W, CORPO_H = 73.0, 58.0
FURO_X, FURO_DY = 6.5, 36.5
FURO3_X, FURO3_Y = 6.5 + 36.0, 30.0
BOCA_ABERTURA = 7.0

# batente em U
BASE_W, BASE_H, FOLGA = 34.65, 20.0, 0.25
FURO_BASE, PASSO_BASE = 4.4, 25.0


def cupom_tranca(x0, y0):
    w, h = CORPO_W + 2 * MARGEM, CORPO_H + 2 * MARGEM
    bx, by = x0 + MARGEM, y0 + MARGEM
    cy = by + CORPO_H / 2.0
    cortes = [
        circle_pts(bx + FURO_X, cy - FURO_DY / 2.0, FURO_M4),
        circle_pts(bx + FURO_X, cy + FURO_DY / 2.0, FURO_M4),
        circle_pts(bx + FURO3_X, by + FURO3_Y, FURO_M4),
        geom.rrect(x0, y0, w, h, 2.0),
    ]
    corpo = geom.rrect(bx, by, CORPO_W, CORPO_H, 0.0)
    boca = [(bx, cy - BOCA_ABERTURA / 2.0), (bx - 4.0, cy), (bx, cy + BOCA_ABERTURA / 2.0)]
    marcas = [corpo + [corpo[0]], boca]
    rotulos = fonte.rotulo("TRANCA", bx + 20.0, y0 + 2.5, 3.0)
    return cortes, marcas, rotulos, w, h


def cupom_gancho(x0, y0):
    pw, ph = BASE_W + 2 * FOLGA, BASE_H + 2 * FOLGA
    w, h = pw + 2 * MARGEM, ph + 2 * MARGEM
    px, py = x0 + MARGEM, y0 + MARGEM
    cx, cy = px + pw / 2.0, py + ph / 2.0
    cortes = [
        circle_pts(cx - PASSO_BASE / 2.0, cy, FURO_BASE),
        circle_pts(cx + PASSO_BASE / 2.0, cy, FURO_BASE),
        geom.rrect(x0, y0, w, h, 2.0),
    ]
    rebaixos = [geom.rrect(px, py, pw, ph, 0.0)]
    rotulos = fonte.rotulo("GANCHO", px + 6.0, y0 + 2.5, 3.0)
    return cortes, rebaixos, rotulos, w, h


def main():
    ct, mt, rt, wt, ht = cupom_tranca(0.0, 0.0)
    cg, rg, rotg, wg, hg = cupom_gancho(wt + GAP, 0.0)
    nome = os.path.join(AQUI, "teste-tranca.dxf")
    # contorno da tranca vai em linha azul junto com os nomes: no amarelo o Fill
    # do bolso do gancho preencheria o corpo inteiro
    perfil.escreve(nome, ct + cg, rebaixos=rg, rotulos=mt + rt + rotg)
    print("%s | %.1f x %.1f mm" % (nome, wt + GAP + wg, max(ht, hg)))


if __name__ == "__main__":
    main()
