from laser import perfil


def _pares(texto):
    linhas = texto.split("\r\n")
    return [(linhas[i].strip(), linhas[i + 1].strip())
            for i in range(0, len(linhas) - 1, 2)]


def test_handseed_fica_acima_de_todo_handle_escrito():
    escritor = perfil.Escritor()
    for i in range(300):
        escritor.circulo(i * 10.0, 0.0, 2.0)
    pares = _pares(escritor.serializa())
    posicao = [i + 1 for i, p in enumerate(pares) if p == ("9", "$HANDSEED")]
    seed = [pares[i][1] for i in posicao]
    handles = [int(v, 16) for i, (c, v) in enumerate(pares)
               if c == "5" and i not in posicao]
    assert len(seed) == 1
    assert int(seed[0], 16) > max(handles)


def test_desenho_sai_sem_moldura_e_com_o_canto_de_baixo_a_esquerda_na_origem(tmp_path):
    quadrado = [(500.0, 300.0), (600.0, 300.0), (600.0, 400.0), (500.0, 400.0)]
    retangulo = [(420.0, 350.0), (480.0, 350.0), (480.0, 380.0), (420.0, 380.0)]
    escritor = perfil.escreve(tmp_path / "t.dxf", [quadrado, retangulo])
    xs = [float(v) for c, v in escritor.pares if c == "10"]
    ys = [float(v) for c, v in escritor.pares if c == "20"]
    camadas = {v for c, v in escritor.pares if c == "8"}
    assert (min(xs), min(ys)) == (0.0, 0.0)
    assert (max(xs), max(ys)) == (180.0, 100.0)
    assert camadas == {perfil.CAMADA_CORTE}
