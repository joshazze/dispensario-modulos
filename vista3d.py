#!/usr/bin/env python3
"""Simulacao 3D do armario em PDF, com varios angulos de vista.

Monta as mesmas pecas que o gerador manda pra maquina: cada contorno 2D e
extrudado na espessura da lamina e posto no lugar. Mundo: X largura (esq ->
dir), Y altura, Z profundidade com o fundo em Z = 0 e a frente em Z = D. O lado
de cada face (giro de u e v) sai do teste de encaixe: os dedos de duas faces
vizinhas tem que preencher o canto sem sobrepor. Peca que invade outra para o
script antes do PDF.

A cena e desenhada com three.js (third_party/three) no Chrome headless, o
mesmo que imprime os PDFs de corte.

    python3 vista3d.py            # docs/armario-3d.pdf e a capa em .png
    python3 vista3d.py --abrir    # e abre no visualizador
"""
import datetime
import functools
import http.server
import shutil
import subprocess
import threading
import time
import itertools
import json
import os
import sys

import numpy as np

import gerador

HTML = os.path.join(gerador.BASE, "vista3d", "render.html")
THREE = os.path.join(gerador.BASE, "third_party", "three", "three.module.js")
SAIDA = os.path.join(gerador.BASE, "docs", "armario-3d.pdf")
CAPA = os.path.join(gerador.BASE, "docs", "armario-3d.png")
TRABALHO = os.path.join(gerador.TMP, "vista3d")


def dentro(poly, px, py):
    """Ray casting vetorizado."""
    p = np.asarray(poly)
    x0, y0 = p[:, 0], p[:, 1]
    x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
    px = px[:, None]
    py = py[:, None]
    cruza = ((y0 > py) != (y1 > py)) & (px < (x1 - x0) * (py - y0) / (y1 - y0 + 1e-12) + x0)
    return cruza.sum(axis=1) % 2 == 1


class Face:
    def __init__(self, nome, outline, w, h, t, base):
        self.nome, self.outline, self.w, self.h, self.t = nome, outline, w, h, t
        self.base = base  # fu, fv -> (origem, eu, ev, ew)

    def frame(self, fu, fv):
        o, eu, ev, ew = (np.array(a, float) for a in self.base)
        if fu:
            o, eu = o + eu * self.w, -eu
        if fv:
            o, ev = o + ev * self.h, -ev
        return o, eu, ev, ew

    def bbox(self, fu, fv):
        o, eu, ev, ew = self.frame(fu, fv)
        cantos = [o + a * eu * self.w + b * ev * self.h + c * ew * self.t
                  for a in (0, 1) for b in (0, 1) for c in (0, 1)]
        c = np.array(cantos)
        return c.min(0), c.max(0)

    def contem(self, pts, fu, fv):
        o, eu, ev, ew = self.frame(fu, fv)
        d = pts - o
        u, v, wv = d @ eu, d @ ev, d @ ew
        ok = (wv > 0) & (wv < self.t) & (u > 0) & (u < self.w) & (v > 0) & (v < self.h)
        res = np.zeros(len(pts), bool)
        if ok.any():
            res[ok] = dentro(self.outline, u[ok], v[ok])
        return res


def faces_da_caixa(defs, W, H, D, t, o):
    """Base sem giro de cada face, vista de fora. o = canto (X, Y, Z) da caixa."""
    ox, oy, oz = o
    X, Y, Z = np.eye(3)
    base = {
        "fundo": ((ox + W, oy, oz), -X, Y, Z),
        "lateral esquerda": ((ox, oy, oz), Z, Y, X),
        "piso": ((ox, oy, oz), X, Z, Y),
        "lateral direita": ((ox + W, oy, oz + D), -Z, Y, -X),
        "teto": ((ox, oy + H, oz), X, Z, -Y),
        "tampa frontal": ((ox, oy, oz + D), X, Y, -Z),
    }
    return [Face(nome, outline, w, h, t, base[nome]) for nome, outline, w, h in defs]


