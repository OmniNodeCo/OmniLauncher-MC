package com.omninode.omnilauncher.api;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

import com.omninode.omnilauncher.util.Async;
import com.omninode.omnilauncher.util.Http;
import com.omninode.omnilauncher.util.Json;
import com.omninode.omnilauncher.util.Log;
import com.omninode.omnilauncher.util.Os;

/**
 * Mojang version manifest API (piston-meta.mojang.com).
 * Cached on disk with ETag revalidation; safe to call before network is up.
 */
public class VersionManifest {

    public static final String MANIFEST_URL =
            "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json";

    public record Entry(String id, String type, String url, String sha1, String releaseTime) {
        public boolean isRelease() { return "release".equals(type); }
        public boolean isSnapshot() { return "snapshot".equals(type); }
        public boolean isHistorical() { return "old_beta".equals(type) || "old_alpha".equals(type); }
    }

    private static volatile List<Entry> entries = List.of();
    private static volatile String latestRelease = "";
    private static volatile String latestSnapshot = "";
    private static volatile long loadedAt;
    private static final long TTL_MS = 10 * 60_000;

    /** Loads (or reloads) the manifest in the background, then invokes the callback on the EDT. */
    public static void loadAsync(Runnable onSuccess, java.util.function.Consumer<String> onError) {
        long age = System.currentTimeMillis() - loadedAt;
        if (!entries.isEmpty() && age < TTL_MS) {
            if (onSuccess != null) Async.ui(onSuccess);
            return;
        }
        Async.io(() -> {
            try {
                loadBlocking();
                if (onSuccess != null) Async.ui(onSuccess);
            } catch (Exception e) {
                Log.error("Manifest load failed", e);
                if (entries.isEmpty() && onError != null)
                    Async.ui(() -> onError.accept("Could not load the version list.\n" + e.getMessage()));
            }
        });
    }

    public static void loadBlocking() throws Exception {
        Path cache = Os.cacheDir().resolve("version_manifest_v2.json");
        Path etagFile = Os.cacheDir().resolve("version_manifest_v2.etag");
        String etag = Files.exists(etagFile) ? Files.readString(etagFile) : null;
        try {
            Map<String, List<String>> rh = new java.util.HashMap<>();
            byte[] body = Http.getIfChanged(MANIFEST_URL, etag, rh);
            if (body != null) {
                Files.write(cache, body);
                List<String> etags = rh.getOrDefault("etag", List.of());
                if (!etags.isEmpty()) Files.writeString(etagFile, etags.get(0));
            }
        } catch (Exception e) {
            if (!Files.exists(cache)) throw e;
            Log.warn("Manifest refresh failed, using cache: " + e.getMessage());
        }
        parse(Files.readString(cache, StandardCharsets.UTF_8));
        loadedAt = System.currentTimeMillis();
    }

    /** Parses manifest JSON (used directly with fixtures in self-test mode). */
    public static void parse(String json) {
        Map<String, Object> root = Json.parseObject(json);
        var latest = Json.map(root, "latest");
        latestRelease = Json.str(latest, "release", "");
        latestSnapshot = Json.str(latest, "snapshot", latestRelease);
        List<Entry> list = new ArrayList<>();
        for (Object o : Json.arr(root, "versions")) {
            var m = Json.asMap(o);
            if (m == null) continue;
            list.add(new Entry(Json.str(m, "id", "?"), Json.str(m, "type", "release"),
                    Json.str(m, "url", ""), Json.str(m, "sha1", null), Json.str(m, "releaseTime", "")));
        }
        list.sort(Comparator.comparing((Entry e) -> e.releaseTime()).reversed());
        entries = List.copyOf(list);
    }

    public static List<Entry> entries() { return entries; }
    public static String latestRelease() { return latestRelease; }
    public static String latestSnapshot() { return latestSnapshot; }

    public static Entry byId(String id) {
        for (Entry e : entries) if (e.id().equals(id)) return e;
        return null;
    }

    /** The version the user currently has selected (or latest release). */
    public static Entry resolveSelected(String lastVersionId) {
        if (lastVersionId != null && !lastVersionId.isBlank()) {
            Entry e = byId(lastVersionId);
            if (e != null) return e;
        }
        return byId(latestRelease);
    }

    /** Entries matching the user's content filters, newest first. */
    public static List<Entry> visibleEntries(boolean showSnapshots, boolean showHistorical) {
        List<Entry> out = new ArrayList<>();
        for (Entry e : entries) {
            if (e.isRelease() || (e.isSnapshot() && showSnapshots) || (e.isHistorical() && showHistorical))
                out.add(e);
        }
        return out;
    }
}
