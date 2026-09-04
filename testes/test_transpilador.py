"""

    # Testes do transpilador TinyDraw
    # Execução: python3 -m unittest discover -s testes -v

"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Inclui o diretório raiz do projeto no sys.path para importar tinydraw
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Bibliotecas do TinyDraw
from tinydraw import gerador, lexico, semantico, sintatico, transpilar
from tinydraw.erros import ErroLexico, ErroSintatico, ErroSemanticoMultiplo

# Programa para teste de ponta a ponta (transpilação, compilação e execução)
# Gera uma tela 10x6 com um retângulo rosa, uma linha preta e um ponto rosa
# Arquivo de sáida: teste.ppm
PROGRAMA_VALIDO = """
tela 10 por 6
cor PRETO = 0, 0, 0
cor ROSA  = 255, 0, 128
usar ROSA
retangulo em 1, 1 tamanho 8 por 4
linha de 0, 0 ate 9, 0
ponto em 5, 3
salvar "teste.ppm"
"""

# Função auxiliar para testar erros semânticos
def _erros_semanticos(fonte: str) -> list[str]:
    programa = sintatico.analisar(lexico.tokenizar(fonte))
    with unittest.TestCase().assertRaises(ErroSemanticoMultiplo) as contexto:
        semantico.analisar(programa)
    return [erro.mensagem for erro in contexto.exception.erros]

# Testes unitários 
class TesteLexico(unittest.TestCase):
    def test_reconhece_palavras_reservadas_e_nomes(self):
        tokens = lexico.tokenizar("tela 4 por 3\ncor AZUL = 0, 0, 255")
        tipos = [t.tipo for t in tokens]
        self.assertEqual(
            tipos,
            ["TELA", "NUMERO", "POR", "NUMERO", "COR", "NOME_COR", "IGUAL",
             "NUMERO", "VIRGULA", "NUMERO", "VIRGULA", "NUMERO", "FIM"],
        )

    def test_ignora_comentarios(self):
        tokens = lexico.tokenizar("# comentario\ntela 4 por 3")
        self.assertEqual(tokens[0].tipo, "TELA")
        self.assertEqual(tokens[0].linha, 2)

    def test_caractere_invalido(self):
        with self.assertRaises(ErroLexico):
            lexico.tokenizar("tela 4 @ 3")

    def test_palavra_minuscula_desconhecida(self):
        with self.assertRaises(ErroLexico):
            lexico.tokenizar("desenhar 1")

# Testes sintáticos e semânticos
class TesteSintatico(unittest.TestCase):
    def test_arvore_do_programa_valido(self):
        programa = sintatico.analisar(lexico.tokenizar(PROGRAMA_VALIDO))
        self.assertEqual((programa.tela.largura, programa.tela.altura), (10, 6))
        self.assertEqual(len(programa.comandos), 6)
        self.assertEqual(programa.salvar.arquivo, "teste.ppm")

    def test_falta_palavra_reservada(self):
        with self.assertRaises(ErroSintatico):
            sintatico.analisar(lexico.tokenizar("tela 10 10\nsalvar \"a.ppm\""))

    def test_salvar_obrigatorio(self):
        with self.assertRaises(ErroSintatico):
            sintatico.analisar(lexico.tokenizar("tela 10 por 10"))

# Testes semânticos
class TesteSemantico(unittest.TestCase):
    def test_programa_valido_nao_gera_erros(self):
        programa = sintatico.analisar(lexico.tokenizar(PROGRAMA_VALIDO))
        tabela = semantico.analisar(programa)
        self.assertEqual([c.nome for c in tabela.cores], ["PRETO", "ROSA"])

    def test_cor_duplicada(self):
        fonte = ('tela 4 por 4\ncor A = 1, 1, 1\ncor A = 2, 2, 2\n'
                 'usar A\nsalvar "s.ppm"')
        self.assertIn("já foi declarada na linha 2", _erros_semanticos(fonte)[0])

    def test_componente_fora_do_intervalo(self):
        fonte = 'tela 4 por 4\ncor A = 1, 1, 999\nsalvar "s.ppm"'
        self.assertIn("entre 0 e 255", _erros_semanticos(fonte)[0])

    def test_cor_nao_declarada(self):
        fonte = 'tela 4 por 4\nusar A\nsalvar "s.ppm"'
        self.assertIn("não foi declarada", _erros_semanticos(fonte)[0])

    def test_desenho_sem_cor_selecionada(self):
        fonte = 'tela 4 por 4\nponto em 1, 1\nsalvar "s.ppm"'
        self.assertIn("nenhuma cor selecionada", _erros_semanticos(fonte)[0])

    def test_coordenada_fora_da_tela(self):
        fonte = ('tela 4 por 4\ncor A = 1, 1, 1\nusar A\nponto em 9, 1\n'
                 'salvar "s.ppm"')
        self.assertIn("fora da tela", _erros_semanticos(fonte)[0])

    def test_linha_diagonal_rejeitada(self):
        fonte = ('tela 8 por 8\ncor A = 1, 1, 1\nusar A\nlinha de 0, 0 ate 3, 3\n'
                 'salvar "s.ppm"')
        self.assertIn("horizontais ou verticais", _erros_semanticos(fonte)[0])

    def test_retangulo_ultrapassa_limites(self):
        fonte = ('tela 8 por 8\ncor A = 1, 1, 1\nusar A\n'
                 'retangulo em 4, 4 tamanho 8 por 8\nsalvar "s.ppm"')
        self.assertIn("ultrapassa os limites", _erros_semanticos(fonte)[0])

    def test_extensao_invalida(self):
        fonte = 'tela 4 por 4\nsalvar "s.png"'
        self.assertIn("terminar em '.ppm'", _erros_semanticos(fonte)[0])

# Testes de geração de código C e execução do programa transpilado
class TesteGeracaoDeCodigo(unittest.TestCase):
    def test_mapeamento_das_construcoes(self):
        codigo_c = transpilar(PROGRAMA_VALIDO)
        self.assertIn("#define TD_LARGURA 10", codigo_c)
        self.assertIn("td_cor_atual = td_paleta[1];", codigo_c)  # usar ROSA
        self.assertIn("td_retangulo(1, 1, 8, 4);", codigo_c) 
        self.assertIn("td_linha(0, 0, 9, 0);", codigo_c)
        self.assertIn("td_ponto(5, 3);", codigo_c)
        self.assertIn('td_salvar("teste.ppm")', codigo_c)

    def test_fluxo_de_ponta_a_ponta(self):
        """Compila o C gerado com gcc, executa e confere o PPM produzido."""
        codigo_c = transpilar(PROGRAMA_VALIDO)
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta)
            fonte_c = caminho / "saida.c"
            fonte_c.write_text(codigo_c, encoding="utf-8")
            binario = caminho / "saida"
            subprocess.run(
                ["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                 str(fonte_c), "-o", str(binario)],
                check=True,
            )
            subprocess.run([str(binario)], cwd=caminho, check=True,
                           stdout=subprocess.DEVNULL)

            ppm = (caminho / "teste.ppm").read_text(encoding="utf-8").split()
            self.assertEqual(ppm[0], "P3")
            self.assertEqual(ppm[1:4], ["10", "6", "255"])
            pixels = [tuple(map(int, ppm[i:i + 3])) for i in range(4, len(ppm), 3)]
            self.assertEqual(len(pixels), 60)
            # ponto em 5, 3 -> linha 3, coluna 5 -> cor ROSA
            self.assertEqual(pixels[3 * 10 + 5], (255, 0, 128))
            # (0, 5) permanece no fundo preto
            self.assertEqual(pixels[5 * 10 + 0], (0, 0, 0))

# Execução dos testes
if __name__ == "__main__":
    unittest.main()
