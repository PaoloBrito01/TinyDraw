# Pontos de correção:

- [x] gerar apenas funções usadas. Atualmente quando não usamos "linha, retangulo, ponto" recebe erro.
  - o gerador escreve todas funções auxiliares td_ponto, td_linha, td_retangulo
  - como no exemplo10 só usamos "ponto" então td_retangulo fica declarado e nunca e usado
  - **Resolvido** em [#2](https://github.com/PaoloBrito01/TinyDraw/pull/2): o gerador emite só as rotinas usadas (retangulo -> linha -> ponto) e `td_paleta`/`td_cor_atual` só quando há `usar`. Mesmo caso cobria `cor` declarada sem `usar`.
