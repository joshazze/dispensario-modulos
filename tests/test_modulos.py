import json
from pathlib import Path

import gerador
from laser import geom


ROOT = Path(__file__).resolve().parents[1]


def load_spec():
    return json.loads((ROOT / "specs" / "modulos.json").read_text())


def build():
    spec = load_spec()
    cuts, engrave, w, h, placed = gerador.build_sheet(spec, gerador.make_groups(spec))
    return spec, cuts, engrave, w, h, placed


def colocadas(spec, placed):
    """Contorno, vazios e codigo de cada peca, ja em coordenada de prancha."""
    saida = []
    for unit, x, y, gira in placed:
        polys = gerador.rot90(unit["polys"]) if gira else unit["polys"]
        vazios = [gerador._gira_rect(v, unit["h"]) if gira else v
                  for v in unit["vazios"]]  # noqa: E501
        saida.append({
            "code": unit["code"],
            "contorno": gerador.moved(polys[0], x, y),
            "vazios": [(vx + x, vy + y, vw, vh) for vx, vy, vw, vh in vazios],
        })
    return saida


def dentro(caixa, rect):
    x0, y0, x1, y1 = caixa
    rx, ry, rw, rh = rect
    return (x0 >= rx - 1e-6 and y0 >= ry - 1e-6
            and x1 <= rx + rw + 1e-6 and y1 <= ry + rh + 1e-6)


def test_paineis_usam_duas_laminas_de_tres_milimetros():
    spec = load_spec()
    assert spec["camadas_por_painel"] == 2
    assert spec["espessura_mm"] == 3.0
    assert spec["espessura_final_mm"] == 6.0
    assert spec["junta_dedo"]["profundidade_mm"] == 6.0
    assert spec["fixacoes_m3"] is False


def test_seis_faces_por_modulo_em_duas_laminas():
    groups = gerador.make_groups(load_spec())
    assert len(groups) == 12
    assert sum(len(group["pieces"]) for group in groups) == 24
    codes = {piece["code"] for group in groups for piece in group["pieces"]}
    assert len(codes) == 24
    assert {"B1I", "B6E", "A1I", "A6E"} <= codes


def test_prancha_e_uma_so_com_legenda_portas_tampas_e_sub_painel():
    _, _, engrave, _, _, placed = build()
    codes = {u["code"] for u, _, _, _ in placed}
    gravados = {i["texto"] for i in engrave if i["tipo"] == "texto"}
    assert len(placed) == 39
    assert "BPM" in codes                                 # placa de manutencao do fundo
    assert {"BP1", "BP2", "BP3"} <= codes                 # tres prateleiras, uma lamina
    assert {"ATR", "ATF", "BTR", "BTF"} <= codes          # tampa rosqueada e cega
    assert "BSP" in codes                                 # sub-painel da interface
    # tres folhas de porta, duas laminas cada, peca solta na prancha
    assert {"AP1I", "AP2I", "AP3I", "AP1E", "AP2E", "AP3E"} <= codes
    naMaquina = {i["texto"] for i in engrave
                 if i["tipo"] == "texto" and i.get("machine", True)}
    assert not naMaquina         # sem gravacao: texto nao vai pra maquina
    assert gravados              # mas o PDF de conferencia mantem o codigo


def test_desenho_sai_sem_texto_e_sem_azul():
    """Gravacao custa tempo de maquina: o desenho sai limpo."""
    spec, _, engrave, w, h, _ = build()
    assert spec["gravar_codigos"] is False
    assert not [i for i in engrave
                if i["tipo"] == "texto" and i.get("machine", True)]
    svg = gerador.svg_sheet([], engrave, w, h, labels=True)
    assert "#0000ff" not in svg and "<text" not in svg


def test_passa_fio_fica_nas_laterais_e_nao_nas_faces_grandes():
    """Um furo na face 2 e um na face 4. Nada de passa-fio no fundo nem na porta."""
    spec = load_spec()
    groups = gerador.make_groups(spec)
    por_codigo = {p["code"]: p for g in groups for p in g["pieces"]}
    d = spec["passa_fio"]["diametro_mm"]

    def passa_fios(code):
        return [f for f in por_codigo[code]["fasteners"]
                if abs(geom.bbox(f)[2] - geom.bbox(f)[0] - d) < 1e-6]

    for code in ("A2I", "A2E", "A4I", "A4E", "B2I", "B2E", "B4I", "B4E"):
        assert len(passa_fios(code)) == 1, code
    for code in ("A1I", "A1E", "A6I", "A6E", "B1I", "B1E", "B6I", "B6E"):
        assert passa_fios(code) == [], code
    for code in ("B6I", "B6E"):
        assert por_codigo[code]["vazios"], code       # janela da interface e vazio util
    for code in ("A6I", "A6E"):
        assert len(por_codigo[code]["vazios"]) == 3   # tres pilulas, tres vazios uteis


