"""Convert SVG assets to BMP and ICO for the installer."""

import cairosvg
from PIL import Image
import os


def convert_assets() -> None:
    os.makedirs("assets", exist_ok=True)

    # SVG to PNG
    cairosvg.svg2png(url="icon.svg", write_to="icon-256.png",
                     output_width=256, output_height=256)
    print("Icon SVG to PNG done")

    cairosvg.svg2png(url="installer-banner.svg", write_to="installer-banner.png",
                     output_width=164, output_height=314)
    print("Banner SVG to PNG done")

    cairosvg.svg2png(url="installer-logo.svg", write_to="installer-logo.png",
                     output_width=55, output_height=55)
    print("Logo SVG to PNG done")

    # Banner PNG to BMP
    Image.open("installer-banner.png").save("assets/installer-banner.bmp")
    print("Banner converted to BMP")

    # Logo PNG to BMP
    Image.open("installer-logo.png").save("assets/installer-logo.bmp")
    print("Logo converted to BMP")

    # Icon PNG to ICO
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