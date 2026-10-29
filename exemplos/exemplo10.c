/* Arquivo gerado automaticamente pelo transpilador TinyDraw.
 * Não editar manualmente. */
#include <stdio.h>
#include <stdlib.h>

#define TD_LARGURA 10
#define TD_ALTURA  10

typedef struct { unsigned char r, g, b; } TdCor;

static TdCor td_tela[TD_ALTURA][TD_LARGURA];
static TdCor td_cor_atual = {0, 0, 0};

static const TdCor td_paleta[] = {
    { 82, 245,   0},  /* VERDE */
    {224, 245,   0},  /* AMARELA */
};

static void td_limpar(void) {
    for (int y = 0; y < TD_ALTURA; y++)
        for (int x = 0; x < TD_LARGURA; x++) {
            td_tela[y][x].r = 0;
            td_tela[y][x].g = 0;
            td_tela[y][x].b = 0;
        }
}

/* Sobreposição: a escrita mais recente prevalece.
 * O teste de limites abaixo é redundante com a análise semântica (R6/R9
 * rejeitam qualquer coordenada fora da tela antes da geração de código).
 * Fica como defesa do código gerado: um defeito no gerador produz uma
 * imagem errada, não escrita fora dos limites de td_tela. */
static void td_ponto(int x, int y) {
    if (x < 0 || x >= TD_LARGURA || y < 0 || y >= TD_ALTURA) return;
    td_tela[y][x] = td_cor_atual;
}

static int td_salvar(const char *caminho) {
    FILE *saida = fopen(caminho, "w");
    if (saida == NULL) {
        fprintf(stderr, "TinyDraw: nao foi possivel gravar '%s'\n", caminho);
        return 1;
    }
    fprintf(saida, "P3\n%d %d\n255\n", TD_LARGURA, TD_ALTURA);
    for (int y = 0; y < TD_ALTURA; y++) {
        for (int x = 0; x < TD_LARGURA; x++)
            fprintf(saida, "%d %d %d ", td_tela[y][x].r,
                    td_tela[y][x].g, td_tela[y][x].b);
        fprintf(saida, "\n");
    }
    fclose(saida);
    return 0;
}

/* Demonstrador textual: torna a semântica observável no terminal. */
static void td_pre_visualizar(void) {
    for (int y = 0; y < TD_ALTURA; y++) {
        for (int x = 0; x < TD_LARGURA; x++) {
            TdCor p = td_tela[y][x];
            putchar((p.r || p.g || p.b) ? '#' : '.');
        }
        putchar('\n');
    }
}

int main(void) {
    td_limpar();
    td_cor_atual = td_paleta[0];  /* usar VERDE */
    td_ponto(0, 0);
    if (td_salvar("exemplo10.ppm") != 0) return 1;
    td_pre_visualizar();
    return 0;
}
