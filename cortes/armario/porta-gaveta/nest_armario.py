"""Nesting das peças do armário em layouts de até 1000 x 1000 mm (eCNC L-1210).

Lê os DXF originais, separa as peças pela caixa de cada uma, reposiciona e
escreve um DXF por chapa (canto de baixo à esquerda em 0,0, sem moldura) e um
HTML de prévia para virar PDF.
"""
import math, sys, pathlib

SRC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
GAP = 5.0
LIM = 1000.0


def ler(fn):
    L = [l.strip() for l in open(fn, encoding="utf-8").read().splitlines()]
    ents, cur = [], None
    for c, v in zip(L[::2], L[1::2]):
        if c == "0":
            cur = {"t": v}
            ents.append(cur)
        elif cur is not None:
            cur.setdefault(c, v)
    out = []
    for e in ents:
        if e["t"] == "LINE":
            out.append(("L", e["8"], float(e["10"]), float(e["20"]), float(e["11"]), float(e["21"])))
        elif e["t"] == "CIRCLE":
            out.append(("C", e["8"], float(e["10"]), float(e["20"]), float(e["40"])))
    return out


def meio(e):
    return ((e[2] + e[4]) / 2, (e[3] + e[5]) / 2) if e[0] == "L" else (e[2], e[3])


def separa(ents, caixas):
    pecas = {k: [] for k in caixas}
    for e in ents:
        x, y = meio(e)
        dono = [k for k, (x0, y0, x1, y1) in caixas.items() if x0 - .01 <= x <= x1 + .01 and y0 - .01 <= y <= y1 + .01]
        assert len(dono) == 1, (e, dono)
        pecas[dono[0]].append(e)
    return pecas


def bbox(ents):
    xs, ys = [], []
    for e in ents:
        if e[0] == "L":
            xs += [e[2], e[4]]; ys += [e[3], e[5]]
        else:
            xs += [e[2] - e[4], e[2] + e[4]]; ys += [e[3] - e[4], e[3] + e[4]]
    return min(xs), min(ys), max(xs), max(ys)


def gira90(ents):
    # anti-horário: (x, y) -> (-y, x)
    r = []
    for e in ents:
        if e[0] == "L":
            r.append(("L", e[1], -e[3], e[2], -e[5], e[4]))
        else:
            r.append(("C", e[1], -e[3], e[2], e[4]))
    return r


def poe(ents, x, y):
    x0, y0, _, _ = bbox(ents)
    dx, dy = x - x0, y - y0
    return [("L", e[1], e[2] + dx, e[3] + dy, e[4] + dx, e[5] + dy) if e[0] == "L"
            else ("C", e[1], e[2] + dx, e[3] + dy, e[4]) for e in ents]


def escreve_dxf(fn, ents):
    f = lambda v: f"{round(v, 4):g}"
    s = ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
         "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", "2",
         "0", "LAYER", "2", "CORTE", "70", "0", "62", "1", "6", "CONTINUOUS",
         "0", "LAYER", "2", "MARCACAO", "70", "0", "62", "5", "6", "CONTINUOUS",
         "0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    for e in ents:
        if e[0] == "L":
            s += ["0", "LINE", "8", e[1], "10", f(e[2]), "20", f(e[3]), "30", "0", "11", f(e[4]), "21", f(e[5]), "31", "0"]
        else:
            s += ["0", "CIRCLE", "8", e[1], "10", f(e[2]), "20", f(e[3]), "30", "0", "40", f(e[4])]
    s += ["0", "ENDSEC", "0", "EOF"]
    pathlib.Path(fn).write_text("\n".join(s) + "\n", encoding="utf-8")


def cantos(ents, T=5.0, borda=(0, 0, 880, 880)):
    """Troca cada linha de MARCACAO por dois traços de T mm nas pontas; o que cai na borda de corte some."""
    r = []
    for e in ents:
        if e[0] != "L" or e[1] != "MARCACAO":
            r.append(e)
            continue
        _, lay, x1, y1, x2, y2 = e
        if (x1 == x2 and x1 in (borda[0], borda[2])) or (y1 == y2 and y1 in (borda[1], borda[3])):
            continue
        n = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / n, (y2 - y1) / n
        t = min(T, n / 2)
        r.append(("L", lay, x1, y1, x1 + ux * t, y1 + uy * t))
        r.append(("L", lay, x2 - ux * t, y2 - uy * t, x2, y2))
    return r


porta = cantos(ler(SRC / "porta-corte.dxf"))
gav = separa(ler(SRC / "gaveta-pecas-corte.dxf"), {
    "fundo A": (10, 10, 325.2, 465.2),
    "lateral B": (10, 475.2, 473, 670.2),
    "base do batente": (500, 10, 540, 80),
    "encaixe 1": (550, 10, 610, 60),
    "encaixe 2": (620, 10, 680, 60),
    "encaixe 3": (690, 10, 750, 60),
})

