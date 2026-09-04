"""

    # Análise semântica
    - regras para verificação semântica da linguagem:

    R1  largura e altura da tela devem ser maiores que zero;
    R2  componentes de cor devem estar no intervalo [0, 255];
    R3  nomes de cor não podem ser declarados duas vezes;
    R4  só é possível selecionar (`usar`) uma cor previamente declarada;
    R5  nenhum comando de desenho pode ocorrer antes de uma seleção de cor;
    R6  toda coordenada deve estar dentro dos limites da tela;
    R7  linhas devem ser estritamente horizontais ou verticais;
    R8  largura e altura de retângulo devem ser maiores que zero;
    R9  o retângulo deve caber inteiramente na tela (senão, erro);
    R10 o arquivo de saída deve terminar em `.ppm`.

    - Erros são acumulados para que o usuário receba vários diagnósticos de uma só vez.
    - A tabela de símbolos guarda as cores declaradas.

"""

from __future__ import annotations
from dataclasses import dataclass
from . import arvore
from .erros import ErroSemantico, ErroSemanticoMultiplo

__all__ = ["TabelaDeSimbolos", "SimboloCor", "ErroSemanticoMultiplo", "analisar"]

# Extensões de arquivo permitidas para o arquivo de saída
EXTENSOES_PERMITIDAS = (".ppm",)

# Classes para representar símbolos de cor e tabela de símbolos
@dataclass
class SimboloCor:
    nome: str
    r: int
    g: int
    b: int
    linha: int
    indice: int  # posição na paleta gerada em C

# Classe para representar a tabela de símbolos, que guarda as cores declaradas
class TabelaDeSimbolos:
    def __init__(self) -> None:
        self._cores: dict[str, SimboloCor] = {}
    # Função que declara uma nova cor na tabela, retornando o símbolo correspondente
    def declarar(self, no: arvore.DeclaracaoCor) -> SimboloCor:
        simbolo = SimboloCor(
            no.nome, no.r, no.g, no.b, no.linha, indice=len(self._cores)
        )
        self._cores[no.nome] = simbolo
        return simbolo
    # Função que verifica se uma cor já foi declarada na tabela
    def existe(self, nome: str) -> bool:
        return nome in self._cores
    # Função que busca uma cor na tabela, retornando o símbolo correspondente
    def buscar(self, nome: str) -> SimboloCor:
        return self._cores[nome]
    # Função com propriedade que retorna a lista de cores declaradas na tabela, ordenadas pelo índice
    @property
    def cores(self) -> list[SimboloCor]:
        return sorted(self._cores.values(), key=lambda c: c.indice)

