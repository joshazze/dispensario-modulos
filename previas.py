#!/usr/bin/env python3
"""Gera as figuras do README em docs/: vista dos modulos e previa de cada cama.

As previas usam a mesma prancha do gerador, com traco grosso e o codigo de cada
peca, para dar pra ler numa tela. Nao sao arquivo de corte.

    python3 previas.py
"""
import json
import math
import os

import gerador

DOCS = os.path.join(gerador.BASE, "docs")
FUNDO = "#ffffff"
CORTE = "#d62828"
TEXTO = "#5f6368"
MOLDURA = "#9aa0a6"


def _num(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


def _path(poly, flip):
    pts = [flip(x, y) for x, y in poly]
    return "M" + "L".join("%s,%s" % (_num(x), _num(y)) for x, y in pts) + "Z"


def svg_cama(cortes, textos, largura, altura, traco):
    flip = lambda x, y: (x, altura - y)
    margem = 20.0
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s %s %s %s">'
        % (_num(-margem), _num(-margem), _num(largura + 2 * margem), _num(altura + 2 * margem)),
        '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>'
        % (_num(-margem), _num(-margem), _num(largura + 2 * margem), _num(altura + 2 * margem), FUNDO),
        '<rect x="0" y="0" width="%s" height="%s" fill="none" stroke="%s" '
        'stroke-width="%s" stroke-dasharray="%s %s"/>'
        % (_num(largura), _num(altura), MOLDURA, _num(traco), _num(6 * traco), _num(4 * traco)),
        '<g fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round">' % (CORTE, _num(traco)),
    ]
    out += ['<path d="%s"/>' % _path(p, flip) for p in cortes]
    out.append('</g>')
    out.append('<g fill="%s" font-family="Helvetica, Arial, sans-serif" font-weight="700">' % TEXTO)
    for t in textos:
        x, y = flip(t["x"], t["y"])
        out.append('<text x="%s" y="%s" font-size="%s">%s</text>'
                   % (_num(x), _num(y), _num(t["tamanho"]), t["texto"]))
    out.append('</g></svg>')
    return "\n".join(out)


def previas_do_modulo(spec, filtro, prefixo, so_prancha=False):
    """Uma figura por cama, ou uma prancha compacta quando a peca nao cabe na mesa."""
    if so_prancha:
        # sem camas: as pecas maiores que a mesa ganhariam uma cama cada e a
        # figura viraria uma torre de 11 m. Aqui so importa ver as pecas.
        spec = json.loads(json.dumps(spec))
        spec["folha"]["bloco_mm"] = None
    groups = gerador.make_groups(spec)
    cortes, grav, largura, altura, _ = gerador.build_sheet(spec, groups, filtro)
    textos = [g for g in grav if g["tipo"] == "texto"]
    gerados = []
    if so_prancha:
        textos = [dict(t, tamanho=t["tamanho"] * 2.5) for t in textos]
        x0 = min(x for p in cortes for x, _ in p)
        y0 = min(y for p in cortes for _, y in p)
        x1 = max(x for p in cortes for x, _ in p)
        y1 = max(y for p in cortes for _, y in p)
        locais = [[(x - x0, y - y0) for x, y in p] for p in cortes]
        tl = [dict(t, x=t["x"] - x0, y=t["y"] - y0) for t in textos]
        nome = "%s-prancha.svg" % prefixo
        with open(os.path.join(DOCS, nome), "w", encoding="utf-8") as f:
            f.write(svg_cama(locais, tl, x1 - x0, y1 - y0, traco=5.0))
        return [nome]
    for indice, (ox, oy, bw, bh, _) in enumerate(gerador.build_sheet.molduras, 1):
        dentro = [p for p in cortes
                  if all(ox - 1e-6 <= x <= ox + bw + 1e-6
                         and oy - 1e-6 <= y <= oy + bh + 1e-6 for x, y in p)]
        x0 = min(x for p in dentro for x, _ in p)
        y0 = min(y for p in dentro for _, y in p)
        locais = [[(x - x0, y - y0) for x, y in p] for p in dentro]
        tl = [dict(t, x=t["x"] - x0, y=t["y"] - y0) for t in textos
              if ox <= t["x"] <= ox + bw and oy <= t["y"] <= oy + bh]
        nome = "%s-cama%d.svg" % (prefixo, indice)
        with open(os.path.join(DOCS, nome), "w", encoding="utf-8") as f:
            f.write(svg_cama(locais, tl, bw, bh, traco=2.2))
        gerados.append(nome)
    return gerados


# ------------------------------------------------------------- vista isometrica

C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))


def iso(x, y, z):
    """x largura, y altura, z profundidade (para tras). Tela com y para baixo."""
    return ((x + z) * C30, (x - z) * S30 - y)