def test_o_vao_da_porta_sai_com_uma_linha_de_corte_so():
    """Contorno concentrico dentro do vao faria a maquina cortar um anel de refugo."""
    spec, _, _, _, _, placed = build()
    porta = spec["porta"]
    for unit, _, _, gira in placed:
        if unit["code"] not in ("A6I", "A6E"):
            continue
        polys = gerador.rot90(unit["polys"]) if gira else unit["polys"]
        assert len(polys) == 1 + porta["quantidade"]      # contorno + 3 vaos
    folhas = [u for u, _, _, _ in placed if u["code"].startswith("AP")]
    assert len(folhas) == 6
    for unit in folhas:
        assert abs(unit["w"] - (porta["pilula_largura_mm"] - 2 * porta["folga_folha_mm"])) < 1e-6
        assert abs(unit["h"] - (porta["pilula_altura_mm"] - 2 * porta["folga_folha_mm"])) < 1e-6


def test_nenhuma_peca_invade_outra():
    """Peca desenhada em cima de outra reprova.

    Bbox dentro de bbox nao e sobreposicao quando a de dentro esta num vazio
    declarado: e o erro oposto, confundir peca aninhada com furo.
    """
    spec, _, _, w, h, placed = build()
    pecas = colocadas(spec, placed)
    gap = spec["encaixe"]["folga_entre_pecas_mm"]
    vazio = spec["encaixe"]["margem_vazio_mm"]
    todos = [v for p in pecas for v in p["vazios"]]
    caixas = [geom.bbox(p["contorno"]) for p in pecas]
    for i, a in enumerate(caixas):
        assert a[0] >= -1e-6 and a[1] >= -1e-6 and a[2] <= w + 1e-6 and a[3] <= h + 1e-6
        for j in range(i + 1, len(caixas)):
            b = caixas[j]
            folga = max(max(a[0] - b[2], b[0] - a[2]),
                        max(a[1] - b[3], b[1] - a[3]))
            no_mesmo_vazio = any(dentro(a, v) and dentro(b, v) for v in todos)
            aninhada = (any(dentro(b, v) for v in pecas[i]["vazios"])
                        or any(dentro(a, v) for v in pecas[j]["vazios"]))
            minimo = vazio if (no_mesmo_vazio or aninhada) else gap
            assert folga >= minimo - 1e-6 or aninhada, \
                "%s x %s: folga %.2f" % (pecas[i]["code"], pecas[j]["code"], folga)


def test_dfm_passa_em_todas_as_pecas():
    spec, _, _, _, _, placed = build()
    assert gerador.valida_prancha(spec, placed) == []


def test_filtro_recorta_o_banco_de_pecas():
    """A camada externa do biometrico e um subconjunto, nao um segundo desenho."""
    spec = load_spec()
    groups = gerador.make_groups(spec)
    _, engrave, w, _, placed = gerador.build_sheet(
        spec, groups, filtro=r"^B[1-6]E$", titulo="PSE BIOMETRICO")
    codes = sorted(u["code"] for u, _, _, _ in placed)
    assert codes == ["B1E", "B2E", "B3E", "B4E", "B5E", "B6E"]
    assert [i for i in engrave if i["tipo"] == "moldura"]   # mesas desenhadas
    assert gerador.valida_prancha(spec, placed) == []


def test_prateleira_bate_com_o_rasgo_da_lateral():
    """Aba da prateleira e rasgo da parede tem que ter a MESMA cota."""
    spec = load_spec()
    pr = spec["prateleiras"]
    groups = gerador.make_groups(spec)
    por_codigo = {p["code"]: p for g in groups for p in g["pieces"]}
    largura, altura = pr["aba_largura_mm"], pr["espessura_mm"]
    for code in ("B2I", "B2E", "B4I", "B4E"):
        rasgos = []
        for f in por_codigo[code]["fasteners"]:
            x0, y0, x1, y1 = geom.bbox(f)
            if abs(x1 - x0 - largura) < 1e-6 and abs(y1 - y0 - altura) < 1e-6:
                rasgos.append((x0 + x1) / 2.0)
        assert len(rasgos) == 3 * 2, code          # tres alturas, duas abas
        assert len(set(round(x, 3) for x in rasgos)) == 2

    contorno = gerador.prateleira_u(pr)
    x0, y0, x1, y1 = geom.bbox(contorno)
    assert abs((x1 - x0) - (pr["largura_mm"] + 2 * pr["aba_mm"])) < 1e-6
    assert abs((y1 - y0) - pr["profundidade_mm"]) < 1e-6
    # o recorte em U e aberto na frente, entao ele faz parte do contorno
    assert any(abs(y - pr["recorte_profundidade_mm"]) < 1e-6 for _, y in contorno)


