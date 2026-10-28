# exemplo de quadro
tela 40 por 40

cor AZUL = 18, 63, 255
cor MARROM = 71, 42, 8
cor VERMELHA = 250, 47, 5
# criando um retangulo
usar MARROM 
retangulo em 0, 0 tamanho 20 por 20

# fazendo duas linhas azul
usar AZUL 
# x, y ate o ponto x, y , fazendo uma linha de borda a borda
linha de 1, 1 ate 18, 1
linha de 1, 2 ate 18, 2

# fazendo um desenho em vermelho
usar VERMELHA
retangulo em 1, 3 tamanho 18 por 16


salvar "exemploQuadro.ppm"
