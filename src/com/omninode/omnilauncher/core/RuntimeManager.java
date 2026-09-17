package com.omninode.omnilauncher.core;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.PosixFilePermissions;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.omninode.omnilauncher.core.DownloadEngine.Job;
import com.omninode.omnilauncher.util.Http;
import com.omninode.omnilauncher.util.Json;
import com.omninode.omnilauncher.util.Os;

/**
 * Downloads and manages Mojang's bundled Java runtimes ("java-runtime-*"),
 * so players don't need to install the right JVM for every version.
 *
 * Flow: products manifest (per component/OS/arch) → runtime file manifest →
 * verified concurrent downloads → executable bits → checksum marker.
 */
public class RuntimeManager {

    public record Product(String component, String version, String manifestUrl,
                          String checksum, String availability) {}

    /** Overridable so the self-test can point this at a local fixture server. */
    public static volatile String productsBaseUrl =
            "https://piston-meta.mojang.com/v1/products/java-runtime";

    private RuntimeManager() {}

    public static String productsUrl(String component, Os os) {
        String osName = switch (os.family) {
            case WINDOWS -> "windows";
            case MACOS -> "mac";
            case LINUX -> "linux";
        };
        String arch = os.arch;
        if (os.family == Os.Family.WINDOWS && arch.equals("arm64")) arch = "x64"; // no win-arm JVM published
        return productsBaseUrl + "/" + component + "/" + osName + "/" + arch + "/all.json";
    }

    /**
     * Parses a products "all.json" response (an array of candidate entries).
     * Prefers the "jre_local" availability when present, else the first entry
     * with a manifest URL. Returns null when nothing usable is published.
     */
    public static Product parseProducts(String json, String component) {
        List<Object> arr = Json.parseArray(json);
        Product any = null;
        for (Object o : arr) {
            Map<String, Object> m = Json.asMap(o);
            if (m == null) continue;
            Map<String, Object> manifest = Json.map(m, "manifest");
            String url = manifest != null ? Json.str(manifest, "url", null) : null;
            if (url == null || url.isBlank()) continue;
            Product p = new Product(component, Json.str(m, "version", ""),
                    url, Json.str(m, "checksum", null), Json.str(m, "availability", ""));
            if ("jre_local".equals(p.availability())) return p;
            if (any == null) any = p;
        }
        return any;
    }

    /** Resolves the product to install for a component on this machine (live API). */
    public static Product resolve(String component) throws Exception {
        byte[] body = Http.get(productsUrl(component, Os.get()));
        Product p = parseProducts(new String(body, StandardCharsets.UTF_8), component);
        if (p == null) throw new IllegalStateException("No Java runtime published for " + component);
        return p;
    }

    public static Path runtimeDir(String component) {
        return Os.dataDir().resolve("runtimes").resolve(component);
    }

    public static Path javaExecutable(String component) {
        return runtimeDir(component).resolve("bin")
                .resolve(Os.get().isWindows() ? "java.exe" : "java");
    }

    /** Major version from a product version string like "21.0.3". */
    public static int majorOfVersion(String version) {
        if (version == null || version.isBlank()) return 0;
        try {
            var m = java.util.regex.Pattern.compile("(\\d+)").matcher(version);
            return m.find() ? Integer.parseInt(m.group(1)) : 0;
        } catch (Exception e) {
            return 0;
        }
    }

    public static boolean isInstalled(Product p) {
        if (p == null) return false;
        if (!Files.isExecutable(javaExecutable(p.component()))) return false;
        if (p.checksum() == null || p.checksum().isBlank()) return true;
        return Files.exists(runtimeDir(p.component()).resolve(".done-" + p.checksum()));
    }

    /** Downloads (or verifies) the runtime described by {@code p}. */
    public static boolean ensure(Product p, java.util.function.Consumer<String> status,
                                 java.util.function.Consumer<Float> progress,
                                 Http.CancelToken cancel) throws Exception {
        if (isInstalled(p)) {
            if (status != null) status.accept("Java " + p.version() + " already installed");
            if (progress != null) progress.accept(1f);
            return true;
        }
        if (status != null) status.accept("Downloading Java " + p.version() + "…");
        String manifestJson = new String(Http.get(p.manifestUrl()), StandardCharsets.UTF_8);
        Map<String, Object> root = Json.parseObject(manifestJson);
        Map<String, Object> files = Json.map(root, "files");
        if (files == null) throw new IllegalStateException("Invalid runtime manifest for " + p.component());

        List<Job> jobs = new ArrayList<>();
        List<String> executables = new ArrayList<>();
        for (Map.Entry<String, Object> e : files.entrySet()) {
            Map<String, Object> m = Json.asMap(e.getValue());
            if (m == null) continue;
            if ("directory".equals(Json.str(m, "type", "file"))) continue;
            Map<String, Object> downloads = Json.map(m, "downloads");
            Map<String, Object> raw = downloads != null ? Json.map(downloads, "raw") : null;
            if (raw == null) continue;
            String url = Json.str(raw, "url", "");
            if (url.isBlank()) continue;
            Path dest = runtimeDir(p.component()).resolve(e.getKey());
            jobs.add(new Job(url, dest, Json.str(raw, "sha1", null),
                    Json.num(raw, "size", -1), true));
            if (Json.bool(m, "executable", false)) executables.add(e.getKey());
        }

        long grand = 0;
        for (Job j : jobs) grand += Math.max(0, j.size);
        final long total = Math.max(1, grand);
        if (progress != null) progress.accept(0f);
        DownloadEngine.run(jobs, new DownloadEngine.Listener() {
            @Override public void status(String message) { /* per-file noise suppressed */ }
            @Override public void progress(long done, long bytesTotal) {
                if (progress != null) progress.accept(Math.min(1f, done / (float) total));
            }
        }, cancel, Settings.get().concurrency);

        if (!Os.get().isWindows()) {
            for (String name : executables) {
                try {
                    Files.setPosixFilePermissions(runtimeDir(p.component()).resolve(name),
                            PosixFilePermissions.fromString("rwxr-xr-x"));
                } catch (Exception ignored) {
                    // non-posix filesystem — nothing sensible to do
                }
            }
        }
        if (p.checksum() != null && !p.checksum().isBlank())
            Files.writeString(runtimeDir(p.component()).resolve(".done-" + p.checksum()), p.checksum());
        if (progress != null) progress.accept(1f);
        return true;
    }

    /** A JavaRuntime handle for an installed component, or null when missing. */
    public static GameLauncher.JavaRuntime javaFor(String component, int expectedMajor) {
        Path exe = javaExecutable(component);
        if (!Files.isExecutable(exe)) return null;
        return new GameLauncher.JavaRuntime(exe, expectedMajor);
    }
}
