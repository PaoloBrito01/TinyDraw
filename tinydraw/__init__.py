"""

    # TinyDraw: DSL para descrição de desenhos simples.
    - fonte -> tokens -> AST -> AST validada -> código C

"""

from __future__ import annotations
from . import gerador, lexico, semantico, sintatico

# Define exportação de funções e módulos do pacote tinydraw
__all__ = ["transpilar", "lexico", "sintatico", "semantico", "gerador"]

# Função principal para transpilar código TinyDraw para C
def transpilar(codigo: str) -> str:
    """Executa o pipeline completo e devolve o código C equivalente."""
    tokens = lexico.tokenizar(codigo)
    programa = sintatico.analisar(tokens)
    tabela = semantico.analisar(programa)
    return gerador.gerar(programa, tabela)
