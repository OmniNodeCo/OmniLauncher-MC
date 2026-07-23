"""Convert SVG assets to BMP and ICO for the installer."""

import subprocess
import os
from PIL import Image


INKSCAPE = r"C:\Program Files\Inkscape\bin\inkscape.exe"


def svg_to_png(svg_file: str, png_file: str, width: int, height: int) -> None:
    subprocess.run(
        [
            INKSCAPE,
            svg_file,
            "--export-type=png",
            f"--export-filename={png_file}",
            f"--export-width={width}",
            f"--export-height={height}",
        ],
        check=True,
    )
    print(f"Converted {svg_file} to {png_file}")


def convert_assets() -> None:
    os.makedirs("assets", exist_ok=True)

    svg_to_png("icon.svg", "icon-256.png", 256, 256)
    svg_to_png("installer-banner.svg", "installer-banner.png", 164, 314)
    svg_to_png("installer-logo.svg", "installer-logo.png", 55, 55)

    Image.open("installer-banner.png").save("assets/installer-banner.bmp")
    print("Banner converted to BMP")

    Image.open("installer-logo.png").save("assets/installer-logo.bmp")
    print("Logo converted to BMP")

    sizes = [16, 32, 48, 64, 128, 256]
    imgs = []
    for size in sizes:
        img = Image.open("icon-256.png").convert("RGBA").resize(
            (size, size), Image.LANCZOS
        )
        imgs.append(img)

    imgs[0].save(
        "assets/icon.ico",
        format="ICO",
        append_images=imgs[1:],
        sizes=[(s, s) for s in sizes],
    )
    print("Icon converted to ICO")
    print("All assets converted successfully")


if __name__ == "__main__":
    convert_assets()