# Chapa 1: porta + peças pequenas na sobra de 115 mm à direita
c1 = [("porta (frente)", poe(porta, 0, 0), False)]
x = 880 + GAP
y = 0.0
for nome in ["base do batente", "encaixe 1", "encaixe 2", "encaixe 3"]:
    p = poe(gav[nome], x, y)
    c1.append((nome, p, False))
    y = bbox(p)[3] + GAP

# Chapa 2: fundo A em pé + lateral B girada 90° ao lado
fundo = poe(gav["fundo A"], 0, 0)
lat = poe(gira90(gav["lateral B"]), bbox(fundo)[2] + GAP, 0)
c2 = [("fundo A", fundo, False), ("lateral B", lat, True)]

paginas = []
for i, chapa in enumerate([c1, c2], 1):
    tudo = [e for _, p, _ in chapa for e in p]
    x0, y0, x1, y1 = bbox(tudo)
    assert x0 >= 0 and y0 >= 0 and x1 <= LIM and y1 <= LIM, (i, x1, y1)
    # sem sobreposição entre caixas
    bxs = [bbox(p) for _, p, _ in chapa]
    for a in range(len(bxs)):
        for b in range(a + 1, len(bxs)):
            A, B = bxs[a], bxs[b]
            assert A[2] + GAP - .01 <= B[0] or B[2] + GAP - .01 <= A[0] or A[3] + GAP - .01 <= B[1] or B[3] + GAP - .01 <= A[1], (i, a, b)
    escreve_dxf(OUT / f"chapa-{i}.dxf", tudo)
    pecas_area = 0
    paginas.append((i, chapa, x1, y1))
    print(f"chapa-{i}: {x1:.1f} x {y1:.1f} mm, {len(tudo)} entidades, peças: " + ", ".join(n + (" (girada 90°)" if g else "") for n, _, g in chapa))


def svg(chapa, W, H):
    M = 30
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-M} {-M} {W + 2*M} {H + 2*M}" style="width:100%;max-height:150mm">',
         f'<rect x="0" y="0" width="{W:.1f}" height="{H:.1f}" fill="#f6efe2" stroke="#999" stroke-width="0.6" stroke-dasharray="6 4"/>']
    for nome, p, g in chapa:
        for e in p:
            cor = "#d0021b" if e[1] == "CORTE" else "#1f5fbf"
            if e[0] == "L":
                s.append(f'<line x1="{e[2]:.2f}" y1="{H - e[3]:.2f}" x2="{e[4]:.2f}" y2="{H - e[5]:.2f}" stroke="{cor}" stroke-width="1.2"/>')
            else:
                s.append(f'<circle cx="{e[2]:.2f}" cy="{H - e[3]:.2f}" r="{e[4]:.2f}" fill="none" stroke="{cor}" stroke-width="1.2"/>')
        bx = bbox(p)
        cx, cy = (bx[0] + bx[2]) / 2, H - (bx[1] + bx[3]) / 2
        fs = 9 if bx[2] - bx[0] < 100 else 22
        rot = f' transform="rotate(-90 {cx:.1f} {cy:.1f})"' if (bx[2] - bx[0]) < 100 else ""
        txt = nome + (" (girada 90°)" if g else "")
        s.append(f'<text x="{cx:.1f}" y="{cy:.1f}" font-size="{fs}" text-anchor="middle" dominant-baseline="middle" fill="#333" font-family="Helvetica"{rot}>{txt}</text>')
    s.append(f'<text x="{W/2:.1f}" y="{H + 22:.1f}" font-size="18" text-anchor="middle" font-family="Helvetica">{W:.1f} mm</text>')
    s.append(f'<text x="{W + 22:.1f}" y="{H/2:.1f}" font-size="18" text-anchor="middle" font-family="Helvetica" transform="rotate(90 {W + 22:.1f} {H/2:.1f})">{H:.1f} mm</text>')
    s.append("</svg>")
    return "\n".join(s)


html = ['<!doctype html><meta charset="utf-8"><style>@page{size:A4 landscape;margin:12mm}body{font-family:Helvetica;margin:0}section{page-break-after:always}h1{font-size:16pt;margin:0 0 2mm}p{font-size:10pt;margin:0 0 4mm;color:#444}</style>']
for i, chapa, W, H in paginas:
    lista = ", ".join(n + (" (girada 90°)" if g else "") for n, _, g in chapa)
    html.append(f"<section><h1>Chapa {i}: {W:.0f} x {H:.0f} mm, MDF 3 mm</h1><p>{lista}. Vermelho corta, azul marca. Folga de {GAP:g} mm entre peças, canto de baixo à esquerda em (0, 0).</p>{svg(chapa, W, H)}</section>")
(OUT / "previa.html").write_text("\n".join(html), encoding="utf-8")
