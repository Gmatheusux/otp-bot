"""
tools/extrair_frames_video.py — Frames de vídeo de hunt -> dataset da visão (pending/), para rotular no console.

    python tools/extrair_frames_video.py "C:\\Users\\Gabe\\Videos\\Captures\\Service 2026-10-09 20-41-41.mp4"
    python tools/extrair_frames_video.py <video> --a-cada 3 --perfil 1920x1009

O vídeo tem que ser gravado da JANELA do jogo (área cliente). Vídeo de 3440 gravado reduzido (2560 de largura) é
ampliado de volta para 3440 antes do recorte, para os sprites ficarem na escala do jogo ao vivo. Recorta só a
`game_area` do perfil de calibração do config. Frames quase iguais ao anterior guardado são pulados.
Só lê o vídeo; nunca apaga nem muda o arquivo de origem.
"""
import argparse
import re
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from otpbot.app import paths  # noqa: E402
from otpbot.interface.config_manager import ConfigManager  # noqa: E402
from otpbot.learning.dataset import Dataset, crop_game_area, group_key, similar  # noqa: E402

# Largura do vídeo -> (largura real da área cliente, perfil). 2560 = 3440 gravado ×0,744 (E03).
KNOWN_WIDTHS = {2560: (3440, "3440x1369"), 3440: (3440, "3440x1369"), 1920: (1920, "1920x1009")}


def source_name(video: Path) -> str:
    stamp = re.search(r"(\d{4})-(\d{2})-(\d{2}) (\d{2})-(\d{2})-(\d{2})", video.stem)
    if stamp:
        return "video-{}{}{}-{}{}{}".format(*stamp.groups())
    return "video-" + re.sub(r"[^A-Za-z0-9]+", "-", video.stem).strip("-")[:40]


def extract(video: Path, every_s: float, profile: str = None, dataset: Dataset = None,
            calibration: dict = None, max_diff: float = 4.0) -> dict:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise SystemExit(f"Não abriu o vídeo: {video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    target_width, auto_profile = KNOWN_WIDTHS.get(width, (width, None))
    profile = profile or auto_profile
    scale = target_width / width
    step = max(1, int(round(every_s * fps)))
    source = source_name(video)
    dataset = dataset or Dataset()
    calibration = calibration if calibration is not None else ConfigManager().config.get("calibration", {})

    saved = skipped = existing = index = 0
    last = None
    while cap.grab():
        if index % step == 0:
            ok, frame = cap.retrieve()
            if not ok:
                break
            if scale != 1.0:
                frame = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            crop, key = crop_game_area(frame, calibration, profile)
            if crop is None:
                raise SystemExit(f"Perfil {key} sem região game_area.")
            t = index / fps
            image_id = f"{source}_t{t:06.1f}"
            if similar(crop, last, max_diff):
                skipped += 1
            elif dataset.exists(image_id):  # rodar de novo não duplica
                last = crop
                existing += 1
            else:
                last = crop
                dataset.add(crop, source=source, group=group_key(source, t), profile=key, image_id=image_id,
                            extra={"video": video.name, "video_time_s": round(t, 1), "video_scale": round(scale, 4)})
                saved += 1
        index += 1
    cap.release()
    return {"video": video.name, "source": source, "profile": profile, "scale": round(scale, 4),
            "saved": saved, "skipped": skipped, "existing": existing}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("videos", nargs="+", type=Path)
    parser.add_argument("--a-cada", type=float, default=3.0, help="segundos entre frames (padrão 3)")
    parser.add_argument("--perfil", default=None, help="perfil de calibração (padrão: pela largura do vídeo)")
    args = parser.parse_args()
    paths.prepare()
    dataset = Dataset()
    for video in args.videos:
        result = extract(video, args.a_cada, args.perfil, dataset)
        print(f"{result['video']}: {result['saved']} frames guardados, {result['skipped']} repetidos pulados, {result['existing']} já no dataset "
              f"(perfil {result['profile']}, escala {result['scale']}) -> {dataset.root / 'pending'}")


if __name__ == "__main__":
    main()