def test_tampas_moram_dentro_da_janela_da_interface():
    spec, _, _, _, _, placed = build()
    pos = {u["code"]: (u, x, y, g) for u, x, y, g in placed}
    host, hx, hy, hgira = pos["B6E"]
    vazios = [gerador._gira_rect(v, host["h"]) if hgira else v
              for v in host["vazios"]]
    janela = [(vx + hx, vy + hy, vw, vh) for vx, vy, vw, vh in vazios]
    for code in ("BTR", "BTF"):
        unit, x, y, gira = pos[code]
        w, h = (unit["h"], unit["w"]) if gira else (unit["w"], unit["h"])
        assert any(dentro((x, y, x + w, y + h), v) for v in janela), code


def test_placa_de_manutencao_cobre_o_vao_e_bate_com_os_furos():
    """A placa recua da aresta do modulo mas sobrepoe o vao com folga."""
    spec = load_spec()
    man = spec["manutencao"]
    bio = [m for m in spec["modulos"] if m["codigo"] == "B"][0]
    assert man["placa_largura_mm"] < bio["largura_externa_mm"]
    assert man["placa_altura_mm"] < bio["altura_externa_mm"]
    # sobreposicao sobre a moldura, dos dois lados, com o parafuso dentro dela
    sobreposicao = man["borda_mm"] - man["recuo_placa_mm"]
    assert man["placa_largura_mm"] >= man["vao_largura_mm"] + 2 * sobreposicao
    assert man["placa_altura_mm"] >= man["vao_altura_mm"] + 2 * sobreposicao
    assert man["recuo_parafuso_mm"] >= sobreposicao / 2.0

    groups = gerador.make_groups(spec)
    por_codigo = {p["code"]: p for g in groups for p in g["pieces"]}
    piloto = spec["passa_fio"]["furo_piloto_mm"]
    for code in ("B1I", "B1E"):
        furos = [f for f in por_codigo[code]["fasteners"]
                 if abs(geom.bbox(f)[2] - geom.bbox(f)[0] - piloto) < 1e-6
                 and abs(geom.bbox(f)[3] - geom.bbox(f)[1] - piloto) < 1e-6]
        assert len(furos) == 2 * man["linhas_parafuso"], code
        assert por_codigo[code]["vazios"], code       # o vao vira retangulo util

    placa = [e for e in spec["pecas_extras"] if e["codigo"] == "BPM"][0]
    ab = placa["aberturas"][0]
    assert (ab["passo_x_mm"], ab["passo_y_mm"]) == (man["passo_x_mm"], man["passo_y_mm"])
    assert ab["linhas_y"] == man["linhas_parafuso"]


def test_agulha_da_prateleira_afina_para_a_frente():
    """Garfo: a ponta e bem mais fina que a raiz, e a aba fica na parte grossa."""
    spec = load_spec()
    pr = spec["prateleiras"]
    ponta = pr["ponta_mm"]
    raiz = (pr["largura_mm"] - pr["recorte_largura_mm"]) / 2.0
    assert ponta < raiz / 3.0
    assert ponta >= spec["espessura_final_mm"] * 2      # piso DFM da peca fina
    contorno = gerador.prateleira_u(pr)
    x0, _, x1, _ = geom.bbox(contorno)
    assert abs((x1 - x0) - (pr["largura_mm"] + 2 * pr["aba_mm"])) < 1e-6
    # na frente (y = 0) so restam as duas agulhas
    na_frente = sorted(x for x, y in contorno if abs(y) < 1e-6)
    assert abs((na_frente[1] - na_frente[0]) - ponta) < 1e-6
    assert abs((na_frente[-1] - na_frente[-2]) - ponta) < 1e-6


