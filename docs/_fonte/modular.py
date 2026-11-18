"""Figuras da modularidade: 1 bio + 1 a 4 arm, cada arm com um de 4 miolos, e o indice das gavetas.
Elevacao frontal em escala (mm), sem porta. Grava docs/site/modular/*.svg (e PNG pro deck com --png DIR).

    python3 docs/_fonte/modular.py
"""
import itertools, pathlib

BIO_W, ARM_W, H = 250.0, 750.0, 1000.0
NICHO_W, NICHO_H = 704.4, 954.4
COLS, GAV_H = 5, 88.0
GAP = 0.0  # modulos encostados

C = dict(mdf="#c8a57a", mdf_esc="#a9875e", fundo="#5b4632", gaveta="#dcbf94",
         ripa="#b8956a", tela="#24313a", tecla="#e9e4da", linha="#3b2d20", etq="#f3ecdf")

TIPOS = {
    "G": ("gavetas em cima", ["g"] * 3 + ["v"] * 3),
    "B": ("gavetas embaixo", ["v"] * 3 + ["g"] * 3),
    "A": ("só nichos altos", ["a"] * 3),
    "T": ("só gavetas", ["g"] * 10),
}


def linhas_mm(seq):
    ng = seq.count("g"); nv = len(seq) - ng
    hg = GAV_H if nv else NICHO_H / ng
    hv = (NICHO_H - ng * hg) / nv if nv else 0
    return [hg if s == "g" else hv for s in seq]


def arm(x, tipo):
    o = [f'<rect x="{x}" y="0" width="{ARM_W}" height="{H}" fill="{C["mdf"]}" stroke="{C["linha"]}" stroke-width="3"/>']
    nx, ny = x + (ARM_W - NICHO_W) / 2, (H - NICHO_H) / 2
    o.append(f'<rect x="{nx}" y="{ny}" width="{NICHO_W}" height="{NICHO_H}" fill="{C["fundo"]}"/>')
    seq = TIPOS[tipo][1]; hs = linhas_mm(seq)
    cw = NICHO_W / COLS
    y = ny
    for s, h in zip(seq, hs):
        for c in range(COLS):
            cx = nx + c * cw
            if s == "g":
                o.append(f'<rect x="{cx+2.5}" y="{y+2.5}" width="{cw-5}" height="{h-5}" rx="2" fill="{C["gaveta"]}" stroke="{C["mdf_esc"]}" stroke-width="1.5"/>')
                mx = cx + cw / 2
                o.append(f'<rect x="{mx-25}" y="{y+h*0.30}" width="50" height="{min(25,h*0.3)}" fill="{C["etq"]}" stroke="{C["mdf_esc"]}" stroke-width="1"/>')
                o.append(f'<path d="M{mx-12},{y+2.5} a12,12 0 0 0 24,0 z" fill="{C["fundo"]}"/>')
            else:
                o.append(f'<rect x="{cx+3}" y="{y+3}" width="{cw-6}" height="{h-6}" fill="{C["fundo"]}" stroke="#4a3828" stroke-width="1"/>')
        y += h
        o.append(f'<rect x="{nx}" y="{y-1.5}" width="{NICHO_W}" height="3" fill="{C["ripa"]}"/>')
    for c in range(1, COLS):
        o.append(f'<rect x="{nx+c*cw-1.5}" y="{ny}" width="3" height="{NICHO_H}" fill="{C["ripa"]}"/>')
    return "".join(o)


