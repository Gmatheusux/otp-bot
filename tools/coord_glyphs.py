"""
tools/coord_glyphs.py — Lê a caixinha "x, y, z" do minimapa e cria os dígitos-modelo que faltam.

Só lê a tela: não manda tecla nem clique.

  python tools/coord_glyphs.py                                   lê ao vivo e salva o recorte ampliado
  python tools/coord_glyphs.py --image print.png                 lê de um print da área cliente
  python tools/coord_glyphs.py --image print.png --text "433, 1501, 7"
                                                                 com o texto certo: salva os caracteres que faltam
                                                                 em defaults/coords/ (--overwrite troca os que já há)

Os prints ao vivo ficam em %APPDATA%\\OTPBot\\e08 (nunca no git).
"""
import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from otpbot.app import paths  # noqa: E402
from otpbot.interface.config_manager import ConfigManager  # noqa: E402
from otpbot.perception import coords  # noqa: E402
from otpbot.platform import game_window  # noqa: E402


def grab_live() -> np.ndarray:
    game_window.enable_dpi_awareness()
    win = game_window.locate()
    if win is None:
        sys.exit("Janela do jogo não encontrada.")
    if game_window.is_covered(win):
        sys.exit("Janela do jogo coberta por outra: deixe o jogo visível.")
    return game_window.capture_client(win)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image", help="print da área cliente (sem: captura ao vivo)")
    ap.add_argument("--text", help="texto certo da caixinha, ex.: '433, 1501, 7'")
    ap.add_argument("--overwrite", action="store_true", help="troca os modelos que já existem")
    args = ap.parse_args()

    if args.image:
        frame = cv2.imdecode(np.fromfile(args.image, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            sys.exit(f"Não consegui abrir {args.image}")
    else:
        frame = grab_live()

    calibration = ConfigManager().config.get("calibration", {})
    rect = coords.coords_rect(calibration, frame.shape)
    if rect is None:
        sys.exit("Sem região 'coords' para este tamanho de frame.")
    x, y, w, h = rect
    crop = frame[y:y + h, x:x + w]
    reading = coords.CoordReader().read(frame, calibration)
    print(f"Frame {frame.shape[1]}x{frame.shape[0]}, região {rect}")
    print(f"Lido: '{reading.text}' -> {reading.coord} (confiança {reading.confidence:.2f})")

    if not args.image:
        out = paths.data_dir() / "e08"
        out.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        game_window.save_png(str(out / f"cliente_{stamp}.png"), frame)
        big = cv2.resize(crop, None, fx=6, fy=6, interpolation=cv2.INTER_NEAREST)
        game_window.save_png(str(out / f"coords_{stamp}.png"), big)
        print(f"Prints em {out} ({stamp})")

    if args.text:
        expected = args.text.replace(" ", "")
        parts = coords.segment(coords.text_mask(crop))
        if len(parts) != len(expected):
            sys.exit(f"Separei {len(parts)} caracteres e o texto tem {len(expected)}: nada salvo.")
        known = coords.load_glyphs()
        for char, mask in zip(expected, parts):
            if char in known and not args.overwrite:
                print(f"  '{char}': já existe (nota {coords.similarity(mask, known[char]):.2f})")
                continue
            print(f"  '{char}': salvo em {coords.save_glyph(mask, char)}")
            known[char] = mask


if __name__ == "__main__":
    main()
