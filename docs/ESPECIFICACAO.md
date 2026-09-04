# TinyDraw — Especificação da linguagem e do transpilador

Fonte única da definição da linguagem TinyDraw e da implementação que a
traduz para C. Cobre os entregáveis **I–IV** do projeto; as seções abaixo
estão marcadas com o entregável correspondente.

- Visão geral e instruções de uso: [`../README.md`](../README.md)
- Cronograma de desenvolvimento (11 etapas): [`../ROADMAP.md`](../ROADMAP.md)

O pipeline completo: leitura do fonte → análise léxica → análise sintática →
análise semântica → geração de código C → compilação com `gcc` → execução →
arquivo PPM.

---

## 1. Delimitação do problema

**Domínio:** descrição declarativa de desenhos raster simples (pontos, linhas
retas e retângulos) sobre uma tela de dimensões fixas.

**Usuário-alvo:** quem precisa produzir figuras esquemáticas reprodutíveis
(diagramas de grade, mapas de bits para testes, ícones) sem escrever código
gráfico nem abrir um editor.

**Por que uma DSL:** em C, o mesmo desenho exige declarar a matriz de pixels,
gerenciar o cabeçalho do arquivo, escrever laços para cada forma e validar
limites manualmente. A DSL reduz o desenho a uma sequência de comandos
declarativos e transfere as validações (limites, paleta, formato de saída)
para o compilador, que as verifica **antes** da execução.

**Aposta central de projeto:** toda coordenada e toda dimensão é um literal
inteiro conhecido em tempo de compilação. Foi essa aposta que manteve a
repetição fora da linguagem (um laço introduziria coordenadas calculadas) e
é ela que torna possível validar todo desenho estaticamente — ver §2 e §5.

**Escopo desta versão:** sem variáveis, expressões, repetição, preenchimento
ou linhas diagonais. A gramática é LL(1), sem produções recursivas.

---

## 2. Decisões de projeto

Duas decisões foram ratificadas pela equipe (A1 e A2) e ficam registradas
aqui, na especificação — um documento à parte só recriaria a duplicação que
este arquivo elimina. O histórico da troca do separador está no Apêndice A.

| Decisão | Escolha | Motivo |
|---|---|---|
| **A1 — separador de dimensões** | `por` (`tela 40 por 20`, `tamanho 12 por 8`) | mantém a leitura em português corrente e preserva o alfabeto de palavras reservadas **inteiramente** em português, como o projeto exige. Um símbolo de uma letra (`x`) classificado como palavra reservada seria a única exceção entre 12 termos. |
| **A2 — coordenada fora da tela** | erro rígido, em tempo de compilação (R6, R9) | toda coordenada é literal estático (§1); rejeitar na compilação é a consequência coerente dessa aposta. Um subsistema de avisos adiaria a decisão para a execução, contradizendo o princípio que sustenta o resto do design. |
| **Palavras reservadas** | português, sem acentuação (`ate`, `retangulo`) | o enunciado exige palavras em português; ASCII puro mantém o alfabeto do scanner mínimo e evita ambiguidade de codificação no fonte. |
| **Sistema de coordenadas** | origem `(0, 0)` no canto superior esquerdo; `x` cresce para a direita, `y` para baixo | convenção de imagem raster. É semântica da linguagem, não da emissão de C: valeria igual para outro alvo. |
| **Sobreposição** | modelo do pintor — a escrita mais recente prevalece, sem transparência | a ordem dos comandos no fonte é a ordem de desenho. Também independe do alvo. |
| **Retângulo** | apenas o contorno, sem preenchimento | preenchimento fica como evolução (`preencher`), ver §9. |
| **Fundo da tela** | preto `(0, 0, 0)` | — |
| **Formato de saída** | PPM P3 (ASCII) | texto legível e comparável linha a linha por `diff` nos testes de regressão. |

---

## 3. Especificação léxica — entregável I

Implementada em [`../tinydraw/lexico.py`](../tinydraw/lexico.py) como lista
ordenada de pares (token, expressão regular), aplicada com a estratégia do
maior casamento na ordem declarada.

