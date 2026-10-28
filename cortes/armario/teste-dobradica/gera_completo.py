"""Regua da dobradica borboleta inteira, aberta, numa placa so (28/10/2026).

Fixo: a dobradica aberta (15,40 ao longo do pino x 11,61, abas de 0,48), furos
de 2,33 a 10,03 entre centros (7,70 pelas bordas de dentro) e a 1,20 da borda de
fora de cada aba. Varia: a folga do bolso por lado, 0,10 a 0,40, gravada embaixo
de cada um. O pino, mais grosso que a aba, passa num rasgo vazado no meio
(fechada ela mede 1,77; rasgo de 2,0).

    PYTHONPATH=~/Projetos/dispensario-modulos python3 gera_completo.py
"""
import os

from laser import fonte, geom, perfil
from laser.geom import circle_pts

AQUI = os.path.dirname(os.path.abspath(__file__))
COMP, LARG = 15.40, 11.61
ABA = LARG / 2.0
FURO, PASSO, BORDA_FURO = 2.33, 7.70 + 2.33, 1.20
RAIO = 2.0
PINO_MM = 2.0   # dobradica fechada mede 1,77 (rolo do pino) + folga
FOLGAS = [0.10, 0.20, 0.30, 0.40]
PASSO_X, MARGEM, ALT = 30.0, 8.0, 2.5


def main():
    w = 2 * MARGEM + COMP + PASSO_X * (len(FOLGAS) - 1)
    h = 2 * MARGEM + LARG + 1.0 + 2.0 + ALT
    cy = h - MARGEM - LARG / 2.0
    cortes, bolsos, rot = [], [], []
    for i, f in enumerate(FOLGAS):
        cx = MARGEM + COMP / 2.0 + PASSO_X * i
        bolsos.append(geom.rrect(cx - COMP / 2.0 - f, cy - LARG / 2.0 - f, COMP + 2 * f, LARG + 2 * f, RAIO))
        cortes.append(geom.rrect(cx - COMP / 2.0 - f, cy - PINO_MM / 2.0, COMP + 2 * f, PINO_MM, 0.0))
        fy = ABA - BORDA_FURO - FURO / 2.0        # do eixo ate o centro do furo
        for sy in (-1, 1):
            for sx in (-1, 1):
                cortes.append(circle_pts(cx + sx * PASSO / 2.0, cy + sy * fy, FURO))
        texto = ("%.2f" % f).replace(".", ",")
        tw = fonte.largura_texto(texto, ALT)
        rot.extend(fonte.rotulo(texto, cx - tw / 2.0, cy - LARG / 2.0 - 1.0 - 2.0 - ALT, ALT))
    cortes.append(geom.rrect(0.0, 0.0, w, h, 2.0))
    nome = os.path.join(AQUI, "teste-dobradica-completa.dxf")
    perfil.escreve(nome, cortes, rebaixos=bolsos, rotulos=rot)
    print("%s | %.1f x %.1f mm | %d variantes" % (nome, w, h, len(FOLGAS)))


if __name__ == "__main__":
    main()
