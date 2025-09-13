# 🚗 Tesla Dash Videos

Un script Python qui assemble automatiquement les 4 vidéos issues de la dashcam Tesla (`front`, `back`, `left_repeater`, `right_repeater`) en une seule vidéo mosaïque 2×2.

---

## ⚙️ Prérequis

- **Python** ≥ 3.9  
- **FFmpeg** (incluant `ffmpeg` et `ffprobe`) doit être installé sur la machine.  

### Installation de FFmpeg
- **macOS** (Homebrew)
brew install ffmpeg

sudo apt update && sudo apt install ffmpeg

sudo dnf install ffmpeg

scoop install ffmpeg

git clone https://github.com/<ton_user>/Tesla_dash_videos.git
cd Tesla_dash_videos
