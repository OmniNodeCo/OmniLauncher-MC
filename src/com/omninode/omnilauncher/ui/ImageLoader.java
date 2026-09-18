package com.omninode.omnilauncher.ui;

import java.awt.Image;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Consumer;

import javax.imageio.ImageIO;

import com.omninode.omnilauncher.util.Async;
import com.omninode.omnilauncher.util.Http;
import com.omninode.omnilauncher.util.Log;
import com.omninode.omnilauncher.util.Os;

/**
 * Loads remote images (news art, player skins) with a persistent disk cache,
 * a small in-memory decoded cache and a failure backoff; results are
 * delivered on the EDT.
 */
public final class ImageLoader {

    /** Decoded images kept in memory so panel rebuilds don't re-decode. */
    private static final int MEMORY_ENTRIES = 32;
    private static final Map<String, Image> MEMORY = new LinkedHashMap<>(16, 0.75f, true) {
        @Override protected boolean removeEldestEntry(Map.Entry<String, Image> e) {
            return size() > MEMORY_ENTRIES;
        }
    };

    /** Failed URLs are not retried until this backoff has elapsed. */
    private static final long RETRY_AFTER_MS = 5 * 60_000;
    private static final Map<String, Long> FAILED_AT = new ConcurrentHashMap<>();

    private ImageLoader() {}

    public static void load(String url, Consumer<Image> onLoaded) {
        if (url == null || url.isBlank()) {
            onLoaded.accept(null);
            return;
        }
        Async.io(() -> {
            Image img = loadBlocking(url);
            Async.ui(() -> onLoaded.accept(img));
        });
    }

    public static Image loadBlocking(String url) {
        if (url == null || url.isBlank()) return null;
        synchronized (MEMORY) {
            Image cached = MEMORY.get(url);
            if (cached != null) return cached;
        }
        Long failedAt = FAILED_AT.get(url);
        if (failedAt != null && System.currentTimeMillis() - failedAt < RETRY_AFTER_MS) return null;
        try {
            Path cache = cacheFileFor(url);
            byte[] bytes;
            if (Files.exists(cache) && Files.size(cache) > 0) {
                bytes = Files.readAllBytes(cache);
            } else {
                bytes = Http.get(url);
                Files.createDirectories(cache.getParent());
                Path part = cache.resolveSibling(cache.getFileName() + ".part");
                Files.write(part, bytes);
                try {
                    Files.move(part, cache, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                } catch (java.io.IOException moveFailed) {
                    Files.write(cache, bytes); // fall back to direct write
                }
            }
            BufferedImage img = ImageIO.read(new ByteArrayInputStream(bytes));
            if (img == null) throw new java.io.IOException("unsupported image format");
            synchronized (MEMORY) { MEMORY.put(url, img); }
            FAILED_AT.remove(url);
            return img;
        } catch (Exception e) {
            FAILED_AT.put(url, System.currentTimeMillis());
            Log.warn("Image load failed: " + url + " (" + e.getMessage() + ")");
            return null;
        }
    }

    /** Stable, filesystem-safe cache path for a URL (also used by tests). */
    static Path cacheFileFor(String url) {
        String name = Integer.toHexString(url.hashCode()) + "-"
                + url.substring(url.lastIndexOf('/') + 1).replaceAll("[^A-Za-z0-9._-]", "");
        return Os.cacheDir().resolve("images").resolve(name);
    }

    /** Test hook: drop all in-memory and failure state. */
    static void resetInMemoryState() {
        synchronized (MEMORY) { MEMORY.clear(); }
        FAILED_AT.clear();
    }
}
