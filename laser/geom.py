"""Primitivas de geometria plana. Poligono = lista de (x, y) em mm, fechado
implicitamente (o ultimo ponto liga no primeiro).

Convencao do projeto: origem no canto inferior esquerdo, X para a direita,
Y para cima, tudo em mm. Nao existe entidade circulo: tudo vira poligono.
"""
import math

TOL = 1e-9


# ---------------------------------------------------------------- basicos

def rot(pts, cx, cy, ang):
    """Gira o poligono em torno de (cx, cy). Angulo em graus."""
    if not ang:
        return pts
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa,
             cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def move(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def area_assinada(pts):
    """Positiva = anti-horario. Em mm^2."""
    n = len(pts)
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
                     for i in range(n))


def area(pts):
    return abs(area_assinada(pts))


def perimetro(pts):
    n = len(pts)
    return sum(math.dist(pts[i], pts[(i + 1) % n]) for i in range(n))


def horario(pts):
    return area_assinada(pts) < 0


def orienta(pts, anti_horario=True):
    """Devolve o poligono na orientacao pedida. Offset e teste de conteneza
    dependem de orientacao conhecida, entao normalizar antes economiza bug."""
    if (area_assinada(pts) > 0) == anti_horario:
        return list(pts)
    return list(reversed(pts))


# ---------------------------------------------------------------- formas

