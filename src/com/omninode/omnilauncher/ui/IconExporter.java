package com.omninode.omnilauncher.ui;

import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

import javax.imageio.ImageIO;

/**
 * Writes the launcher artwork as real icon files used by the native
 * packages: multi-size PNGs, a Windows .ico (PNG-compressed entries), a
 * macOS .icns and a resolution-independent SVG — all rendered from the
 * procedural brand badge, no binaries
 * in the repo.
 */
public final class IconExporter {

    private static final int[] PNG_SIZES = {16, 24, 32, 48, 64, 128, 256, 512};

    private IconExporter() {}

    /** Writes icon-<size>.png, OmniLauncher.ico and OmniLauncher.icns into {@code dir}. */
    public static Map<String, Path> exportAll(Path dir) throws IOException {
        Files.createDirectories(dir);
        var written = new java.util.LinkedHashMap<String, Path>();

        var pngs = new java.util.LinkedHashMap<Integer, byte[]>();
        for (int size : PNG_SIZES) {
            byte[] png = renderPng(size);
            pngs.put(size, png);
            Path p = dir.resolve("icon-" + size + ".png");
            Files.write(p, png);
            written.put("png-" + size, p);
        }

        Path ico = dir.resolve("OmniLauncher.ico");
        Files.write(ico, buildIco(pngs));
        written.put("ico", ico);

        Path icns = dir.resolve("OmniLauncher.icns");
        Files.write(icns, buildIcns(pngs));
        written.put("icns", icns);

        Path svg = dir.resolve("OmniLauncher.svg");
        Files.writeString(svg, brandSvg());
        written.put("svg", svg);
        return written;
    }

    private static byte[] renderPng(int size) throws IOException {
        java.awt.Image src = Icons.brandBadge(size);
        BufferedImage img = new BufferedImage(size, size, BufferedImage.TYPE_INT_ARGB);
        var g = img.createGraphics();
        g.drawImage(src, 0, 0, size, size, null);
        g.dispose();
        var out = new ByteArrayOutputStream();
        if (!ImageIO.write(img, "png", out))
            throw new IOException("PNG encoding failed for size " + size);
        return out.toByteArray();
    }

    /** ICO container with PNG-compressed entries (valid on Windows Vista+). */
    /**
     * Resolution-independent vector version of the brand badge, hand-authored
     * to mirror the procedural renderer (rounded badge, green glow, isometric
     * grass block). Used for README/wiki/web branding.
     */
    public static String brandSvg() {
        return """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="face" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#2e3540"/>
      <stop offset="1" stop-color="#151920"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.55" r="0.6">
      <stop offset="0" stop-color="#7cb342" stop-opacity="0.30"/>
      <stop offset="1" stop-color="#7cb342" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect x="26" y="26" width="460" height="460" rx="110" fill="url(#face)"/>
  <rect x="26" y="26" width="460" height="460" rx="110" fill="none" stroke="#ffffff" stroke-opacity="0.14" stroke-width="4"/>
  <rect x="30" y="30" width="452" height="452" rx="106" fill="none" stroke="#000000" stroke-opacity="0.28" stroke-width="3"/>
  <ellipse cx="256" cy="295" rx="175" ry="160" fill="url(#glow)"/>
  <g>
    <ellipse cx="256" cy="415" rx="150" ry="34" fill="#000000" opacity="0.20"/>
    <polygon points="256,64 448,169 256,274 64,169" fill="#7cb342"/>
    <polygon points="256,274 64,169 64,364 256,469" fill="#7a5230"/>
    <polygon points="256,274 448,169 448,364 256,469" fill="#5d3f26"/>
    <polygon points="256,64 448,169 256,274 64,169" fill="#ffffff" opacity="0.10"/>
    <polygon points="256,274 448,169 448,364 256,469" fill="#000000" opacity="0.09"/>
    <polygon points="64,169 256,274 256,290 64,185" fill="#68a13a"/>
    <polygon points="256,274 448,169 448,185 256,290" fill="#68a13a"/>
    <g fill="#8ec954">
      <rect x="150" y="130" width="22" height="22" transform="skewY(26)" opacity="0.0"/>
    </g>
    <g fill="#8ec954" opacity="0.85">
      <path d="M176 140 l24 13 0 12 -24 -13 z"/>
      <path d="M300 172 l26 14 0 12 -26 -14 z"/>
      <path d="M236 190 l20 11 0 11 -20 -11 z"/>
    </g>
    <g fill="#5f3d24" opacity="0.7">
      <path d="M150 260 l26 14 0 24 -26 -14 z"/>
      <path d="M300 320 l22 12 0 22 -22 -12 z"/>
      <path d="M215 320 l18 10 0 20 -18 -10 z"/>
      <path d="M355 255 l20 11 0 20 -20 -11 z"/>
    </g>
  </g>
</svg>
""";
    }

    private static byte[] buildIco(Map<Integer, byte[]> pngs) {
        int[] sizes = {16, 24, 32, 48, 64, 128, 256};
        var buf = new ByteArrayOutputStream();
        buf.write(0); buf.write(0);              // reserved
        buf.write(1); buf.write(0);              // type: icon
        buf.write(sizes.length); buf.write(0);   // entry count
        int offset = 6 + 16 * sizes.length;
        for (int size : sizes) {
            int w = size >= 256 ? 0 : size;
            buf.write(w); buf.write(w);          // width, height (0 = 256)
            buf.write(0); buf.write(0);          // palette, reserved
            buf.write(1); buf.write(0);          // planes
            buf.write(32); buf.write(0);         // bpp
            int len = pngs.get(size).length;
            for (int i = 0; i < 4; i++) buf.write((len >> (8 * i)) & 0xFF);
            for (int i = 0; i < 4; i++) buf.write((offset >> (8 * i)) & 0xFF);
            offset += len;
        }
        for (int size : sizes) buf.write(pngs.get(size), 0, pngs.get(size).length);
        return buf.toByteArray();
    }

    /** Minimal ICNS writer using PNG-based chunk types. */
    private static byte[] buildIcns(Map<Integer, byte[]> pngs) {
        record Chunk(String type, int size) {}
        var chunks = new Object[] {
                new Chunk("icp4", 16),   // 16×16
                new Chunk("icp5", 32),   // 32×32
                new Chunk("ic07", 128),  // 128×128
                new Chunk("ic08", 256),  // 256×256
                new Chunk("ic09", 512),  // 512×512
        };
        int total = 8;
        for (Object o : chunks) {
            Chunk c = (Chunk) o;
            total += 8 + pngs.get(c.size()).length;
        }
        ByteBuffer out = ByteBuffer.allocate(total);
        out.put((byte) 'i').put((byte) 'c').put((byte) 'n').put((byte) 's');
        out.putInt(total);
        for (Object o : chunks) {
            Chunk c = (Chunk) o;
            out.put(c.type().getBytes(java.nio.charset.StandardCharsets.US_ASCII));
            out.putInt(8 + pngs.get(c.size()).length);
            out.put(pngs.get(c.size()));
        }
        return out.array();
    }
}
