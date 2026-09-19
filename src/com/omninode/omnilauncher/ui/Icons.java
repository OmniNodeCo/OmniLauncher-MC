package com.omninode.omnilauncher.ui;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.RenderingHints;
import java.awt.geom.Path2D;
import java.awt.geom.RoundRectangle2D;
import java.awt.image.BufferedImage;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Random;

/** All launcher artwork, drawn procedurally with Java2D — zero binary assets. */
public final class Icons {

    public enum Glyph {
        PLAY, NEWS, GEAR, USER, FOLDER, PLUS, REFRESH, SEARCH, CLOSE, MINIMIZE,
        MAXIMIZE, BACK, EXTERNAL, DOWNLOAD, STOP, CHECK, CHEVRON_DOWN, TRASH, COPY
    }

    /** Bounded LRU so long sessions can't grow the cache without limit. */
    private static final Map<String, Image> CACHE = java.util.Collections.synchronizedMap(
            new LinkedHashMap<>(64, 0.75f, true) {
                @Override protected boolean removeEldestEntry(Map.Entry<String, Image> e) {
                    return size() > 128;
                }
            });

    private Icons() {}

    /** Renders a glyph in the given color/size (cached). */
    public static Image glyph(Glyph g, int size, Color color) {
        String key = g + "@" + size + "@" + Integer.toHexString(color.getRGB());
        Image img = CACHE.get(key);
        if (img != null) return img;
        img = drawGlyph(g, size, color);
        CACHE.put(key, img);
        return img;
    }