def amostra_canto(a, b, giro_a, giro_b, passo=1.0):
    lo = np.maximum(a.bbox(*giro_a)[0], b.bbox(*giro_b)[0])
    hi = np.minimum(a.bbox(*giro_a)[1], b.bbox(*giro_b)[1])
    if np.any(hi - lo < 1.0):
        return None
    eixos = [np.arange(l + passo / 2, h, passo) for l, h in zip(lo, hi)]
    g = np.stack(np.meshgrid(*eixos, indexing="ij"), -1).reshape(-1, 3)
    ia, ib = a.contem(g, *giro_a), b.contem(g, *giro_b)
    return int((ia & ib).sum()), int((~ia & ~ib).sum()), len(g)


def escolhe_giros(faces):
    giros = list(itertools.product((False, True), repeat=2))
    pares = {}
    for i, j in itertools.combinations(range(len(faces)), 2):
        for gi in giros:
            for gj in giros:
                r = amostra_canto(faces[i], faces[j], gi, gj)
                if r is not None:
                    pares[(i, j, gi, gj)] = r[0] + r[1]
    melhor = None
    for combo in itertools.product(giros, repeat=len(faces)):
        if combo[0] != (False, False):
            continue  # o fundo fica como referencia
        custo = sum(c for (i, j, gi, gj), c in pares.items() if combo[i] == gi and combo[j] == gj)
        # empate: prefere a convencao de vista de fora (sem giro)
        chave = (custo, sum(a + b for a, b in combo))
        if melhor is None or chave < melhor[0]:
            melhor = (chave, combo)
    return melhor[1], melhor[0][0]


def relatorio_cantos(faces, combo, rotulo):
    total_sob = total_vazio = 0
    for i, j in itertools.combinations(range(len(faces)), 2):
        r = amostra_canto(faces[i], faces[j], combo[i], combo[j], passo=0.5)
        if r:
            total_sob += r[0]
            total_vazio += r[1]
            print("  %s %-17s x %-17s sobrepoe %5d  vazio %5d  de %d"
                  % (rotulo, faces[i].nome, faces[j].nome, r[0], r[1], r[2]))
    return total_sob, total_vazio


def ring(poly):
    p = [list(map(float, q)) for q in poly]
    if p[0] == p[-1]:
        p = p[:-1]
    return p


def peca(code, grupo, outline, furos, frame, z0, t, w, h):
    o, eu, ev, ew = frame
    o = o + ew * z0
    return {
        "code": code, "grupo": grupo,
        "outline": ring(outline), "furos": [ring(f) for f in furos],
        "t": t, "o": o.tolist(), "eu": eu.tolist(), "ev": ev.tolist(), "ew": ew.tolist(),
        "w": w, "h": h,
    }


