#!/usr/bin/env python3
"""Figuras do docs/aprendizados.md: cada decisao desenhada com as medidas da spec.

Nao sao arquivo de corte. As geometrias saem do mesmo gerador (vao do LCD,
furos do teclado, espacador), entao a figura muda junto com a spec.

    python3 figuras.py
"""
import json
import math
import os

import gerador
from laser import geom

PASTA = os.path.join(gerador.BASE, "docs", "figuras")
FUNDO = "#ffffff"
TINTA = "#202124"
CINZA = "#5f6368"
CLARO = "#bdc1c6"
CORTE = "#d62828"
NOVO = "#1a73e8"
MDF = "#d9bf96"
MDF_ESCURO = "#b8956a"
NICHO = "#ecdcbc"
ESPACADOR = "#7a8fa6"
FONTE = 'font-family="Helvetica, Arial, sans-serif"'


def _n(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def svg(w, h, corpo):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" width="%s" height="%s" %s>'
            '<rect width="100%%" height="100%%" fill="%s"/>%s</svg>'
            % (_n(w), _n(h), _n(w), _n(h), FONTE, FUNDO, "".join(corpo)))


def caminho(pts, tx, **est):
    d = "M" + "L".join("%s,%s" % (_n(a), _n(b)) for a, b in (tx(x, y) for x, y in pts)) + "Z"
    return '<path d="%s" %s/>' % (d, _est(est))


def ret(x, y, w, h, **est):
    return '<rect x="%s" y="%s" width="%s" height="%s" %s/>' % (_n(x), _n(y), _n(w), _n(h), _est(est))


def linha(x1, y1, x2, y2, **est):
    return '<line x1="%s" y1="%s" x2="%s" y2="%s" %s/>' % (_n(x1), _n(y1), _n(x2), _n(y2), _est(est))


def texto(x, y, t, tam=13, cor=CINZA, peso=400, ancora="start"):
    return ('<text x="%s" y="%s" font-size="%s" fill="%s" font-weight="%d" text-anchor="%s">%s</text>'
            % (_n(x), _n(y), _n(tam), cor, peso, ancora, t))


def _est(est):
    traduz = {"fill": "fill", "stroke": "stroke", "sw": "stroke-width", "dash": "stroke-dasharray",
              "op": "opacity", "fop": "fill-opacity", "join": "stroke-linejoin"}
    est.setdefault("fill", "none")
    return " ".join('%s="%s"' % (traduz[k], v) for k, v in est.items())


def cota_h(x1, x2, y, rotulo, cor=TINTA, tam=12):
    """Cota horizontal com traco de chamada nas pontas."""
    out = [linha(x1, y, x2, y, stroke=cor, sw=1),
           linha(x1, y - 5, x1, y + 5, stroke=cor, sw=1),
           linha(x2, y - 5, x2, y + 5, stroke=cor, sw=1),
           texto((x1 + x2) / 2, y - 7, rotulo, tam, cor, 600, "middle")]
    return "".join(out)


def cota_v(x, y1, y2, rotulo, cor=TINTA, tam=12, lado=1):
    out = [linha(x, y1, x, y2, stroke=cor, sw=1),
           linha(x - 5, y1, x + 5, y1, stroke=cor, sw=1),
           linha(x - 5, y2, x + 5, y2, stroke=cor, sw=1),
           texto(x + 8 * lado, (y1 + y2) / 2 + 4, rotulo, tam, cor, 600, "start" if lado > 0 else "end")]
    return "".join(out)


def grava(nome, conteudo):
    os.makedirs(PASTA, exist_ok=True)
    with open(os.path.join(PASTA, nome), "w", encoding="utf-8") as f:
        f.write(conteudo)
    print("docs/figuras/" + nome)


# ------------------------------------------------------------------ a mesa manda

