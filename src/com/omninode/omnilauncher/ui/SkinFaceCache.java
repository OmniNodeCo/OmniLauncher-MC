package com.omninode.omnilauncher.ui;

import java.awt.Image;
import java.awt.image.BufferedImage;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

import com.omninode.omnilauncher.util.Async;

/** Fetches player skin textures and crops the 8×8 head for avatars. */
public final class SkinFaceCache {

    private static final Map<String, Image> FACES = new ConcurrentHashMap<>();
    private static final Set<String> INFLIGHT = ConcurrentHashMap.newKeySet();

    private SkinFaceCache() {}

    public static Image faceFor(String textureUrl) {
        return FACES.get(textureUrl);
    }

    /** Kicks off an async load; calls back on the EDT when done (once). */
    public static void request(String textureUrl, Runnable onDone) {
        if (!INFLIGHT.add(textureUrl)) return;
        Async.io(() -> {
            Image face = null;
            try {
                Image skin = ImageLoader.loadBlocking(textureUrl);
                if (skin instanceof BufferedImage img && img.getWidth() == img.getHeight()) {
                    int u = img.getWidth() / 64;
                    if (u > 0) {
                        var head = new BufferedImage(8 * u, 8 * u, BufferedImage.TYPE_INT_ARGB);
                        var g2 = head.createGraphics();
                        // front face of the head: (8,8)-(16,16) in the 64x64 layout
                        g2.drawImage(img, 0, 0, 8 * u, 8 * u, 8 * u, 8 * u, 16 * u, 16 * u, null);
                        g2.dispose();
                        face = head.getScaledInstance(36, 36, Image.SCALE_SMOOTH);
                    }
                }
            } catch (Throwable ignored) {}
            if (face != null) FACES.put(textureUrl, face);
            Async.ui(() -> {
                INFLIGHT.remove(textureUrl);
                if (onDone != null) onDone.run();
            });
        });
    }
}