def test_gota_de_parede_aponta_pra_cima_e_escapa_da_placa():
    """Fenda pra cima nas quatro: o modulo desce sobre o parafuso ja chumbado."""
    spec = load_spec()
    fix = spec["fixacao_parede"]
    man = spec["manutencao"]
    groups = gerador.make_groups(spec)
    por_codigo = {p["code"]: p for g in groups for p in g["pieces"]}
    for code in ("B1I", "B1E"):
        alt_esperada = (fix["cabeca_mm"] / 2.0 + fix["comprimento_mm"]
                        + fix["haste_mm"] / 2.0)
        gotas = [f for f in por_codigo[code]["fasteners"]
                 if abs(geom.bbox(f)[3] - geom.bbox(f)[1] - alt_esperada) < 1e-6]
        assert len(gotas) == fix["quantidade"], code
        for g in gotas:
            x0, y0, x1, y1 = geom.bbox(g)
            # a fenda fica em CIMA: a largura no topo e a da haste, nao a da cabeca
            no_topo = [x for x, y in g if y > y1 - 0.5]
            assert max(no_topo) - min(no_topo) <= fix["haste_mm"] + 1e-6
            # e a cabeca redonda fica embaixo, com o diametro cheio
            meio_cabeca = [x for x, y in g if abs(y - (y0 + fix["cabeca_mm"] / 2.0)) < 0.5]
            assert max(meio_cabeca) - min(meio_cabeca) > fix["haste_mm"] * 1.5
            assert abs((x1 - x0) - fix["cabeca_mm"]) < 0.05
    assert man["recuo_placa_mm"] > 0
    _, _, _, _, placed = gerador.build_sheet(spec, groups, filtro=r"^B1[IE]$")
    assert gerador.valida_prancha(spec, placed) == []


def test_gota_nao_fica_debaixo_da_placa_de_manutencao():
    spec = load_spec()
    fix = spec["fixacao_parede"]
    man = spec["manutencao"]
    H = [m for m in spec["modulos"] if m["codigo"] == "B"][0]["altura_externa_mm"]
    faixa_baixa = man["recuo_placa_mm"]
    faixa_alta = H - man["recuo_placa_mm"]
    topo_da_fenda = fix["comprimento_mm"] + fix["haste_mm"] / 2.0
    # gota de baixo: cabeca e fenda inteiras abaixo da placa
    assert fix["y_baixo_mm"] + topo_da_fenda <= faixa_baixa
    assert fix["y_baixo_mm"] - fix["cabeca_mm"] / 2.0 >= 2 * spec["espessura_mm"]
    # gota de cima: cabeca inteira acima da placa, fenda longe da borda
    assert fix["y_alto_mm"] - fix["cabeca_mm"] / 2.0 >= faixa_alta
    assert H - (fix["y_alto_mm"] + topo_da_fenda) >= 2 * spec["espessura_mm"]


def _rasgos_eg(peca, eg, em_pe):
    """Separa os rasgos de enforca-gato pela orientacao do retangulo."""
    comp, larg = eg["rasgo_comprimento_mm"], eg["rasgo_largura_mm"]
    alvo = (larg, comp) if em_pe else (comp, larg)
    saida = []
    for f in peca["fasteners"]:
        x0, y0, x1, y1 = geom.bbox(f)
        if abs(x1 - x0 - alvo[0]) < 1e-6 and abs(y1 - y0 - alvo[1]) < 1e-6:
            saida.append(f)
    return saida


def test_enforca_gato_em_pe_com_uma_dupla_por_peca():
    """Nos cantos verticais: rasgo em pe, par LADO A LADO, junto da aresta."""
    spec = load_spec()
    eg = spec["enforca_gato"]
    comp, larg = eg["rasgo_comprimento_mm"], eg["rasgo_largura_mm"]
    assert comp > larg                        # rasgo em pe, nao deitado
    assert larg > eg["fita_espessura_mm"]
    assert comp > eg["fita_largura_mm"]
    groups = gerador.make_groups(spec)
    por_codigo = {p["code"]: p for g in groups for p in g["pieces"]}
    esperado = 2 * len(eg["alturas_mm"]) * 2  # duas arestas, N estacoes, um par
    for face in eg["faces"]:
        for lamina in ("I", "E"):
            code = "B%d%s" % (face, lamina)
            rasgos = _rasgos_eg(por_codigo[code], eg, em_pe=True)
            assert len(rasgos) == esperado, code
            x0, _, x1, _ = geom.bbox(por_codigo[code]["outline"])
            limite = eg["recuo_aresta_mm"] + eg["afastamento_par_mm"]
            for r in rasgos:
                cx = (geom.bbox(r)[0] + geom.bbox(r)[2]) / 2.0
                assert min(cx - x0, x1 - cx) <= limite + 1e-6
            alturas = {round((geom.bbox(r)[1] + geom.bbox(r)[3]) / 2.0, 3) for r in rasgos}
            assert len(alturas) == len(eg["alturas_mm"])
            larguras = {round((geom.bbox(r)[0] + geom.bbox(r)[2]) / 2.0, 3) for r in rasgos}
            assert len(larguras) == 4


