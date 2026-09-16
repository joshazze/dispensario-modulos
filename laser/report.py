"""Relatorio de folha: o que torna 'economico' uma medida em vez de impressao.

Uma margem de nesting travada em 4 mm ja deixou peca fora de um vazio onde ela
cabia, e a perda ficou escondida ate alguem tropecar nela. Baixar pra 3
derrubou a folha 36%. Numero que ninguem imprime e numero que ninguem corta.
"""
import math

from . import geom

# mm/s por material e espessura, so pra ordem de grandeza do tempo. Nao e
# cotacao: sem maquina registrada, isso e chute honesto.
VELOCIDADE_PADRAO = 15.0


def folha(pecas, folha=None, velocidade=VELOCIDADE_PADRAO):
    """Metricas da chapa inteira."""
    if not pecas:
        return dict(pecas=0, area_pecas_m2=0.0, area_folha_m2=0.0,
                    aproveitamento=0.0, perimetro_mm=0.0, tempo_min=0.0,
                    folha=None, ponte_minima=None)

    area_pecas = 0.0
    perim = 0.0
    pontes = []
    x1 = y1 = -float("inf")
    x0 = y0 = float("inf")
    for p in pecas:
        c = p["contorno"]
        area_pecas += geom.area(c)
        perim += geom.perimetro(c)
        for f in p.get("feicoes", []):
            perim += geom.perimetro(f)
            area_pecas -= geom.area(f)
        bx0, by0, bx1, by1 = geom.bbox(c)
        x0, y0 = min(x0, bx0), min(y0, by0)
        x1, y1 = max(x1, bx1), max(y1, by1)
        if p.get("ponte_minima") is not None:
            pontes.append((p["ponte_minima"], p.get("nome", "?")))

    if folha is None:
        folha = (x1 - x0, y1 - y0)
    area_folha = folha[0] * folha[1]

    return dict(
        pecas=len(pecas),
        folha=folha,
        area_pecas_m2=area_pecas / 1e6,
        area_folha_m2=area_folha / 1e6,
        aproveitamento=(area_pecas / area_folha) if area_folha else 0.0,
        perimetro_mm=perim,
        tempo_min=perim / velocidade / 60.0 if velocidade else 0.0,
        ponte_minima=min(pontes) if pontes else None,
    )


def texto(r, material=None):
    if not r["pecas"]:
        return "relatorio: nenhuma peca"
    L = [
        "folha           %.1f x %.1f mm  (%.4f m2)" % (r["folha"][0], r["folha"][1],
                                                       r["area_folha_m2"]),
        "pecas           %d" % r["pecas"],
        "area util       %.4f m2" % r["area_pecas_m2"],
        "aproveitamento  %.1f%%" % (100.0 * r["aproveitamento"]),
        "perimetro       %.0f mm de corte" % r["perimetro_mm"],
        "tempo estimado  %.1f min a %.0f mm/s" % (r["tempo_min"], VELOCIDADE_PADRAO),
    ]
    if r["ponte_minima"]:
        L.append("ponte mais fina %.2f mm  (peca '%s')" % r["ponte_minima"])
    if material is not None and getattr(material, "estimado", False):
        L.append("")
        L.append("AVISO  " + material.aviso)
    return "\n".join(L)
