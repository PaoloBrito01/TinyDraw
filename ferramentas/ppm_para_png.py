#!/usr/bin/env python3
"""

    # Conversor de PPM para PNG
    - Lê um PPM (P3 ASCII ou P6 binário) e grava o PNG equivalente, RGB de
      8 bits, sem redimensionar.
    - Só biblioteca padrão (`zlib`, `struct`): não requer Pillow. Serve de
      complemento ao `transpilador.py --executar`, que só emite PPM.

    # Uso:
        python3 ferramentas/ppm_para_png.py exemplos/testeQuadro.ppm
        python3 ferramentas/ppm_para_png.py entrada.ppm -o saida.png
        python3 ferramentas/ppm_para_png.py exemplos/*.ppm        # em lote

    Sem `-o/--saida`, o PNG recebe o nome do PPM com a extensão trocada, na
    mesma pasta.

"""

from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path


class ErroPPM(ValueError):
    """PPM malformado ou fora do subconjunto suportado (P3/P6)."""


def _tokens_cabecalho(dados: bytes):
    """Gera (token, posição_após_o_token) do cabeçalho PPM.

    Espaços em branco separam tokens; um '#' inicia um comentário que vai
    até o fim da linha. A posição devolvida é relativa a `dados`.
    """
    i, n = 0, len(dados)
    while i < n:
        c = dados[i]
        if c in b" \t\r\n":
            i += 1
        elif c == 0x23:  # '#'
            while i < n and dados[i] not in b"\r\n":
                i += 1
        else:
            inicio = i
            while i < n and dados[i] not in b" \t\r\n":
                i += 1
            yield dados[inicio:i], i


def ler_ppm(caminho: Path) -> tuple[int, int, bytearray]:
    """Devolve (largura, altura, pixels) — pixels em RGB de 8 bits, sem alfa."""
    dados = caminho.read_bytes()
    formato = dados[:2]
    if formato not in (b"P3", b"P6"):
        raise ErroPPM(f"{caminho.name}: não é PPM P3 nem P6")

    tokens = _tokens_cabecalho(dados[2:])
    try:
        largura = int(next(tokens)[0])
        altura = int(next(tokens)[0])
        bruto_max, pos = next(tokens)
        maxval = int(bruto_max)
    except (StopIteration, ValueError):
        raise ErroPPM(f"{caminho.name}: cabeçalho incompleto ou inválido") from None
    if largura <= 0 or altura <= 0:
        raise ErroPPM(f"{caminho.name}: dimensões inválidas ({largura}x{altura})")
    if not 0 < maxval < 65536:
        raise ErroPPM(f"{caminho.name}: valor máximo inválido ({maxval})")

    total = largura * altura * 3
    corpo = dados[2 + pos:]

    if formato == b"P3":
        try:
            amostras = [int(a) for a in corpo.split()[:total]]
        except ValueError:
            raise ErroPPM(f"{caminho.name}: amostra não numérica no corpo") from None
    else:  # P6: um separador após o maxval, depois bytes crus
        corpo = corpo[1:]
        passo = 1 if maxval < 256 else 2
        need = total * passo
        if len(corpo) < need:
            raise ErroPPM(f"{caminho.name}: dados binários truncados")
        if passo == 1:
            amostras = list(corpo[:need])
        else:
            amostras = [(corpo[k] << 8) | corpo[k + 1] for k in range(0, need, 2)]

    if len(amostras) < total:
        raise ErroPPM(
            f"{caminho.name}: esperava {total} amostras, encontrei {len(amostras)}"
        )

    if maxval == 255:
        return largura, altura, bytearray(amostras)
    # Reescala [0, maxval] -> [0, 255] com arredondamento inteiro (sem float).
    return largura, altura, bytearray(
        min(255, (v * 255 + maxval // 2) // maxval) for v in amostras
    )


def _chunk(tipo: bytes, dados: bytes) -> bytes:
    return (
        struct.pack(">I", len(dados))
        + tipo
        + dados
        + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)
    )


def escrever_png(caminho: Path, largura: int, altura: int, pixels: bytes) -> None:
    """Grava um PNG truecolor de 8 bits, filtro None em todas as linhas."""
    passo = largura * 3
    cru = bytearray()
    for y in range(altura):
        cru.append(0)  # tipo de filtro da linha: None
        cru.extend(pixels[y * passo:(y + 1) * passo])
    ihdr = struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0)
    caminho.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(cru), 9))
        + _chunk(b"IEND", b"")
    )


def converter(ppm: Path, saida: Path | None = None) -> Path:
    largura, altura, pixels = ler_ppm(ppm)
    destino = saida or ppm.with_suffix(".png")
    escrever_png(destino, largura, altura, pixels)
    return destino


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(
        description="Converte PPM (P3 ou P6) em PNG RGB de 8 bits — só stdlib."
    )
    analisador.add_argument("fonte", type=Path, nargs="+", help="arquivo(s) .ppm")
    analisador.add_argument(
        "-o", "--saida", type=Path, help="arquivo .png de saída (uma fonte só)"
    )
    args = analisador.parse_args(argv)

    if args.saida and len(args.fonte) > 1:
        print("ppm_para_png: -o/--saida exige uma única fonte", file=sys.stderr)
        return 2

    codigo = 0
    for ppm in args.fonte:
        try:
            destino = converter(ppm, args.saida)
        except (OSError, ErroPPM) as erro:
            print(f"ppm_para_png: {erro}", file=sys.stderr)
            codigo = 1
            continue
        print(f"{ppm.name} -> {destino.name}")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
