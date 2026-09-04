"""

    # Diagnósticos do transpilador:
    - cada erro é uma instância de uma subclasse de ErroTinyDraw;
    - cada erro guarda a linha e a coluna do token que o originou, para que os
      diagnósticos sejam posicionados, no formato:

        arquivo:linha:coluna: <fase>: mensagem

"""

from __future__ import annotations

class ErroTinyDraw(Exception):
  
    fase = "erro"

    def __init__(self, mensagem: str, linha: int, coluna: int):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna

    def formatar(self, arquivo: str = "<entrada>") -> str:
        return f"{arquivo}:{self.linha}:{self.coluna}: {self.fase}: {self.mensagem}"


class ErroLexico(ErroTinyDraw):
    fase = "erro léxico"


class ErroSintatico(ErroTinyDraw):
    fase = "erro sintático"


class ErroSemantico(ErroTinyDraw):
    fase = "erro semântico"


class ErroSemanticoMultiplo(ErroTinyDraw):
    # Agrupa os erros de uma passagem semântica para relatá-los de uma vez.
    fase = "erro semântico"
    # Lista de erros semânticos encontrados na análise.
    def __init__(self, erros: list[ErroSemantico]):
        self.erros = list(erros)
        primeiro = self.erros[0]
        super().__init__(
            f"{len(self.erros)} erro(s) semântico(s)",
            primeiro.linha,
            primeiro.coluna,
        )

    def formatar(self, arquivo: str = "<entrada>") -> str:
        return "\n".join(erro.formatar(arquivo) for erro in self.erros)
