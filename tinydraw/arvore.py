"""

    # Estrutura intermediária: árvore sintática abstrata (AST) do TinyDraw,
    produzida pela análise sintática.
    - cada nó é uma instância de uma das dataclasses abaixo;
    - cada nó guarda a linha e a coluna do token que o originou, para que as
      fases seguintes possam emitir diagnósticos posicionados.

"""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class No:
    linha: int
    coluna: int

@dataclass
class Tela(No):
    largura: int
    altura: int

@dataclass
class DeclaracaoCor(No):
    nome: str
    r: int
    g: int
    b: int

@dataclass
class SelecaoCor(No):
    nome: str

@dataclass
class Ponto(No):
    x: int
    y: int

@dataclass
class Linha(No):
    x1: int
    y1: int
    x2: int
    y2: int

@dataclass
class Retangulo(No):
    x: int
    y: int
    largura: int
    altura: int

@dataclass
class Salvar(No):
    arquivo: str

@dataclass
class Programa(No):
    tela: Tela
    comandos: list[No] = field(default_factory=list)
    salvar: Salvar | None = None
