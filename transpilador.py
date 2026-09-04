#!/usr/bin/env python3
"""

    # Interface de linha de comando do transpilador
    - encadeia as quatro fases (léxica, sintática, semântica, geração de C)
      reusando a fachada `tinydraw.transpilar`;
    - opcionalmente compila o C gerado com `gcc` e executa o binário.

    # Uso:
        python3 transpilador.py exemplos/bandeira.td              # gera o .c
        python3 transpilador.py exemplos/bandeira.td --executar   # gera, compila e roda
        python3 transpilador.py exemplos/bandeira.td --tokens     # lista os tokens
        python3 transpilador.py exemplos/bandeira.td -o saida.c   # define o .c de saída

"""

from __future__ import annotations
from pathlib import Path

import argparse
import subprocess
import sys

from tinydraw import lexico, transpilar
from tinydraw.erros import ErroTinyDraw

# Mesmas flags usadas na suíte de testes, para que um C que compila nos testes
# também compile aqui.
_FLAGS_GCC = ["-std=c11", "-Wall", "-Wextra", "-Werror"]


def _listar_tokens(codigo: str) -> int:
    for token in lexico.tokenizar(codigo):
        print(f"{token.linha:>3}:{token.coluna:<3} {token.tipo:<10} {token.lexema}")
    return 0


def _compilar_e_executar(destino: Path) -> int:
    binario = destino.with_suffix("")
    compilacao = subprocess.run(["gcc", *_FLAGS_GCC, str(destino), "-o", str(binario)])
    if compilacao.returncode != 0:
        print("TinyDraw: falha ao compilar o C gerado", file=sys.stderr)
        return 3
    # flush antes de ceder o terminal ao binário, para não intercalar a saída.
    print(f"compilado: {binario}\n", flush=True)
    return subprocess.run(
        [str(binario.resolve())], cwd=destino.resolve().parent
    ).returncode


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description="Transpilador TinyDraw -> C")
    analisador.add_argument("fonte", type=Path, help="arquivo .td de entrada")
    analisador.add_argument("-o", "--saida", type=Path, help="arquivo .c de saída")
    analisador.add_argument(
        "--tokens", action="store_true", help="apenas listar os tokens"
    )
    analisador.add_argument(
        "--executar",
        action="store_true",
        help="compilar o C gerado com gcc e executar o resultado",
    )
    args = analisador.parse_args(argv)

    try:
        codigo = args.fonte.read_text(encoding="utf-8")
    except OSError as erro:
        print(f"TinyDraw: {erro}", file=sys.stderr)
        return 2

    try:
        if args.tokens:
            return _listar_tokens(codigo)
        codigo_c = transpilar(codigo)
    except ErroTinyDraw as erro:
        print(erro.formatar(str(args.fonte)), file=sys.stderr)
        return 1

    destino = args.saida or args.fonte.with_suffix(".c")
    # newline="\n": o .c sai idêntico em qualquer SO, para casar com o
    # arquivo versionado (ver testes/test_exemplos.py).
    destino.write_text(codigo_c, encoding="utf-8", newline="\n")
    print(f"gerado: {destino}", flush=True)

    if args.executar:
        return _compilar_e_executar(destino)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
