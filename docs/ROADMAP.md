# TinyDraw — Roadmap de desenvolvimento

As 11 etapas do projeto, do recorte do problema à apresentação. A definição
da linguagem e da implementação está em
[`docs/ESPECIFICACAO.md`](docs/ESPECIFICACAO.md).

### 1 · Delimitação do problema
Modelagem computacional do domínio, definição de usuário, propósito, limites
e resultado esperado. Justificativa da criação de uma DSL frente às
alternativas.
`Modelagem de problemas · DSL vs. linguagem de propósito geral · engenharia de requisitos`

### 2 · Vocabulário e tokens
Escrita dos primeiros programas representativos, dos quais se deriva o
vocabulário e a tabela de tokens.
`Alfabeto · lexema, token e padrão · palavras reservadas vs. identificadores`

### 3 · Especificação léxica
Formalização de cada categoria de token por expressão regular. Definição das
classes de teste do scanner.
`Expressões regulares · linguagens regulares · classes de equivalência`

### 4 · Scanner e gramática
Implementação do analisador léxico. Definição das regras de produção da
linguagem.
`Autômatos finitos · BNF/EBNF · gramáticas livres de contexto`

### 5 · Analisador sintático
Construção do parser a partir da gramática, produzindo a estrutura de
representação do programa.
`Análise descendente recursiva · FIRST/FOLLOW · derivação e árvore sintática`

### 6 · Integração
Finalização do parser, acoplamento com o scanner e definição das primeiras
regras de contexto.
`Pipeline de compilação · AST · recuperação de erros`

### 7 · Análise semântica
Implementação das dez regras de contexto (R1–R10): dimensões da tela e do
retângulo maiores que zero, coordenadas e retângulo dentro da tela, linhas
estritamente horizontais ou verticais, cores declaradas antes do uso,
componentes RGB em [0, 255] e extensão `.ppm` no arquivo de saída.
`Tabela de símbolos · regras de contexto · verificação estática`

### 8 · Geração de código
Mapeamento das construções da DSL para C. Primeira execução de ponta a ponta
do pipeline completo.
`Tradução dirigida por sintaxe · travessia da AST · emissão de código`

### 9 · Visualização
Finalização do gerador e do sistema que torna observável a semântica do
programa-fonte.
`Matriz de pixels · serialização PPM · algoritmo do pintor`

### 10 · Testes e revisão
Ampliação da bateria de testes em todas as fases, com casos válidos e casos
que devem falhar.
`Cobertura por classe de erro · diagnósticos localizados · testes de regressão`

### 11 · Finalização
Correções finais, documentação completa e preparação da apresentação.
`Argumentação de decisões de projeto · limitações e evolução da linguagem`
