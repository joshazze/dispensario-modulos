"""Biblioteca de corte a laser usada pelo gerador dos modulos.

Python puro, sem dependencia externa.

    geom       primitivas de poligono, cantos, topologia
    perfil     escritor de DXF no perfil AutoCAD 2018 que a maquina aceita
    report     aproveitamento, perimetro, tempo, ponte mais fina
    materials  registro de material, com origem `estimado` ou `medido`
"""
from . import geom, materials, perfil, report

__all__ = ["geom", "perfil", "report", "materials"]
