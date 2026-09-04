# Exemplo 2: sobreposicao. O ultimo comando desenhado prevalece,
# por isso o traco vermelho aparece por cima do retangulo azul.

tela 24 por 12

cor AZUL     = 30, 60, 200
cor VERMELHO = 220, 30, 30

usar AZUL
retangulo em 2, 2 tamanho 20 por 8

usar VERMELHO
linha de 2, 6 ate 21, 6
ponto em 2, 2

salvar "moldura.ppm"
