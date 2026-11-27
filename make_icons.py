"""
Makes the site's icons from the club crest:
- favicon.ico (16, 32, 48 px)  for browser tabs, bookmarks and Google results
- apple-touch-icon.png (180)   for iPhone home screens
- icon-192.png, icon-512.png   for Android home screens
- share-card.png (1200 x 630)  for link previews on WhatsApp, X and others

    python make_icons.py path/to/your/crest.png
"""

import sys
from pathlib import Path

from PIL import Image, ImageOps

# Where the icons go: inside the website app's static files
OUT = Path("website/static/website/img/icons")


def place(crest, width, height, padding, background):
    """The crest centred on a canvas of the given size, with some space around it."""
    canvas = Image.new("RGBA", (width, height), background)
    copy = crest.copy()
    # Shrink to fit inside the padding, keeping the crest's shape
    copy.thumbnail((int(width * (1 - 2 * padding)), int(height * (1 - 2 * padding))), Image.LANCZOS)
    canvas.alpha_composite(copy, ((width - copy.width) // 2, (height - copy.height) // 2))
    return canvas


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python make_icons.py path/to/crest.png")

    # RGBA = colour plus transparency, so every step works the same way
    crest = ImageOps.exif_transpose(Image.open(sys.argv[1])).convert("RGBA")

    # Fill the empty space with the colour of the crest's own corner,
    # so the edges blend in instead of showing a box
    background = crest.getpixel((0, 0))

    OUT.mkdir(parents=True, exist_ok=True)

    # Tiny tab icon: as little padding as possible, so the crest stays readable
    place(crest, 256, 256, 0.02, background).save(
        OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)]
    )

    # Home-screen icons: a bit more space, because phones round the corners
    place(crest, 180, 180, 0.08, background).save(OUT / "apple-touch-icon.png")
    place(crest, 192, 192, 0.08, background).save(OUT / "icon-192.png")
    place(crest, 512, 512, 0.08, background).save(OUT / "icon-512.png")

    # Wide card shown in link previews
    place(crest, 1200, 630, 0.08, background).save(OUT / "share-card.png")

    print(f"Icons saved in {OUT}")


if __name__ == "__main__":
    main()