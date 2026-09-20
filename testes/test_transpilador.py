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
# Serve para testar a geração de código C e a execução do programa transpilado
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
    """Testes do scanner, organizados pelas classes do item 6 da
    especificação: aceitação, descarte, fronteira, rejeição e regressão."""

    def _tipos(self, fonte: str) -> list[str]:
        return [t.tipo for t in lexico.tokenizar(fonte)]

    def _erro(self, fonte: str) -> ErroLexico:
        with self.assertRaises(ErroLexico) as contexto:
            lexico.tokenizar(fonte)
        return contexto.exception

    # Aceitação: um caso por categoria de token, ou seja, um teste para cada linha
    def test_aceita_palavras_reservadas(self):
        fonte = ("tela cor usar ponto linha retangulo salvar "
                 "em de ate tamanho por")
        self.assertEqual(
            self._tipos(fonte),
            ["TELA", "COR", "USAR", "PONTO", "LINHA", "RETANGULO", "SALVAR",
             "EM", "DE", "ATE", "TAMANHO", "POR", "FIM"],
        )

    def test_aceita_numero(self):
        tokens = lexico.tokenizar("007 99999")
        self.assertEqual([t.tipo for t in tokens], ["NUMERO", "NUMERO", "FIM"])
        # O léxico reconhece a forma, não a faixa (item 5 da especificação).
        self.assertEqual([t.lexema for t in tokens[:2]], ["007", "99999"])

    def test_aceita_nome_cor(self):
        tokens = lexico.tokenizar("VERMELHO AZUL_2 A")
        self.assertEqual([t.tipo for t in tokens[:3]], ["NOME_COR"] * 3)

    def test_aceita_cadeia(self):
        token = lexico.tokenizar('"desenho.ppm"')[0]
        self.assertEqual(token.tipo, "CADEIA")
        self.assertEqual(token.lexema, '"desenho.ppm"')

    def test_aceita_simbolos(self):
        self.assertEqual(self._tipos("= ,"), ["IGUAL", "VIRGULA", "FIM"])

    def test_posicao_linha_coluna(self):
        tokens = lexico.tokenizar("tela 4 por 3")
        self.assertEqual(
            [(t.linha, t.coluna) for t in tokens[:4]],
            [(1, 1), (1, 6), (1, 8), (1, 12)],
        )

    def test_coluna_reinicia_apos_quebra_de_linha(self):
        tokens = lexico.tokenizar("tela 4 por 3\ncor AZUL")
        self.assertEqual((tokens[0].linha, tokens[0].coluna), (1, 1))
        self.assertEqual((tokens[4].linha, tokens[4].coluna), (2, 1))  # cor
        self.assertEqual((tokens[5].linha, tokens[5].coluna), (2, 5))  # AZUL

    # Descarte: mostra que o scnanner ignora comentários, espaços e quebras de linha, sem gerar tokens 
    def test_descarta_comentario_no_fim_sem_quebra_de_linha(self):
        self.assertEqual(self._tipos("tela # sem quebra no fim"), ["TELA", "FIM"])

    def test_descarta_espacos_e_tabulacoes(self):
        self.assertEqual(self._tipos("tela \t\t   4"), ["TELA", "NUMERO", "FIM"])

    def test_descarta_linhas_em_branco(self):
        tokens = lexico.tokenizar("tela\n\n\n4")
        self.assertEqual([t.tipo for t in tokens], ["TELA", "NUMERO", "FIM"])
        self.assertEqual(tokens[1].linha, 4)  # contador de linha avança

    # Fronteira: mostra que o scanner reconhece corretamente o limite entre tokens, sem gerar novos
    def test_arquivo_vazio(self):
        tokens = lexico.tokenizar("")
        self.assertEqual([t.tipo for t in tokens], ["FIM"])
        self.assertEqual((tokens[0].linha, tokens[0].coluna), (1, 1))

    def test_arquivo_so_com_comentarios(self):
        self.assertEqual(self._tipos("# um\n# dois\n"), ["FIM"])

    def test_posicao_do_token_fim(self):
        fim = lexico.tokenizar("tela 4 por 3")[-1]
        self.assertEqual((fim.linha, fim.coluna), (1, 13))
        fim_com_quebra = lexico.tokenizar("tela 4 por 3\n")[-1]
        self.assertEqual((fim_com_quebra.linha, fim_com_quebra.coluna), (2, 1))

    def test_cadeia_vazia(self):
        token = lexico.tokenizar('""')[0]
        self.assertEqual((token.tipo, token.lexema), ("CADEIA", '""'))

    # Rejeição: mostra que o scanner rejeita entradas inválidas, levanta ErroLexico e aponta a posição do erro
    def test_rejeita_caractere_fora_do_alfabeto(self):
        erro = self._erro("tela 4 @ 3")
        self.assertIn("fora do alfabeto", erro.mensagem)
        self.assertEqual((erro.linha, erro.coluna), (1, 8))

    def test_rejeita_caractere_acentuado(self):
        """`retângulo` deve acusar o acento, não o prefixo 'ret'."""
        erro = self._erro("retângulo em 1, 1")
        self.assertIn("'â'", erro.mensagem)
        self.assertIn("sem acentuação", erro.mensagem)
        self.assertNotIn("palavra desconhecida", erro.mensagem)
        self.assertEqual((erro.linha, erro.coluna), (1, 4))

    def test_rejeita_cadeia_nao_fechada(self):
        erro = self._erro('salvar "desenho.ppm')
        self.assertIn("cadeia não terminada", erro.mensagem)
        self.assertEqual((erro.linha, erro.coluna), (1, 8))

    def test_rejeita_cadeia_com_quebra_de_linha_interna(self):
        erro = self._erro('salvar "dese\nnho.ppm"')
        self.assertIn("cadeia não terminada", erro.mensagem)
        self.assertEqual((erro.linha, erro.coluna), (1, 8))

    def test_rejeita_palavra_minuscula_desconhecida(self):
        erro = self._erro("desenhar 1")
        self.assertIn("palavra desconhecida 'desenhar'", erro.mensagem)
        self.assertEqual((erro.linha, erro.coluna), (1, 1))

    def test_rejeita_nome_de_cor_em_minuscula(self):
        erro = self._erro("cor azul = 1, 1, 1")
        self.assertIn("palavra desconhecida 'azul'", erro.mensagem)
        self.assertIn("maiúsculas", erro.mensagem)
        self.assertEqual((erro.linha, erro.coluna), (1, 5))

    # Regressão: testes que garantem que erros previamente corrigidos não voltem a ocorrer
    def test_separador_x_permanece_rejeitado(self):
        """Trava a decisão de usar `por` como separador: se `x` voltar a ser
        palavra reservada, este teste falha."""
        erro = self._erro("tela 40 x 20")
        self.assertIn("palavra desconhecida 'x'", erro.mensagem)
        self.assertEqual((erro.linha, erro.coluna), (1, 9))

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
