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
 * packages: multi-size PNGs, a Windows .ico (PNG-compressed entries) and a
 * macOS .icns — all rendered from the procedural grass block, no binaries
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
        return written;
    }

    private static byte[] renderPng(int size) throws IOException {
        java.awt.Image src = Icons.grassBlock(size);
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
