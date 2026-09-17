package com.omninode.omnilauncher.ui;

import java.awt.Image;
import java.awt.image.BufferedImage;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.function.Consumer;

import javax.imageio.ImageIO;

import com.omninode.omnilauncher.util.Async;
import com.omninode.omnilauncher.util.Http;
import com.omninode.omnilauncher.util.Log;
import com.omninode.omnilauncher.util.Os;

/** Loads remote images with a persistent disk cache; result delivered on the EDT. */
public final class ImageLoader {

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
        try {
            String name = Integer.toHexString(url.hashCode()) + "-" +
                    url.substring(url.lastIndexOf('/') + 1).replaceAll("[^A-Za-z0-9._-]", "");
            Path cache = Os.cacheDir().resolve("images").resolve(name);
            byte[] bytes;
            if (Files.exists(cache) && Files.size(cache) > 0) {
                bytes = Files.readAllBytes(cache);
            } else {
                bytes = Http.get(url);
                Files.createDirectories(cache.getParent());
                Files.write(cache, bytes);
            }
            BufferedImage img = ImageIO.read(new java.io.ByteArrayInputStream(bytes));
            return img;
        } catch (Exception e) {
            Log.warn("Image load failed: " + url + " (" + e.getMessage() + ")");
            return null;
        }
    }
}