def poli_iso(pts, cor, contorno, largura_traco):
    d = "M" + "L".join("%s,%s" % (_num(a), _num(b)) for a, b in pts) + "Z"
    return ('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>'
            % (d, cor, contorno, _num(largura_traco)))


def caixa(ox, w, h, d, aberturas_frente, rotulo, medida):
    """Frente no plano z = 0 virada para a esquerda, lateral direita em x = w."""
    def p(x, y, z):
        a, b = iso(x + ox, y, z)
        return (a, b)
    out = []
    frente = [p(0, 0, 0), p(w, 0, 0), p(w, h, 0), p(0, h, 0)]
    lado = [p(w, 0, 0), p(w, 0, d), p(w, h, d), p(w, h, 0)]
    topo = [p(0, h, 0), p(w, h, 0), p(w, h, d), p(0, h, d)]
    out.append(poli_iso(frente, "#f3ede4", "#3c4043", 3))
    out.append(poli_iso(lado, "#e2d8c9", "#3c4043", 3))
    out.append(poli_iso(topo, "#faf7f2", "#3c4043", 3))
    for forma in aberturas_frente:
        out.append(poli_iso([p(x, y, 0) for x, y in forma], "#ffffff", CORTE, 3))
    # rotulo debaixo do vertice mais baixo da caixa, fora das faces
    base = p(w, 0, 0)
    out.append('<text x="%s" y="%s" text-anchor="middle" font-size="46" font-weight="700">%s</text>'
               % (_num(base[0]), _num(base[1] + 80), rotulo))
    out.append('<text x="%s" y="%s" text-anchor="middle" font-size="34" fill="%s">%s</text>'
               % (_num(base[0]), _num(base[1] + 125), TEXTO, medida))
    return out


def vista(spec):
    mods = {m["codigo"]: m for m in spec["modulos"]}
    bio, arm = mods["B"], mods["A"]
    formas_bio = []
    for ab in bio["aberturas"]:
        if ab.get("face") == 6 and ab["tipo"] == "janela":
            formas_bio += gerador.abertura_polys(ab, bio["largura_externa_mm"], bio["altura_externa_mm"])
    formas_arm = []
    for ab in arm["aberturas"]:
        if ab.get("face") == 6 and ab["tipo"] == "pilula":
            formas_arm += gerador.abertura_polys(ab, arm["largura_externa_mm"], arm["altura_externa_mm"])
    partes = []
    partes += caixa(0, arm["largura_externa_mm"], arm["altura_externa_mm"],
                    arm["profundidade_externa_mm"], formas_arm, "Armario",
                    "%s x %s x %s mm" % tuple(_num(arm[k]) for k in
                                              ("largura_externa_mm", "altura_externa_mm", "profundidade_externa_mm")))
    partes += caixa(arm["largura_externa_mm"] + 600, bio["largura_externa_mm"], bio["altura_externa_mm"],
                    bio["profundidade_externa_mm"], formas_bio, "Biometrico",
                    "%s x %s x %s mm" % tuple(_num(bio[k]) for k in
                                              ("largura_externa_mm", "altura_externa_mm", "profundidade_externa_mm")))
    # enquadramento a partir dos pontos desenhados
    xs, ys = [], []
    for m, ox in ((arm, 0), (bio, arm["largura_externa_mm"] + 600)):
        for x in (0, m["largura_externa_mm"]):
            for y in (0, m["altura_externa_mm"]):
                for z in (0, m["profundidade_externa_mm"]):
                    a, b = iso(x + ox, y, z)
                    xs.append(a)
                    ys.append(b)
    x0, x1 = min(xs) - 160, max(xs) + 60
    y0, y1 = min(ys) - 60, max(ys) + 180
    cab = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s %s %s %s" '
           'font-family="Helvetica, Arial, sans-serif" fill="#202124">'
           % (_num(x0), _num(y0), _num(x1 - x0), _num(y1 - y0)))
    fundo = ('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>'
             % (_num(x0), _num(y0), _num(x1 - x0), _num(y1 - y0), FUNDO))
    return "\n".join([cab, fundo] + partes + ["</svg>"])


def main():
    os.makedirs(DOCS, exist_ok=True)
    with open(gerador.SPEC_PATH, encoding="utf-8") as f:
        spec = json.load(f)
    feitos = ["vista-modulos.svg"]
    with open(os.path.join(DOCS, feitos[0]), "w", encoding="utf-8") as f:
        f.write(vista(spec))
    # a previa mostra o codigo de cada peca, mesmo com a gravacao desligada
    feitos += previas_do_modulo(spec, "^B", "biometrico")
    feitos += previas_do_modulo(spec, "^A", "armario", so_prancha=True)
    for nome in feitos:
        print("docs/" + nome)


if __name__ == "__main__":
    main()