def rrect(x, y, w, h, r=0.0, seg=14):
    """Retangulo com cantos arredondados. (x, y) = canto inferior esquerdo."""
    r = max(0.0, min(r, w / 2.0, h / 2.0))
    if r <= 0:
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    pts = []
    for cx, cy, a0, a1 in ((x + w - r, y + r, -90, 0), (x + w - r, y + h - r, 0, 90),
                           (x + r, y + h - r, 90, 180), (x + r, y + r, 180, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + (a1 - a0) * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def circle_pts(cx, cy, d, seg=72):
    """Circulo poligonizado, cotado por DIAMETRO."""
    r = d / 2.0
    return [(cx + r * math.cos(2 * math.pi * i / seg),
             cy + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]


def hexagono(cx, cy, entre_faces):
    """Hexagono de porca, cotado ENTRE FACES (5.5 = M3). Duas faces horizontais."""
    r = entre_faces / math.sqrt(3.0)
    return [(cx + r * math.cos(math.radians(60 * k)),
             cy + r * math.sin(math.radians(60 * k))) for k in range(6)]


# ---------------------------------------------------------------- cantos

def arredonda(pts, raios, seg=10):
    """Arredonda cada vertice por arco tangente. raios = lista paralela (0 = vivo).
    Funciona em vertice convexo e reentrante."""
    n = len(pts)
    out = []
    for i in range(n):
        A, B, C = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        r = raios[i] if isinstance(raios, (list, tuple)) else raios
        v1 = (A[0] - B[0], A[1] - B[1])
        v2 = (C[0] - B[0], C[1] - B[1])
        l1 = math.hypot(*v1)
        l2 = math.hypot(*v2)
        if r <= 0 or l1 < TOL or l2 < TOL:
            out.append(B)
            continue
        u1 = (v1[0] / l1, v1[1] / l1)
        u2 = (v2[0] / l2, v2[1] / l2)
        cosang = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))
        ang = math.acos(cosang)
        if ang < 1e-6 or abs(ang - math.pi) < 1e-6:
            out.append(B)
            continue
        d = r / math.tan(ang / 2.0)
        d = min(d, l1 / 2.0, l2 / 2.0)
        r = d * math.tan(ang / 2.0)
        P1 = (B[0] + u1[0] * d, B[1] + u1[1] * d)
        P2 = (B[0] + u2[0] * d, B[1] + u2[1] * d)
        bis = (u1[0] + u2[0], u1[1] + u2[1])
        lb = math.hypot(*bis) or 1.0
        hh = r / math.sin(ang / 2.0)
        O = (B[0] + bis[0] / lb * hh, B[1] + bis[1] / lb * hh)
        a1 = math.atan2(P1[1] - O[1], P1[0] - O[0])
        a2 = math.atan2(P2[1] - O[1], P2[0] - O[0])
        da = a2 - a1
        while da > math.pi:
            da -= 2 * math.pi
        while da < -math.pi:
            da += 2 * math.pi
        for k in range(seg + 1):
            a = a1 + da * k / seg
            out.append((O[0] + r * math.cos(a), O[1] + r * math.sin(a)))
    return out


def chanfra(pts, cortes):
    """Corta cada vertice com uma diagonal reta. cortes = lista paralela (0 = vivo)."""
    n = len(pts)
    out = []
    for i in range(n):
        A, B, C = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        c = cortes[i] if isinstance(cortes, (list, tuple)) else cortes
        v1 = (A[0] - B[0], A[1] - B[1])
        v2 = (C[0] - B[0], C[1] - B[1])
        l1 = math.hypot(*v1)
        l2 = math.hypot(*v2)
        if c <= 0 or l1 < TOL or l2 < TOL:
            out.append(B)
            continue
        d = min(c, l1 / 2.0, l2 / 2.0)
        out.append((B[0] + v1[0] / l1 * d, B[1] + v1[1] / l1 * d))
        out.append((B[0] + v2[0] / l2 * d, B[1] + v2[1] / l2 * d))
    return out


def raios_convexos(pts, r):
    """Raios para `arredonda`: r no vertice convexo, 0 no reentrante.

    Erro ja pago: arredondar a RAIZ de um dedo
    impede a peca de assentar rente na chapa. Raio e chanfro so em canto
    convexo; a raiz do dedo fica viva de proposito.
    """
    n = len(pts)
    sgn = 1.0 if area_assinada(pts) > 0 else -1.0
    out = []
    for i in range(n):
        A, B, C = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        cross = (B[0] - A[0]) * (C[1] - B[1]) - (B[1] - A[1]) * (C[0] - B[0])
        out.append(r if cross * sgn > 0 else 0.0)
    return out


# ---------------------------------------------------------------- topologia

def ponto_dentro(p, poly):
    """Ray casting. Ponto exatamente na aresta e indefinido, e tudo bem: o uso
    aqui e classificar furo dentro de contorno, onde a distancia e grande."""
    x, y = p
    dentro = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                dentro = not dentro
    return dentro


def bbox_dentro(a, b, folga=0.0):
    """Bounding box de `a` cabe dentro da de `b`?"""
    ax0, ay0, ax1, ay1 = bbox(a)
    bx0, by0, bx1, by1 = bbox(b)
    return (ax0 >= bx0 - folga and ay0 >= by0 - folga
            and ax1 <= bx1 + folga and ay1 <= by1 + folga)


def bbox_intersecta(a, b, folga=0.0):
    ax0, ay0, ax1, ay1 = bbox(a)
    bx0, by0, bx1, by1 = bbox(b)
    return not (ax1 <= bx0 + folga or bx1 <= ax0 + folga
                or ay1 <= by0 + folga or by1 <= ay0 + folga)


def agrupa(polis):
    """Agrupa poligonos em pecas: o contorno externo vira raiz e tudo que cai
    dentro dele vira filho (furo, rasgo, janela).

    Devolve lista de dicts {raiz: idx, filhos: [idx, ...]}. E este agrupamento
    que da o PAPEL de cada poligono, e o papel e quem decide o sinal do kerf.

    Erro ja pago: bounding box NAO basta. Depois do nesting, uma
    peca pequena encaixada no vazio de uma peca grande cai dentro da bbox dela
    sem estar dentro do contorno, e virava "furo" de uma peca que ela nao toca.
    Por isso o teste real e ponto-em-poligono contra o contorno, com a
    bbox servindo so de filtro barato.
    """
    ordem = sorted(range(len(polis)), key=lambda i: -area(polis[i]))
    grupos = []
    for i in ordem:
        pai = None
        for g in grupos:
            mae = polis[g["raiz"]]
            if not bbox_dentro(polis[i], mae):
                continue
            if area(polis[i]) >= area(mae):
                continue
            # amostra alguns vertices: se o poligono esta mesmo dentro do
            # contorno, todos caem dentro. Um so ja separa peca aninhada no
            # vazio de furo de verdade.
            amostra = polis[i][::max(1, len(polis[i]) // 8)][:8]
            if all(ponto_dentro(p, mae) for p in amostra):
                pai = g
                break
        if pai is None:
            grupos.append({"raiz": i, "filhos": []})
        else:
            pai["filhos"].append(i)
    return grupos


def dist_ponto_segmento(p, a, b):
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 < TOL:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.dist(p, (ax + t * dx, ay + t * dy))


def dist_poligonos(a, b):
    """Menor distancia entre dois poligonos (contornos). E o que mede a PONTE
    de material entre duas feicoes cortadas na mesma peca."""
    melhor = float("inf")
    na, nb = len(a), len(b)
    for i in range(na):
        for j in range(nb):
            melhor = min(melhor,
                         dist_ponto_segmento(a[i], b[j], b[(j + 1) % nb]),
                         dist_ponto_segmento(b[j], a[i], a[(i + 1) % na]))
            if melhor < TOL:
                return 0.0
    return melhor


def segmentos_cruzam(p1, p2, p3, p4):
    """Interseccao propria de dois segmentos (ignora toque em extremidade)."""
    def orient(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(v) < 1e-12:
            return 0
        return 1 if v > 0 else -1
    o1 = orient(p1, p2, p3)
    o2 = orient(p1, p2, p4)
    o3 = orient(p3, p4, p1)
    o4 = orient(p3, p4, p2)
    return o1 != o2 and o3 != o4 and o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0


def auto_intersecta(pts):
    """Poligono que cruza a si mesmo vira caminho ambiguo pra maquina."""
    n = len(pts)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if segmentos_cruzam(pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n]):
                return True
    return False
