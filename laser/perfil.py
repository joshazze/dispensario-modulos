"""Escreve DXF no perfil que o tecnico do corte mandou.

O `Chapa1.dxf` que ele enviou em 03/09/2026 e AC1032 (AutoCAD 2018) com header
completo, tabela de camadas e secao OBJECTS. Reproduzir isso a mao e frageil e
sem graca: em vez disso o arquivo dele vira TEMPLATE. Copiamos HEADER, CLASSES,
TABLES, BLOCKS, OBJECTS e ACDSDATA byte a byte e trocamos so a secao ENTITIES.
Assim a maquina recebe exatamente a configuracao que ela ja aceita.

Perfil extraido (ver `perfis/perfil-tecnico.json`):

| item | valor |
|---|---|
| versao | AC1032 |
| unidade | `$INSUNITS` 4, milimetro, `$MEASUREMENT` 1 metrico |
| camada de corte | `CORTE`, cor ACI 1 (vermelho), Continuous, lineweight 0 |
| camada de marcacao | `MARCACAO` com cedilha e til, cor ACI 2 (amarelo) |
| moldura da folha | camada `0`, cor 7 |
| entidades | LWPOLYLINE, CIRCLE, LINE |
| arquivo | cp1252 com fim de linha CRLF |

Handle e owner importam: toda entidade leva grupo 5 (handle hexadecimal unico)
e grupo 330 apontando para o model space. Sem isso o AutoCAD recusa o arquivo.
"""
import math
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(BASE, "perfis", "chapa-tecnico.dxf")
ENCODING = "cp1252"
CAMADA_CORTE = "CORTE"
CAMADA_MARCACAO = "MARCAÇÃO"
CAMADA_MOLDURA = "0"
MODEL_SPACE = "1F"


def _pares(texto):
    linhas = texto.replace("\r\n", "\n").split("\n")
    return [(linhas[i].strip(), linhas[i + 1].strip())
            for i in range(0, len(linhas) - 1, 2)]


def carrega(template=None):
    """Devolve (prefixo, sufixo, proximo_handle) do template do tecnico."""
    with open(template or TEMPLATE, encoding=ENCODING, errors="replace") as f:
        pares = _pares(f.read())
    inicio = fim = None
    for i, (c, v) in enumerate(pares):
        if c == "2" and v == "ENTITIES" and pares[i - 1] == ("0", "SECTION"):
            inicio = i + 1
        elif inicio is not None and c == "0" and v == "ENDSEC":
            fim = i
            break
    if inicio is None or fim is None:
        raise ValueError("template sem secao ENTITIES: %s" % (template or TEMPLATE))
    usados = [int(v, 16) for c, v in pares
              if c == "5" and v and all(ch in "0123456789ABCDEFabcdef" for ch in v)]
    return pares[:inicio], pares[fim:], max(usados or [0x20]) + 1


