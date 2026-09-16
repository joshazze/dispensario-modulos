#!/usr/bin/env python3
"""Gera as chapas laminadas dos modulos do dispensario em SVG, DXF e PDF.

Cada painel acabado e formado pelo numero de laminas definido na spec.
As coordenadas e dimensoes de corte sao sempre expressas em milimetros.

    python3 gerador.py                                   # todas as pecas
    python3 gerador.py --filtro '^B' --nome biometrico/modulo-biometrico
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys

from laser import geom, materials, perfil, report
from laser.geom import circle_pts, hexagono


BASE = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = os.path.join(BASE, "specs", "modulos.json")
OUTPUT = os.path.join(BASE, "cortes")
TMP = os.path.join(BASE, "tmp")
BOXMAKER_DIR = os.path.join(BASE, "third_party", "tabbedboxmaker")
sys.path.insert(0, BOXMAKER_DIR)

from boxmaker_constants import BoxType, LayoutStyle, TabType
from boxmaker_core import BoxMakerCore


def acha_chrome():
    """Chrome ou Chromium para imprimir o PDF 1:1. Sem nenhum, o PDF e pulado."""
    candidatos = [
        os.environ.get("CHROME"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("chrome"),
    ]
    for caminho in candidatos:
        if caminho and os.path.exists(caminho):
            return caminho
    return None


def path_d(pts, flip):
    p = [flip(x, y) for x, y in pts]
    return "M " + " L ".join("%.4f,%.4f" % q for q in p) + " Z"


def clean_polygon(points):
    """Normaliza um contorno fechado e remove pontos consecutivos repetidos."""
    out = []
    for x, y in points:
        point = (0.0 if abs(x) < 1e-8 else x, 0.0 if abs(y) < 1e-8 else y)
        if not out or math.hypot(point[0] - out[-1][0], point[1] - out[-1][1]) > 1e-8:
            out.append(point)
    if out and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) > 1e-8:
        out.append(out[0])
    return out


def boxmaker_panel_defs(module, spec):
    """Gera as seis faces com a matriz de encaixes do TabbedBoxMaker.

    As dimensoes informadas sao externas. A espessura estrutural e a soma das
    laminas. O gerador de referencia cuida dos deslocamentos de canto,
    numero impar de divisoes e polaridade de cada uma das 24 arestas.
    """
    core = BoxMakerCore()
    core.set_parameters(
        length=module["largura_externa_mm"],
        width=module["profundidade_externa_mm"],
        height=module["altura_externa_mm"],
        thickness=spec["espessura_final_mm"],
        kerf=spec["kerf_mm"] if spec["compensar_kerf"] else 0.0,
        tab=spec["junta_dedo"]["passo_alvo_mm"],
        style=LayoutStyle.SEPARATED,
        boxtype=BoxType.FULL_BOX,
        tabtype=TabType.LASER,
        div_l=0,
        div_w=0,
        inside=0,
    )
    result = core.generate_box()
    paths = result["paths"]
    if len(paths) != 24:
        raise ValueError("esperadas 24 arestas para seis faces, recebidas %d" % len(paths))

    # Ordem produzida pelo layout diagramatico da biblioteca.
    face_names = ["fundo", "lateral esquerda", "piso", "lateral direita", "teto", "tampa frontal"]
    faces = []
    for index, title in enumerate(face_names):
        points = []
        for path in paths[index * 4:index * 4 + 4]:
            edge = core.extract_coords_from_path(path["data"])
            if points and edge and math.hypot(points[-1][0] - edge[0][0], points[-1][1] - edge[0][1]) < 1e-7:
                edge = edge[1:]
            points.extend(edge)
        min_x = min(x for x, _ in points)
        min_y = min(y for _, y in points)
        normalized = clean_polygon([(x - min_x, y - min_y) for x, y in points])
        width = max(x for x, _ in normalized)
        height = max(y for _, y in normalized)
        if title.startswith("lateral"):
            normalized = clean_polygon([(y, width - x) for x, y in normalized])
            width, height = height, width
        faces.append((title, normalized, width, height))
    return faces


def positions(length, end_margin, max_step):
    margin = min(end_margin, length / 4.0)
    usable = max(0.0, length - 2 * margin)
    intervals = max(1, int(math.ceil(usable / max_step)))
    return [margin + usable * i / intervals for i in range(intervals + 1)]


def panel_hole_centers(w, h, cfg):
    edge = cfg["margem_mm"]
    end = cfg["margem_extremidade_mm"]
    step = cfg["passo_maximo_mm"]
    centers = []
    centers += [(x, edge) for x in positions(w, end, step)]
    centers += [(x, h - edge) for x in positions(w, end, step)]
    centers += [(edge, y) for y in positions(h, end, step)]
    centers += [(w - edge, y) for y in positions(h, end, step)]
    if h >= 600:
        center_xs = [w / 2.0] if w < 500 else [w / 3.0, 2 * w / 3.0]
        center_ys = [h / 4.0, h / 2.0, 3 * h / 4.0]
    elif w >= 600:
        center_xs = [w / 4.0, w / 2.0, 3 * w / 4.0]
        center_ys = [h / 2.0]
    else:
        center_xs = [w / 2.0]
        center_ys = [h / 2.0]
    centers += [(x, y) for x in center_xs for y in center_ys]
    unique = []
    for q in centers:
        if all(math.hypot(q[0] - r[0], q[1] - r[1]) > cfg["diametro_furo_mm"] for r in unique):
            unique.append(q)
    return unique


def layer_fasteners(centers, layer, panel_height, cfg):
    """Furos e bolsos alternados por metade horizontal do painel.

    Na camada externa, a metade superior recebe furos circulares e a metade
    inferior recebe bolsos sextavados. A camada interna usa o inverso. Assim,
    pontos da mesma linha nunca misturam o sentido de montagem dos parafusos.
    """
    cuts = []
    for x, y in centers:
        if layer == "central":
            pocket = False
        elif layer == "externa":
            pocket = y <= panel_height / 2.0
        else:
            pocket = y > panel_height / 2.0
        if pocket:
            cuts.append(hexagono(x, y, cfg["bolso_porca_entre_faces_mm"]))
        else:
            cuts.append(circle_pts(x, y, cfg["diametro_furo_mm"]))
    return cuts


def layer_names(count):
    """Nomes e ordem das laminas, da face interna para a externa."""
    layouts = {
        2: ("interna", "externa"),
        3: ("interna", "central", "externa"),
    }
    if count not in layouts:
        raise ValueError("camadas_por_painel deve ser 2 ou 3")
    return layouts[count]


def moved(poly, dx, dy):
    return [(x + dx, y + dy) for x, y in poly]


def largura_texto(texto, tamanho):
    """Largura aproximada de Helvetica Bold em caixa alta: 0,62 em por caractere."""
    return 0.62 * tamanho * len(texto)


def posicao_rotulo(contorno, feicoes, tamanho, texto):
    """Centraliza o codigo na peca e foge das feicoes.

    Numa tampa o centro e justamente o furo do prensa-cabo, e o canto inferior
    esquerdo cai em cima de um parafuso: o rotulo precisa escolher lugar, nao
    ficar num offset fixo.
    """
    bx0, by0, bx1, by1 = geom.bbox(contorno)
    tw = largura_texto(texto, tamanho)
    th = tamanho
    cx = (bx0 + bx1) / 2.0
    largura, altura = bx1 - bx0, by1 - by0
    candidatos = [
        (cx, (by0 + by1) / 2.0 - th / 2.0),
        (cx, by0 + 0.22 * altura),
        (cx, by1 - 0.22 * altura),
        (cx, by0 + 0.035 * altura),                 # faixa de baixo da moldura
        (cx, by1 - 0.035 * altura - th),            # faixa de cima da moldura
        (bx0 + 0.27 * largura, (by0 + by1) / 2.0 - th / 2.0),
        (bx1 - 0.27 * largura, (by0 + by1) / 2.0 - th / 2.0),
        (bx0 + tw / 2.0 + 15.0, by0 + 15.0),
    ]
    caixas = [geom.bbox(f) for f in feicoes]
    for cxi, base in candidatos:
        caixa = (cxi - tw / 2.0, base, cxi + tw / 2.0, base + th)
        cantos = [(caixa[0], caixa[1]), (caixa[2], caixa[1]),
                  (caixa[2], caixa[3]), (caixa[0], caixa[3])]
        if not all(geom.ponto_dentro(q, contorno) for q in cantos):
            continue
        if any(caixa[0] < f[2] + 4.0 and f[0] < caixa[2] + 4.0
               and caixa[1] < f[3] + 4.0 and f[1] < caixa[3] + 4.0 for f in caixas):
            continue
        return caixa[0], base
    return bx0 + 20.0, by0 + 20.0


def _ancora(ab, w, h, espelhado):
    """Centro da feicao em mm, medido do canto inferior esquerdo do painel."""
    cx = w / 2.0 if ab.get("centro_x") else ab["x_mm"]
    cy = h / 2.0 if ab.get("centro_y") else ab["y_mm"]
    return (w - cx if espelhado else cx), cy


def gota(cx, cy, d_cabeca, d_haste, comprimento, seg=48):
    """Furo em gota (keyhole): circulo embaixo, fenda estreita subindo.

    O modulo desce sobre o parafuso ja chumbado: a cabeca passa pelo circulo e
    a haste sobe para a fenda, que por isso fica SEMPRE para cima. Inverter o
    sentido de um dos quatro furos e o erro que impede o modulo de assentar.
    """
    raio = d_cabeca / 2.0
    meia = d_haste / 2.0
    alt = math.sqrt(max(raio * raio - meia * meia, 0.0))
    t1 = math.atan2(alt, meia)
    t2 = math.atan2(alt, -meia) - 2.0 * math.pi
    pts = [(cx + raio * math.cos(t1 + (t2 - t1) * i / seg),
            cy + raio * math.sin(t1 + (t2 - t1) * i / seg)) for i in range(seg + 1)]
    pts.append((cx - meia, cy + comprimento))
    tampa = max(4, seg // 4)
    pts += [(cx + meia * math.cos(math.pi - math.pi * i / tampa),
             cy + comprimento + meia * math.sin(math.pi - math.pi * i / tampa))
            for i in range(tampa + 1)]
    pts.append((cx + meia, cy + alt))
    return pts


def _centros_repetidos(ab, cx, cy):
    """Centros das copias em linha, distribuidas em torno de (cx, cy).

    `eixo` diz em que direcao elas se repetem: "x" lado a lado, "y" empilhadas.
    """
    n = ab.get("repete", 1)
    passo = ab.get("passo_mm", 0.0)
    eixo = ab.get("eixo", "x")
    saida = []
    for i in range(n):
        d = (i - (n - 1) / 2.0) * passo
        saida.append((cx + d, cy) if eixo == "x" else (cx, cy + d))
    return saida


def abertura_polys(ab, w, h):
    """Uma abertura da spec vira os poligonos de corte dela, ja posicionados.

    `x_mm` e `y_mm` sao o CENTRO da feicao. `espelhado` repete a feicao no lado
    oposto do painel, que e como os dois passa-fios do fundo sao declarados uma
    vez so. Cada vao sai com UMA linha de corte: o contorno concentrico da folha
    dentro do vao faria a maquina cortar um anel de 4 mm de refugo junto.
    """
    saida = []
    for espelhado in ((False, True) if ab.get("espelhado") else (False,)):
        cx, cy = _ancora(ab, w, h, espelhado)
        tipo = ab["tipo"]
        if tipo == "pilula":
            lw, lh = ab["largura_mm"], ab["altura_mm"]
            for cxi, cyi in _centros_repetidos(ab, cx, cy):
                saida.append(geom.rrect(cxi - lw / 2.0, cyi - lh / 2.0,
                                        lw, lh, min(lw, lh) / 2.0))
        elif tipo == "gota":
            for cxi, cyi in _centros_repetidos(ab, cx, cy):
                saida.append(gota(cxi, cyi, ab["cabeca_mm"], ab["haste_mm"],
                                  ab["comprimento_mm"]))
        elif tipo == "rasgo":
            lw, lh = ab["largura_mm"], ab["altura_mm"]
            for cxi, cyi in _centros_repetidos(ab, cx, cy):
                saida.append(geom.rrect(cxi - lw / 2.0, cyi - lh / 2.0,
                                        lw, lh, ab.get("raio_mm", 0.0)))
        elif tipo == "furo":
            saida.append(circle_pts(cx, cy, ab["diametro_mm"]))
        elif tipo == "janela":
            lw = ab["largura_mm"]
            lh = ab["altura_mm"]
            saida.append(geom.rrect(cx - lw / 2.0, cy - lh / 2.0, lw, lh,
                                    ab.get("raio_mm", 0.0)))
        elif tipo == "parafusos":
            # grade de nx por ny sobre o retangulo passo_x por passo_y.
            # 2 x 2 e o quadrado de cantos; ny maior distribui a fixacao ao
            # longo do lado comprido, que e onde o vao entre parafusos abre.
            nx = ab.get("linhas_x", 2)
            ny = ab.get("linhas_y", 2)
            px, py = ab["passo_x_mm"], ab["passo_y_mm"]
            for i in range(nx):
                for j in range(ny):
                    fx = cx - px / 2.0 + (px * i / (nx - 1) if nx > 1 else px / 2.0)
                    fy = cy - py / 2.0 + (py * j / (ny - 1) if ny > 1 else py / 2.0)
                    saida.append(circle_pts(fx, fy, ab["diametro_mm"]))
        else:
            raise ValueError("tipo de abertura desconhecido: %s" % tipo)
    return saida


def vazios_da_face(dono, face_number, layer, w, h, margem):
    """Retangulos reaproveitaveis, derivados das janelas que existem de verdade.

    Declarar vazio numa peca macica faz o nesting cortar outra peca dentro
    dela. Por isso o vazio sai da
    propria abertura tipo `janela`, nunca de um campo escrito a mao.
    """
    saida = []
    for ab in dono.get("aberturas", []):
        if ab["tipo"] not in ("janela", "pilula"):
            continue
        if face_number is not None and ab.get("face") != face_number:
            continue
        alvo = ab.get("camadas", "todas")
        if alvo != "todas" and alvo != layer:
            continue
        lw, lh = ab["largura_mm"], ab["altura_mm"]
        if ab["tipo"] == "pilula":
            # so o trecho reto do estadio e retangulo de verdade
            raio = min(lw, lh) / 2.0
            lw, lh = lw - 2 * raio, lh
            if lw <= 1.0:
                lw, lh = ab["largura_mm"], lh - 2 * raio
        for espelhado in ((False, True) if ab.get("espelhado") else (False,)):
            cx, cy = _ancora(ab, w, h, espelhado)
            for cxi, cyi in _centros_repetidos(ab, cx, cy):
                vw, vh = lw - 2 * margem, lh - 2 * margem
                if vw > 1.0 and vh > 1.0:
                    saida.append((cxi - vw / 2.0, cyi - vh / 2.0, vw, vh))
    return saida


def aberturas_da_face(dono, face_number, layer, w, h):
    """Filtra as aberturas pela face e pela lamina em que elas existem."""
    saida = []
    for ab in dono.get("aberturas", []):
        if face_number is not None and ab.get("face") != face_number:
            continue
        alvo = ab.get("camadas", "todas")
        if alvo != "todas" and alvo != layer:
            continue
        saida.extend(abertura_polys(ab, w, h))
    return saida


def checa_aberturas(nome, contorno, feicoes, espessura, piso_ponte):
    """DFM: feicao dentro da peca, longe da borda e longe das vizinhas.

    Furo a >= 2x a espessura da borda, ponte entre dois cortes >= 50% da
    espessura. Feicao fora da peca e o erro de desenhar em espaco deslocado e
    esquecer de somar a origem.
    """
    problemas = []
    bx0, by0, bx1, by1 = geom.bbox(contorno)
    folga_borda = 2.0 * espessura
    for i, f in enumerate(feicoes):
        fx0, fy0, fx1, fy1 = geom.bbox(f)
        if fx0 < bx0 or fy0 < by0 or fx1 > bx1 or fy1 > by1:
            problemas.append("%s: feicao %d cai fora do contorno" % (nome, i + 1))
            continue
        borda = min(fx0 - bx0, fy0 - by0, bx1 - fx1, by1 - fy1)
        if borda < folga_borda - 1e-6:
            problemas.append("%s: feicao %d a %.1f mm da borda, minimo %.1f"
                             % (nome, i + 1, borda, folga_borda))
        for j, g in enumerate(feicoes[i + 1:], i + 2):
            d = geom.dist_poligonos(f, g)
            if d < piso_ponte - 1e-6:
                problemas.append("%s: ponte de %.1f mm entre feicoes %d e %d, minimo %.1f"
                                 % (nome, d, i + 1, j, piso_ponte))
    return problemas


def prateleira_u(cfg):
    """Prateleira plana com recorte em U na frente e abas que atravessam a parede.

    A aba tem o comprimento da parede acabada, entao ela sai rente na face
    externa e o rasgo correspondente aparece nas duas laminas da lateral. Os
    centros das abas sao simetricos em relacao ao meio da profundidade, o que
    tira a duvida de qual ponta da lateral e a frente.
    """
    w = cfg["largura_mm"]
    d = cfg["profundidade_mm"]
    aba = cfg["aba_mm"]
    aw = cfg["aba_largura_mm"]
    centros = cfg["aba_centros_mm"]
    rw = cfg["recorte_largura_mm"]
    rd = cfg["recorte_profundidade_mm"]

    # o recorte pode abrir em direcao a frente: a ponta do garfo afina, e a
    # conicidade sai pelo lado de dentro pra aba nao perder material
    rwf = cfg.get("recorte_largura_frente_mm", rw)
    esq, dir_ = (w - rw) / 2.0, (w + rw) / 2.0
    esq_f, dir_f = (w - rwf) / 2.0, (w + rwf) / 2.0
    pts = [(0.0, 0.0), (esq_f, 0.0), (esq, rd), (dir_, rd), (dir_f, 0.0), (w, 0.0)]
    for c in centros:
        pts += [(w, c - aw / 2.0), (w + aba, c - aw / 2.0),
                (w + aba, c + aw / 2.0), (w, c + aw / 2.0)]
    pts += [(w, d), (0.0, d)]
    for c in reversed(centros):
        pts += [(0.0, c + aw / 2.0), (-aba, c + aw / 2.0),
                (-aba, c - aw / 2.0), (0.0, c - aw / 2.0)]
    return [(x + aba, y) for x, y in pts]


def pecas_extras(spec):
    """Folhas de porta, sub-painel da interface e tampas dos passa-fios.

    Sao pecas soltas, nao faces da caixa: entram na prancha pelo mesmo nesting.
    """
    unidades = []
    for extra in spec.get("pecas_extras", []):
        if extra["tipo"] == "disco":
            d = extra["diametro_mm"]
            contorno = circle_pts(d / 2.0, d / 2.0, d)
            w = h = d
        elif extra["tipo"] == "prateleira_u":
            contorno = prateleira_u(extra)
            x0, y0, x1, y1 = geom.bbox(contorno)
            w, h = x1 - x0, y1 - y0
        elif extra["tipo"] == "pilula":
            w = extra["largura_mm"]
            h = extra["altura_mm"]
            contorno = geom.rrect(0.0, 0.0, w, h, min(w, h) / 2.0)
        elif extra["tipo"] == "retangulo":
            w = extra["largura_mm"]
            h = extra["altura_mm"]
            contorno = geom.rrect(0.0, 0.0, w, h, extra.get("raio_mm", 0.0))
        else:
            raise ValueError("tipo de peca extra desconhecido: %s" % extra["tipo"])
        laminas = extra.get("laminas", 1)
        sufixos = {1: [""], 2: ["I", "E"]}[laminas]
        for sufixo in sufixos:
            layer = {"I": "interna", "E": "externa", "": "unica"}[sufixo]
            feicoes = aberturas_da_face(extra, None, layer, w, h)
            unidades.append({
                "code": extra["codigo"] + sufixo,
                "nome": extra["nome"],
                "polys": [contorno] + feicoes,
                "vazios": [],
                "alojar_em": extra.get("alojar_em"),
                "w": w,
                "h": h,
                "legenda": False,
                "gira": True,
            })
    return unidades


def make_groups(spec):
    laminated = spec["espessura_mm"] * spec["camadas_por_painel"]
    if abs(laminated - spec["espessura_final_mm"]) > 1e-8:
        raise ValueError("espessura final difere da soma das laminas")
    if abs(spec["junta_dedo"]["profundidade_mm"] - spec["espessura_final_mm"]) > 1e-8:
        raise ValueError("profundidade da junta deve ser igual a espessura final")
    layers = layer_names(spec["camadas_por_painel"])
    groups = []
    for module in spec["modulos"]:
        for face_number, (title, outline, w, h) in enumerate(boxmaker_panel_defs(module, spec), 1):
            centers = (panel_hole_centers(w, h, spec["m3"])
                       if spec.get("fixacoes_m3", False) else [])
            pieces = []
            for layer in layers:
                layer_code = "I" if layer == "interna" else ("E" if layer == "externa" else "C")
                feicoes = (layer_fasteners(centers, layer, h, spec["m3"])
                           + aberturas_da_face(module, face_number, layer, w, h))
                pieces.append({
                    "code": "%s%d%s" % (module["codigo"], face_number, layer_code),
                    "outline": outline,
                    "fasteners": feicoes,
                    "vazios": vazios_da_face(module, face_number, layer, w, h,
                                             spec["encaixe"]["margem_vazio_mm"]),
                    "w": w,
                    "h": h,
                })
            groups.append({
                "title": "%s | %s" % (module["nome"], title),
                "module_prefix": module["prefixo"],
                "module_name": module["nome"],
                "pieces": pieces,
                "w": len(layers) * w + (len(layers) - 1) * spec["encaixe"]["folga_entre_pecas_mm"],
                "h": h,
            })
    return groups


def rot90(polys):
    """Gira 90 graus o conjunto de contornos de uma peca e reencosta na origem.

    Contorno e feicoes giram no MESMO referencial. Renormalizar cada poligono
    em separado jogaria os furos pra fora da peca.
    """
    turned = [[(-y, x) for x, y in poly] for poly in polys]
    min_x = min(x for poly in turned for x, _ in poly)
    min_y = min(y for poly in turned for _, y in poly)
    return [[(x - min_x, y - min_y) for x, y in poly] for poly in turned]


LEGENDA_LINHAS = [
    ("LEGENDA", 10.0, 84.0, 8.0),
    ("B  BIOMETRICO", 10.0, 68.0, None),
    ("A  ARMARIO", 10.0, 56.0, None),
    ("I  INTERNA", 10.0, 44.0, None),
    ("E  EXTERNA", 10.0, 32.0, None),
    ("1  FUNDO", 105.0, 68.0, None),
    ("2  LAT ESQ", 105.0, 56.0, None),
    ("3  PISO", 105.0, 44.0, None),
    ("4  LAT DIR", 105.0, 32.0, None),
    ("5  TETO", 105.0, 20.0, None),
    ("6  TAMPA", 105.0, 8.0, None),
]


def sheet_units(spec, groups):
    """Uma unidade de nesting por lamina, mais a peca de legenda.

    As duas laminas de um painel tem o mesmo contorno mas nao precisam ficar
    lado a lado: cada uma leva o proprio codigo gravado.
    """
    units = []
    for group in groups:
        for piece in group["pieces"]:
            units.append({
                "code": piece["code"],
                "polys": [piece["outline"]] + list(piece["fasteners"]),
                "vazios": list(piece.get("vazios", [])),
                "w": piece["w"],
                "h": piece["h"],
                "legenda": False,
                "gira": True,
            })
    units.extend(pecas_extras(spec))
    if not spec.get("gravar_codigos", True):
        return units          # sem gravacao, a peca de legenda vira refugo
    legenda = spec["legenda"]
    lw = legenda["largura_mm"]
    lh = legenda["altura_mm"]
    units.append({
        "code": "LEG",
        "polys": [[(0.0, 0.0), (lw, 0.0), (lw, lh), (0.0, lh)]],
        "vazios": [],
        "w": lw,
        "h": lh,
        "legenda": True,
        "gira": False,
    })
    return units


def _gira_rect(vazio, h):
    """Um vazio local acompanha a rotacao de 90 graus da peca que o contem."""
    vx, vy, vw, vh = vazio
    return (h - vy - vh, vx, vh, vw)


def _giros_permitidos(unit):
    """Orientacoes permitidas para uma peca durante o nesting.

    Quando a mesa pede retangulares deitadas, o lado maior fica sempre no
    eixo horizontal. Quadrados continuam na orientacao original.
    """
    if not unit["gira"]:
        return (False,)
    if unit.get("orientacao") == "deitada":
        return (True,) if unit["h"] > unit["w"] else (False,)
    return (False, True)


def _first_fit(units, chave, width, gap, margin, margem_vazio, criterio="baixo"):
    """Guilhotina com lista de retangulos livres, testando rotacao de 90 graus.

    Cada retangulo livre carrega a propria folga: dentro do vazio de uma peca
    grande vale `margem_vazio`, que e o numero que decide se a peca aninhada
    cabe.
    """
    livres = [(margin, margin, width - 2 * margin, 1e7, gap, False)]
    placed = []
    em_vazio = 0
    # no criterio "vazio" quem OFERECE vazio entra antes: o buraco precisa
    # existir na lista de livres para as pecas pequenas caberem nele
    ordena = ((lambda u: (0 if u["vazios"] else 1, chave(u)))
              if criterio == "vazio" else chave)
    for unit in sorted(units, key=ordena):
        best = None
        for i, (rx, ry, rw, rh, rgap, vazio) in enumerate(livres):
            for gira in _giros_permitidos(unit):
                pw, ph = (unit["h"], unit["w"]) if gira else (unit["w"], unit["h"])
                if pw <= rw + 1e-9 and ph <= rh + 1e-9:
                    sobra = rw * rh - pw * ph
                    if criterio == "baixo":
                        ordem = (ry, rx, sobra)
                    elif criterio == "justo":
                        ordem = (sobra, ry, rx)
                    else:
                        # o vazio de uma peca grande e material ja pago:
                        # encher ele primeiro nao gasta folha nenhuma
                        ordem = (0 if vazio else 1, sobra, ry, rx)
                    if best is None or ordem < best[0]:
                        best = (ordem, i, gira, pw, ph)
        if best is None:
            raise ValueError(
                "peca %s (%.0f x %.0f mm) nao cabe na largura de folha de %.0f mm"
                % (unit["code"], unit["w"], unit["h"], width))
        _, i, gira, pw, ph = best
        rx, ry, rw, rh, rgap, era_vazio = livres.pop(i)
        em_vazio += 1 if era_vazio else 0
        placed.append((unit, rx, ry, gira))
        if rw - pw - rgap > 1.0:
            livres.append((rx + pw + rgap, ry, rw - pw - rgap, ph, rgap, era_vazio))
        if rh - ph - rgap > 1.0:
            livres.append((rx, ry + ph + rgap, rw, rh - ph - rgap, rgap, era_vazio))
        for vazio in unit["vazios"]:
            vx, vy, vw, vh = _gira_rect(vazio, unit["h"]) if gira else vazio
            livres.append((rx + vx, ry + vy, vw, vh, margem_vazio, True))
        livres.sort(key=lambda r: (r[1], r[0]))
    topo = max(y + (u["w"] if g else u["h"]) for u, _, y, g in placed)
    return placed, topo, em_vazio


def aloja_no_vazio(placed, pendentes, margem):
    """Coloca as pecas que a spec mandou morar dentro do vazio de outra.

    O nesting escolhe por area e nem sempre acha que vale a pena usar o buraco.
    Quando o projeto DIZ onde a peca mora, quem manda e o projeto: a tampa do
    passa-fio sai de dentro da janela da interface, e nao de folha nova.
    """
    if not pendentes:
        return placed, []
    hosts = {}
    for unit, x, y, gira in placed:
        for vazio in unit["vazios"]:
            vx, vy, vw, vh = _gira_rect(vazio, unit["h"]) if gira else vazio
            hosts.setdefault(unit["code"], []).append((x + vx, y + vy, vw, vh))
    colocadas = []
    sobrou = []
    cursor = {}
    for unit in pendentes:
        vagas = hosts.get(unit["alojar_em"], [])
        posto = None
        for indice, (vx, vy, vw, vh) in enumerate(vagas):
            cx, cy, faixa = cursor.get((unit["alojar_em"], indice), (0.0, 0.0, 0.0))
            for gira in _giros_permitidos(unit):
                pw, ph = (unit["h"], unit["w"]) if gira else (unit["w"], unit["h"])
                px, py = cx, cy
                if py + ph > vh + 1e-9:            # coluna cheia, abre a proxima
                    px, py = cx + faixa + margem, 0.0
                if px + pw <= vw + 1e-9 and py + ph <= vh + 1e-9:
                    posto = (vx + px, vy + py, gira)
                    cursor[(unit["alojar_em"], indice)] = (
                        px, py + ph + margem, max(faixa if px == cx else 0.0, pw))
                    break
            if posto:
                break
        if posto:
            colocadas.append((unit, posto[0], posto[1], posto[2]))
        else:
            sobrou.append(unit)
    return placed + colocadas, sobrou


def pack_sheet(units, spec):
    """Todas as pecas numa prancha so.

    O first-fit e refem da ordem em que as pecas chegam, entao roda seis
    ordenacoes e fica com a folha de menor area.
    """
    width = spec["folha"]["largura_mm"]
    gap = spec["encaixe"]["folga_entre_pecas_mm"]
    margin = spec["encaixe"]["margem_mm"]
    if spec["folha"].get("travar_rotacao"):
        # a peca sai na prancha na mesma orientacao em que ela fica montada.
        # Custa folha, e paga em conferencia: rasgo empilhado no modulo em pe
        # aparecia deitado no desenho, e isso ja fez a peca parecer errada.
        for unit in units:
            unit["gira"] = False
    ordens = [
        lambda u: -(u["w"] * u["h"]),
        lambda u: -max(u["w"], u["h"]),
        lambda u: -u["h"],
        lambda u: -u["w"],
        lambda u: -(u["w"] + u["h"]),
        lambda u: u["w"] * u["h"],
    ]
    def largura_usada(placed):
        return max(x + (u["h"] if g else u["w"]) for u, x, _, g in placed)

    melhor = None
    for chave in ordens:
        for criterio in ("baixo", "justo", "vazio"):
            placed, topo, em_vazio = _first_fit(
                units, chave, width, gap, margin,
                spec["encaixe"]["margem_vazio_mm"], criterio)
            # o alvo e a AREA da folha, nao a altura: num subconjunto pequeno,
            # empilhar mais alto pode sair mais barato que abrir outra coluna.
            # Empatou a area, ganha quem enfiou mais peca no vazio de outra:
            # ali o material ja esta pago e a peca nao ocupa folha nova.
            usada = min(width, largura_usada(placed) + margin)
            marca = (round(usada * (topo + margin), 3), -em_vazio, round(topo, 3))
            if melhor is None or marca < melhor[0]:
                melhor = (marca, placed, usada, topo)
    _, placed, usada, topo = melhor
    return placed, usada, topo + margin


def corpo_do_rotulo(poly):
    """Altura de letra proporcional a peca, entre 8 e 24 mm."""
    x0, y0, x1, y1 = geom.bbox(poly)
    return max(8.0, min(24.0, 0.10 * min(x1 - x0, y1 - y0)))


def rotulos_da_peca(unit, polys):
    """Uma marcacao por peca: o codigo dela, longe das feicoes."""
    return [(unit["code"], polys[0], polys[1:], corpo_do_rotulo(polys[0]))]


def seleciona(units, filtro):
    """Recorta o banco de pecas por expressao regular no codigo."""
    if not filtro:
        return units
    rx = re.compile(filtro)
    escolhidas = [u for u in units if rx.match(u["code"])]
    if not escolhidas:
        raise ValueError("filtro %r nao casou com nenhuma peca" % filtro)
    return escolhidas


def _fit_bloco(units, largura, altura, gap, margin, margem_vazio):
    """Enche UM bloco. Devolve (colocadas, sobras) sem estourar a altura."""
    livres = [(margin, margin, largura - 2 * margin, altura - 2 * margin, gap, False)]
    colocadas, sobras = [], []
    for unit in units:
        best = None
        for i, (rx, ry, rw, rh, rgap, vazio) in enumerate(livres):
            for gira in _giros_permitidos(unit):
                pw, ph = (unit["h"], unit["w"]) if gira else (unit["w"], unit["h"])
                if pw <= rw + 1e-9 and ph <= rh + 1e-9:
                    ordem = (0 if vazio else 1, ry, rx, rw * rh - pw * ph)
                    if best is None or ordem < best[0]:
                        best = (ordem, i, gira, pw, ph)
        if best is None:
            sobras.append(unit)
            continue
        _, i, gira, pw, ph = best
        rx, ry, rw, rh, rgap, era_vazio = livres.pop(i)
        colocadas.append((unit, rx, ry, gira))
        if rw - pw - rgap > 1.0:
            livres.append((rx + pw + rgap, ry, rw - pw - rgap, ph, rgap, era_vazio))
        if rh - ph - rgap > 1.0:
            livres.append((rx, ry + ph + rgap, rw, rh - ph - rgap, rgap, era_vazio))
        for vz in unit["vazios"]:
            vx, vy, vw, vh = _gira_rect(vz, unit["h"]) if gira else vz
            livres.append((rx + vx, ry + vy, vw, vh, margem_vazio, True))
        livres.sort(key=lambda r: (r[1], r[0]))
    return colocadas, sobras


def pack_blocos(units, spec):
    """Distribui TODAS as pecas em mesas. Nenhuma fica de fora.

    Quem cabe na mesa padrao vai enchendo mesa por mesa, e o que sobra passa
    pra proxima. Peca maior que a mesa ganha mesa PROPRIA, dimensionada nela e
    marcada como fora de medida: o arquivo sai, e o aviso sai junto.
    """
    bloco_w, bloco_h = spec["folha"]["bloco_mm"]
    gap = spec["encaixe"]["folga_entre_pecas_mm"]
    margin = spec["encaixe"]["margem_mm"]
    vazio = spec["encaixe"]["margem_vazio_mm"]
    util_w, util_h = bloco_w - 2 * margin, bloco_h - 2 * margin

    normais, grandes = [], []
    for u in units:
        maior, menor = max(u["w"], u["h"]), min(u["w"], u["h"])
        if maior <= max(util_w, util_h) + 1e-9 and menor <= min(util_w, util_h) + 1e-9:
            normais.append(u)
        else:
            grandes.append(u)

    blocos = []          # (colocadas, largura, altura, fora_de_medida)
    restantes = sorted(normais, key=lambda u: -(u["w"] * u["h"]))
    while restantes:
        colocadas, restantes = _fit_bloco(restantes, bloco_w, bloco_h,
                                          gap, margin, vazio)
        if not colocadas:
            raise ValueError("nenhuma peca coube numa mesa vazia: revise bloco_mm")
        blocos.append((colocadas, bloco_w, bloco_h, False))

    # cada peca fora de medida deitada na propria mesa, no lado mais curto
    for u in sorted(grandes, key=lambda u: -(u["w"] * u["h"])):
        gira = _giros_permitidos(u)[0]
        pw, ph = (u["h"], u["w"]) if gira else (u["w"], u["h"])
        bw = max(bloco_w, pw + 2 * margin)
        bh = max(bloco_h, ph + 2 * margin)
        blocos.append(([(u, margin, margin, gira)], bw, bh, True))

    placed, molduras = [], []
    x = y = 0.0
    linha_h = 0.0
    largura_folha = spec["folha"]["largura_mm"]
    for colocadas, bw, bh, fora in blocos:
        if x > 0 and x + bw > largura_folha:
            x = 0.0
            y += linha_h + gap
            linha_h = 0.0
        molduras.append((x, y, bw, bh, fora))
        placed += [(u, px + x, py + y, g) for u, px, py, g in colocadas]
        x += bw + gap
        linha_h = max(linha_h, bh)
    largura = max(mx + mw for mx, _, mw, _, _ in molduras)
    altura = max(my + mh for _, my, _, mh, _ in molduras)
    return placed, largura, altura, molduras, []


def build_sheet(spec, groups, filtro=None, titulo=None):
    """Prancha em escala 1:1. Sem filtro sai o banco inteiro de pecas."""
    units = seleciona(sheet_units(spec, groups), filtro)
    if spec["folha"].get("retangulares_deitadas"):
        for unit in units:
            unit["orientacao"] = "deitada"
    if spec["folha"].get("travar_rotacao"):
        for unit in units:
            unit["gira"] = False
    bloco = spec["folha"].get("bloco_mm")
    if bloco:
        # hospedeiro que nao cabe na mesa nao pode alojar ninguem: a peca
        # pequena volta pro empacotamento normal em vez de virar recusada
        margin = spec["encaixe"]["margem_mm"]
        util = (bloco[0] - 2 * margin, bloco[1] - 2 * margin)
        codigos = {u["code"] for u in units
                   if max(u["w"], u["h"]) <= max(util) + 1e-9
                   and min(u["w"], u["h"]) <= min(util) + 1e-9}
    else:
        codigos = {u["code"] for u in units}
    alojar = [u for u in units if u.get("alojar_em") in codigos]
    soltas = [u for u in units if u not in alojar]
    molduras, recusadas = [], []
    if spec["folha"].get("bloco_mm"):
        placed, sheet_w, content_top, molduras, recusadas = pack_blocos(soltas, spec)
    else:
        placed, sheet_w, content_top = pack_sheet(soltas, spec)
    placed, sobrou = aloja_no_vazio(placed, alojar, spec["encaixe"]["margem_vazio_mm"])
    recusadas = recusadas + sobrou
    cuts = []
    engrave = []
    gravar = spec.get("gravar_codigos", True)
    for unit, x, y, gira in placed:
        polys = rot90(unit["polys"]) if gira else unit["polys"]
        # Interno antes de externo, sempre. Cortado o
        # perimetro a peca se solta e desalinha, e furo depois disso sai torto.
        cuts.extend(moved(poly, x, y) for poly in polys[1:])
        cuts.append(moved(polys[0], x, y))
        if unit["legenda"]:
            for texto, ox, oy, tamanho in LEGENDA_LINHAS:
                engrave.append({
                    "tipo": "texto",
                    "texto": texto,
                    "x": x + ox,
                    "y": y + oy,
                    "tamanho": tamanho or spec["legenda"]["fonte_mm"],
                    "ancora": "start",
                    "rot": 0,
                    "peso": 700,
                    "machine": gravar,
                })
        else:
            for texto, poly, feicoes, tamanho in rotulos_da_peca(unit, polys):
                rx, ry = posicao_rotulo(poly, feicoes, tamanho, texto)
                engrave.append({
                    "tipo": "texto",
                    "texto": texto,
                    "x": x + rx,
                    "y": y + ry,
                    "tamanho": tamanho,
                    "ancora": "start",
                    "rot": 0,
                    "peso": 700,
                    "machine": gravar,
                })
    for ox, oy, bw, bh, fora in molduras:
        engrave.append({"tipo": "moldura", "fora": fora,
                        "pontos": [(ox, oy), (ox + bw, oy),
                                   (ox + bw, oy + bh), (ox, oy + bh)]})
    build_sheet.recusadas = recusadas
    build_sheet.molduras = molduras
    return cuts, engrave, sheet_w, content_top + 64.0, placed


def svg_sheet(cuts, engrave, width, height, labels=True):
    flip = lambda x, y: (x, height - y)
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%.4fmm" height="%.4fmm" viewBox="0 0 %.4f %.4f">'
        % (width, height, width, height),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<g fill="none" stroke="#ff0000" stroke-width="0.05">',
    ]
    for poly in cuts:
        out.append('<path d="%s"/>' % path_d(poly, flip))
    out.append('</g>')
    if labels:
        # so a moldura do bloco de mesa, em cinza. Nada de azul no desenho:
        # gravacao e cabecalho poluem a conferencia e nao vao pra maquina.
        out.append('<g fill="none" stroke="#9aa0a6" stroke-width="1.5" '
                   'stroke-dasharray="14 9">')
        for item in engrave:
            if item["tipo"] == "moldura":
                pts = " ".join("%.4f,%.4f" % flip(x, y) for x, y in item["pontos"])
                out.append('<polygon points="%s"/>' % pts)
        out.append('</g>')
    out.append('</svg>')
    return "\n".join(out)


def write_pdf(svg_text, width, height, path):
    """PDF em escala 1:1 pelo Chrome headless. Sem Chrome, avisa e segue."""
    chrome = acha_chrome()
    if chrome is None:
        if not getattr(write_pdf, "avisado", False):
            print("AVISO Chrome nao encontrado (defina CHROME=<caminho>): PDFs pulados")
            write_pdf.avisado = True
        return
    os.makedirs(TMP, exist_ok=True)
    stem = os.path.basename(os.path.splitext(path)[0])
    html_path = os.path.join(TMP, stem + "-pdf.html")
    html = ('<!doctype html><meta charset="utf-8"><title>%s</title><style>'
            '@page{size:%.4fmm %.4fmm;margin:0}html,body{margin:0;padding:0;background:#fff}'
            'svg{display:block}</style>%s' % (stem, width, height, svg_text))
    with open(html_path, "w", encoding="utf-8") as stream:
        stream.write(html)
    subprocess.run([
        chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw", "--virtual-time-budget=2000",
        "--print-to-pdf=" + os.path.abspath(path),
        "file://" + os.path.abspath(html_path),
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def valida_prancha(spec, placed):
    """Roda o DFM em toda peca colocada. Lista vazia e o portao para a maquina."""
    espessura = spec["espessura_mm"]
    piso_ponte = 0.5 * espessura
    problemas = []
    for unit, x, y, gira in placed:
        polys = rot90(unit["polys"]) if gira else unit["polys"]
        problemas.extend(checa_aberturas(unit["code"], polys[0], polys[1:],
                                         espessura, piso_ponte))
    return problemas


def relatorio(spec, placed, sheet_w, sheet_h):
    """Aproveitamento, perimetro e tamanho de peca.

    Desperdicio que ninguem mede ninguem corta.
    """
    pecas = []
    for unit, x, y, gira in placed:
        polys = rot90(unit["polys"]) if gira else unit["polys"]
        pecas.append({
            "nome": unit["code"],
            "contorno": moved(polys[0], x, y),
            "feicoes": [moved(p, x, y) for p in polys[1:]],
        })
    r = report.folha(pecas, folha=(sheet_w, sheet_h))
    chapa_w, chapa_h = spec["folha"]["chapa_padrao_mm"]
    linhas = [
        "prancha unica: %.0f x %.0f mm | %d pecas" % (sheet_w, sheet_h, r["pecas"]),
        "aproveitamento: %.1f%% | area das pecas %.3f m2 em folha de %.3f m2"
        % (r["aproveitamento"] * 100, r["area_pecas_m2"], r["area_folha_m2"]),
        "perimetro de corte: %.0f mm | chapas %.0fx%.0f necessarias: %.1f"
        % (r["perimetro_mm"], chapa_w, chapa_h, r["area_pecas_m2"] / (chapa_w * chapa_h / 1e6)),
    ]
    return linhas, r


def tabela_pecas(placed, mesa=None):
    """Tamanho final de cada peca, com aviso de peca maior que a mesa."""
    linhas = ["", "%-6s %-18s %s" % ("codigo", "medida (mm)", "cabe na mesa")]
    fora = []
    for unit, _, _, gira in sorted(placed, key=lambda p: p[0]["code"]):
        w, h = (unit["h"], unit["w"]) if gira else (unit["w"], unit["h"])
        veredito = ""
        if mesa:
            cabe = (max(w, h) <= max(mesa) + 1e-9 and min(w, h) <= min(mesa) + 1e-9)
            veredito = "sim" if cabe else "NAO"
            if not cabe:
                fora.append(unit["code"])
        linhas.append("%-6s %-18s %s" % (unit["code"], "%.0f x %.0f" % (w, h), veredito))
    return linhas, fora


def opcoes(argv):
    """--filtro REGEX recorta o banco de pecas, --nome STEM nomeia a saida."""
    filtro = nome = titulo = None
    argv = list(argv)
    while argv:
        arg = argv.pop(0)
        if arg == "--filtro" and argv:
            filtro = argv.pop(0)
        elif arg == "--nome" and argv:
            nome = argv.pop(0)
        elif arg == "--titulo" and argv:
            titulo = argv.pop(0)
        else:
            raise SystemExit(
                "uso: gerador.py [--filtro REGEX] [--nome PASTA/STEM] [--titulo TEXTO]")
    return filtro, nome, titulo


def main(argv=None):
    filtro, nome_saida, titulo = opcoes(sys.argv[1:] if argv is None else argv)
    with open(SPEC_PATH, encoding="utf-8") as stream:
        spec = json.load(stream)
    groups = make_groups(spec)
    nome = nome_saida or spec["nome"]
    os.makedirs(os.path.dirname(os.path.join(OUTPUT, nome)), exist_ok=True)
    cuts, engrave, sheet_w, sheet_h, placed = build_sheet(spec, groups, filtro, titulo)

    svg_cotado = svg_sheet(cuts, engrave, sheet_w, sheet_h, labels=True)
    with open(os.path.join(OUTPUT, nome + "_cotado.svg"), "w", encoding="utf-8") as stream:
        stream.write(svg_cotado)
    with open(os.path.join(OUTPUT, nome + ".svg"), "w", encoding="utf-8") as stream:
        stream.write(svg_sheet(cuts, engrave, sheet_w, sheet_h, labels=False))
    textos = [g for g in engrave
              if g["tipo"] == "texto" and g.get("machine", True)]
    perfil.escreve(os.path.join(OUTPUT, nome + ".dxf"), cuts, textos=textos)
    write_pdf(svg_cotado, sheet_w, sheet_h, os.path.join(OUTPUT, nome + ".pdf"))

    # um arquivo por bloco: e assim que a peca chega na mesa, uma carga por vez
    molduras_blocos = getattr(build_sheet, "molduras", [])
    saidas = []
    for indice, (ox, oy, bw, bh, fora) in enumerate(molduras_blocos, 1):
        dentro = [poly for poly in cuts
                  if all(ox - 1e-6 <= x <= ox + bw + 1e-6
                         and oy - 1e-6 <= y <= oy + bh + 1e-6 for x, y in poly)]
        # mesma origem do DXF: o ponto mais baixo a esquerda encosta no canto da mesa
        x0 = min(x for poly in dentro for x, _ in poly)
        y0 = min(y for poly in dentro for _, y in poly)
        locais = [[(x - x0, y - y0) for x, y in poly] for poly in dentro]
        stem = "%s-bloco%d" % (nome, indice)
        quadro = [(0.0, 0.0), (bw, 0.0), (bw, bh), (0.0, bh)]
        perfil.escreve(os.path.join(OUTPUT, stem + ".dxf"), locais)
        svg_bloco = svg_sheet(locais, [{"tipo": "moldura", "pontos": quadro}],
                              bw, bh, labels=True)
        with open(os.path.join(OUTPUT, stem + ".svg"), "w", encoding="utf-8") as f:
            f.write(svg_bloco)
        write_pdf(svg_bloco, bw, bh, os.path.join(OUTPUT, stem + ".pdf"))
        saidas.append((stem, len(locais), bw, bh, fora))
    for stem, n, bw, bh, fora in saidas:
        print("mesa %-28s %4.0f x %4.0f mm | %2d contornos%s"
              % (stem + ".dxf", bw, bh, n, "  FORA DE MEDIDA" if fora else ""))

    for linha in relatorio(spec, placed, sheet_w, sheet_h)[0]:
        print(linha)
    recusadas = getattr(build_sheet, "recusadas", [])
    molduras_n = len(getattr(build_sheet, "molduras", []))
    if molduras_n:
        bw, bh = spec["folha"]["bloco_mm"]
        print("blocos de mesa %.0f x %.0f mm: %d" % (bw, bh, molduras_n))
    if recusadas:
        bw, bh = spec["folha"]["bloco_mm"]
        print("\nNAO CABEM NA MESA de %.0f x %.0f mm, %d pecas:" % (bw, bh, len(recusadas)))
        for u in sorted(recusadas, key=lambda x: x["code"]):
            print("  %-5s %.0f x %.0f mm" % (u["code"], u["w"], u["h"]))
    problemas = valida_prancha(spec, placed)
    if problemas:
        print("\nDFM REPROVADO, %d problemas:" % len(problemas))
        for linha in problemas:
            print("  " + linha)
    mesa = spec["folha"].get("mesa_mm")
    linhas, fora = tabela_pecas(placed, mesa)
    print("\n".join(linhas))
    if fora:
        print("\nAVISO %d pecas maiores que a mesa %s: %s"
              % (len(fora), mesa, ", ".join(fora)))
    elif not mesa:
        print("\nAVISO mesa da maquina nao declarada em folha.mesa_mm: "
              "nenhuma peca foi conferida contra a area de corte.")
    material = materials.busca(spec["material"])
    if material is None:
        print("AVISO material %s nao esta em materiais.json" % spec["material"])
    elif material.estimado:
        print("AVISO " + material.aviso)


if __name__ == "__main__":
    main()
