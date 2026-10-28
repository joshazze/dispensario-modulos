"""Cupom de teste da dobradica borboleta da porta do armario (28/10/2026).

Medidas do Josh com paquimetro: aberta, 15,40 de comprimento (ao longo do pino)
por 11,61 de largura, entao cada aba tem ~5,8. Dois furos de 2,33 por aba,
7,70 de ponta a ponta (centros a 5,37) e a 1,20 da borda de fora da aba.

Duas plaquinhas, MOLDURA e PORTA, com o pino na aresta de encontro: cada uma tem
o bolso gravado do tamanho da aba (com 0,25 de folga) encostado na aresta e os 2
furos. A aba tem 0,48 de espessura: o bolso vai com Fill 150/80 em 1 passada
(a de 2 passadas e a do botao, mais funda) e a profundidade se confere no cupom.

    PYTHONPATH=~/Projetos/dispensario-modulos python3 gera.py
"""
import os

from laser import fonte, geom, perfil
from laser.geom import circle_pts

AQUI = os.path.dirname(os.path.abspath(__file__))
COMP, LARG_ABERTA = 15.40, 11.61
ABA = LARG_ABERTA / 2.0
FURO, PONTA_A_PONTA, BORDA_FURO = 2.33, 7.70, 1.20
PASSO = PONTA_A_PONTA - FURO
FOLGA = 0.25
RAIO = 2.0   # canto arredondado da aba (estimado, conferir)
W, H, GAP = 40.0, 22.0, 5.0


def plaquinha(x0, nome):
    """Aresta do pino em y = 0 da plaquinha; bolso e furos encostados nela."""
    cx = x0 + W / 2.0
    # cantos de fora arredondados como a aba; os da aresta do pino ficam retos
    # (o retangulo desce RAIO abaixo da aresta e e recortado nela)
    bolso = [(x, max(y, 0.0)) for x, y in
             geom.rrect(cx - COMP / 2.0 - FOLGA, -RAIO, COMP + 2 * FOLGA, ABA + FOLGA + RAIO, RAIO)]
    fy = ABA - BORDA_FURO - FURO / 2.0
    furos = [circle_pts(cx - PASSO / 2.0, fy, FURO), circle_pts(cx + PASSO / 2.0, fy, FURO)]
    tw = fonte.largura_texto(nome, 3.0)
    rot = fonte.rotulo(nome, cx - tw / 2.0, H - 6.0, 3.0)
    return furos + [geom.rrect(x0, 0.0, W, H, 0.0)], [bolso], rot


def main():
    c1, r1, t1 = plaquinha(0.0, "MOLDURA")
    c2, r2, t2 = plaquinha(W + GAP, "PORTA")
    nome = os.path.join(AQUI, "teste-dobradica.dxf")
    perfil.escreve(nome, c1 + c2, rebaixos=r1 + r2, rotulos=t1 + t2)
    print("%s | %.1f x %.1f mm | furos a %.2f entre centros" % (nome, 2 * W + GAP, H, PASSO))


if __name__ == "__main__":
    main()
