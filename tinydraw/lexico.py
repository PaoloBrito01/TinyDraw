"""

    # Análise léxica:
    - a especificação léxica é declarada como uma lista de pares
      (nome do token, expressão regular);
    - a ordem da lista NÃO é critério de desempate: os nove padrões são
      disjuntos pelo primeiro caractere (ESPECIFICACAO.md, item 4.1), de
      modo que no máximo um deles pode casar em cada posição da entrada.
      Primeiro-casamento e maior-casamento produzem o mesmo
      resultado, e a especificação dispensa qualquer regra de desempate.

    Nota de implementação: a alternância do módulo `re` do Python é
    primeiro-casamento na ordem declarada, não maior-casamento.

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

# Especificação léxica da linguagem é declarada como uma lista de pares
# (nome do token, expressão regular). A ordem NÃO é critério de desempate:
# os padrões são disjuntos pelo primeiro caractere ( ou seja, o primeiro caractere de cada padrão é único).
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

# Expressão regular mestre: alterna os padrões de ESPECIFICACAO_LEXICA. A ordem
# é irrelevante porque os padrões são disjuntos pelo primeiro caractere.
# O token FIM não vai ser reconhecido aqui, ele é acrescentado ao fim da lista por tokenizar().
_REGEX_MESTRE = re.compile(
    "|".join(f"(?P<{nome}>{padrao})" for nome, padrao in ESPECIFICACAO_LEXICA)
)

# Alfabeto Σ da linguagem (ESPECIFICACAO.md, item 1). Usado apenas para
# distinguir, no ramo de erro, "caractere fora de Σ" de outras rejeições.
_ALFABETO = re.compile(r'[a-zA-Z0-9_#"=, \t\r\n]')

# Função auxiliar para verificar se um caractere está fora do alfabeto da linguagem
def _fora_do_alfabeto(caractere: str) -> bool:
    return _ALFABETO.match(caractere) is None

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
            # caracter que falhou em casar, é usado para identificar o erro léxico, levanta ErroLexico com a posição do erro
            caractere = codigo[posicao]

            if caractere == '"':
                raise ErroLexico(
                    "cadeia não terminada; falta a aspa de fechamento antes "
                    "do fim da linha",
                    linha,
                    coluna,
                )
            if _fora_do_alfabeto(caractere):
                raise ErroLexico(
                    f"caractere {caractere!r} fora do alfabeto da linguagem",
                    linha,
                    coluna,
                )
            raise ErroLexico(
                f"caractere inesperado {caractere!r}", linha, coluna
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
                    # Se lexema não for palavra reservada retorna fim do casamento e verifica o próximo caracter
                    # Item 1 da especificação exige apontar o caractere fora de Σ na posição exata.
                    fim = casamento.end()
                    if fim < len(codigo) and _fora_do_alfabeto(codigo[fim]):
                        raise ErroLexico(
                            f"caractere {codigo[fim]!r} fora do alfabeto da "
                            f"linguagem; as palavras reservadas são escritas "
                            f"sem acentuação",
                            linha,
                            coluna + len(lexema),
                        )
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
