package com.omninode.omnilauncher.api;

import java.io.IOException;
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
    public static final String NEWS_FALLBACK_URL = "https://launchercontent.mojang.com/news.json";
    public static final String CONTENT_BASE = "https://launchercontent.mojang.com";

    public record Item(String title, String date, String category, String shortText,
                       String longText, String imageUrl, String detailImageUrl,
                       String readMoreUrl) {
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
        byte[] body = null;
        Exception failure = null;
        try {
            body = Http.get(NEWS_URL);
        } catch (Exception e) {
            failure = e;
            try { body = Http.get(NEWS_FALLBACK_URL); } catch (Exception e2) { failure.addSuppressed(e2); }
        }
        if (body != null && body.length > 0) {
            parse(new String(body, StandardCharsets.UTF_8));
            loadedAt = System.currentTimeMillis();
            staleCache = false;
            try {
                Files.createDirectories(cache.getParent());
                Files.write(cache, body);
            } catch (IOException io) {
                Log.warn("News cache write failed: " + io.getMessage());
            }
            return;
        }
        if (Files.exists(cache)) {
            staleCache = true;
            parse(Files.readString(cache, StandardCharsets.UTF_8));
            loadedAt = System.currentTimeMillis();
            Log.warn("News served from cache: " + failure);
            return;
        }
        throw failure != null ? failure : new IOException("News feed unavailable");
    }

    /** Ignores the TTL and refetches (used by the UI refresh/retry buttons). */
    public static void forceReload(Runnable onSuccess, java.util.function.Consumer<String> onError) {
        loadedAt = 0;
        loadAsync(onSuccess, onError);
    }

    /**
     * Parses the Minecraft news API payload. The v2 endpoint returns a bare
     * array; the legacy endpoint wraps it as {"entries":[...]}. Each entry
     * carries an HTML {@code text} body (plus optional {@code body}), from
     * which the short card blurb is derived.
     */
    public static void parse(String json) {
        List<Object> arr;
        try {
            arr = Json.parseArray(json);
        } catch (Exception bareArrayFailed) {
            Map<String, Object> root = Json.parseObject(json);
            List<Object> entries = root == null ? null : Json.arr(root, "entries");
            arr = entries == null ? List.of() : entries;
        }
        List<Item> out = new ArrayList<>();
        for (Object o : arr) {
            Map<String, Object> m = Json.asMap(o);
            if (m == null) continue;
            String text = Json.str(m, "text", "");
            if (text.isBlank()) text = Json.str(m, "body", "");
            String category = Json.str(m, "category", "");
            if (category.isBlank()) category = Json.str(m, "type", "news");
            String shortText = Json.str(m, "shortText", "");
            if (shortText.isBlank()) shortText = summarize(text, 150);
            String article = Json.str(m, "articleBody", "");
            String longText = article.isBlank() ? text : article;
            out.add(new Item(
                    Json.str(m, "title", "Untitled"),
                    Json.str(m, "date", ""),
                    category,
                    shortText,
                    longText,
                    extractImageUrl(m, "image", "playPageImage", "newsPageImage"),
                    extractImageUrl(m, "newsPageImage", "image", "playPageImage"),
                    normalizeUrl(Json.str(m, "readMoreLink", ""))));
        }
        items = List.copyOf(out);
    }

    /** Absolute-ifies a link that may be protocol-relative or root-relative. */
    private static String normalizeUrl(String url) {
        if (url == null || url.isBlank()) return null;
        if (url.startsWith("//")) return "https:" + url;
        if (url.startsWith("http")) return url;
        if (url.startsWith("/")) return CONTENT_BASE + url;
        return url;
    }

    /**
     * Builds the full blog-style article document for the reader page: the
     * complete body (raw HTML when the feed provides markup, otherwise plain
     * text escaped and split into paragraphs) plus a "read more" link when
     * the entry has one. Images are composed by the UI around this document.
     */
    public static String buildArticleHtml(Item it) {
        StringBuilder sb = new StringBuilder("<html><body>");
        String body = it.longText() == null ? "" : it.longText().trim();
        if (looksLikeHtml(body)) {
            sb.append(body);
        } else if (!body.isEmpty()) {
            for (String para : body.split("\\n\\s*\\n+")) {
                if (para.isBlank()) continue;
                sb.append("<p>").append(escapeAndBreaks(para.trim())).append("</p>");
            }
        }
        if (it.readMoreUrl() != null && !it.readMoreUrl().isBlank()) {
            sb.append("<p style=\"margin-top:14px\"><a href=\"").append(it.readMoreUrl())
              .append("\">Read the full article on minecraft.net &#8599;</a></p>");
        }
        sb.append("</body></html>");
        return sb.toString();
    }

    private static boolean looksLikeHtml(String s) {
        return s != null && s.length() > 3 && s.chars().anyMatch(c -> c == '<')
                && java.util.regex.Pattern
                        .compile("<\\s*(p|div|ul|ol|li|h[1-6]|table|thead|tbody|blockquote|img)\\b",
                                java.util.regex.Pattern.CASE_INSENSITIVE)
                        .matcher(s).find();
    }

    private static String escapeAndBreaks(String s) {
        String e = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
        return e.replace("\r\n", "\n").replace("\n", "<br>");
    }

    /** Strips an HTML body down to a single-line plain text, truncated at a word boundary. */
    public static String summarize(String html, int max) {
        String t = stripHtml(html).replaceAll("\\s+", " ");
        if (t.length() <= max) return t;
        int cut = t.lastIndexOf(' ', max);
        if (cut < max / 2) cut = max;
        return t.substring(0, cut).trim() + "…";
    }

    /**
     * The article as readable plain text: paragraphs preserved, tags and
     * entities resolved — used for the reader's "Copy text" button.
     */
    public static String articlePlainText(Item it) {
        return stripHtml(it.longText() == null ? "" : it.longText());
    }

    /**
     * Removes tags/scripts/styles and unescapes the entities Mojang uses.
     * Block-level boundaries become paragraph breaks so the result reads
     * like the original article instead of one melted line.
     */
    public static String stripHtml(String html) {
        if (html == null || html.isBlank()) return "";
        String s = html.replaceAll("(?is)<(script|style)\\b.*?</\\1>", " ");
        s = s.replaceAll("(?i)<br\\s*/?>", "\n");
        s = s.replaceAll("(?i)</(p|div|li|h[1-6]|tr|blockquote)>", "\n\n");
        s = s.replaceAll("(?i)<li\\b[^>]*>", "\u2022 ");
        s = s.replaceAll("<[^>]+>", "");
        s = unescapeEntities(s);
        s = s.replaceAll("[^\\S\\n]+", " ");          // collapse spaces/tabs, keep newlines
        s = s.replaceAll(" *\n *", "\n");              // trim around newlines
        s = s.replaceAll("\n{3,}", "\n\n");            // max one blank line
        return s.trim();
    }

    private static String unescapeEntities(String s) {
        if (!s.contains("&")) return s;
        String r = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", "\"").replace("&#39;", "'").replace("&apos;", "'")
                .replace("&nbsp;", " ").replace("&hellip;", "…").replace("&mdash;", "—")
                .replace("&ndash;", "–").replace("&rsquo;", "’").replace("&lsquo;", "‘")
                .replace("&ldquo;", "“").replace("&rdquo;", "”");
        StringBuilder sb = new StringBuilder(r.length());
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("&#(x?)([0-9a-fA-F]+);").matcher(r);
        int copied = 0;
        while (m.find()) {
            sb.append(r, copied, m.start());
            try {
                int code = Integer.parseInt(m.group(2), m.group(1).isEmpty() ? 10 : 16);
                if (code > 0 && code < Character.MAX_VALUE) sb.append((char) code);
            } catch (NumberFormatException ignored) {
                sb.append(m.group());
            }
            copied = m.end();
        }
        sb.append(r, copied, r.length());
        return sb.toString();
    }

    /**
     * Resolves the first usable image URL from the given candidate keys.
     * The real feed stores art in {@code playPageImage} (700x466 card) and
     * {@code newsPageImage} (772x350 banner); older shapes used a plain
     * {@code image} string or object. Values may be absolute URLs or paths
     * relative to the content CDN.
     */
    private static String extractImageUrl(Map<String, Object> m, String... keys) {
        for (String key : keys) {
            Object img = m.get(key);
            String url = null;
            if (img instanceof Map) url = Json.str(Json.asMap(img), "url", null);
            else if (img instanceof String s) url = s;
            if (url != null && !url.isBlank()) {
                if (url.startsWith("http")) return url;
                return CONTENT_BASE + (url.startsWith("/") ? url : "/" + url);
            }
        }
        return null;
    }

    public static List<Item> items() { return items; }
}