| Token | Expressão regular | Observação |
|---|---|---|
| `COMENTARIO` | `#[^\n]*` | descartado |
| `ESPACO` | `[ \t\r]+` | descartado |
| `NOVA_LINHA` | `\n` | descartado; incrementa o contador de linha |
| `CADEIA` | `"[^"\n]*"` | nome do arquivo de saída |
| `NUMERO` | `[0-9]+` | inteiros não negativos |
| `PALAVRA` | `[a-z][a-z_]*` | reclassificada em palavra reservada |
| `NOME_COR` | `[A-Z][A-Z0-9_]*` | identificador de cor |
| `IGUAL` | `=` | |
| `VIRGULA` | `,` | |

**Palavras reservadas (todas em português):** `tela`, `por`, `cor`, `usar`,
`ponto`, `linha`, `retangulo`, `salvar`, `em`, `de`, `ate`, `tamanho`.

Os domínios são disjuntos por caixa: minúsculas são exclusivas das palavras
reservadas, maiúsculas são exclusivas dos nomes de cor. Não há conflito entre
identificadores e palavras-chave, e uma palavra minúscula desconhecida é
rejeitada já na análise léxica (`palavra desconhecida 'desenhar'`).

O token `FIM` não é reconhecido por expressão regular; é acrescentado ao fim
da lista de tokens por `tokenizar()`.

---

## 4. Sintaxe — entregável II

Gramática em EBNF, implementada por descida recursiva em
[`../tinydraw/sintatico.py`](../tinydraw/sintatico.py):

```ebnf
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
```

A estrutura da tela no início e do `salvar` no fim é imposta pela própria
gramática, não pela semântica.

### 4.1. Conjuntos FIRST e prova de que a gramática é LL(1)

```
FIRST(programa)      = { "tela" }
FIRST(decl_tela)     = { "tela" }
FIRST(comando)       = { "cor", "usar", "ponto", "linha", "retangulo" }
FIRST(decl_cor)      = { "cor" }
FIRST(sel_cor)       = { "usar" }
FIRST(cmd_ponto)     = { "ponto" }
FIRST(cmd_linha)     = { "linha" }
FIRST(cmd_retangulo) = { "retangulo" }
FIRST(cmd_salvar)    = { "salvar" }
FIRST(coordenada)    = { NUMERO }
```

Nenhum não-terminal deriva ε, então basta analisar os conjuntos FIRST:

1. As cinco alternativas de `comando` têm conjuntos FIRST **disjuntos dois a
   dois** (cinco palavras reservadas distintas). A alternativa é decidida
   pelo token corrente, sem retrocesso.
2. A repetição `{ comando }` encerra quando o token corrente ∉
   FIRST(comando). O único token que pode seguir a lista de comandos é
   `"salvar"` (FIRST(cmd_salvar)), que **não** pertence a FIRST(comando) —
   não há conflito entre "repetir" e "sair do laço".
3. As demais produções são sequências fixas de terminais e não-terminais,
   sem escolha a resolver.

Portanto um único token de lookahead basta: a gramática é LL(1).

### 4.2. Árvore sintática abstrata

A saída do analisador é uma AST ([`../tinydraw/arvore.py`](../tinydraw/arvore.py)),
com nós `Programa`, `Tela`, `DeclaracaoCor`, `SelecaoCor`, `Ponto`, `Linha`,
`Retangulo` e `Salvar`. Todo nó guarda linha e coluna de origem, para que as
fases seguintes emitam diagnósticos posicionados.

---

## 5. Regras semânticas — entregável III

Implementadas em [`../tinydraw/semantico.py`](../tinydraw/semantico.py), sobre
uma **tabela de símbolos** que associa cada nome de cor a seus componentes
RGB e ao índice na paleta gerada.

| # | Regra | Diagnóstico |
|---|---|---|
| R1 | dimensões da tela > 0 | erro |
| R2 | componentes RGB em [0, 255] | erro |
| R3 | nome de cor não redeclarado | erro (aponta a linha anterior) |
| R4 | `usar` referencia cor declarada | erro |
| R5 | há cor selecionada antes de desenhar | erro |
| R6 | coordenadas dentro da tela | erro (informa o intervalo válido) |
| R7 | linhas estritamente horizontais ou verticais | erro (diagonais fora do escopo) |
| R8 | dimensões do retângulo > 0 | erro |
| R9 | retângulo cabe inteiramente na tela | erro |
| R10 | arquivo de saída termina em `.ppm` | erro |

