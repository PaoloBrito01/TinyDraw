"""

    # Geração de código C a partir da AST(Árvore Sintática Abstrata)
    - representação em árvore da estrutura do código-fonte, onde cada nó é uma construção
    da linguagem (comando, declaração, etc.). É abstrata porque descarta detalhes sintáticos (parênteses, vírgulas, etc.).

    - Mapeamento das construções da linguagem para C:
    tela L por A          -> #define TD_LARGURA/TD_ALTURA + matriz de pixels
    cor NOME = r, g, b    -> entrada constante na paleta `td_paleta[]`
    usar NOME             -> atribuição a `td_cor_atual`
    ponto em x, y         -> td_ponto(x, y)
    linha de a,b ate c,d  -> td_linha(a, b, c, d)
    retangulo ...         -> td_retangulo(x, y, largura, altura)
    salvar "arq.ppm"      -> td_salvar("arq.ppm")  (formato PPM P3)


    # Convenções da linguagem, documentadas e implementadas:
  
    * origem (0, 0) no canto superior esquerdo, x para a direita e y para baixo;
    * sobreposição: o último comando desenhado prevalece sobre os anteriores;
    * o fundo da tela é preto (0, 0, 0).

"""

from __future__ import annotations
from . import arvore
from .semantico import TabelaDeSimbolos

# Definição do cabeçalho do arquivo C gerado
# O cabeçalho contém:
# - comentários de aviso de geração automática
# - includes de bibliotecas padrão
# - definição de macros para largura e altura da tela
# - definição da estrutura TdCor para representar cores
# - declaração da matriz td_tela para armazenar os pixels da tela
# - declaração da variável td_cor_atual para armazenar a cor atual
# - declaração da paleta de cores td_paleta
# - implementação das funções td_limpar, td_ponto, td_linha, td_retangulo, td_salvar e td_pre_visualizar
# - implementação da função main que inicializa a tela, executa os comandos e salva a imagem
# - O corpo do programa é gerado a partir da AST, traduzindo cada nó para a função correspondente em C.

_CABECALHO = """\
/* Arquivo gerado automaticamente pelo transpilador TinyDraw.
 * Não editar manualmente. */
#include <stdio.h>
#include <stdlib.h>

#define TD_LARGURA {largura}
#define TD_ALTURA  {altura}

typedef struct {{ unsigned char r, g, b; }} TdCor;

static TdCor td_tela[TD_ALTURA][TD_LARGURA];
static TdCor td_cor_atual = {{0, 0, 0}};

static const TdCor td_paleta[] = {{
{paleta}}};

static void td_limpar(void) {{
    for (int y = 0; y < TD_ALTURA; y++)
        for (int x = 0; x < TD_LARGURA; x++) {{
            td_tela[y][x].r = 0;
            td_tela[y][x].g = 0;
            td_tela[y][x].b = 0;
        }}
}}

/* Sobreposição: a escrita mais recente prevalece.
 * O teste de limites abaixo é redundante com a análise semântica (R6/R9
 * rejeitam qualquer coordenada fora da tela antes da geração de código).
 * Fica como defesa do código gerado: um defeito no gerador produz uma
 * imagem errada, não escrita fora dos limites de td_tela. */
static void td_ponto(int x, int y) {{
    if (x < 0 || x >= TD_LARGURA || y < 0 || y >= TD_ALTURA) return;
    td_tela[y][x] = td_cor_atual;
}}

static void td_linha(int x1, int y1, int x2, int y2) {{
    if (y1 == y2) {{
        int inicio = x1 < x2 ? x1 : x2;
        int fim    = x1 < x2 ? x2 : x1;
        for (int x = inicio; x <= fim; x++) td_ponto(x, y1);
    }} else {{
        int inicio = y1 < y2 ? y1 : y2;
        int fim    = y1 < y2 ? y2 : y1;
        for (int y = inicio; y <= fim; y++) td_ponto(x1, y);
    }}
}}

/* Retângulo sem preenchimento (apenas o contorno). */
static void td_retangulo(int x, int y, int largura, int altura) {{
    int direita = x + largura - 1;
    int base    = y + altura - 1;
    td_linha(x, y, direita, y);
    td_linha(x, base, direita, base);
    td_linha(x, y, x, base);
    td_linha(direita, y, direita, base);
}}

static int td_salvar(const char *caminho) {{
    FILE *saida = fopen(caminho, "w");
    if (saida == NULL) {{
        fprintf(stderr, "TinyDraw: nao foi possivel gravar '%s'\\n", caminho);
        return 1;
    }}
    fprintf(saida, "P3\\n%d %d\\n255\\n", TD_LARGURA, TD_ALTURA);
    for (int y = 0; y < TD_ALTURA; y++) {{
        for (int x = 0; x < TD_LARGURA; x++)
            fprintf(saida, "%d %d %d ", td_tela[y][x].r,
                    td_tela[y][x].g, td_tela[y][x].b);
        fprintf(saida, "\\n");
    }}
    fclose(saida);
    return 0;
}}

/* Demonstrador textual: torna a semântica observável no terminal. */
static void td_pre_visualizar(void) {{
    for (int y = 0; y < TD_ALTURA; y++) {{
        for (int x = 0; x < TD_LARGURA; x++) {{
            TdCor p = td_tela[y][x];
            putchar((p.r || p.g || p.b) ? '#' : '.');
        }}
        putchar('\\n');
    }}
}}

int main(void) {{
    td_limpar();
{corpo}
    td_pre_visualizar();
    return 0;
}}
"""