def bio(x):
    o = [f'<rect x="{x}" y="0" width="{BIO_W}" height="{H}" fill="{C["mdf"]}" stroke="{C["linha"]}" stroke-width="3"/>']
    # janela 180 x 500, centro a 650 do piso do modulo; BSP 240 x 560 atras
    jx, jy = x + 35, H - 900
    o.append(f'<rect x="{jx}" y="{jy}" width="180" height="500" rx="3" fill="{C["mdf_esc"]}"/>')
    bx, by0 = x + 5, 370.0  # canto da BSP (y do piso)
    Y = lambda yb: H - (by0 + yb)
    o.append(f'<rect x="{bx+120-40}" y="{Y(400)-18}" width="80" height="36" rx="2" fill="#2c6b3f"/>')
    o.append(f'<rect x="{bx+120-36}" y="{Y(400)-12}" width="72" height="24" fill="#7fd08a"/>')
    o.append(f'<circle cx="{bx+50}" cy="{Y(445)}" r="4" fill="#5fd0ff"/>')
    kx, ky = bx + 84 - 30, Y(140) - 29
    o.append(f'<rect x="{kx}" y="{ky}" width="60" height="58" rx="3" fill="{C["tela"]}"/>')
    for i, j in itertools.product(range(4), range(4)):
        o.append(f'<rect x="{kx+4+i*14}" y="{ky+4+j*13.5}" width="10" height="10" rx="1.5" fill="{C["tecla"]}"/>')
    o.append(f'<rect x="{bx+166-14}" y="{Y(140)-16}" width="28" height="32" rx="4" fill="{C["tela"]}"/>')
    o.append(f'<rect x="{bx+166-10}" y="{Y(140)-9}" width="20" height="18" rx="2" fill="#8fa3b0"/>')
    return "".join(o)


def montagem(pos_bio, tipos, escala, rotulo=True):
    """pos_bio: indice do bio na fileira (0..len(tipos))."""
    ordem = list(tipos); ordem.insert(pos_bio, "BIO")
    larg = sum(BIO_W if t == "BIO" else ARM_W for t in ordem)
    x, o = 0.0, []
    for t in ordem:
        o.append(bio(x) if t == "BIO" else arm(x, t))
        x += BIO_W if t == "BIO" else ARM_W
    pad = 30
    w, h = (larg + 2 * pad) * escala, (H + 2 * pad) * escala
    nome = " + ".join("bio" if t == "BIO" else t for t in ordem)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
           f'viewBox="{-pad} {-pad} {larg+2*pad} {H+2*pad}">{"".join(o)}</svg>')
    cap = f'<figcaption>{nome}</figcaption>' if rotulo else ""
    return f'<figure>{svg}{cap}</figure>'




def fileira(pos_bio, tipos, pad=30):
    ordem = list(tipos); ordem.insert(pos_bio, "BIO")
    larg = sum(BIO_W if t == "BIO" else ARM_W for t in ordem)
    x, o = 0.0, []
    for t in ordem:
        o.append(bio(x) if t == "BIO" else arm(x, t)); x += BIO_W if t == "BIO" else ARM_W
    nome = " + ".join("bio" if t == "BIO" else t for t in ordem)
    return larg, "".join(o), nome