def fig_mesa(spec):
    """Antes e depois contra a mesa de 1150 x 1000 e a carga de 1000 x 1000."""
    mw, mh = spec["folha"]["mesa_mm"]
    cw, ch = spec["folha"]["bloco_mm"]
    mods = {m["codigo"]: m for m in spec["modulos"]}
    arm, bio = mods["A"], mods["B"]
    k = 0.24
    painel_w = 1560 * k + 60
    corpo = []

    def mesa(ox, oy):
        return [ret(ox, oy, mw * k, mh * k, fill="#f1f3f4", stroke=CLARO, sw=1.5, dash="6 4"),
                ret(ox, oy, cw * k, ch * k, fill="#e8f0fe", stroke=NOVO, sw=1, op=0.9)]

    A, H = arm["largura_externa_mm"], arm["altura_externa_mm"]
    B = bio["largura_externa_mm"]
    ox, oy = 30, 70
    y_bio = oy + 1260 * k + 24
    fim = y_bio + 250 * k
    # antes: armario de 1260 x 1500 e biometrico de 1500 de altura, deitados
    corpo.append(texto(ox, 34, "Antes: painéis de 1500 mm de altura", 16, TINTA, 700))
    corpo += mesa(ox, oy)
    corpo.append(ret(ox, oy, 1500 * k, 1260 * k, fill=CORTE, fop=0.06, stroke=CORTE, sw=2, dash="8 5"))
    corpo.append(texto(ox + 1500 * k / 2, oy + 1260 * k - 12, "frente do armário 1500 x 1260", 12, CORTE, 700, "middle"))
    corpo.append(ret(ox, y_bio, 1500 * k, 250 * k, fill=CORTE, fop=0.06, stroke=CORTE, sw=2, dash="8 5"))
    corpo.append(texto(ox + 1500 * k / 2, y_bio + 250 * k / 2 + 4,
                       "lateral do biométrico 1500 x 250", 12, CORTE, 700, "middle"))
    corpo.append(texto(ox, fim + 24, "nenhum dos dois entra na mesa sem emenda", 13, CORTE, 600))

    # depois: 1000 de altura, os paineis grandes deitados dentro da carga
    ox = 30 + painel_w
    corpo.append(texto(ox, 34, "Depois: 1000 mm de altura", 16, TINTA, 700))
    corpo += mesa(ox, oy)
    corpo.append(ret(ox, oy, H * k, A * k, fill=MDF, fop=0.6, stroke=TINTA, sw=1.5))
    corpo.append(texto(ox + H * k / 2, oy + A * k / 2 + 4,
                       "frente do armário %d x %d" % (H, A), 12, TINTA, 700, "middle"))
    corpo += mesa(ox, y_bio)
    corpo.append(ret(ox, y_bio, H * k, B * k, fill=MDF, fop=0.6, stroke=TINTA, sw=1.5))
    corpo.append(texto(ox + H * k / 2, y_bio + B * k / 2 + 4,
                       "lateral do biométrico %d x %d" % (H, B), 12, TINTA, 700, "middle"))
    corpo.append(texto(ox, fim + 24 + (mh - 250) * k, "cada painel cabe numa carga, deitado", 13, NOVO, 600))
    # legenda
    ly = fim + 24 + (mh - 250) * k + 34
    corpo.append(ret(30, ly - 11, 14, 14, fill="#e8f0fe", stroke=NOVO, sw=1))
    corpo.append(texto(52, ly, "carga de %d x %d (o que vai pra máquina de uma vez)" % (cw, ch), 12))
    corpo.append(ret(400, ly - 11, 14, 14, fill="#f1f3f4", stroke=CLARO, sw=1.5, dash="4 3"))
    corpo.append(texto(422, ly, "mesa de %d x %d da eCNC L-1210" % (mw, mh), 12))
    grava("mesa-antes-depois.svg", svg(30 + 2 * painel_w, ly + 20, corpo))


# ------------------------------------------------------------------ vao do LCD

def _bsp(spec):
    return [p for p in spec["pecas_extras"] if p["codigo"] == "BSP"][0]


def _ab(peca, nome):
    return [a for a in peca["aberturas"] if a["nome"] == nome][0]


