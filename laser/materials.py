"""Registro de material: kerf, espessura real e folga, com origem e data.

O ponto todo e a diferenca entre `estimado` e `medido`. Enquanto o numero nao
veio de um cupom cortado na propria maquina, ele e chute, e o build tem que
dizer isso em voz alta. As fontes publicadas divergem em FATOR 3 para o mesmo
par material/espessura (MDF 3 mm: 0,08 na Sculpteo, 0,30 num GS9070 de 100 W),
entao tabela serve so pra escolher o ponto de partida do cupom.
"""
import json
import os

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PADRAO = os.path.join(AQUI, "materiais.json")


class Material(dict):
    @property
    def estimado(self):
        return self.get("origem") != "medido"

    @property
    def aviso(self):
        if not self.estimado:
            return ""
        return ("material %s: kerf %.3f e espessura %.2f sao ESTIMATIVA, nao medida. "
                "Cortar um cupom de calibracao em %s antes de "
                "confiar no encaixe."
                % (self.get("_slug", "?"), self.get("kerf", 0.0),
                   self.get("espessura_real", 0.0), self.get("material", "?")))


def carrega(caminho=None):
    with open(caminho or PADRAO, encoding="utf-8") as f:
        return json.load(f)


def busca(slug, caminho=None):
    """Devolve o Material do slug (ex.: 'acrilico-3mm'), ou None."""
    if not slug:
        return None
    d = carrega(caminho)
    m = (d.get("materiais") or {}).get(slug)
    if m is None:
        return None
    out = Material(m)
    out["_slug"] = slug
    out["_maquina_padrao"] = d.get("maquina_padrao")
    return out


def lista(caminho=None):
    return sorted((carrega(caminho).get("materiais") or {}).keys())


def da_spec(spec, caminho=None):
    """Material referenciado por uma spec. A spec pode dizer `material` (slug do
    registro) e ainda assim sobrescrever `espessura_mm` e `kerf_mm`: valor
    escrito na spec ganha, porque as vezes a chapa da vez e outra."""
    m = busca(spec.get("material"), caminho)
    if m is None:
        m = Material(dict(kerf=float(spec.get("kerf_mm", 0.0) or 0.0),
                          espessura_real=float(spec.get("espessura_mm", 0.0) or 0.0),
                          folga_dedo=0.0, folga_bolso=0.3,
                          ponte_minima=float(spec.get("espessura_mm", 3.0) or 3.0),
                          origem="spec", material="?"))
        m["_slug"] = "(sem registro)"
        return m
    if "espessura_mm" in spec:
        m["espessura_real"] = float(spec["espessura_mm"])
    if "kerf_mm" in spec:
        m["kerf"] = float(spec["kerf_mm"])
    return m


def registra_medida(slug, caminho=None, **campos):
    """Grava numero medido e promove a origem de `estimado` para `medido`.
    E o passo que fecha o laco depois de cortar o cupom."""
    import datetime
    caminho = caminho or PADRAO
    d = carrega(caminho)
    mats = d.setdefault("materiais", {})
    m = mats.setdefault(slug, {})
    m.update({k: v for k, v in campos.items() if v is not None})
    m["origem"] = "medido"
    m["medido_em"] = datetime.date.today().isoformat()
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, caminho)
    return Material(m)