def test_junta_horizontal_tem_dupla_em_cada_parede_e_quatro_no_piso():
    """Parede leva par no topo e no rodape; piso e teto levam 4 duplas radiais."""
    spec = load_spec()
    eg = spec["enforca_gato"]
    groups = gerador.make_groups(spec)
    por_codigo = {p["code"]: p for g in groups for p in g["pieces"]}
    for face in eg["faces"]:
        for lamina in ("I", "E"):
            peca = por_codigo["B%d%s" % (face, lamina)]
            deitados = _rasgos_eg(peca, eg, em_pe=False)
            assert len(deitados) == 4, "B%d%s" % (face, lamina)
            _, y0, _, y1 = geom.bbox(peca["outline"])
            perto_do_topo = [r for r in deitados
                             if y1 - (geom.bbox(r)[1] + geom.bbox(r)[3]) / 2.0 < 60]
            assert len(perto_do_topo) == 2
    for face in eg["faces_tampa"]:
        for lamina in ("I", "E"):
            peca = por_codigo["B%d%s" % (face, lamina)]
            total = (len(_rasgos_eg(peca, eg, em_pe=False))
                     + len(_rasgos_eg(peca, eg, em_pe=True)))
            assert total == 8, "B%d%s" % (face, lamina)   # 4 duplas radiais


def test_prancha_nao_gira_peca_quando_a_trava_esta_ligada():
    """Peca deitada no desenho contra peca em pe no modulo confunde a conferencia."""
    spec = load_spec()
    assert spec["folha"]["travar_rotacao"] is False   # eficiencia venceu
    assert spec["folha"]["bloco_mm"] == [1000.0, 1000.0]


def test_mesa_1150x1000_deixa_toda_peca_retangular_deitada():
    spec = load_spec()
    assert spec["folha"]["mesa_mm"] == [1150.0, 1000.0]
    assert spec["folha"]["retangulares_deitadas"] is True
    groups = gerador.make_groups(spec)
    _, _, _, _, placed = gerador.build_sheet(spec, groups, filtro="^B")
    for unit, _, _, gira in placed:
        largura = unit["h"] if gira else unit["w"]
        altura = unit["w"] if gira else unit["h"]
        if abs(unit["w"] - unit["h"]) > 1e-9:
            assert largura > altura, unit["code"]


def test_cada_cama_tem_no_maximo_um_metro_de_largura():
    """A mesa tem 1150, mas a carga usa 1000 de largura e a sobra fica de folga."""
    spec = load_spec()
    groups = gerador.make_groups(spec)
    _, _, _, _, placed = gerador.build_sheet(spec, groups, filtro="^B")
    for ox, oy, bw, bh, fora in gerador.build_sheet.molduras:
        dentro = [(x, unit["h"] if gira else unit["w"]) for unit, x, y, gira in placed
                  if ox - 1e-6 <= x < ox + bw and oy - 1e-6 <= y < oy + bh]
        assert dentro
        esquerda = min(x for x, _ in dentro)
        direita = max(x + w for x, w in dentro)
        assert direita - esquerda <= 1000.0 + 1e-6, (ox, oy)


def test_enforca_gato_nao_encosta_em_outra_feicao():
    """Ponte de 3,75 mm entre o rasgo e a borda da janela ja passou aqui.

    O DFM aceita 1,5 mm (metade da espessura), mas isso e piso de ruptura, nao
    projeto: aqui a barra e 3x a espessura.
    """
    spec = load_spec()
    eg = spec["enforca_gato"]
    piso = 3.0 * spec["espessura_mm"]
    groups = gerador.make_groups(spec)
    por_codigo = {p["code"]: p for g in groups for p in g["pieces"]}
    for face in eg["faces"]:
        for lamina in ("I", "E"):
            peca = por_codigo["B%d%s" % (face, lamina)]
            rasgos = (_rasgos_eg(peca, eg, em_pe=True)
                      + _rasgos_eg(peca, eg, em_pe=False))
            outros = [f for f in peca["fasteners"] if f not in rasgos]
            for r in rasgos:
                for o in outros:
                    d = geom.dist_poligonos(r, o)
                    assert d >= piso, "B%d%s: ponte de %.2f mm" % (face, lamina, d)
