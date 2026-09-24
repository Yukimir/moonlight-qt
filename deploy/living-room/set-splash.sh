#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/3840x2160-image.png" >&2
  exit 2
fi

image=$(realpath -- "$1")
python3 - "$image" <<'PY'
from PIL import Image
import sys
with Image.open(sys.argv[1]) as image:
    if image.size != (3840, 2160):
        raise SystemExit("Splash image must be exactly 3840x2160 pixels")
    if image.format != "PNG":
        raise SystemExit("Splash image must be PNG")
PY

install -Dm644 "$image" "$HOME/.local/share/moonlight-vplus/splash.png"
sudo install -Dm644 "$image" /usr/share/plymouth/themes/moonlight/splash.png
sudo update-initramfs -u -k all
echo "Splash updated. Boot image will change on the next reboot."
