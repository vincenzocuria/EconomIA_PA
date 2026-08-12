"""Genera scripts/ecogest.ico dal favicon dell'app."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PNG = ROOT / "app" / "static" / "img" / "favicon.png"
ICO = ROOT / "scripts" / "ecogest.ico"


def main() -> None:
    img = Image.open(PNG).convert("RGBA")
    img.save(ICO, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print(ICO)


if __name__ == "__main__":
    main()