def modelo():
    with open(gerador.SPEC_PATH, encoding="utf-8") as f:
        spec = json.load(f)
    mods = {m["codigo"]: m for m in spec["modulos"]}
    A, N = mods["A"], mods["AN"]
    lam = spec["espessura_mm"]
    W, H, D = A["largura_externa_mm"], A["altura_externa_mm"], A["profundidade_externa_mm"]
    tA = gerador.espessura_do_modulo(A, spec)
    tN = gerador.espessura_do_modulo(N, spec)
    nW, nH, nD = N["largura_externa_mm"], N["altura_externa_mm"], N["profundidade_externa_mm"]
    # nicho centrado na casca (os rasgos dos dois lados sao simetricos e batem assim)
    nO = ((W - nW) / 2.0, (H - nH) / 2.0, (D - nD) / 2.0)

    defsA = gerador.boxmaker_panel_defs(A, spec)
    defsN = gerador.boxmaker_panel_defs(N, spec)
    facesA = faces_da_caixa(defsA, W, H, D, tA, (0, 0, 0))
    facesN = faces_da_caixa(defsN, nW, nH, nD, tN, nO)

    comboA, custoA = escolhe_giros(facesA)
    comboN, custoN = escolhe_giros(facesN)
    print("giros casca:", comboA, "custo", custoA)
    print("giros nicho:", comboN, "custo", custoN)
    sa = relatorio_cantos(facesA, comboA, "A ")
    sn = relatorio_cantos(facesN, comboN, "AN")

    groups = {g["pieces"][0]["code"][:-1] if g["pieces"][0]["code"][-1] in "IE" else g["pieces"][0]["code"]: g
              for g in gerador.make_groups(spec)}
    pecas = []
    for n, face in enumerate(facesA, 1):
        g = groups["A%d" % n]
        fr = face.frame(*comboA[n - 1])
        for p in g["pieces"]:
            # externa por fora (w de 0 a 3), interna por dentro (3 a 6)
            z0 = 0.0 if p["code"].endswith("E") else lam
            pecas.append(peca(p["code"], "casca-" + p["code"][-1], p["outline"], p["fasteners"],
                              fr, z0, lam, face.w, face.h))
    for n, face in enumerate(facesN, 1):
        g = groups["AN%d" % n]
        fr = face.frame(*comboN[n - 1])
        p = g["pieces"][0]
        pecas.append(peca(p["code"], "nicho", p["outline"], p["fasteners"], fr, 0.0, tN, face.w, face.h))

    extras = {e["code"]: e for e in gerador.pecas_extras(spec)}
    X, Y, Z = np.eye(3)
    esp = [e for c, e in sorted(extras.items()) if c.startswith("AE")]
    esp.sort(key=lambda e: int(e["code"][2:]))
    cfg = [x for x in spec["pecas_extras"] if x["codigo"] == "AE1"][0]
    comp = cfg["comprimento_mm"]
    z_ini = D / 2.0 - comp / 2.0
    lugares = []
    for y in (250.0, 500.0, 750.0):  # lateral esquerda e direita, placa deitada
        lugares.append(((lam, y - lam / 2.0, z_ini), Z, X, Y))
        lugares.append(((W - lam, y + lam / 2.0, z_ini), Z, -X, -Y))
    lugares = lugares[0::2] + lugares[1::2]
    for x in (250.0, 500.0):  # piso, placa em pe
        lugares.append(((x - lam / 2.0, lam, z_ini), Z, Y, X))
    for x in (250.0, 500.0):  # teto
        lugares.append(((x + lam / 2.0, H - lam, z_ini), Z, -Y, -X))
    for e, (o, eu, ev, ew) in zip(esp, lugares):
        pecas.append(peca(e["code"], "espacador", e["polys"][0], e["polys"][1:],
                          (np.array(o), eu, ev, ew), 0.0, lam, e["w"], e["h"]))

    # tampas dos passa-fios por fora das laterais, centradas no furo
    pf = spec["passa_fio"]
    r = pf["tampa_diametro_mm"] / 2.0
    zc_esq = 90.0  # x da face 2 conta a partir do fundo
    zc_dir = D - 160.0  # face 4 vista de fora: x conta a partir da frente
    for code, xo, zc, ew in (("ATR", 0.0, zc_esq, -X), ("ATF", W, zc_dir, X)):
        e = extras[code]
        o = np.array([xo, pf["altura_centro_mm"] - r, zc - r if ew[0] < 0 else zc + r])
        eu = Z if ew[0] < 0 else -Z
        pecas.append(peca(code, "tampa", e["polys"][0], e["polys"][1:], (o, eu, Y, ew), 0.0, lam, e["w"], e["h"]))

    sob = sa[0] + sn[0] + sum(invasoes(pecas))
    if sob:
        raise SystemExit("ERRO pecas se sobrepoem (%d amostras de 0,5 mm): o PDF nao sai" % sob)
    dados = {"data": datetime.date.today().strftime("%d/%m/%Y"), "W": W, "H": H, "D": D, "nicho": {"o": nO, "w": nW, "h": nH, "d": nD},
             "pecas": pecas,
             "encaixe": {"casca": {"sobrepoe": sa[0], "vazio": sa[1]},
                         "nicho": {"sobrepoe": sn[0], "vazio": sn[1]}}}
    print(len(pecas), "pecas:", " ".join(p["code"] for p in pecas))
    return dados


def _contem(p, pts):
    o, eu, ev, ew = (np.array(p[k]) for k in ("o", "eu", "ev", "ew"))
    d = pts - o
    u, v, w = d @ eu, d @ ev, d @ ew
    ok = (w > 0) & (w < p["t"])
    res = np.zeros(len(pts), bool)
    if ok.any():
        r = dentro(p["outline"], u[ok], v[ok])
        for f in p["furos"]:
            r &= ~dentro(f, u[ok], v[ok])
        res[ok] = r
    return res


