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
