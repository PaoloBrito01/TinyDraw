/* Arquivo gerado automaticamente pelo transpilador TinyDraw.
 * Não editar manualmente. */
#include <stdio.h>
#include <stdlib.h>

#define TD_LARGURA 40
#define TD_ALTURA  20

typedef struct { unsigned char r, g, b; } TdCor;

static TdCor td_tela[TD_ALTURA][TD_LARGURA];
static TdCor td_cor_atual = {0, 0, 0};

static const TdCor td_paleta[] = {
    {  0, 160,  60},  /* VERDE */
    {255, 210,   0},  /* AMARELO */
    {255, 255, 255},  /* BRANCO */
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

static void td_linha(int x1, int y1, int x2, int y2) {
    if (y1 == y2) {
        int inicio = x1 < x2 ? x1 : x2;
        int fim    = x1 < x2 ? x2 : x1;
        for (int x = inicio; x <= fim; x++) td_ponto(x, y1);
    } else {
        int inicio = y1 < y2 ? y1 : y2;
        int fim    = y1 < y2 ? y2 : y1;
        for (int y = inicio; y <= fim; y++) td_ponto(x1, y);
    }
}

/* Retângulo sem preenchimento (apenas o contorno). */
static void td_retangulo(int x, int y, int largura, int altura) {
    int direita = x + largura - 1;
    int base    = y + altura - 1;
    td_linha(x, y, direita, y);
    td_linha(x, base, direita, base);
    td_linha(x, y, x, base);
    td_linha(direita, y, direita, base);
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
    td_retangulo(0, 0, 40, 20);
    td_cor_atual = td_paleta[1];  /* usar AMARELO */
    td_retangulo(8, 4, 24, 12);
    td_linha(8, 10, 31, 10);
    td_cor_atual = td_paleta[2];  /* usar BRANCO */
    td_ponto(20, 10);
    if (td_salvar("bandeira.ppm") != 0) return 1;
    td_pre_visualizar();
    return 0;
}
