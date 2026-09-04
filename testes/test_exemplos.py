"""

    # Testes de contrato dos programas de exemplo
    - Todo arquivo em exemplos/ passa pelo pipeline completo: os programas
      válidos transpilam (e compilam sem aviso, se houver gcc); os programas
      'erro_*.td' são rejeitados pela fase correspondente.
    - Os artefatos versionados não mentem sobre o .td: o .c guardado no
      repositório é idêntico ao que o transpilador produz agora, e o PNG de
      pré-visualização é um upscale uniforme da tela declarada.
    - O exemplo canônico (bandeira.td) é comparado com o bloco embutido em
      docs/ESPECIFICACAO.md, para que documento e arquivo não divirjam sem
      quebrar o build.

    # Execução: python3 -m unittest discover -s testes -v

"""

from __future__ import annotations

import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from tinydraw import transpilar
from tinydraw.erros import ErroSintatico, ErroSemanticoMultiplo

EXEMPLOS = RAIZ / "exemplos"
ESPECIFICACAO = RAIZ / "docs" / "ESPECIFICACAO.md"

# Programas que devem transpilar sem erro.
VALIDOS = ["bandeira.td", "moldura.td"]

# Programas inválidos e a exceção da fase que deve rejeitar cada um.
INVALIDOS = {
    "erro_sintatico.td": ErroSintatico,
    "erro_semantico.td": ErroSemanticoMultiplo,
}


def _fonte(nome: str) -> str:
    return (EXEMPLOS / nome).read_text(encoding="utf-8")

# Teste de exemplos válidos: cada um transpila e compila sem aviso
class TesteExemplosValidos(unittest.TestCase):
    def test_todos_transpilam(self):
        for nome in VALIDOS:
            with self.subTest(exemplo=nome):
                codigo_c = transpilar(_fonte(nome))
                self.assertIn("int main(void)", codigo_c)

    @unittest.skipUnless(shutil.which("gcc"), "gcc não encontrado no PATH")
    def test_todos_compilam_sem_aviso(self):
        for nome in VALIDOS:
            with self.subTest(exemplo=nome):
                codigo_c = transpilar(_fonte(nome))
                with tempfile.TemporaryDirectory() as pasta:
                    fonte_c = Path(pasta) / "saida.c"
                    fonte_c.write_text(codigo_c, encoding="utf-8")
                    subprocess.run(
                        ["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                         str(fonte_c), "-o", str(Path(pasta) / "saida")],
                        check=True,
                    )

# Teste de exemplos inválidos: cada um é rejeitado pela fase certa
class TesteExemplosInvalidos(unittest.TestCase):
    def test_cada_um_e_rejeitado_pela_fase_certa(self):
        for nome, excecao in INVALIDOS.items():
            with self.subTest(exemplo=nome):
                with self.assertRaises(excecao):
                    transpilar(_fonte(nome))

# Teste de sincronização entre o TinyDraw e os artefatos versionados
class TesteArtefatosVersionados(unittest.TestCase):
    def test_c_versionado_reflete_o_td(self):
        for nome in VALIDOS:
            with self.subTest(exemplo=nome):
                esperado = transpilar(_fonte(nome))
                arquivo_c = (EXEMPLOS / nome).with_suffix(".c")
                atual = arquivo_c.read_text(encoding="utf-8")
                self.assertEqual(
                    esperado,
                    atual,
                    msg=(
                        f"{arquivo_c.name} está defasado em relação a "
                        f"{nome}. Regenere: "
                        f"python3 transpilador.py exemplos/{nome}"
                    ),
                )

    def test_preview_reflete_a_tela_do_td(self):
        for nome in VALIDOS:
            with self.subTest(exemplo=nome):
                png = (EXEMPLOS / nome).with_name(
                    Path(nome).stem + "_preview.png"
                )
                self.assertTrue(png.exists(), f"{png.name} não existe")
                cabecalho = png.read_bytes()[:24]
                self.assertEqual(
                    cabecalho[:8],
                    b"\x89PNG\r\n\x1a\n",
                    f"{png.name} não é um PNG válido",
                )
                larg_px, alt_px = struct.unpack(">II", cabecalho[16:24])

                fonte = _fonte(nome)
                m = re.search(r"tela\s+(\d+)\s+por\s+(\d+)", fonte)
                self.assertIsNotNone(m, f"'tela ... por ...' não achado em {nome}")
                larg_td, alt_td = int(m.group(1)), int(m.group(2))

                self.assertEqual(larg_px % larg_td, 0, "largura não é múltipla")
                self.assertEqual(alt_px % alt_td, 0, "altura não é múltipla")
                self.assertEqual(
                    larg_px // larg_td,
                    alt_px // alt_td,
                    f"{png.name} não é um upscale uniforme de {nome} "
                    f"(rode python3 exemplos/gerar_previews.py)",
                )

# Teste de sincronização entre o exemplo canônico e a especificação
class TesteEspecificacaoSincronizada(unittest.TestCase):
    def test_bandeira_esta_embutida_no_spec(self):
        if not ESPECIFICACAO.exists():
            self.skipTest("docs/ESPECIFICACAO.md ainda não existe")
        arquivo = _fonte("bandeira.td").replace("\r\n", "\n").strip()
        spec = ESPECIFICACAO.read_text(encoding="utf-8").replace("\r\n", "\n")
        self.assertIn(
            arquivo,
            spec,
            msg=(
                "exemplos/bandeira.td e docs/ESPECIFICACAO.md divergiram. "
                "A fonte de verdade é exemplos/bandeira.td: edite "
                "docs/ESPECIFICACAO.md para reproduzir o conteúdo atual do .td "
                "(bloco na seção 'Programas de verificação')."
            ),
        )


if __name__ == "__main__":
    unittest.main()