Os erros são **acumulados** em uma única passagem, para que o usuário receba
todos os diagnósticos de uma vez. Ao final, se houver qualquer erro, a fase
levanta `ErroSemanticoMultiplo` (definido em
[`../tinydraw/erros.py`](../tinydraw/erros.py), subclasse de `ErroTinyDraw`),
cujo `formatar()` devolve todos os diagnósticos, um por linha.

Há recuperação de erro em R4: uma cor inexistente ainda conta como seleção,
evitando erros em cascata de R5.

Formato dos diagnósticos: `arquivo:linha:coluna: fase: mensagem`. Para
`exemplos/erro_semantico.td`:

```
exemplos/erro_semantico.td:9:1: erro semântico: cor 'AZUL' já foi declarada na linha 8
exemplos/erro_semantico.td:10:1: erro semântico: componente B da cor 'NEON' deve estar entre 0 e 255 (recebido 300)
exemplos/erro_semantico.td:12:6: erro semântico: cor 'ROXO' não foi declarada
exemplos/erro_semantico.td:13:1: erro semântico: coordenada (50, 3) fora da tela (20 por 10); x deve estar em [0, 19] e y em [0, 9]
exemplos/erro_semantico.td:14:1: erro semântico: linhas devem ser horizontais ou verticais nesta versão da linguagem
exemplos/erro_semantico.td:16:1: erro semântico: arquivo de saída deve terminar em '.ppm' (recebido 'saida.png')
```

(Em `x deve estar em [0, 19]`, `x` é o nome do eixo, não a antiga palavra
reservada.)

---

## 6. Geração de código C

Geração de código não é um entregável numerado do projeto — é parte da
construção do transpilador (entregável IV). `tinydraw/gerador.py` percorre a
AST e emite C:

| Construção TinyDraw | Construção C |
|---|---|
| `tela L por A` | `#define TD_LARGURA/TD_ALTURA` + `TdCor td_tela[A][L]` |
| `cor NOME = r, g, b` | entrada constante em `td_paleta[]` |
| `usar NOME` | `td_cor_atual = td_paleta[i];` |
| `ponto em x, y` | `td_ponto(x, y);` |
| `linha de a,b ate c,d` | `td_linha(a, b, c, d);` |
| `retangulo em x,y tamanho L por A` | `td_retangulo(x, y, L, A);` |
| `salvar "arq.ppm"` | `td_salvar("arq.ppm");` (PPM P3) |

O guarda de limites em `td_ponto` (`if (x < 0 || x >= TD_LARGURA || ...)
return;`) é redundante com R6/R9, que rejeitam qualquer coordenada fora da
tela antes da geração. Ele permanece como defesa do código gerado: um
defeito no gerador produz uma imagem errada, não escrita fora dos limites de
`td_tela`. O comentário no C gerado registra isso.

O programa gerado imprime uma **pré-visualização textual** no terminal (`#`
para pixel pintado, `.` para fundo), o que torna a semântica do fonte
observável sem abrir a imagem. O C é compilado com `-Wall -Wextra -Werror`
tanto nos testes quanto em `transpilador.py --executar`.

---

## 7. Programas de verificação — entregável IV

Os exemplos vivem em [`../exemplos/`](../exemplos/) e são exercitados pela
suíte ([`../testes/`](../testes/)): `test_exemplos.py` roda todos eles pelo
pipeline (os válidos transpilam e compilam sem aviso; os `erro_*.td` são
rejeitados pela fase correspondente), e `test_transpilador.py` cobre cada
fase isoladamente e um fluxo de ponta a ponta com `gcc`.

**`exemplos/bandeira.td`** — núcleo mínimo da linguagem: três cores, seleção,
retângulo, linha e ponto. Este bloco é a fonte de verdade do exemplo
canônico; `test_exemplos.py` falha se ele divergir do arquivo.

```
# Exemplo 1: uso do nucleo minimo da linguagem.
# Tela 40x20, tres cores nomeadas, ponto, linha e retangulo.

tela 40 por 20

cor VERDE    = 0, 160, 60
cor AMARELO  = 255, 210, 0
cor BRANCO   = 255, 255, 255

usar VERDE
retangulo em 0, 0 tamanho 40 por 20

usar AMARELO
retangulo em 8, 4 tamanho 24 por 12
linha de 8, 10 ate 31, 10

usar BRANCO
ponto em 20, 10

salvar "bandeira.ppm"
```

