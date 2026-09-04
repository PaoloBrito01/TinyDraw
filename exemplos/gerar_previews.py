#!/usr/bin/env python3
"""

    # Produtor das pré-visualizações PNG dos exemplos
    - Converte cada exemplos/<nome>.ppm em exemplos/<nome>_preview.png.
    - A conversão é um upscale inteiro por vizinho-mais-próximo: o lado maior
      da imagem fica com pelo menos ALVO pixels. É determinística e não
      depende de editor.
    - Os .ppm são intermediários (ignorados pelo git). Regere-os antes:

        python3 transpilador.py exemplos/bandeira.td --executar
        python3 transpilador.py exemplos/moldura.td  --executar
        python3 exemplos/gerar_previews.py

    # Requer Pillow (pip install pillow); usado só para os previews, não
    # pelo transpilador nem pela suíte principal.

"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ALVO = 480  # pixels no lado maior, após o upscale

AQUI = Path(__file__).resolve().parent


def gerar(ppm: Path) -> Path:
    destino = ppm.with_name(ppm.stem + "_preview.png")
    with Image.open(ppm) as img:
        fator = max(1, -(-ALVO // max(img.size)))  # divisão para cima
        ampliada = img.resize(
            (img.width * fator, img.height * fator), Image.NEAREST
        )
        ampliada.save(destino)
    return destino


def main() -> int:
    ppms = sorted(AQUI.glob("*.ppm"))
    if not ppms:
        print(
            "nenhum .ppm em exemplos/ — rode antes 'transpilador.py <td> "
            "--executar'",
            file=sys.stderr,
        )
        return 1
    for ppm in ppms:
        print(f"{ppm.name} -> {gerar(ppm).name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
