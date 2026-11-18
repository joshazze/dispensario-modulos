#!/usr/bin/env python3
"""Diagramas UML e matriz de rastreabilidade do dispensario, em SVG desenhado a mao.

    python3 docs/_fonte/uml.py                 # site: docs/site/uml/*.svg
    python3 docs/_fonte/uml.py --sem-camera D  # variante sem a camera, gravada em D

Convencoes de caso de uso seguidas: ator principal (quem inicia) a direita do sistema, ator
secundario (quem reage) a esquerda, caso de uso nomeado por verbo + substantivo.
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

INK, MUT, LINE, PAPER, ACC, SOFT = "#1f1a14", "#6b6257", "#cbbfac", "#fffdf9", "#8a4b1f", "#f1e3d3"
OK, WARN, BAD, BLUE = "#2f6b3a", "#9a5b00", "#a3322a", "#2c5d8a"
FONT = "Avenir Next, Segoe UI, Helvetica, Arial, sans-serif"

SEM_CAMERA = "--sem-camera" in sys.argv
SAIDA = Path(sys.argv[sys.argv.index("--sem-camera") + 1]) if SEM_CAMERA else Path(__file__).resolve().parent.parent / "site" / "uml"


def svg(w, h, corpo, titulo):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'font-family="{FONT}" role="img" aria-label="{escape(titulo)}">'
            f'<defs><marker id="seta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>'
            f'<marker id="aberta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10" fill="none" stroke="{INK}" stroke-width="1.4"/></marker>'
            f'<marker id="heranca" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="13" markerHeight="13" orient="auto-start-reverse">'
            f'<path d="M0,0 L12,6 L0,12 z" fill="{PAPER}" stroke="{INK}" stroke-width="1.2"/></marker>'
            f'<marker id="losango" viewBox="0 0 16 10" refX="15" refY="5" markerWidth="14" markerHeight="10" orient="auto-start-reverse">'
            f'<path d="M0,5 L8,0 L16,5 L8,10 z" fill="{INK}"/></marker></defs>'
            f'<rect width="{w}" height="{h}" fill="{PAPER}"/>{corpo}</svg>')


def txt(x, y, s, size=15, anchor="middle", weight=400, color=INK, italic=False):
    st = ' font-style="italic"' if italic else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{color}"{st}>{escape(s)}</text>'


def ator(x, y, nome):
    o = [f'<g stroke="{INK}" stroke-width="2" fill="none"><circle cx="{x}" cy="{y}" r="13"/>'
         f'<line x1="{x}" y1="{y+13}" x2="{x}" y2="{y+48}"/><line x1="{x-22}" y1="{y+26}" x2="{x+22}" y2="{y+26}"/>'
         f'<line x1="{x}" y1="{y+48}" x2="{x-18}" y2="{y+78}"/><line x1="{x}" y1="{y+48}" x2="{x+18}" y2="{y+78}"/></g>']
    for i, linha in enumerate(nome.split("\n")):
        o.append(txt(x, y + 100 + i * 18, linha, 15, weight=600))
    return "".join(o)


def oval(cx, cy, nome, w=190, h=50, cor=PAPER):
    o = [f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" fill="{cor}" stroke="{INK}" stroke-width="1.6"/>']
    ls = nome.split("\n")
    for i, linha in enumerate(ls):
        o.append(txt(cx, cy + 5 + (i - (len(ls) - 1) / 2) * 17, linha, 14.5))
    return "".join(o)


def seta(x1, y1, x2, y2, tipo="seta", rotulo=None, tracejada=False, cor=INK):
    d = ' stroke-dasharray="6 5"' if tracejada else ""
    o = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{cor}" stroke-width="1.5"{d} marker-end="url(#{tipo})"/>' if tipo else \
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{cor}" stroke-width="1.5"{d}/>'
    if rotulo:
        o += txt((x1 + x2) / 2, (y1 + y2) / 2 - 6, rotulo, 12.5, color=MUT, italic=True)
    return o


# ---------------------------------------------------------------- casos de uso
def casos_de_uso():
    W, H = 1260, 780
    o = [f'<rect x="250" y="40" width="760" height="710" rx="14" fill="none" stroke="{INK}" stroke-width="2"/>',
         txt(630, 74, "Dispensário Eletrônico", 19, weight=700)]
    uc = {
        "aut": (420, 145, "Autenticar\nProfissional"),
        "dig": (320, 265, "Verificar\nDigital", 140),
        "sen": (470, 275, "Verificar\nID e Senha", 140),
        "car": (620, 265, "Ler\nCrachá", 130),
        "abr": (800, 145, "Abrir\nPorta"),
        "ale": (880, 265, "Alertar Porta\nAberta", 180),
        "reg": (620, 385, "Registrar\nEvento"),
        "cad": (870, 490, "Cadastrar\nProfissional", 180),
        "vin": (650, 530, "Vincular\nCrachá", 140),
        "des": (870, 585, "Desativar\nProfissional", 180),
        "red": (520, 670, "Redefinir\nSenha", 160),
        "his": (870, 680, "Consultar\nHistórico", 180),
    }
    if not SEM_CAMERA:
        uc["fot"] = (400, 470, "Capturar\nFoto", 140)
    for k, v in uc.items():
        cx, cy, n = v[:3]
        o.append(oval(cx, cy, n, v[3] if len(v) > 3 else 190))
    def dep(x1, y1, x2, y2, r, dx=0, dy=0):
        o.append(seta(x1, y1, x2, y2, "aberta", None, True))
        o.append(txt((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, r, 11.5, color=MUT, italic=True))
    dep(330, 240, 380, 168, "«incluir»", -34, 0)
    dep(460, 250, 440, 170, "«incluir»", 34, 0)
    dep(590, 242, 480, 166, "«estender»", 40, 4)
    dep(515, 145, 700, 145, "«incluir»", 0, -8)
    dep(760, 168, 650, 360, "«incluir»", 42, 0)
    dep(860, 240, 815, 170, "«estender»", 44, 4)
    dep(785, 495, 700, 520, "«estender»", 0, -12)
    if not SEM_CAMERA:
        dep(450, 448, 540, 400, "«estender»", -30, -8)
    o.append(ator(1140, 110, "Profissional\nde Enfermagem"))
    o.append(ator(1140, 480, "Administrador"))
    o.append(seta(1115, 150, 895, 145, None))
    o.append(seta(1115, 160, 970, 255, None))
    for x, y in [(960, 490), (960, 585), (960, 680), (600, 670), (720, 532)]:
        o.append(seta(1115, 530, x, y, None))
    o.append(ator(120, 330, "Servidor de\nAuditoria"))
    o.append(seta(145, 385, 525, 385, None))
    o.append(seta(145, 395, 445, 665, None))
    if not SEM_CAMERA:
        o.append(seta(145, 390, 330, 465, None))
    o.append(txt(120, 510, "(faz o papel da API", 12.5, color=MUT, italic=True))
    o.append(txt(120, 527, "do hospital)", 12.5, color=MUT, italic=True))
    o.append(txt(1140, 250, "principal: inicia", 12, color=MUT, italic=True))
    o.append(txt(120, 300, "secundário: reage", 12, color=MUT, italic=True))
    return svg(W, H, "".join(o), "Diagrama de casos de uso do dispensário")


# ---------------------------------------------------------------- classes
def classe(x, y, w, nome, attrs, metodos, estereotipo=None, abstrata=False):
    lh = 19
    h = 34 + (16 if estereotipo else 0) + 10 + lh * len(attrs) + 10 + lh * max(1, len(metodos))
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>']
    yy = y + 22
    if estereotipo:
        o.append(txt(x + w / 2, yy, f"«{estereotipo}»", 12, color=MUT)); yy += 16
    o.append(txt(x + w / 2, yy, nome, 15.5, weight=700, italic=abstrata))
    yy += 12
    o.append(f'<line x1="{x}" y1="{yy}" x2="{x+w}" y2="{yy}" stroke="{INK}" stroke-width="1.2"/>')
    yy += 6
    for a in attrs:
        yy += lh; o.append(txt(x + 10, yy - 4, a, 13.2, anchor="start"))
    yy += 10
    o.append(f'<line x1="{x}" y1="{yy-4}" x2="{x+w}" y2="{yy-4}" stroke="{INK}" stroke-width="1.2"/>')
    for m in metodos:
        yy += lh; o.append(txt(x + 10, yy - 4, m, 13.2, anchor="start"))
    return "".join(o), h


def classes():
    W, H = 1180, 780
    o = []
    blocos = {}
    def add(k, *a, **kw):
        s, h = classe(*a, **kw); o.append(s); blocos[k] = (a[0], a[1], a[2], h)
    add("disp", 40, 40, 260, "Dispensario", ["- id: String", "- leitos: int = 20", "- portaAberta: bool", "- estado: EstadoPorta"],
        ["+ autenticar(c: Credencial): bool", "+ liberarTrava(): void", "+ registrar(e: Evento): void"])
    add("prof", 450, 40, 270, "Profissional", ["- id: int  {1..100}", "- ativo: bool", "- senhaHash: byte[16]", "- sal: byte[4]"],
        ["+ desativar(): void", "+ reativar(): void"])
    add("cred", 860, 40, 270, "Credencial", ["- tipo: Metodo"], ["+ validar(): bool"], abstrata=True, estereotipo="abstrata")
    add("dig", 800, 250, 160, "Digital", ["- slot: int"], ["+ validar(): bool"])
    add("sen", 975, 250, 160, "Senha", ["- digitos: 6"], ["+ validar(): bool"])
    add("car", 888, 410, 170, "CartaoRFID", ["- uid: byte[]"], ["+ validar(): bool"])
    add("ev", 40, 330, 270, "Evento", ["- id: String  {único}", "- tipo: TipoEvento", "- metodo: Metodo", "- horario: DataHora", "- origemHorario: String"],
        ["+ enviar(): bool"])
    add("adm", 450, 330, 270, "Administrador", ["- pin: 10 dígitos"],
        ["+ cadastrar(p): Profissional", "+ vincularCartao(p, c): void", "+ redefinirSenha(p): Comando"])
    add("cmd", 450, 560, 270, "Comando", ["- pendente: bool", "- expiraEm: 24 h"], ["+ aplicar(): bool"])
    if not SEM_CAMERA:
        add("foto", 40, 600, 270, "Foto", ["- jpeg: até 256 KB", "- frescor: provado"], ["+ anexar(e: Evento): void"])
    def b(k, lado):
        x, y, w, h = blocos[k]
        return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y), "b": (x + w / 2, y + h), "b1": (x + 50, y + h)}[lado]
    # associacoes com multiplicidade
    def assoc(a, la, bb, lb, ma, mb, rot=None, comp=False):
        (x1, y1), (x2, y2) = b(a, la), b(bb, lb)
        o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" stroke-width="1.5"' + (' marker-start="url(#losango)"' if comp else "") + "/>")
        o.append(txt(x1 + (14 if x2 >= x1 else -14), y1 + (-8 if abs(y2 - y1) < 5 else (18 if y2 > y1 else -10)), ma, 13, color=ACC, weight=600))
        o.append(txt(x2 + (-14 if x2 >= x1 else 14), y2 + (-8 if abs(y2 - y1) < 5 else (-10 if y2 > y1 else 18)), mb, 13, color=ACC, weight=600))
        if rot:
            o.append(txt((x1 + x2) / 2, (y1 + y2) / 2 - 8, rot, 12.5, color=MUT, italic=True))
    assoc("disp", "r", "prof", "l", "1", "0..100", "cadastra")
    assoc("prof", "r", "cred", "l", "1", "1..3", "possui", comp=True)
    assoc("disp", "b", "ev", "t", "1", "0..*", "registra", comp=True)
    assoc("prof", "b", "adm", "t", "0..1", "*", "é gerido por")
    assoc("adm", "b", "cmd", "t", "1", "0..*", "emite")
    assoc("ev", "r", "prof", "b1", "0..*", "0..1", "identifica")
    if not SEM_CAMERA:
        assoc("ev", "b", "foto", "t", "1", "0..1", "anexa", comp=True)
    # heranca
    for k in ("dig", "sen", "car"):
        x, y, w, h = blocos[k]
        cx, cy = blocos["cred"][0] + blocos["cred"][2] / 2, blocos["cred"][1] + blocos["cred"][3]
        o.append(seta(x + w / 2, y, cx + (x + w / 2 - cx) * 0.15, cy, "heranca"))
    return svg(W, H, "".join(o), "Diagrama de classes do dispensário")


# ---------------------------------------------------------------- sequencia
def sequencia():
    vidas = ["Profissional", "Leitor R307S", "Arduino Mega", "Fechadura", "ESP32 (rede)", "Servidor"]
    W = 1180
    xs = [100 + i * 196 for i in range(len(vidas))]
    msgs = [
        (0, 1, "põe o dedo"),
        (2, 1, "getImage() / search()"),
        (1, 2, "id = 007, confiança", True),
        (2, 2, "validar ativo + trava do teclado"),
        (2, 3, "pulso no relé (D35)"),
        (2, 0, "LED verde, \"Abra a porta\"", True),
        (0, 2, "abre a porta (botões soltam)"),
        (2, 4, "evento access_granted + CRC-16"),
        (4, 2, "ACK", True),
    ]
    if not SEM_CAMERA:
        msgs.append((4, 4, "captura foto, pede prova de frescor"))
    msgs += [
        (4, 5, "POST /api/device/events  (HTTPS)"),
        (5, 4, "200, idempotente pelo id", True),
    ]
    if not SEM_CAMERA:
        msgs.append((4, 5, "POST /api/device/photo"))
    msgs += [(2, 0, "fecha: door_closed, trava volta", True)]
    H = 150 + 52 * len(msgs) + 22 * sum(1 for m in msgs if m[0] == m[1]) + 40
    o = []
    for x, n in zip(xs, vidas):
        o.append(f'<rect x="{x-80}" y="30" width="160" height="46" rx="6" fill="{SOFT}" stroke="{INK}" stroke-width="1.5"/>')
        o.append(txt(x, 59, n, 15, weight=700))
        o.append(f'<line x1="{x}" y1="76" x2="{x}" y2="{H-20}" stroke="{MUT}" stroke-width="1.3" stroke-dasharray="5 5"/>')
    y = 120
    for m in msgs:
        a, bb, rot = m[:3]
        ret = len(m) > 3
        if a == bb:
            x = xs[a]
            o.append(f'<path d="M{x},{y} h40 v24 h-36" fill="none" stroke="{INK}" stroke-width="1.5" marker-end="url(#seta)"/>')
            o.append(txt(x + 48, y + 16, rot, 13.5, anchor="start"))
            y += 22
        else:
            x1, x2 = xs[a], xs[bb]
            o.append(seta(x1 + (4 if x2 > x1 else -4), y, x2 + (-4 if x2 > x1 else 4), y, "aberta" if ret else "seta", None, ret))
            o.append(txt((x1 + x2) / 2, y - 8, rot, 13.5))
        y += 52
    return svg(W, H, "".join(o), "Diagrama de sequência de um acesso por digital")


# ---------------------------------------------------------------- estados
def estados():
    W, H = 1180, 600
    st = {
        "E1": (150, 140, "Bloqueado", "trava fechada"),
        "E2": (450, 140, "Autenticando", "digital, ID+senha ou crachá"),
        "E3": (750, 140, "Autorizado", "evento criado"),
        "E4": (1040, 140, "Destravado", "espera abrir (60 s)"),
        "E5": (1040, 330, "Porta aberta", "conta 5 min"),
        "E6": (750, 330, "Alerta", "bipe + vermelho piscando"),
        "E7": (450, 330, "Fechando", "trava volta"),
        "E8": (150, 330, "Falha", "sensor, leitor, relógio, rede"),
        "E9": (150, 510, "Violação", "aberta sem autorização"),
    }
    o = []
    for k, (x, y, n, d) in st.items():
        cor = "#f6dcd8" if k in ("E6", "E9", "E8") else ("#dfeedd" if k in ("E3", "E4", "E5") else SOFT)
        o.append(f'<rect x="{x-115}" y="{y-38}" width="230" height="76" rx="22" fill="{cor}" stroke="{INK}" stroke-width="1.6"/>')
        o.append(txt(x, y - 6, f"{k} · {n}", 16, weight=700))
        o.append(txt(x, y + 17, d, 13, color=MUT))
    def cam(pts, rot, lx, ly):
        d = "M" + " L".join(f"{x},{y}" for x, y in pts)
        o.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="1.5" marker-end="url(#seta)"/>')
        o.append(txt(lx, ly, rot, 12.5, color=MUT, italic=True))
    o.append(f'<circle cx="150" cy="40" r="10" fill="{INK}"/>')
    cam([(150, 50), (150, 101)], "liga / reinicia", 205, 82)
    cam([(265, 128), (334, 128)], "credencial", 300, 120)
    cam([(335, 154), (266, 154)], "negada", 300, 172)
    cam([(565, 140), (634, 140)], "válida", 600, 132)
    cam([(865, 140), (924, 140)], "pulso", 895, 132)
    cam([(1040, 101), (1040, 66), (230, 66), (230, 101)], "60 s sem abrir: trava de novo", 640, 58)
    cam([(1040, 178), (1040, 291)], "abriu", 1072, 240)
    cam([(925, 330), (866, 330)], "5 min", 895, 322)
    cam([(635, 330), (566, 330)], "fechou", 600, 322)
    cam([(1040, 368), (1040, 412), (450, 412), (450, 369)], "fechou antes de 5 min", 745, 430)
    cam([(380, 292), (235, 179)], "trava", 330, 225)
    cam([(150, 292), (150, 179)], "recuperou", 108, 240)
    cam([(35, 150), (14, 150), (14, 510), (34, 510)], "", 0, 0)
    o.append(txt(22, 450, "porta abre sem credencial", 12.5, "start", color=MUT, italic=True))
    cam([(265, 500), (400, 369)], "fechou", 355, 450)
    o.append(txt(760, 520, "Qualquer estado vai para E8 quando um periférico falha.", 13.5, color=MUT))
    o.append(txt(760, 540, "Depois de reiniciar, o sistema sempre começa em E1 e confere os sensores.", 13.5, color=MUT))
    return svg(W, H, "".join(o), "Máquina de estados da porta")


# ---------------------------------------------------------------- matriz
REQ = [
    ("RF01", "Autenticação biométrica", "ok", "leitor de digital R307S no Mega"),
    ("RF02", "Senha como alternativa", "ok", "ID + senha de 6 dígitos no teclado"),
    ("RF03", "Controle da porta", "ok", "relé + fechadura 12 V em pulso"),
    ("RF04", "Registro de acesso", "ok", "evento com método, resultado e horário"),
    ("RF05", "Monitoramento da porta", "ok", "dois botões que a porta aperta"),
    ("RF06", "Alerta de porta aberta", "ok", "bipe baixo depois de 5 min"),
    ("RF07", "Associação ao paciente", "nao", "depende da API do hospital"),
    ("RF08", "Envio de eventos", "adapt", "servidor próprio no lugar da API"),
    ("RF09", "Integração de estoque", "nao", "baixa e saldo ficam no sistema do hospital"),
    ("RF10", "Banco do Instituto via API", "adapt", "API não chegou: SQLite na nuvem"),
    ("RF11", "Correlação com câmera", "alem", "NTP + foto do próprio acesso"),
    ("RF12", "Acesso a todo o conteúdo", "ok", "porta única, sem trava por gaveta"),
    ("RF13", "Prescrição em tela touch", "nao", "desejável; depende da API"),
]
ALEM = [
    ("+01", "Crachá RFID como 3º método", "alem", "MIFARE no RC522, junto de digital e senha"),
    ("+02", "Painel web com HTTPS", "alem", "VM em São Paulo, senha + PIN"),
    ("+03", "Troca de senha remota", "alem", "comando do painel aplicado pelo Mega"),
    ("+04", "Gaveteiro por letra", "alem", "15 gavetas pela RENAME 2024"),
    ("+05", "Gabinete modular", "alem", "1 bio + 1 a 4 arm, 1592 montagens"),
    ("+06", "Trava do teclado", "alem", "5 falhas seguidas bloqueiam 60 s"),
]
COR = {"ok": (OK, "#dfeedd", "atendido"), "adapt": (WARN, "#f6e7cc", "atendido de outro jeito"),
       "nao": (BAD, "#f6dcd8", "não feito"), "alem": (BLUE, "#dbe7f2", "além do pedido")}


def matriz():
    linhas = REQ + [None] + ALEM
    W, H = 1180, 120 + 40 * len(linhas) + 30
    o = [txt(40, 46, "Requisito", 14, "start", 700, MUT), txt(470, 46, "Situação", 14, "start", 700, MUT),
         txt(700, 46, "Como", 14, "start", 700, MUT)]
    lx = 40
    for k in ("ok", "adapt", "nao", "alem"):
        c, bg, n = COR[k]
        o.append(f'<rect x="{lx}" y="{H-40}" width="18" height="18" rx="4" fill="{bg}" stroke="{c}"/>')
        o.append(txt(lx + 26, H - 26, n, 13.5, "start", color=c, weight=600)); lx += 230
    y = 64
    for l in linhas:
        if l is None:
            o.append(txt(40, y + 30, "Além do que foi pedido", 15, "start", 700, BLUE)); y += 40; continue
        cod, nome, st, como = l
        c, bg, n = COR[st]
        if cod in ("RF11",) and SEM_CAMERA:
            nome, como = "Correlação de evidências", "NTP com horário de origem em cada evento"
        o.append(f'<rect x="30" y="{y+4}" width="{W-60}" height="34" rx="8" fill="{bg}" opacity=".55"/>')
        o.append(txt(44, y + 27, cod, 14.5, "start", 700, c))
        o.append(txt(110, y + 27, nome, 14.5, "start"))
        o.append(f'<rect x="466" y="{y+10}" width="200" height="22" rx="11" fill="{PAPER}" stroke="{c}"/>')
        o.append(txt(566, y + 26, n, 12.5, color=c, weight=600))
        o.append(txt(700, y + 27, como, 14, "start", color=MUT))
        y += 40
    return svg(W, H, "".join(o), "Matriz de rastreabilidade dos requisitos")


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    for nome, f in [("casos-de-uso", casos_de_uso), ("classes", classes), ("sequencia", sequencia),
                    ("estados", estados), ("matriz", matriz)]:
        (SAIDA / f"{nome}.svg").write_text(f(), encoding="utf-8")
        print("ok", SAIDA / f"{nome}.svg")


if __name__ == "__main__":
    main()
