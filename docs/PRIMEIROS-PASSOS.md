# TinyDraw — Fazendo uma imagem
 
Ordem:
 
```
meu.td ──▶ python3 transpilador.py meu.td --executar ──▶ meu.c ──▶ gcc ──▶ meu.ppm + prévia
```
 
Definição completa da linguagem: [`ESPECIFICACAO.md`](ESPECIFICACAO.md)
 
---
 
## 1. Pré-requisitos
 
- **Python 3.10+** 
- **gcc** — para `--executar`. 
 
---
 
## 2. Criar um arquivo `.td`
 
Criar um arquivo .td em `/exemplos`. A primeira instrução sempre é `tela` e a última sempre
é `salvar`. 
 
`exemplo.td`:
 
```
# uma janela com moldura, travessas e trinco
 
tela 20 por 16
 
cor MOLDURA = 120, 80, 40
cor VIDRO   = 140, 200, 235
cor TRINCO  = 30, 30, 30
 
usar VIDRO
retangulo em 3, 2 tamanho 14 por 12
 
usar MOLDURA
retangulo em 3, 2 tamanho 14 por 12
linha de 10, 2 ate 10, 13
linha de 3, 8 ate 16, 8
 
usar TRINCO
ponto em 6, 11
 
salvar "janela.ppm"
```
 
---
 
## 3. A linguagem
 
`X`, `Y`, `L`, `A`, `R`, `G`, `B` são números inteiros.
 
| Forma | O que faz |
|---|---|
| `tela L por A` | cria a tela: `L` colunas por `A` linhas, fundo preto |
| `cor NOME = R, G, B` | registra uma cor. `NOME` em MAIÚSCULAS, componentes de 0 a 255 |
| `usar NOME` | seleciona a cor dos próximos desenhos |
| `ponto em X, Y` | pinta um pixel |
| `linha de X, Y ate X, Y` | linha reta — só **horizontal ou vertical** |
| `retangulo em X, Y tamanho L por A` | só o **contorno**; canto superior esquerdo em `X, Y` |
| `salvar "arquivo.ppm"` | grava a imagem; o nome tem de terminar em `.ppm` |
| `# texto` | comentário até o fim da linha |
 
Obs:

- origem `(0, 0)` no canto superior esquerdo, `x` para a direita e `y` para
  baixo. Tudo tem de caber em `x ∈ [0, L-1]`, `y ∈ [0, A-1]`
- quem é desenhado por último fica por cima
- é preciso um `usar` antes do primeiro desenho
- palavras reservadas são sempre minúsculas e nomes de cor sempre MAIÚSCULOS
- não existem variáveis, repetição, diagonais, círculos nem preenchimento
---
 
## 4. Executar

Na raiz do projeto (a pasta com `transpilador.py`). Os arquivos gerados
nascem ao lado do `.td`, com o mesmo nome.
 
| Comando | Resultado |
|---|---|
| `python3 transpilador.py x.td` | gera `x.c` e para |
| `python3 transpilador.py x.td -o saida.c` | gera o `.c` no caminho indicado |
| `python3 transpilador.py x.td --executar` | gera o `.c`, compila, roda, grava `x.ppm` + prévia |
| `python3 transpilador.py x.td --tokens` | lista `linha:coluna TIPO lexema` e para |
 
Com `--executar`, a prévia no terminal mostra o desenho sem abrir a imagem
(`#` = pixel pintado, `.` = fundo):
 
```
....................
...##############...
...#......#.....#...
...#......#.....#...
...#......#.....#...
...##############...
...#......#.....#...
...#..#...#.....#...
...##############...
....................
```
 
O `.ppm` é texto (PPM P3). Abra no GIMP ou converta usando:
```bash
python3 ferramentas/ppm_para_png.py nome_arquivo.ppm
```
 
---
 
## 5. Quando dá erro
 
Nenhum C é gerado. O formato é `arquivo:linha:coluna: fase: mensagem`, e os
erros semânticos saem todos de uma vez:
 
```
exemplos/erro_semantico.td:12:6: erro semântico: cor 'ROXO' não foi declarada
exemplos/erro_semantico.td:13:1: erro semântico: coordenada (50, 3) fora da tela (20 por 10); x deve estar em [0, 19] e y em [0, 9]
```
 
Alguns erros comuns: 
- dimensão ≤ 0 
- RGB fora de `[0, 255]`
- cor redeclarada, `usar` com cor inexistente 
- desenhar sem `usar` antes
- coordenada fora da tela
- linha diagonal e saída sem `.ppm`.
 
Em `exemplos/erro_sintatico.td` e `exemplos/erro_semantico.td` se pode ver os
diagnósticos.
 
Código de saída: `0` sucesso · `1` erro TinyDraw · `2` arquivo não abre ·
`3` gcc falhou.
 
---
 
## 6. Leitura adicional
 
- [`ESPECIFICACAO.md`](ESPECIFICACAO.md) — EBNF, regras R1–R10, mapeamento
  para C e decisões de projeto
- [`../exemplos/`](../exemplos/) — `bandeira.td` (núcleo mínimo) e
  `moldura.td` (sobreposição)
- [`../ROADMAP.md`](../ROADMAP.md) — as 11 etapas
