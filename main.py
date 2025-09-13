#!/usr/bin/env python3
import subprocess, sys, json, shlex
from pathlib import Path

# Binaries (Homebrew sur Mac: /opt/homebrew/bin/* si besoin)
FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"

# Motifs des fichiers Tesla
PATTERNS = {
    "front": "*front.mp4",
    "back": "*back.mp4",
    "left": "*left_repeater.mp4",
    "right": "*right_repeater.mp4",
}

# Paramètres tuiles/sortie
TILE_W, TILE_H = 960, 540           # 16:9
TARGET_FPS = 30
CRF = 20
PRESET = "medium"

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = SCRIPT_DIR / "mosaic.mp4"

def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed:\n{' '.join(shlex.quote(c) for c in cmd)}\n{p.stderr}")
    return p.stdout

def ffprobe_duration(path: Path) -> float:
    out = run([FFPROBE_BIN, "-v", "error", "-select_streams", "v:0",
               "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(out)["format"]["duration"])

def find_inputs(folder: Path) -> dict:
    inputs = {}
    for key, pattern in PATTERNS.items():
        matches = sorted(folder.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"Aucun fichier trouvé pour '{key}' ({pattern})")
        inputs[key] = max(matches, key=lambda p: p.stat().st_mtime)
    return inputs

def build_ffmpeg_cmd(inputs: dict, out: Path):
    order = ["front", "back", "left", "right"]
    files = [inputs[k] for k in order]
    t = min(ffprobe_duration(f) for f in files)

    # COVER: on remplit la tuile en rognant (pas de bandes)
    # 1) scale avec force_original_aspect_ratio=increase (agrandit jusqu'à couvrir)
    # 2) crop centré à la taille exacte de la tuile
    # 3) fps fixe + SAR=1
    vf_parts = []
    for i in range(4):
        vf_parts.append(
            f"[{i}:v]"
            f"scale={TILE_W}:{TILE_H}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={TILE_W}:{TILE_H}:(iw-{TILE_W})/2:(ih-{TILE_H})/2,"
            f"fps={TARGET_FPS},setsar=1[v{i}]"
        )
    vf_scale = ";".join(vf_parts)

    # Grille fixe 2x2 → 1920x1080
    layout = f"0_0|{TILE_W}_0|0_{TILE_H}|{TILE_W}_{TILE_H}"
    # Post-empilage: format sûr + dimensions paires (sécurité chroma)
    vf_stack = (
        f"{vf_scale};"
        f"[v0][v1][v2][v3]xstack=inputs=4:layout={layout}[vtmp];"
        f"[vtmp]format=yuv420p,setsar=1,pad=ceil(iw/2)*2:ceil(ih/2)*2[vout]"
    )

    cmd = [FFMPEG_BIN, "-y"]
    for f in files:
        cmd += ["-fflags", "+genpts", "-i", str(f)]
    cmd += ["-t", f"{t:.3f}",
            "-filter_complex", vf_stack, "-map", "[vout]",
            "-an",
            "-r", str(TARGET_FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", PRESET, "-crf", str(CRF),
            "-movflags", "+faststart",
            str(out)]
    return cmd

def main():
    try:
        inputs = find_inputs(SCRIPT_DIR)
        cmd = build_ffmpeg_cmd(inputs, OUTPUT_FILE)
        print("Commande FFmpeg :", " ".join(shlex.quote(c) for c in cmd))
        subprocess.check_call(cmd)
        print(f"Vidéo générée : {OUTPUT_FILE}")
    except FileNotFoundError as e:
        print("Échec FFmpeg: binaire introuvable (installe: brew install ffmpeg)\nDétails:", e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Échec FFmpeg: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()