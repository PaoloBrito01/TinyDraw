"""

    # Análise sintática(descida recursiva, LL(1)).
    - Gramática da linguagem é declarada em EBNF(linguagem de Backus-Naur Estendida):

    programa      ::= decl_tela { comando } cmd_salvar FIM
    decl_tela     ::= "tela" NUMERO "por" NUMERO
    comando       ::= decl_cor | sel_cor | cmd_ponto | cmd_linha | cmd_retangulo
    decl_cor      ::= "cor" NOME_COR "=" NUMERO "," NUMERO "," NUMERO
    sel_cor       ::= "usar" NOME_COR
    cmd_ponto     ::= "ponto" "em" coordenada
    cmd_linha     ::= "linha" "de" coordenada "ate" coordenada
    cmd_retangulo ::= "retangulo" "em" coordenada "tamanho" NUMERO "por" NUMERO
    cmd_salvar    ::= "salvar" CADEIA
    coordenada    ::= NUMERO "," NUMERO

    - Gramática da linguagem é LL(1): cada alternativa de `comando` é decidida pelo token
      corrente, sem retrocesso e sem necessidade de lookahead adicional.

"""

from __future__ import annotations
from . import arvore
from .erros import ErroSintatico
from .lexico import Token

# Lexemas amigáveis para as mensagens de erro, para cada tipo de token.
_NOMES_AMIGAVEIS = {
    "TELA": "'tela'",
    "COR": "'cor'",
    "USAR": "'usar'",
    "PONTO": "'ponto'",
    "LINHA": "'linha'",
    "RETANGULO": "'retangulo'",
    "SALVAR": "'salvar'",
    "EM": "'em'",
    "DE": "'de'",
    "ATE": "'ate'",
    "TAMANHO": "'tamanho'",
    "POR": "'por'",
    "IGUAL": "'='",
    "VIRGULA": "','",
    "NUMERO": "um número inteiro",
    "CADEIA": "um nome de arquivo entre aspas",
    "NOME_COR": "um nome de cor em maiúsculas",
    "FIM": "o fim do programa",
}

# Conjunto de tokens que iniciam um comando.
_INICIO_COMANDO = {"COR", "USAR", "PONTO", "LINHA", "RETANGULO"}

# Classe que implementa o analisador sintático da linguagem TinyDraw.
class AnalisadorSintatico:
    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._pos = 0

    # Funções auxiliares para consumir tokens e verificar o token corrente.
    @property
    def _atual(self) -> Token:
        return self._tokens[self._pos]
    # Função para consumir o token corrente, verificando se ele é do tipo esperado.
    def _consumir(self, tipo: str) -> Token:
        token = self._atual
        if token.tipo != tipo:
            esperado = _NOMES_AMIGAVEIS.get(tipo, tipo)
            encontrado = (
                _NOMES_AMIGAVEIS.get(token.tipo, token.tipo)
                if token.tipo == "FIM"
                else f"{token.lexema!r}"
            )
            raise ErroSintatico(
                f"esperava {esperado}, encontrou {encontrado}",
                token.linha,
                token.coluna,
            )
        self._pos += 1
        return token
    # Função para verificar se o token corrente é do tipo esperado, sem consumir
    def _numero(self) -> tuple[int, Token]:
        token = self._consumir("NUMERO")
        return int(token.lexema), token
    # Função para analisar uma coordenada, que consiste em dois números separados por vírgula
    def _coordenada(self) -> tuple[int, int, Token]:
        x, token = self._numero()
        self._consumir("VIRGULA")
        y, _ = self._numero()
        return x, y, token

    # Produz a AST a partir dos tokens, seguindo a gramática acima.
    def analisar(self) -> arvore.Programa:
        tela = self._decl_tela()
        programa = arvore.Programa(tela.linha, tela.coluna, tela=tela)
        # Loop para analisar os comandos do programa, enquanto houver tokens que iniciam um comando
        while self._atual.tipo in _INICIO_COMANDO:
            programa.comandos.append(self._comando())

        programa.salvar = self._cmd_salvar()
        self._consumir("FIM")
        return programa
    # decl_tela ::= "tela" NUMERO "por" NUMERO
    def _decl_tela(self) -> arvore.Tela:
        token = self._consumir("TELA")
        largura, _ = self._numero()
        self._consumir("POR")
        altura, _ = self._numero()
        return arvore.Tela(token.linha, token.coluna, largura, altura)
    # Função para analisar um comando, que pode ser uma declaração de cor, seleção de cor, ponto, linha ou retângulo
    def _comando(self):
        despacho = {
            "COR": self._decl_cor,
            "USAR": self._sel_cor,
            "PONTO": self._cmd_ponto,
            "LINHA": self._cmd_linha,
            "RETANGULO": self._cmd_retangulo,
        }
        return despacho[self._atual.tipo]()
    # Função para analisar a declaração de cor, que consiste em um token "COR" seguido por um nome de cor, um sinal de igual e três números separados por vírgula
    def _decl_cor(self) -> arvore.DeclaracaoCor:
        token = self._consumir("COR")
        nome = self._consumir("NOME_COR").lexema
        self._consumir("IGUAL")
        r, _ = self._numero()
        self._consumir("VIRGULA")
        g, _ = self._numero()
        self._consumir("VIRGULA")
        b, _ = self._numero()
        return arvore.DeclaracaoCor(token.linha, token.coluna, nome, r, g, b)
    # Funções para analisar seleção de cor, ponto, linha, retângulo e salvar, de acordo com a gramática da linguagem
    def _sel_cor(self) -> arvore.SelecaoCor:
        token = self._consumir("USAR")
        nome_token = self._consumir("NOME_COR")
        return arvore.SelecaoCor(nome_token.linha, nome_token.coluna, nome_token.lexema)

    def _cmd_ponto(self) -> arvore.Ponto:
        token = self._consumir("PONTO")
        self._consumir("EM")
        x, y, _ = self._coordenada()
        return arvore.Ponto(token.linha, token.coluna, x, y)

    def _cmd_linha(self) -> arvore.Linha:
        token = self._consumir("LINHA")
        self._consumir("DE")
        x1, y1, _ = self._coordenada()
        self._consumir("ATE")
        x2, y2, _ = self._coordenada()
        return arvore.Linha(token.linha, token.coluna, x1, y1, x2, y2)

    def _cmd_retangulo(self) -> arvore.Retangulo:
        token = self._consumir("RETANGULO")
        self._consumir("EM")
        x, y, _ = self._coordenada()
        self._consumir("TAMANHO")
        largura, _ = self._numero()
        self._consumir("POR")
        altura, _ = self._numero()
        return arvore.Retangulo(token.linha, token.coluna, x, y, largura, altura)

    def _cmd_salvar(self) -> arvore.Salvar:
        token = self._consumir("SALVAR")
        cadeia = self._consumir("CADEIA").lexema[1:-1]
        return arvore.Salvar(token.linha, token.coluna, cadeia)

# Função de análise sintática, que recebe uma lista de tokens e retorna a árvore sintática do programa
def analisar(tokens: list[Token]) -> arvore.Programa:
    return AnalisadorSintatico(tokens).analisar()