    private static Image drawGlyph(Glyph g, int size, Color color) {
        BufferedImage img = new BufferedImage(size, size, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g2 = img.createGraphics();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE);
        float w = Math.max(1.4f, size / 11f);
        g2.setStroke(new BasicStroke(w, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
        g2.setColor(color);
        float pad = size * 0.18f;
        float inner = size - pad * 2;

        switch (g) {
            case PLAY -> {
                Path2D p = new Path2D.Float();
                p.moveTo(pad + inner * 0.12f, pad);
                p.lineTo(pad + inner, pad + inner / 2);
                p.lineTo(pad + inner * 0.12f, pad + inner);
                p.closePath();
                g2.fill(p);
            }
            case NEWS -> {
                g2.draw(new RoundRectangle2D.Float(pad, pad + size * 0.06f, inner, inner * 0.82f, 4, 4));
                float x = pad + inner * 0.16f, y = pad + size * 0.06f + inner * 0.2f;
                g2.drawLine(Math.round(x), Math.round(y), Math.round(x + inner * 0.68f), Math.round(y));
                g2.drawLine(Math.round(x), Math.round(y + size * 0.12f), Math.round(x + inner * 0.68f), Math.round(y + size * 0.12f));
                g2.drawLine(Math.round(x), Math.round(y + size * 0.24f), Math.round(x + inner * 0.42f), Math.round(y + size * 0.24f));
            }
            case GEAR -> {
                double cx = size / 2.0, cy = size / 2.0;
                double rOuter = inner * 0.52, rInner = inner * 0.38, rHole = inner * 0.18;
                for (int i = 0; i < 8; i++) {
                    double a = Math.PI * i / 4.0;
                    g2.drawLine((int) (cx + Math.cos(a) * rInner), (int) (cy + Math.sin(a) * rInner),
                            (int) (cx + Math.cos(a) * rOuter), (int) (cy + Math.sin(a) * rOuter));
                }
                g2.drawOval((int) (cx - rInner), (int) (cy - rInner), (int) (rInner * 2), (int) (rInner * 2));
                g2.drawOval((int) (cx - rHole), (int) (cy - rHole), (int) (rHole * 2), (int) (rHole * 2));
            }
            case USER -> {
                g2.drawOval(Math.round(size * 0.34f), Math.round(size * 0.16f),
                        Math.round(size * 0.32f), Math.round(size * 0.32f));
                Path2D p = new Path2D.Float();
                p.moveTo(pad, size - pad * 0.7f);
                p.quadTo(size / 2.0, size * 0.42f, size - pad, size - pad * 0.7f);
                g2.draw(p);
            }
            case FOLDER -> {
                Path2D p = new Path2D.Float();
                p.moveTo(pad, size - pad);
                p.lineTo(pad, pad + inner * 0.22f);
                p.lineTo(pad + inner * 0.38f, pad + inner * 0.22f);
                p.lineTo(pad + inner * 0.5f, pad + inner * 0.38f);
                p.lineTo(size - pad, pad + inner * 0.38f);
                p.lineTo(size - pad, size - pad);
                p.closePath();
                g2.draw(p);
            }
            case PLUS -> {
                g2.drawLine(Math.round(size / 2f), Math.round(pad), Math.round(size / 2f), Math.round(size - pad));
                g2.drawLine(Math.round(pad), Math.round(size / 2f), Math.round(size - pad), Math.round(size / 2f));
            }
            case REFRESH -> {
                float r = inner * 0.38f, cx = size / 2f, cy = size / 2f;
                g2.drawArc(Math.round(cx - r), Math.round(cy - r), Math.round(r * 2), Math.round(r * 2),
                        90, 270);
                // arrow head at the arc end (top of the circle)
                float ax = cx, ay = cy - r;
                Path2D arrow = new Path2D.Float();
                arrow.moveTo(ax - size * 0.16f, ay - size * 0.06f);
                arrow.lineTo(ax + size * 0.10f, ay - size * 0.10f);
                arrow.lineTo(ax - size * 0.02f, ay + size * 0.12f);
                arrow.closePath();
                g2.fill(arrow);
            }
            case SEARCH -> {
                float r = inner * 0.36f, cx = pad + inner * 0.4f, cy = pad + inner * 0.4f;
                g2.drawOval(Math.round(cx - r), Math.round(cy - r), Math.round(r * 2), Math.round(r * 2));
                g2.drawLine(Math.round(cx + r * 0.72f), Math.round(cy + r * 0.72f),
                        Math.round(pad + inner), Math.round(pad + inner));
            }
            case CLOSE -> {
                g2.drawLine(Math.round(pad + 1), Math.round(pad + 1),
                        Math.round(size - pad - 1), Math.round(size - pad - 1));
                g2.drawLine(Math.round(size - pad - 1), Math.round(pad + 1),
                        Math.round(pad + 1), Math.round(size - pad - 1));
            }
            case MINIMIZE -> g2.drawLine(Math.round(pad), Math.round(size / 2f),
                    Math.round(size - pad), Math.round(size / 2f));
            case MAXIMIZE -> g2.draw(new RoundRectangle2D.Float(pad, pad, inner, inner, 3, 3));
            case BACK -> {
                g2.drawLine(Math.round(pad + inner * 0.7f), Math.round(pad),
                        Math.round(pad), Math.round(size / 2f));
                g2.drawLine(Math.round(pad), Math.round(size / 2f),
                        Math.round(pad + inner * 0.7f), Math.round(size - pad));
                g2.drawLine(Math.round(pad), Math.round(size / 2f),
                        Math.round(size - pad), Math.round(size / 2f));
            }
            case EXTERNAL -> {
                g2.drawLine(Math.round(pad), Math.round(size - pad), Math.round(pad), Math.round(pad + inner * 0.2f));
                g2.drawLine(Math.round(pad), Math.round(pad + inner * 0.2f), Math.round(pad + inner * 0.4f), Math.round(pad + inner * 0.2f));
                g2.drawLine(Math.round(size - pad), Math.round(size - pad), Math.round(pad), Math.round(size - pad));
                g2.drawLine(Math.round(size - pad), Math.round(size - pad), Math.round(size - pad), Math.round(pad + inner * 0.5f));
                g2.drawLine(Math.round(size * 0.55f), Math.round(size * 0.45f), Math.round(size - pad + 1), Math.round(pad));
                g2.drawLine(Math.round(size - pad + 1), Math.round(pad), Math.round(size * 0.62f), Math.round(pad));
                g2.drawLine(Math.round(size - pad + 1), Math.round(pad), Math.round(size - pad + 1), Math.round(size * 0.38f));
            }
            case DOWNLOAD -> {
                g2.drawLine(Math.round(size / 2f), Math.round(pad), Math.round(size / 2f), Math.round(size * 0.58f));
                g2.drawLine(Math.round(size * 0.30f), Math.round(size * 0.42f), Math.round(size / 2f), Math.round(size * 0.60f));
                g2.drawLine(Math.round(size * 0.70f), Math.round(size * 0.42f), Math.round(size / 2f), Math.round(size * 0.60f));
                g2.drawLine(Math.round(pad), Math.round(size - pad), Math.round(size - pad), Math.round(size - pad));
            }
            case STOP -> g2.fill(new RoundRectangle2D.Float(pad + 1, pad + 1, inner - 2, inner - 2, 3, 3));
            case CHECK -> {
                g2.drawLine(Math.round(pad), Math.round(size * 0.54f), Math.round(size * 0.40f), Math.round(size - pad));
                g2.drawLine(Math.round(size * 0.40f), Math.round(size - pad), Math.round(size - pad), Math.round(pad + inner * 0.12f));
            }
            case CHEVRON_DOWN -> {
                g2.drawLine(Math.round(pad), Math.round(size * 0.38f), Math.round(size / 2f), Math.round(size * 0.66f));
                g2.drawLine(Math.round(size / 2f), Math.round(size * 0.66f), Math.round(size - pad), Math.round(size * 0.38f));
            }
            case TRASH -> {
                g2.drawLine(Math.round(size * 0.25f), Math.round(pad + inner * 0.12f),
                        Math.round(size * 0.75f), Math.round(pad + inner * 0.12f));
                g2.drawLine(Math.round(size * 0.42f), Math.round(pad + inner * 0.12f),
                        Math.round(size * 0.42f), Math.round(pad));
                g2.drawLine(Math.round(size * 0.42f), Math.round(pad),
                        Math.round(size * 0.58f), Math.round(pad));
                g2.drawLine(Math.round(size * 0.58f), Math.round(pad),
                        Math.round(size * 0.58f), Math.round(pad + inner * 0.12f));
                Path2D p = new Path2D.Float();
                p.moveTo(size * 0.28f, pad + inner * 0.12f);
                p.lineTo(size * 0.32f, size - pad);
                p.lineTo(size * 0.68f, size - pad);
                p.lineTo(size * 0.72f, pad + inner * 0.12f);
                g2.draw(p);
            }
            case COPY -> {
                g2.draw(new RoundRectangle2D.Float(pad, pad, inner * 0.62f, inner * 0.62f, 4, 4));
                Path2D p = new Path2D.Float();
                p.moveTo(pad + inner * 0.28f, pad + inner * 0.28f);
                p.lineTo(size - pad - inner * 0.08f, pad + inner * 0.28f);
                p.lineTo(size - pad - inner * 0.08f, size - pad - inner * 0.24f);
                p.lineTo(pad + inner * 0.28f, size - pad - inner * 0.24f);
                p.closePath();
                g2.draw(p);
            }
        }
        g2.dispose();
        return img;
    }

    /* ------------------------------------------------------------- logo */

    /** Isometric grass block — the launcher's brand mark. */
    public static Image grassBlock(int size) {
        String key = "block@" + size;
        Image img = CACHE.get(key);
        if (img != null) return img;

        BufferedImage buf = new BufferedImage(size, size, BufferedImage.TYPE_INT_ARGB);
        Image imgRef = buf;
        Graphics2D g2 = buf.createGraphics();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        float w = size, h = size;
        float cx = w / 2f;

        // faces
        Path2D top = new Path2D.Float();
        top.moveTo(cx, h * 0.06f);
        top.lineTo(w * 0.94f, h * 0.30f);
        top.lineTo(cx, h * 0.54f);
        top.lineTo(w * 0.06f, h * 0.30f);
        top.closePath();

        Path2D left = new Path2D.Float();
        left.moveTo(w * 0.06f, h * 0.30f);
        left.lineTo(cx, h * 0.54f);
        left.lineTo(cx, h * 0.96f);
        left.lineTo(w * 0.06f, h * 0.72f);
        left.closePath();

        Path2D right = new Path2D.Float();
        right.moveTo(cx, h * 0.54f);
        right.lineTo(w * 0.94f, h * 0.30f);
        right.lineTo(w * 0.94f, h * 0.72f);
        right.lineTo(cx, h * 0.96f);
        right.closePath();

        // soft drop shadow
        g2.setColor(Theme.withAlpha(new Color(0x000000), 50));
        g2.fill(new java.awt.geom.Ellipse2D.Float(w * 0.14f, h * 0.78f, w * 0.72f, h * 0.24f));

        g2.setColor(new Color(0x7cb342));
        g2.fill(top);
        g2.setColor(new Color(0x7a5230));
        g2.fill(left);
        g2.setColor(new Color(0x5d3f26));
        g2.fill(right);
        // facet shading for depth
        g2.setColor(Theme.withAlpha(new Color(0xffffff), 26));
        g2.fill(top);
        g2.setColor(Theme.withAlpha(new Color(0x000000), 22));
        g2.fill(right);

        // pixel noise
        Random rnd = new Random(42);
        float step = size / 26f;
        for (int i = 0; i < 90; i++) {
            float u = rnd.nextFloat(), v = rnd.nextFloat();
            // pick a face
            int face = rnd.nextInt(3);
            Color c;
            Path2D facePath;
            float jx, jy;
            if (face == 0) {
                facePath = top;
                c = rnd.nextBoolean() ? new Color(0x7fbf4a) : new Color(0x639937);
            } else if (face == 1) {
                facePath = left;
                c = rnd.nextBoolean() ? new Color(0x7d5433) : new Color(0x5f3d24);
            } else {
                facePath = right;
                c = rnd.nextBoolean() ? new Color(0x67452a) : new Color(0x4e301c);
            }
            if (!facePath.contains(u * w, v * h)) continue;
            jx = u * w; jy = v * h;
            g2.setColor(c);
            g2.fill(new java.awt.geom.Rectangle2D.Float(jx, jy, step, step));
        }

        // grass overhang strips hugging the top edges of the side faces
        g2.setColor(new Color(0x68a13a));
        float oh = Math.max(2f, step * 0.8f);
        Path2D ohL = new Path2D.Float();
        ohL.moveTo(w * 0.06f, h * 0.30f);
        ohL.lineTo(cx, h * 0.54f);
        ohL.lineTo(cx, h * 0.54f + oh);
        ohL.lineTo(w * 0.06f, h * 0.30f + oh);
        ohL.closePath();
        g2.fill(ohL);
        Path2D ohR = new Path2D.Float();
        ohR.moveTo(cx, h * 0.54f);
        ohR.lineTo(w * 0.94f, h * 0.30f);
        ohR.lineTo(w * 0.94f, h * 0.30f + oh);
        ohR.lineTo(cx, h * 0.54f + oh);
        ohR.closePath();
        g2.fill(ohR);

        // subtle outline
        g2.setStroke(new BasicStroke(Math.max(1f, size / 90f)));
        g2.setColor(Theme.withAlpha(new Color(0x000000), 60));
        g2.draw(top);
        g2.draw(left);
        g2.draw(right);

        g2.dispose();
        CACHE.put(key, imgRef);
        return imgRef;
    }

    /**
     * The launcher's brand mark: the grass block on a rounded badge with a
     * dark gradient, subtle rim light and a soft shadow. Used for the window
     * icon, the nav rail, the title bar and every exported icon file.
     */
    public static Image brandBadge(int size) {
        String key = "badge@" + size;
        Image img = CACHE.get(key);
        if (img != null) return img;

        BufferedImage buf = new BufferedImage(size, size, BufferedImage.TYPE_INT_ARGB);
        Image imgRef = buf;
        Graphics2D g2 = buf.createGraphics();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE);

        float pad = size * 0.05f;
        var badge = new java.awt.geom.RoundRectangle2D.Float(
                pad, pad, size - pad * 2, size - pad * 2, size * 0.24f, size * 0.24f);

        // vertical gradient face
        var face = new java.awt.GradientPaint(0, pad, new Color(0x2e3540), 0, size - pad, new Color(0x151920));
        g2.setPaint(face);
        g2.fill(badge);

        // green glow behind the block
        g2.setColor(Theme.withAlpha(new Color(0x7cb342), 36));
        g2.fill(new java.awt.geom.Ellipse2D.Float(size * 0.16f, size * 0.22f, size * 0.68f, size * 0.62f));

        // the block, slightly inset
        float block = size * 0.72f;
        float off = (size - block) / 2f;
        Image b = grassBlock(Math.max(24, Math.round(block)));
        g2.drawImage(b, Math.round(off), Math.round(off), Math.round(block), Math.round(block), null);

        // rim light + hairline border
        g2.setStroke(new BasicStroke(Math.max(1f, size / 64f)));
        g2.setColor(Theme.withAlpha(new Color(0xffffff), 36));
        g2.draw(badge);
        g2.setColor(Theme.withAlpha(new Color(0x000000), 70));
        var inner = new java.awt.geom.RoundRectangle2D.Float(
                pad + 1, pad + 1, size - pad * 2 - 2, size - pad * 2 - 2, size * 0.24f, size * 0.24f);
        g2.draw(inner);

        g2.dispose();
        CACHE.put(key, imgRef);
        return imgRef;
    }

    /* ----------------------------------------------------------- avatar */

    /** Classic-style pixel face; deterministic per seed so offline names look distinct. */
    public static Image avatarFace(String seed, int size) {
        String key = "face@" + seed + "@" + size;
        Image img = CACHE.get(key);
        if (img != null) return img;

        int px = 8;
        BufferedImage buf = new BufferedImage(px, px, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g2 = buf.createGraphics();
        Random rnd = new Random(seed == null ? 0 : seed.hashCode());

        Color skin = new Color(0xb5876b);
        Color hair = new Color(0x3b2a1d);
        Color eyeW = new Color(0xffffff);
        Color eyeI = new Color(rnd.nextInt(0x5050a0) + 0x404060);
        Color mouth = new Color(0x6f4a35);

        for (int y = 0; y < px; y++) {
            for (int x = 0; x < px; x++) {
                Color c = skin;
                if (y == 0 || (y == 1 && rnd.nextBoolean()) || x == 0 || x == px - 1) {
                    if (y <= 1 || rnd.nextInt(10) < 8) c = hair;
                }
                if (y == 3 && (x == 2 || x == 5)) c = eyeW;
                if (y == 3 && (x == 3 || x == 4)) {
                    if ((x == 3 && seed != null) || x == 4) c = eyeI;
                }
                if (y == 5 && x >= 3 && x <= 4) c = mouth;
                if (y == 6 && x >= 2 && x <= 5 && rnd.nextBoolean()) c = skin;
                g2.setColor(c);
                g2.fillRect(x, y, 1, 1);
            }
        }
        g2.dispose();

        Image scaled = buf.getScaledInstance(size, size, java.awt.Image.SCALE_FAST);
        CACHE.put(key, scaled);
        return scaled;
    }

    /** Soft gradient placeholder used for news images that failed to load. */
    public static Image newsPlaceholder(int w, int h, String seed) {
        String key = "ph@" + w + "x" + h + "@" + seed;
        Image img = CACHE.get(key);
        if (img != null) return img;
        BufferedImage buf = new BufferedImage(w, h, BufferedImage.TYPE_INT_RGB);
        Graphics2D g2 = buf.createGraphics();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        Random rnd = new Random(seed == null ? 7 : seed.hashCode());
        Color a = new Color(0x2b3a2a);
        Color b = new Color(0x22303f);
        var gp = new java.awt.GradientPaint(0, 0, a, w, h, b);
        g2.setPaint(gp);
        g2.fillRect(0, 0, w, h);
        g2.setComposite(java.awt.AlphaComposite.SrcOver.derive(0.35f));
        for (int i = 0; i < 6; i++) {
            int bs = 24 + rnd.nextInt(40);
            g2.setColor(rnd.nextBoolean() ? Theme.GREEN : new Color(0x4daafc));
            g2.fill(new RoundRectangle2D.Float(rnd.nextInt(Math.max(1, w - bs)), rnd.nextInt(Math.max(1, h - bs)), bs, bs, 8, 8));
        }
        g2.dispose();
        CACHE.put(key, buf);
        return buf;
    }
}
