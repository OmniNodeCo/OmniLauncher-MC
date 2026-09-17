package com.omninode.omnilauncher.api;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.omninode.omnilauncher.util.Async;
import com.omninode.omnilauncher.util.Http;
import com.omninode.omnilauncher.util.Json;
import com.omninode.omnilauncher.util.Log;
import com.omninode.omnilauncher.util.Os;

/**
 * Official launcher news feed (launchercontent.mojang.com/v2/news.json) —
 * the same patch notes / deep dives the stock Minecraft launcher shows.
 */
public class NewsService {

    public static final String NEWS_URL = "https://launchercontent.mojang.com/v2/news.json";
    public static final String CONTENT_BASE = "https://launchercontent.mojang.com";

    public record Item(String title, String date, String category, String shortText,
                       String longText, String imageUrl) {
        public String formattedDate() {
            try {
                var d = java.time.LocalDate.parse(date.substring(0, 10));
                return d.format(java.time.format.DateTimeFormatter.ofPattern("MMMM d, yyyy")
                        .withLocale(java.util.Locale.ENGLISH));
            } catch (Exception e) {
                return date;
            }
        }
    }

    private static volatile List<Item> items = List.of();
    private static volatile long loadedAt;
    private static volatile boolean staleCache;
    private static final long TTL_MS = 30 * 60_000;

    /** True when the displayed news come from the on-disk cache after a failed refresh. */
    public static boolean isStaleCache() { return staleCache; }

    public static void loadAsync(Runnable onSuccess, java.util.function.Consumer<String> onError) {
        long age = System.currentTimeMillis() - loadedAt;
        if (!items.isEmpty() && age < TTL_MS) {
            if (onSuccess != null) Async.ui(onSuccess);
            return;
        }
        Async.io(() -> {
            try {
                loadBlocking();
                if (onSuccess != null) Async.ui(onSuccess);
            } catch (Exception e) {
                Log.warn("News load failed: " + e.getMessage());
                if (items.isEmpty() && onError != null) Async.ui(() -> onError.accept(e.getMessage()));
            }
        });
    }

    public static void loadBlocking() throws Exception {
        Path cache = Os.cacheDir().resolve("news.json");
        try {
            byte[] body = Http.get(NEWS_URL);
            Files.write(cache, body);
            staleCache = false;
        } catch (Exception e) {
            if (!Files.exists(cache)) throw e;
            staleCache = true;
            Log.warn("Using cached news: " + e.getMessage());
        }
        parse(Files.readString(cache, StandardCharsets.UTF_8));
        loadedAt = System.currentTimeMillis();
    }

    /** Ignores the TTL and refetches (used by the UI refresh/retry buttons). */
    public static void forceReload(Runnable onSuccess, java.util.function.Consumer<String> onError) {
        loadedAt = 0;
        loadAsync(onSuccess, onError);
    }

    public static void parse(String json) {
        List<Object> arr = Json.parseArray(json);
        List<Item> out = new ArrayList<>();
        for (Object o : arr) {
            Map<String, Object> m = Json.asMap(o);
            if (m == null) continue;
            out.add(new Item(
                    Json.str(m, "title", "Untitled"),
                    Json.str(m, "date", ""),
                    Json.str(m, "category", "news"),
                    Json.str(m, "shortText", ""),
                    Json.str(m, "longText", ""),
                    extractImageUrl(m)));
        }
        items = List.copyOf(out);
    }

    private static String extractImageUrl(Map<String, Object> m) {
        Object img = m.get("image");
        String url = null;
        if (img instanceof Map) url = Json.str(Json.asMap(img), "url", null);
        else if (img instanceof String s) url = s;
        if (url == null || url.isBlank()) return null;
        if (url.startsWith("http")) return url;
        return CONTENT_BASE + (url.startsWith("/") ? url : "/" + url);
    }

    public static List<Item> items() { return items; }
}