class Escritor:
    """Acumula entidades e serializa no formato do template."""

    def __init__(self, template=None):
        self.prefixo, self.sufixo, self._handle = carrega(template)
        self.pares = []

    def _cabecalho(self, tipo, camada, subclasse):
        self.pares += [("0", tipo), ("5", "%X" % self._handle), ("330", MODEL_SPACE),
                       ("100", "AcDbEntity"), ("8", camada), ("100", subclasse)]
        self._handle += 1

    def polilinha(self, pontos, camada=CAMADA_CORTE, fechada=True):
        self._cabecalho("LWPOLYLINE", camada, "AcDbPolyline")
        self.pares += [("90", str(len(pontos))), ("70", "1" if fechada else "0"),
                       ("43", "0.0")]
        for x, y in pontos:
            self.pares += [("10", "%.6f" % x), ("20", "%.6f" % y)]

    def circulo(self, cx, cy, raio, camada=CAMADA_CORTE):
        self._cabecalho("CIRCLE", camada, "AcDbCircle")
        self.pares += [("10", "%.6f" % cx), ("20", "%.6f" % cy), ("30", "0.0"),
                       ("40", "%.6f" % raio)]

    def linha(self, x1, y1, x2, y2, camada=CAMADA_MARCACAO):
        self._cabecalho("LINE", camada, "AcDbLine")
        self.pares += [("10", "%.6f" % x1), ("20", "%.6f" % y1), ("30", "0.0"),
                       ("11", "%.6f" % x2), ("21", "%.6f" % y2), ("31", "0.0")]

    def texto(self, x, y, altura, conteudo, camada=CAMADA_MARCACAO):
        self._cabecalho("TEXT", camada, "AcDbText")
        self.pares += [("10", "%.6f" % x), ("20", "%.6f" % y), ("30", "0.0"),
                       ("40", "%.6f" % altura), ("1", conteudo),
                       ("100", "AcDbText")]

    def serializa(self):
        # $HANDSEED e o proximo handle livre. Herdado do template fica abaixo dos
        # handles novos e o AutoCAD para a abertura num "Press ENTER to continue".
        prefixo = list(self.prefixo)
        for i, (c, v) in enumerate(prefixo[:-1]):
            if c == "9" and v == "$HANDSEED":
                prefixo[i + 1] = (prefixo[i + 1][0], "%X" % self._handle)
        saida = []
        for c, v in prefixo + self.pares + self.sufixo:
            saida.append("%3s" % c if len(c) <= 3 else c)
            saida.append(v)
        return "\r\n".join(saida) + "\r\n"

    def escreve(self, caminho):
        with open(caminho, "w", encoding=ENCODING, errors="replace",
                  newline="") as f:
            f.write(self.serializa())


def _circulo_de(pontos, tol=0.05):
    """So devolve centro e raio quando o poligono E MESMO um circulo.

    Erro ja pago: a versao antiga comparava o raio medio a partir
    do CENTROIDE com folga de 1%. Retangulo arredondado tem pontos so nos
    quatro cantos, todos a meia diagonal do centro, entao ele passava no teste:
    o sub-painel de 240 x 560 saiu no DXF como uma circunferencia de raio 303 e
    a peca nao foi cortada. Agora o teste e absoluto e em tres frentes:
    bbox quadrada, raio medido da bbox e desvio maximo de 0,05 mm.
    """
    if len(pontos) < 24:
        return None
    xs = [x for x, _ in pontos]
    ys = [y for _, y in pontos]
    largura, altura = max(xs) - min(xs), max(ys) - min(ys)
    if largura <= 0 or abs(largura - altura) > tol:
        return None
    cx, cy, raio = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0, largura / 2.0
    if any(abs(math.hypot(x - cx, y - cy) - raio) > tol for x, y in pontos):
        return None
    return cx, cy, raio


def escreve(caminho, cortes, marcas=(), textos=(), template=None):
    """Grava o DXF no perfil do tecnico.

    `cortes` sao os contornos fechados, `marcas` as polilinhas de marcacao e
    `textos` os rotulos. Nada de moldura da mesa no arquivo, e o ponto mais
    baixo a esquerda do desenho vai para (0, 0): e por ele que as pecas se
    alinham na maquina.
    """
    pontos = [p for poly in list(cortes) + list(marcas) for p in poly]
    dx = min((x for x, _ in pontos), default=0.0)
    dy = min((y for _, y in pontos), default=0.0)
    cortes = [[(x - dx, y - dy) for x, y in poly] for poly in cortes]
    marcas = [[(x - dx, y - dy) for x, y in m] for m in marcas]
    textos = [dict(t, x=t["x"] - dx, y=t["y"] - dy) for t in textos]
    e = Escritor(template)
    for poly in cortes:
        circ = _circulo_de(poly)
        if circ:
            e.circulo(circ[0], circ[1], circ[2])
        else:
            e.polilinha(poly, camada=CAMADA_CORTE)
    for m in marcas:
        if len(m) > 1:
            e.polilinha(m, camada=CAMADA_MARCACAO, fechada=False)
    for t in textos:
        e.texto(t["x"], t["y"], t.get("tamanho", 5.0), t["texto"])
    e.escreve(caminho)
    return e