# Classe responsável por gerar o código C a partir da AST referenciada e da tabela de símbolos fornecida.
class GeradorC:
    def __init__(self, programa: arvore.Programa, tabela: TabelaDeSimbolos):
        self._programa = programa
        self._tabela = tabela
    # Gera o código C correspondente a AST e a tabela de simbolos, retorna uma string
    def gerar(self) -> str:
        paleta = "".join(
            f"    {{{c.r:3d}, {c.g:3d}, {c.b:3d}}},  /* {c.nome} */\n"
            for c in self._tabela.cores
        ) or "    {0, 0, 0}\n"
        # Gera corpo do programa C, traduz cada nó da AST para uma função correspondente em C
        # Adiciona a chamada da função td_salvar ao final do corpo do programa
        # Remove linhas vazias do corpo do programa
        linhas: list[str] = []
        for comando in self._programa.comandos:
            linhas.append(self._traduzir(comando))

        linhas = [linha for linha in linhas if linha]
        salvar = self._programa.salvar
        linhas.append(f'    if (td_salvar("{salvar.arquivo}") != 0) return 1;')
        # Retorna o código C completo, incluindo o cabeçalho e o corpo do programa
        return _CABECALHO.format(
            largura=self._programa.tela.largura,
            altura=self._programa.tela.altura,
            paleta=paleta,
            corpo="\n".join(linhas),
        )
    
    # Tradução de cada nó da AST para a função correspondente em C
    def _traduzir(self, no: arvore.No) -> str:
        if isinstance(no, arvore.DeclaracaoCor):
            return ""  # já materializada na paleta
        if isinstance(no, arvore.SelecaoCor):
            indice = self._tabela.buscar(no.nome).indice
            return f"    td_cor_atual = td_paleta[{indice}];  /* usar {no.nome} */"
        if isinstance(no, arvore.Ponto):
            return f"    td_ponto({no.x}, {no.y});"
        if isinstance(no, arvore.Linha):
            return f"    td_linha({no.x1}, {no.y1}, {no.x2}, {no.y2});"
        if isinstance(no, arvore.Retangulo):
            return (
                f"    td_retangulo({no.x}, {no.y}, {no.largura}, {no.altura});"
            )
        raise AssertionError(f"nó não suportado: {type(no).__name__}")

# Função para gerar o código C e a tabela de símbolos
def gerar(programa: arvore.Programa, tabela: TabelaDeSimbolos) -> str:
    return GeradorC(programa, tabela).gerar()
