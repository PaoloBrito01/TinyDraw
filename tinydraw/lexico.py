"""

    # Análise léxica:
    - a especificação léxica é declarada como uma lista ordenada de pares,
      (nome do token, expressão regular);
    - o scanner aplica a estratégia de "maior casamento na ordem declarada". Mesmo princípio
    do lex/flex, percorrendo a entrada da esquerda para a direita.

"""

from __future__ import annotations
from .erros import ErroLexico
from dataclasses import dataclass
import re

# Especificação léxica da linguagem (palavras reservadas, símbolos e padrões de tokens)
PALAVRAS_RESERVADAS = {
    "tela": "TELA",
    "cor": "COR",
    "usar": "USAR",
    "ponto": "PONTO",
    "linha": "LINHA",
    "retangulo": "RETANGULO",
    "salvar": "SALVAR",
    "em": "EM",
    "de": "DE",
    "ate": "ATE",
    "tamanho": "TAMANHO",
    "por": "POR",
}

# Especificação léxica da linguagem é declarada como uma lista ordenada de pares
# (nome do token, expressão regular)
# Ordem importa: PALAVRA vem antes de NOME_COR , ordem geral garante que os comentários e cadeias 
# sejam reconhecidos antes dos símbolos.
ESPECIFICACAO_LEXICA = [
    ("COMENTARIO", r"#[^\n]*"),
    ("ESPACO", r"[ \t\r]+"),
    ("NOVA_LINHA", r"\n"),
    ("CADEIA", r'"[^"\n]*"'),
    ("NUMERO", r"[0-9]+"),
    ("PALAVRA", r"[a-z][a-z_]*"),
    ("NOME_COR", r"[A-Z][A-Z0-9_]*"),
    ("IGUAL", r"="),
    ("VIRGULA", r","),
]

# Tokens ignorados pelo analisador léxico (comentários, espaços e novas linhas)
_TOKENS_IGNORADOS = {"COMENTARIO", "ESPACO", "NOVA_LINHA"}

# Expressão regular mestre: alterna os padrões de ESPECIFICACAO_LEXICA na ordem
# declarada, o que dá a estratégia de "maior casamento na ordem declarada".
# O token FIM não é reconhecido aqui; é acrescentado ao fim da lista por tokenizar().
_REGEX_MESTRE = re.compile(
    "|".join(f"(?P<{nome}>{padrao})" for nome, padrao in ESPECIFICACAO_LEXICA)
)

# Classe para representar um token, atributos: tipo, lexema, linha e coluna
@dataclass(frozen=True)
class Token:
    tipo: str
    lexema: str
    linha: int
    coluna: int
    # Print do token para depuração, formato: <tipo 'lexema' linha:coluna>
    def __str__(self) -> str:  # pragma: no cover - apoio a depuração
        return f"<{self.tipo} '{self.lexema}' {self.linha}:{self.coluna}>"

# Função para tokenizar o código-fonte, recebe uma string e retorna uma lista de tokens
def tokenizar(codigo: str) -> list[Token]:
    """
    - Converte o texto-fonte em uma lista de tokens.
    - Levanta ErroLexico no primeiro caractere que não pertence ao alfabeto
    - Retorna a lista de tokens
    - Tokenizar percorre o código da esquerda para direita, aplica estratégia de casamento
    - Inicia a contagem de linha x coluna a partir da posição 1,1 (linha 1, coluna 1)
    - Finaliza a lista de tokens na posição final do código com o token "FIM"
    """
    # Lista de tokens gerados pelo scanner
    tokens: list[Token] = []
    linha = 1
    inicio_linha = 0
    posicao = 0
    # Laço principal, percorre o código da esquerda para direita, aplica estratégia de casamento
    while posicao < len(codigo):
        casamento = _REGEX_MESTRE.match(codigo, posicao)
        # Verifica se houve casamento, caso contrário levanta ErroLexico com a posição do erro
        if casamento is None:
            coluna = posicao - inicio_linha + 1
            raise ErroLexico(
                f"caractere inesperado {codigo[posicao]!r}", linha, coluna
            )
        # Identifica o tipo do token, lexema e coluna do token
        # Se o tipo do token for "NOVA_LINHA", incrementa a linha e atualiza o início da linha
        # Se o tipo do token não estiver na lista de tokens ignorados, adiciona o token à lista de tokens
        tipo = casamento.lastgroup
        lexema = casamento.group()
        coluna = posicao - inicio_linha + 1

        if tipo == "NOVA_LINHA":
            linha += 1
            inicio_linha = casamento.end()
        elif tipo not in _TOKENS_IGNORADOS:
            if tipo == "PALAVRA":
                if lexema not in PALAVRAS_RESERVADAS:
                    raise ErroLexico(
                        f"palavra desconhecida {lexema!r}; nomes de cor devem "
                        f"ser escritos em maiúsculas",
                        linha,
                        coluna,
                    )
                tipo = PALAVRAS_RESERVADAS[lexema]
            tokens.append(Token(tipo, lexema, linha, coluna))

        posicao = casamento.end()
    # Adiciona o token "FIM" ao final da lista de tokens, indicando o fim do código-fonte
    tokens.append(Token("FIM", "", linha, posicao - inicio_linha + 1))
    return tokens
