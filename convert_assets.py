"""Convert SVG assets to BMP and ICO for the installer."""

from PIL import Image
import os


def convert_assets() -> None:
    os.makedirs("assets", exist_ok=True)

    # Banner
    Image.open("installer-banner.png").save("assets/installer-banner.bmp")
    print("Banner converted to BMP")

    # Logo
    Image.open("installer-logo.png").save("assets/installer-logo.bmp")
    print("Logo converted to BMP")

    # Icon - multiple sizes
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