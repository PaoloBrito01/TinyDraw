# TinyDraw

Uma linguagem de domínio específico para descrever desenhos rasterizados —
e o transpilador, em Python, que a traduz para C.

```
desenho.td ──▶ [transpilador Python] ──▶ desenho.c ──▶ gcc ──▶ imagem.ppm
              léxico · sintático · AST · semântico · geração
```

Em C, o mesmo desenho exige declarar a matriz de pixels, montar o cabeçalho
do arquivo, escrever laços por forma e validar limites à mão. TinyDraw reduz
o desenho a comandos declarativos e transfere as validações — limites,
paleta, formato de saída — para o compilador, que as verifica **antes** da
execução.

## Exemplo

```
tela 40 por 20

cor VERDE   = 0, 160, 60
cor AMARELO = 255, 210, 0

usar VERDE
retangulo em 0, 0 tamanho 40 por 20
usar AMARELO
linha de 8, 10 ate 31, 10

salvar "bandeira.ppm"
```

## Como executar

```bash
python3 transpilador.py exemplos/bandeira.td              # só gera o .c ao lado do .td
python3 transpilador.py exemplos/bandeira.td --executar   # gera .c, compila com gcc e roda
python3 transpilador.py exemplos/bandeira.td -o saida.c   # gera o .c no caminho indicado
python3 transpilador.py exemplos/bandeira.td --tokens     # lista os tokens
python3 -m unittest discover -s testes -v                 # roda a suíte
```

Sem `-o/--saida`, o `.c` recebe o nome do `.td` com a extensão trocada. Com
`--executar`, o C é compilado com `gcc -std=c11 -Wall -Wextra -Werror` e o
binário resultante é executado — ele grava o PPM e imprime uma
pré-visualização textual no terminal.

## Documentação

- **[`docs/ESPECIFICACAO.md`](docs/ESPECIFICACAO.md)** — definição da
  linguagem e da implementação: léxico, gramática EBNF (com conjuntos FIRST),
  regras semânticas R1–R10, geração de código, decisões de projeto e
  estrutura. Cobre os entregáveis I–IV.
- **[`ROADMAP.md`](ROADMAP.md)** — as 11 etapas de desenvolvimento do
  projeto.

## Stack

`Python` (transpilador) · `C` (código gerado) · `gcc` (compilação) ·
`PPM P3` (saída).