def fig_lcd(spec):
    """Datasheet, foto da peca e o vao que foi cortado, sobre os mesmos furos."""
    bsp = _bsp(spec)
    w, h = bsp["largura_mm"], bsp["altura_mm"]
    vao = gerador.abertura_polys(_ab(bsp, "moldura do lcd 1602A"), w, h)[0]
    furos = gerador.abertura_polys(_ab(bsp, "parafusos do lcd 1602A"), w, h)
    x0, y0, x1, y1 = geom.bbox(vao)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    k = 7.0
    W, Hs = 760, 500
    ox, oy = W / 2, 190
    tx = lambda x, y: (ox + (x - cx) * k, oy - (y - cy) * k)
    corpo = [texto(30, 34, "Vão do LCD 1602A: o datasheet contra a peça na mão", 16, TINTA, 700)]

    def moldura(lw, lh, cor, dash, rot, n):
        a, b = tx(-lw / 2 + cx, lh / 2 + cy)
        ly = oy + 15.5 * k + 80 + 22 * n
        return [ret(a, b, lw * k, lh * k, stroke=cor, sw=2, dash=dash),
                linha(70, ly - 4, 100, ly - 4, stroke=cor, sw=2, dash=dash),
                texto(110, ly, rot, 12, cor, 600)]

    corpo.append(caminho(vao, tx, fill=CORTE, fop=0.08, stroke=CORTE, sw=2.5, join="round"))
    ly2 = oy + 15.5 * k + 80 + 44
    corpo.append(linha(70, ly2 - 4, 100, ly2 - 4, stroke=CORTE, sw=2.5))
    corpo.append(texto(110, ly2, "vão cortado na BSP", 12, CORTE, 600))
    corpo += moldura(71.3, 26.8, CINZA, "6 4", "moldura nos datasheets (Tinsharp, EONE, HJ1602A): 71,3 x 26,8 ou menor", 0)
    corpo += moldura(76.5, 25.0, NOVO, "3 3", "moldura medida na foto da peça do grupo: ~76,5 x 25", 1)
    for f in furos:
        corpo.append(caminho(f, tx, fill="#ffffff", stroke=TINTA, sw=1.5))
    fx0, fy0, fx1, fy1 = geom.bbox(furos[0] + furos[-1])
    a = tx(cx - 37.5, 0)[0]
    b = tx(cx + 37.5, 0)[0]
    corpo.append(cota_h(a, b, oy + 15.5 * k + 38, "furos 75 x 31 (iguais em todas as fontes)"))
    l, r = tx(x0, 0)[0], tx(x1, 0)[0]
    corpo.append(cota_h(l, r, oy - 13 * k - 34, "vão cortado: 78 x 26 + lingueta de 10 x 1 nas pontas", CORTE))
    corpo.append(texto(30, Hs - 22, "A moldura do clone passa ~1 mm da linha dos furos em cada ponta; "
                                    "a lingueta é a borda branca do backlight.", 12))
    grava("lcd-datasheet-vs-peca.svg", svg(W, Hs, corpo))


# ------------------------------------------------------------------ ponte do teclado

def fig_ponte(spec):
    """Canto do vao do teclado: 0,95 mm de MDF entre o furo e o recorte."""
    bsp = _bsp(spec)
    w, h = bsp["largura_mm"], bsp["altura_mm"]
    ab = _ab(bsp, "bloco do teclado 4x4")
    vao = gerador.abertura_polys(ab, w, h)[0]
    furos = gerador.abertura_polys(_ab(bsp, "parafusos do teclado 4x4"), w, h)
    x0, y0, x1, y1 = geom.bbox(vao)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    furo = max(furos, key=lambda f: (geom.bbox(f)[0], geom.bbox(f)[1]))
    fx = (geom.bbox(furo)[0] + geom.bbox(furo)[2]) / 2
    fy = (geom.bbox(furo)[1] + geom.bbox(furo)[3]) / 2
    rf = (geom.bbox(furo)[2] - geom.bbox(furo)[0]) / 2
    r = ab["raio_mm"]
    # centro do arco do canto e o ponto mais proximo de cada lado
    ax, ay = x1 - r, y1 - r
    d = math.hypot(fx - ax, fy - ay)
    ux, uy = (fx - ax) / d, (fy - ay) / d
    p_vao = (ax + ux * r, ay + uy * r)
    p_furo = (fx - ux * rf, fy - uy * rf)
    ponte = d - r - rf

    W, Hs = 820, 470
    k_g, k_z = 4.2, 34.0
    corpo = [texto(30, 34, "Teclado 4x4: a ponte que ficou abaixo do piso", 16, TINTA, 700)]
    # esquerda: vao inteiro
    ogx, ogy = 190, 250
    tg = lambda x, y: (ogx + (x - cx) * k_g, ogy - (y - cy) * k_g)
    corpo.append(caminho(vao, tg, fill=CORTE, fop=0.08, stroke=CORTE, sw=2, join="round"))
    for f in furos:
        corpo.append(caminho(f, tg, fill="#ffffff", stroke=TINTA, sw=1.5))
    zx, zy = tg(fx, fy)
    corpo.append('<circle cx="%s" cy="%s" r="22" fill="none" stroke="%s" stroke-width="1.5"/>'
                 % (_n(zx - 6), _n(zy + 6), NOVO))
    corpo.append(texto(ogx, ogy + 60.5 * k_g / 2 + 40, "recorte 60,5 x 57,5 R4,25, furos ⌀2,4 em 60 x 59",
                       12, CINZA, 400, "middle"))
    # direita: zoom no canto
    ozx, ozy = 590, 245
    mx, my = (fx + ax) / 2, (fy + ay) / 2
    tz = lambda x, y: (ozx + (x - mx) * k_z, ozy - (y - my) * k_z)
    corpo.append('<clipPath id="z"><circle cx="%s" cy="%s" r="175"/></clipPath>' % (_n(ozx), _n(ozy)))
    corpo.append('<g clip-path="url(#z)">')
    corpo.append('<circle cx="%s" cy="%s" r="175" fill="%s" fill-opacity="0.45"/>' % (_n(ozx), _n(ozy), MDF))
    corpo.append(caminho(vao, tz, fill="#ffffff", stroke=CORTE, sw=2.5, join="round"))
    corpo.append(caminho(furo, tz, fill="#ffffff", stroke=TINTA, sw=2))
    a, b = tz(*p_vao), tz(*p_furo)
    corpo.append(linha(a[0], a[1], b[0], b[1], stroke=NOVO, sw=2.5))
    corpo.append('</g>')
    corpo.append('<circle cx="%s" cy="%s" r="175" fill="none" stroke="%s" stroke-width="1.5"/>'
                 % (_n(ozx), _n(ozy), NOVO))
    corpo.append(linha(zx + 14, zy - 8, ozx - 175, ozy, stroke=NOVO, sw=1, dash="4 3"))
    corpo.append(texto((a[0] + b[0]) / 2 + 14, (a[1] + b[1]) / 2 - 6,
                       ("%.2f mm" % ponte).replace(".", ","), 16, NOVO, 700))
    corpo.append(texto(ozx, ozy + 205, "piso do projeto: 1,5 mm (metade da espessura)", 12, CINZA, 400, "middle"))
    corpo.append(texto(ozx, ozy + 223, "exceção declarada na spec da BSP, só nela", 12, CORTE, 600, "middle"))
    grava("teclado-ponte.svg", svg(W, Hs, corpo))