def grade(combos, cols, titulo, cel_w=None, legenda=True):
    """Varias fileiras numa grade, cada uma reduzida pra caber numa celula."""
    pad, gap, cap = 40, 60, 60
    larg_max = max(fileira(p, t)[0] for p, t in combos)
    cel_w = cel_w or larg_max
    cel_h = H + cap
    rows = -(-len(combos) // cols)
    W = cols * cel_w + (cols - 1) * gap + 2 * pad
    Ht = rows * cel_h + (rows - 1) * gap + 2 * pad
    o = [f'<rect width="{W}" height="{Ht}" fill="#fbf8f2"/>']
    for i, (p, t) in enumerate(combos):
        r, c = divmod(i, cols)
        larg, g, nome = fileira(p, t)
        x0 = pad + c * (cel_w + gap) + (cel_w - larg) / 2
        y0 = pad + r * (cel_h + gap)
        o.append(f'<g transform="translate({x0},{y0})">{g}</g>')
        if legenda:
            o.append(f'<text x="{pad + c * (cel_w + gap) + cel_w / 2}" y="{y0 + H + 44}" font-size="34" text-anchor="middle" fill="#6b5a48" font-family="Avenir Next, Helvetica, sans-serif">{nome}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Ht}" width="{W/6:.0f}" height="{Ht/6:.0f}" role="img" aria-label="{titulo}">'
            + "".join(o) + "</svg>")


def indice_gaveta():
    """Vista de cima de uma gaveta com 5 divisorias: orelhas escalonadas D0..D5."""
    W, Hh = 900, 600
    o = [f'<rect width="{W}" height="{Hh}" fill="#fbf8f2"/>']
    gx, gy, gw, gd = 120, 70, 300, 440   # gaveta vista de cima: largura x profundidade (fundo em cima)
    o.append(f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gd}" fill="{C["gaveta"]}" stroke="{C["linha"]}" stroke-width="4"/>')
    o.append(f'<rect x="{gx-6}" y="{gy+gd}" width="{gw+12}" height="18" fill="{C["mdf_esc"]}"/>')
    o.append(f'<text x="{gx+gw/2}" y="{gy+gd+52}" font-size="22" text-anchor="middle" fill="#6b5a48" font-family="Avenir Next, Helvetica">frente (etiqueta "D")</text>')
    o.append(f'<text x="{gx+gw/2}" y="{gy-18}" font-size="22" text-anchor="middle" fill="#6b5a48" font-family="Avenir Next, Helvetica">fundo</text>')
    passo = gd / 6
    for k in range(6):
        y = gy + k * passo
        if k:
            o.append(f'<rect x="{gx}" y="{y-3}" width="{gw}" height="6" fill="#2c5d8a"/>')
        ox = gx + 30 + k * 44
        o.append(f'<circle cx="{ox}" cy="{y+4 if k else y+16}" r="18" fill="#f3ecdf" stroke="#2c5d8a" stroke-width="3"/>')
        o.append(f'<text x="{ox}" y="{(y+4 if k else y+16)+7}" font-size="17" font-weight="700" text-anchor="middle" fill="#2c5d8a" font-family="Avenir Next, Helvetica">D{k}</text>')
        o.append(f'<text x="{gx+gw+30}" y="{y+passo/2+8}" font-size="21" fill="#1f1a14" font-family="Avenir Next, Helvetica">D{k}: {["fundo da gaveta", "atrás da divisória 1", "atrás da divisória 2", "atrás da divisória 3", "atrás da divisória 4", "na frente, atrás da divisória 5"][k]}</text>')
    o.append(f'<text x="{gx+gw+30}" y="{gy+gd+80}" font-size="21" fill="#8a4b1f" font-weight="700" font-family="Avenir Next, Helvetica">D3 = gaveta D, compartimento 3</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Hh}" width="{W}" height="{Hh}" role="img" aria-label="Índice das gavetas, D0 a D5">' + "".join(o) + "</svg>"


def todas(n):
    return [(p, t) for t in itertools.product(TIPOS, repeat=n) for p in range(n + 1)]


def destaque(n):
    base = ["G", "B", "A", "T"]
    return [(0, tuple(["G"] * n)), (0, tuple(["A"] * n)), (n // 2, tuple(["G"] * n)),
            (n // 2, tuple((base * 2)[:n])), (0, tuple(["T"] + ["B"] * (n - 1))),
            (n, tuple(["A"] * (n - 1) + ["G"])), (n // 2, tuple(["A"] + ["T"] * (n - 2) + ["A"])),
            (1, tuple(["B"] * n))]


def main():
    import sys
    out = pathlib.Path(__file__).resolve().parent.parent / "site" / "modular"
    out.mkdir(parents=True, exist_ok=True)
    figs = {
        "miolos": grade([(0, (k,)) for k in TIPOS], 4, "Os quatro miolos do armário"),
        "n1": grade(todas(1), 4, "1 bio + 1 arm: as 8 montagens"),
        "n2": grade(todas(2), 4, "1 bio + 2 arm: as 48 montagens"),
        "n3": grade(destaque(3), 2, "1 bio + 3 arm: 8 das 256 montagens"),
        "n4": grade(destaque(4), 2, "1 bio + 4 arm: 8 das 1280 montagens"),
        "indice-gaveta": indice_gaveta(),
    }
    # sequencia de montagem pro deck: bio, bio+G, bio+G+G, ...
    seq = [(0, ()), (0, ("G",)), (0, ("G", "B")), (1, ("G", "A", "B")), (2, ("T", "G", "A", "B"))]
    for i, (p, t) in enumerate(seq):
        figs[f"monta-{i}"] = grade([(p, t)], 1, "montagem", cel_w=fileira(0, ("G",) * 4)[0], legenda=False)
    for k, v in figs.items():
        (out / f"{k}.svg").write_text(v, encoding="utf-8")
        print("ok", k, len(v))


if __name__ == "__main__":
    main()