def _amostras(p, passo=0.5):
    o, eu, ev, ew = (np.array(p[k]) for k in ("o", "eu", "ev", "ew"))
    xs = [q[0] for q in p["outline"]]
    ys = [q[1] for q in p["outline"]]
    U, V, T = np.meshgrid(np.arange(min(xs) + passo / 2, max(xs), passo),
                          np.arange(min(ys) + passo / 2, max(ys), passo),
                          np.arange(passo / 2, p["t"], passo), indexing="ij")
    U, V, T = U.ravel(), V.ravel(), T.ravel()
    ins = dentro(p["outline"], U, V)
    for f in p["furos"]:
        ins &= ~dentro(f, U, V)
    return o + np.outer(U[ins], eu) + np.outer(V[ins], ev) + np.outer(T[ins], ew)


def invasoes(pecas):
    """Espacadores e tampas contra as paredes: aba tem que cair dentro do rasgo."""
    soltas = [p for p in pecas if p["grupo"] in ("espacador", "tampa")]
    paredes = [p for p in pecas if p["grupo"] not in ("espacador", "tampa")]
    for s in soltas:
        pts = _amostras(s)
        for q in paredes:
            n = int(_contem(q, pts).sum())
            if n:
                print("  %s invade %s: %d amostras" % (s["code"], q["code"], n))
            yield n


class _Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def imprime(dados, saida):
    """Serve a pagina em localhost (fetch nao funciona em file://) e imprime pelo Chrome."""
    chrome = gerador.acha_chrome()
    if chrome is None:
        raise SystemExit("Chrome nao encontrado (defina CHROME=<caminho>)")
    os.makedirs(TRABALHO, exist_ok=True)
    shutil.copy(HTML, os.path.join(TRABALHO, "render.html"))
    shutil.copy(THREE, os.path.join(TRABALHO, "three.module.js"))
    with open(os.path.join(TRABALHO, "modelo.json"), "w") as f:
        json.dump(dados, f)
    srv = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(_Silencioso, directory=TRABALHO))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    tmp_pdf = os.path.join(TRABALHO, "saida.pdf")
    if os.path.exists(tmp_pdf):
        os.remove(tmp_pdf)
    proc = subprocess.Popen([
        chrome, "--headless=new", "--no-pdf-header-footer",
        "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
        "--run-all-compositor-stages-before-draw", "--virtual-time-budget=120000",
        "--user-data-dir=" + os.path.join(TRABALHO, "chrome"),
        "--print-to-pdf=" + tmp_pdf,
        "http://127.0.0.1:%d/render.html" % srv.server_address[1],
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # o Chrome escreve o PDF e as vezes nao sai sozinho: espera o arquivo parar de crescer
    ultimo, limite = -1, time.time() + 240
    try:
        while time.time() < limite:
            time.sleep(2)
            if proc.poll() is not None and os.path.exists(tmp_pdf):
                break
            if os.path.exists(tmp_pdf):
                tam = os.path.getsize(tmp_pdf)
                if tam > 0 and tam == ultimo:
                    break
                ultimo = tam
        else:
            raise SystemExit("ERRO o Chrome nao gerou o PDF em 4 minutos")
    finally:
        if proc.poll() is None:
            proc.kill()
        srv.shutdown()
    shutil.move(tmp_pdf, saida)
    print(os.path.relpath(saida, gerador.BASE))


def capa_png(pdf, png):
    """Capa do PDF em PNG para o README. Precisa do pdftoppm (poppler); sem ele, pula."""
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm is None:
        print("AVISO pdftoppm nao encontrado: capa do README nao atualizada")
        return
    subprocess.run([pdftoppm, "-png", "-r", "110", "-f", "1", "-l", "1", "-singlefile",
                    pdf, os.path.splitext(png)[0]], check=True)
    print(os.path.relpath(png, gerador.BASE))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    imprime(modelo(), SAIDA)
    capa_png(SAIDA, CAPA)
    if "--abrir" in argv:
        subprocess.run(["open", SAIDA])


if __name__ == "__main__":
    main()