# ------------------------------------------------------------------ circulo fantasma

def fig_circulo(spec):
    """O retangulo arredondado que o DXF levou como circunferencia."""
    bsp = _bsp(spec)
    w, h = bsp["largura_mm"], bsp["altura_mm"]
    r_fantasma = math.hypot(w / 2, h / 2)
    k = 0.42
    W, Hs = 780, 2 * r_fantasma * k + 110
    ox, oy = 200, Hs / 2 + 14
    corpo = [texto(30, 34, "O sub-painel que virou círculo", 16, TINTA, 700)]
    corpo.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="2" stroke-dasharray="7 5"/>'
                 % (_n(ox), _n(oy), _n(r_fantasma * k), CINZA))
    corpo.append(ret(ox - w / 2 * k, oy - h / 2 * k, w * k, h * k, fill=MDF, fop=0.5, stroke=CORTE, sw=2.5))
    for sx in (-1, 1):
        for sy in (-1, 1):
            corpo.append('<circle cx="%s" cy="%s" r="4" fill="%s"/>'
                         % (_n(ox + sx * w / 2 * k), _n(oy + sy * h / 2 * k), TINTA))
    corpo.append(linha(ox, oy, ox + w / 2 * k, oy - h / 2 * k, stroke=TINTA, sw=1, dash="3 3"))
    tx = 410
    corpo.append(texto(tx, oy - 70, "desenhado: BSP 240 x 560, cantos R3", 13, CORTE, 700))
    corpo.append(texto(tx, oy - 50, "o que foi pro DXF: círculo de raio ~%d" % round(r_fantasma), 13, CINZA, 700))
    corpo.append(texto(tx, oy - 10, "O detector de círculo media a distância", 12))
    corpo.append(texto(tx, oy + 8, "dos pontos ao centro, com 1% de folga.", 12))
    corpo.append(texto(tx, oy + 26, "Retângulo de canto curto só tem pontos", 12))
    corpo.append(texto(tx, oy + 44, "nos quatro cantos, todos à meia diagonal:", 12))
    corpo.append(texto(tx, oy + 62, "passou no teste.", 12))
    grava("bsp-virou-circulo.svg", svg(W, Hs, corpo))


# ------------------------------------------------------------------ folga de 61 mm