# Classe para realizar a análise semântica do programa, verifica as regras semânticas
class AnalisadorSemantico:
    def __init__(self, programa: arvore.Programa):
        self._programa = programa
        self.tabela = TabelaDeSimbolos()
        self.erros: list[ErroSemantico] = []
    # Função auxiliar para registrar um erro semântico, adicionando-o à lista de erros
    def _erro(self, mensagem: str, no: arvore.No) -> None:
        self.erros.append(ErroSemantico(mensagem, no.linha, no.coluna))
    # Função principal que realiza a análise semântica do programa, verificando todas as regras e retornando a tabela de símbolos
    def analisar(self) -> TabelaDeSimbolos:
        tela = self._programa.tela

        # R1: verifica dimensões da tela e registra erro se forem inválidas
        if tela.largura <= 0 or tela.altura <= 0:
            self._erro("as dimensões da tela devem ser maiores que zero", tela)
        # rastreia a cor selecionada atual, para verificar se comandos de desenho são válidos
        cor_selecionada: str | None = None
        # Laço que percorre todos os comandos do programa, verificando cada um de acordo com seu tipo
        for comando in self._programa.comandos:
            if isinstance(comando, arvore.DeclaracaoCor):
                self._verificar_declaracao_cor(comando)
            elif isinstance(comando, arvore.SelecaoCor):
                # R4: verifica se a cor selecionada foi previamente declarada, caso contrário registra erro
                if not self.tabela.existe(comando.nome):
                    self._erro(f"cor {comando.nome!r} não foi declarada", comando)
                # Recuperação de erro: mesmo que a cor não exista, considera-se
                # que houve seleção, para não gerar diagnósticos em cascata
                # (R5) nos comandos de desenho seguintes.
                cor_selecionada = comando.nome
            else:
                # R5: verifica se uma cor foi selecionada antes de desenhar, caso contrário registra erro
                if cor_selecionada is None:
                    self._erro(
                        "nenhuma cor selecionada; use 'usar <COR>' antes de desenhar",
                        comando,
                    )
                self._verificar_desenho(comando, tela)

        # R10: verifica se o arquivo de saída termina com a extensão permitida, caso contrário registra erro
        salvar = self._programa.salvar
        if salvar is not None and not salvar.arquivo.endswith(EXTENSOES_PERMITIDAS):
            self._erro(
                f"arquivo de saída deve terminar em '.ppm' (recebido {salvar.arquivo!r})",
                salvar,
            )

        if self.erros:
            raise ErroSemanticoMultiplo(self.erros)
        return self.tabela


    # Verificações auxiliares para cada tipo de comando
    # Aplica as regras R2, R3 e R4 para declarações de cor
    def _verificar_declaracao_cor(self, no: arvore.DeclaracaoCor) -> None:
        # R3
        if self.tabela.existe(no.nome):
            anterior = self.tabela.buscar(no.nome).linha
            self._erro(
                f"cor {no.nome!r} já foi declarada na linha {anterior}", no
            )
            return
        # R2
        for rotulo, valor in (("R", no.r), ("G", no.g), ("B", no.b)):
            if not 0 <= valor <= 255:
                self._erro(
                    f"componente {rotulo} da cor {no.nome!r} deve estar entre "
                    f"0 e 255 (recebido {valor})",
                    no,
                )
                return
        self.tabela.declarar(no)
    # Verifica se os comandos de desenho estão corretos, aplicando as regras R6, R7, R8 e R9
    def _verificar_desenho(self, no: arvore.No, tela: arvore.Tela) -> None:
        if isinstance(no, arvore.Ponto):
            self._verificar_coordenada(no.x, no.y, tela, no)
        elif isinstance(no, arvore.Linha):
            # R7: verifica se a linha é horizontal ou vertical, caso contrário registra erro
            if no.x1 != no.x2 and no.y1 != no.y2:
                self._erro(
                    "linhas devem ser horizontais ou verticais nesta versão da "
                    "linguagem",
                    no,
                )
            self._verificar_coordenada(no.x1, no.y1, tela, no)
            self._verificar_coordenada(no.x2, no.y2, tela, no)
        elif isinstance(no, arvore.Retangulo):
            # R8: verifica se largura e altura do retângulo são maiores que zero, caso contrário registra erro
            if no.largura <= 0 or no.altura <= 0:
                self._erro(
                    "largura e altura do retângulo devem ser maiores que zero", no
                )
                return
            self._verificar_coordenada(no.x, no.y, tela, no)
            # R9
            if no.x + no.largura > tela.largura or no.y + no.altura > tela.altura:
                self._erro(
                    f"retângulo ultrapassa os limites da tela "
                    f"({tela.largura} por {tela.altura})",
                    no,
                )
    # Função auxiliar que verifica se uma coordenada está dentro dos limites da tela, aplicando a regra R6
    def _verificar_coordenada(
        self, x: int, y: int, tela: arvore.Tela, no: arvore.No
    ) -> None:
        # R6
        if not (0 <= x < tela.largura and 0 <= y < tela.altura):
            self._erro(
                f"coordenada ({x}, {y}) fora da tela "
                f"({tela.largura} por {tela.altura}); x deve estar em [0, "
                f"{tela.largura - 1}] e y em [0, {tela.altura - 1}]",
                no,
            )

# Analisa semanticamente o programa; devolve a tabela de símbolos com as cores
# declaradas ou levanta ErroSemanticoMultiplo (definido em tinydraw.erros).
def analisar(programa: arvore.Programa) -> TabelaDeSimbolos:
    return AnalisadorSemantico(programa).analisar()
