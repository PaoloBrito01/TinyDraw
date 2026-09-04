# Exemplo 3: programa invalido, usado para demonstrar os diagnosticos
# da analise semantica. Erros: cor duplicada, componente fora do
# intervalo, cor nao declarada, coordenada fora da tela, linha
# diagonal e extensao de arquivo nao permitida.

tela 20 por 10

cor AZUL = 0, 0, 255
cor AZUL = 10, 10, 200
cor NEON = 0, 0, 300

usar ROXO
ponto em 50, 3
linha de 1, 1 ate 8, 5

salvar "saida.png"