def fig_folga(spec):
    """Corte horizontal no canto da frente: casca, folga, nicho e o espacador."""
    mods = {m["codigo"]: m for m in spec["modulos"]}
    arm, nic = mods["A"], mods["AN"]
    t = spec["espessura_mm"]
    tA = gerador.espessura_do_modulo(arm, spec)
    D = arm["profundidade_externa_mm"]
    mold = arm["moldura_frontal_mm"]
    folga = (arm["largura_externa_mm"] - nic["largura_externa_mm"]) / 2 - tA
    ae = [p for p in spec["pecas_extras"] if p["codigo"] == "AE1"][0]
    comp = ae["comprimento_mm"]
    k = 1.9
    W, Hs = 720, 70 + 250 * 1.9 + 130
    ox, oy = 90, 70
    # X para a direita (de fora para dentro), Z para baixo (do fundo para a frente)
    tx = lambda x, z: (ox + x * k, oy + z * k)
    X = 150
    corpo = [texto(30, 34, "Corte a 500 mm de altura, lateral esquerda vista de cima", 16, TINTA, 700)]

    def bloco(x0, z0, x1, z1, cor, **e):
        a, b = tx(x0, z0)
        return ret(a, b, (x1 - x0) * k, (z1 - z0) * k, fill=cor, stroke=TINTA, sw=1, **e)

    # casca: lateral (2 laminas), fundo e moldura da frente
    corpo.append(bloco(0, 0, t, D, MDF_ESCURO))
    corpo.append(bloco(t, tA, tA, D - tA, MDF))
    corpo.append(bloco(tA, 0, X, t, MDF_ESCURO))
    corpo.append(bloco(tA, t, X, tA, MDF))
    corpo.append(bloco(tA, D - t, mold, D, MDF_ESCURO))
    corpo.append(bloco(tA, D - tA, mold, D - t, MDF))
    # nicho
    nx = tA + folga
    z0n = (D - nic["profundidade_externa_mm"]) / 2
    corpo.append(bloco(nx, z0n, nx + t, D - z0n, NICHO))
    corpo.append(bloco(nx, z0n, X, z0n + t, NICHO))
    # espacador deitado entre as duas caixas, abas nos rasgos
    zs = D / 2 - comp / 2
    corpo.append(caminho([(tA, zs), (nx, zs), (nx, zs + comp), (tA, zs + comp)], tx,
                         fill=ESPACADOR, fop=0.85, stroke=TINTA, sw=1))
    meia_aba = ae["aba_largura_mm"] / 2
    for c in ae["aba_centros_mm"]:
        for xa in ((t, tA), (nx, nx + t)):
            corpo.append(bloco(xa[0], zs + c - meia_aba, xa[1], zs + c + meia_aba, ESPACADOR, op=0.95))
    # cotas
    yb = oy + D * k + 26
    corpo.append(cota_h(tx(0, 0)[0], tx(tA, 0)[0], yb, _n(tA), tam=11))
    corpo.append(cota_h(tx(tA, 0)[0], tx(nx, 0)[0], yb, "%s folga" % _n(folga), NOVO))
    corpo.append(cota_h(tx(nx, 0)[0], tx(nx + t, 0)[0], yb + 24, _n(t), tam=11))
    corpo.append(cota_h(tx(0, 0)[0], tx(mold, 0)[0], yb + 56, "moldura de %s = %s + %s + %s"
                        % (_n(mold), _n(tA), _n(folga), _n(t))))
    lx = tx(X, 0)[0] + 30
    corpo.append(texto(lx, oy + 40, "fundo", 13, TINTA, 600))
    corpo.append(texto(lx, oy + D * k - 4, "frente (moldura)", 13, TINTA, 600))
    corpo.append(texto(lx, tx(0, D / 2)[1] - 10, "espaçador AE1 (azul): as abas", 13, ESPACADOR, 700))
    corpo.append(texto(lx, tx(0, D / 2)[1] + 8, "atravessam o nicho e entram só", 13, ESPACADOR, 700))
    corpo.append(texto(lx, tx(0, D / 2)[1] + 26, "na lâmina interna da casca", 13, ESPACADOR, 700))
    corpo.append(texto(lx, tx(0, D / 2)[1] + 56, "por fora a lateral fica lisa", 12))
    corpo.append(texto(lx, tx(0, D / 2)[1] + 74, "os fios correm na folga", 12))
    corpo.append(texto(tx(0, 0)[0] - 10, tx(0, D / 2)[1], "casca", 13, TINTA, 600, "end"))
    corpo.append(texto(tx(nx + t, 0)[0] + 8, tx(0, z0n)[1] + 40, "nicho", 13, TINTA, 600))
    grava("armario-folga-61.svg", svg(W, Hs, corpo))


def main():
    with open(gerador.SPEC_PATH, encoding="utf-8") as f:
        spec = json.load(f)
    fig_mesa(spec)
    fig_lcd(spec)
    fig_ponte(spec)
    fig_circulo(spec)
    fig_folga(spec)


if __name__ == "__main__":
    main()