**`exemplos/moldura.td`** — demonstra a regra de sobreposição: o traço
vermelho aparece por cima do retângulo azul porque é desenhado depois.

**`exemplos/erro_semantico.td`** e **`exemplos/erro_sintatico.td`** —
programas inválidos, usados para verificar os diagnósticos (ver §5).

### 7.1. Artefatos versionados

Para cada exemplo válido, o repositório guarda dois artefatos derivados, e a
suíte garante que nenhum deles minta sobre o `.td`:

| Artefato | Como é produzido | Guarda de regressão |
|---|---|---|
| `exemplos/<nome>.c` | `python3 transpilador.py exemplos/<nome>.td` (escrito sempre com `\n`, ver `.gitattributes`) | `test_exemplos.py` compara byte a byte com o que o transpilador produz agora |
| `exemplos/<nome>_preview.png` | `<nome>.ppm` (de `--executar`) ampliado por vizinho-mais-próximo até o lado maior ter ≥ 480 px, por `python3 exemplos/gerar_previews.py` (requer Pillow) | `test_exemplos.py` confere assinatura PNG e que as dimensões são um múltiplo inteiro uniforme da tela do `.td` |

Sequência completa para regerar os dois:

```bash
python3 transpilador.py exemplos/bandeira.td --executar
python3 transpilador.py exemplos/moldura.td  --executar
python3 exemplos/gerar_previews.py
```

Os `.ppm` e os binários são intermediários e ficam fora do controle de
versão (`.gitignore`).

---

## 8. Estrutura do projeto — entregável IV

```
transpilador.py            interface de linha de comando
tinydraw/__init__.py       fachada transpilar(): encadeia as quatro fases
tinydraw/lexico.py         especificação léxica e scanner
tinydraw/arvore.py         nós da AST
tinydraw/sintatico.py      analisador descendente recursivo
tinydraw/semantico.py      tabela de símbolos e regras R1–R10
tinydraw/gerador.py        emissão de código C
tinydraw/erros.py          hierarquia de diagnósticos posicionados
testes/test_transpilador.py   fases isoladas + fluxo de ponta a ponta
testes/test_exemplos.py       contrato dos exemplos e dos artefatos versionados
exemplos/                  programas .td, .c versionados e previews
exemplos/gerar_previews.py conversão .ppm -> _preview.png (Pillow)
docs/ESPECIFICACAO.md      este documento
.gitattributes             finais de linha LF para todo texto
.gitignore                 caches, binários e .ppm gerados
```

Cada fase é um módulo independente, com interface própria e testada
isoladamente. A fachada `tinydraw.transpilar()` é o **único** ponto onde o
pipeline é montado: `transpilador.py` apenas cuida de argumentos, E/S de
arquivos e da chamada ao `gcc`.

---

## 9. Limitações e evolução

Limitações atuais: sem preenchimento, círculos, diagonais, repetição ou
camadas; tela de dimensões constantes; nenhuma otimização do código gerado.

Evolução natural: `preencher` como modificador do retângulo; algoritmo de
Bresenham para diagonais; laço `repetir n vezes` — este exigiria escopo na
tabela de símbolos, geração de `for` em C e, sobretudo, abandonar a aposta
de coordenadas estáticas (§1), o que muda a natureza da análise semântica.

---

## Apêndice A — Histórico: separador `x` → `por`

Uma versão anterior da linguagem usava `x` como separador de dimensões
(`tela 40 x 20`). A justificativa original era evitar colisão com um
identificador de coordenada; essa justificativa deixou de valer quando
`coordenada` passou a ser sempre `NUMERO "," NUMERO`, sem a letra `x`.

Com `x` na tabela, a linguagem teria 12 palavras reservadas, das quais 11 em
português e uma — `x` — um símbolo de uma letra fora do registro. A troca
para `por` (decisão A1) elimina essa exceção. O custo foi baixo: no léxico,
uma entrada no dicionário de palavras reservadas (`por` já casa o padrão
`PALAVRA`, sem alterar expressão regular); no parser, o token consumido em
`_decl_tela` e `_cmd_retangulo`; e a propagação para gramática, exemplos e
testes.
