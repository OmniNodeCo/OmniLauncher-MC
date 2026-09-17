package com.omninode.omnilauncher.core;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

import com.omninode.omnilauncher.api.VersionManifest;
import com.omninode.omnilauncher.core.DownloadEngine.Job;
import com.omninode.omnilauncher.util.Http;
import com.omninode.omnilauncher.util.Log;
import com.omninode.omnilauncher.util.Os;

/**
 * Installs a Minecraft version: client jar, libraries, natives, assets and
 * logging config — verifying hashes and skipping anything already present.
 */
public class VersionInstaller {

    /** Base URL for object downloads (overridable so tests can serve fixtures locally). */
    public static volatile String assetBaseUrl = "https://resources.download.minecraft.net";

    public record InstalledVersion(Path versionDir, Path clientJar, List<Path> classpath,
                                   Path nativesDir, VersionJson json) {}

    /** Install everything needed to play {@code entry}. */
    public static InstalledVersion install(VersionManifest.Entry entry,
                                           java.util.function.Consumer<String> status,
                                           java.util.function.Consumer<Float> progress,
                                           Http.CancelToken cancel) throws Exception {
        return install(entry, new DownloadEngine.Listener() {
            private long lastTotal = 1;
            @Override public void status(String message) { status.accept(message); }
            @Override public void progress(long bytesDone, long bytesTotal) {
                if (bytesTotal > 0) lastTotal = bytesTotal;
                progress.accept(Math.min(1f, bytesDone / (float) Math.max(1, lastTotal)));
            }
        }, cancel);
    }

    private static InstalledVersion install(VersionManifest.Entry entry,
                                            DownloadEngine.Listener listener,
                                            Http.CancelToken cancel) throws Exception {
        Os os = Os.get();
        Path versionDir = Os.versionsDir().resolve(entry.id());
        Files.createDirectories(versionDir);
        listener.status("Fetching version metadata…");

        // ------------------------------------------------------- version json
        VersionJson version = fetchVersionJson(entry, versionDir, cancel);

        // ------------------------------------------------------- plan jobs
        List<Job> jobs = new ArrayList<>();
        Set<String> features = new HashSet<>();
        if (!Settings.get().fullscreen && Settings.get().gameWidth > 0) features.add("has_custom_resolution");

        Path clientJar = versionDir.resolve(entry.id() + ".jar");
        if (version.client != null && !version.client.url().isBlank()) {
            jobs.add(new Job(version.client.url(), clientJar, version.client.sha1(),
                    version.client.size(), true));
        } else {
            Log.warn("Version " + entry.id() + " has no client download entry (very old format).");
        }

        List<Path> classpath = new ArrayList<>();
        List<VersionJson.Download> nativesJars = new ArrayList<>();
        for (VersionJson.Library lib : version.libraries) {
            if (!lib.allowedByRules(os, features)) continue;
            if (lib.artifact != null && !lib.artifact.url().isBlank()) {
                String rel = lib.artifact.path() != null ? lib.artifact.path()
                        : libPathFromName(lib.name);
                Path dest = Os.librariesDir().resolve(rel);
                classpath.add(dest);
                jobs.add(new Job(lib.artifact.url(), dest, lib.artifact.sha1(), lib.artifact.size(), true));
            }
            if (lib.nativesMap != null && lib.classifiers != null) {
                String key = lib.nativesKey(os);
                VersionJson.Download n = lib.classifiers.get(key);
                if (n == null) {
                    Log.warn("No natives classifier '" + key + "' for " + lib.name);
                } else {
                    String rel = n.path() != null ? n.path() : libPathFromName(key + "-" + lib.name + ".jar");
                    Path dest = Os.librariesDir().resolve(rel);
                    nativesJars.add(new VersionJson.Download(n.url(), n.sha1(), n.size(), dest.toString()));
                    jobs.add(new Job(n.url(), dest, n.sha1(), n.size(), true));
                }
            }
        }

        // assets
        Map<String, Object> assetObjects = null;
        Path indexFile = null;
        if (version.assetIndex != null && !version.assetIndex.url().isBlank()) {
            listener.status("Fetching asset index…");
            Files.createDirectories(Os.assetsDir().resolve("indexes"));
            indexFile = Os.assetsDir().resolve("indexes").resolve(version.assetIndex.id() + ".json");
            fetchIfMissing(version.assetIndex.url(), indexFile, version.assetIndex.sha1(), cancel);
            var indexRoot = com.omninode.omnilauncher.util.Json.parseObject(Files.readString(indexFile));
            // "objects" maps asset name → {hash, size}
            assetObjects = com.omninode.omnilauncher.util.Json.map(indexRoot, "objects");
            Files.createDirectories(Os.assetsDir().resolve("objects"));
            if (assetObjects != null) {
                for (Map.Entry<String, Object> e : assetObjects.entrySet()) {
                    var m = com.omninode.omnilauncher.util.Json.asMap(e.getValue());
                    if (m == null) continue;
                    String hash = com.omninode.omnilauncher.util.Json.str(m, "hash", "");
                    long size = com.omninode.omnilauncher.util.Json.num(m, "size", -1);
                    if (hash.length() < 3) continue;
                    Path dest = Os.assetsDir().resolve("objects").resolve(hash.substring(0, 2)).resolve(hash);
                    jobs.add(new Job(assetBaseUrl + "/"
                            + hash.substring(0, 2) + "/" + hash, dest, null, size, false));
                }
            }
        }

        // logging config
        Path logConfigFile = null;
        if (version.logging != null && version.logging.url() != null && !version.logging.url().isBlank()) {
            logConfigFile = Os.assetsDir().resolve("log_configs").resolve(version.logging.id());
            jobs.add(new Job(version.logging.url(), logConfigFile, version.logging.sha1(),
                    version.logging.size(), true));
        }

        // ------------------------------------------------------- download
        long totalBytes = 0;
        for (Job j : jobs) totalBytes += Math.max(0, j.size);
        listener.status("Checking " + jobs.size() + " files…");
        // Pre-pass: hash/size checks happen inside the engine; report totals immediately.
        listener.progress(0, Math.max(1, totalBytes));
        DownloadEngine.run(jobs, new DownloadEngine.Listener() {
            @Override public void status(String message) { listener.status(message); }
            @Override public void progress(long bytesDone, long bytesTotal) { listener.progress(bytesDone, bytesTotal); }
        }, cancel, Settings.get().concurrency);

        // ------------------------------------------------------- natives
        Path nativesDir = versionDir.resolve("natives-" + os.mojangName() + "-" + os.arch);
        if (!nativesJars.isEmpty()) extractNatives(nativesJars, nativesDir);

        // ------------------------------------------------------- virtual assets
        if (assetObjects != null && indexFile != null) {
            if (version.assetIndex.virtual()) mirrorAssets(assetObjects,
                    Os.assetsDir().resolve("virtual").resolve(version.assetIndex.id()));
            if (version.assetIndex.mapToResources()) mirrorAssets(assetObjects,
                    Settings.get().resolveGameDir().resolve("resources"));
        }

        listener.status("Ready");
        List<Path> fullClasspath = new ArrayList<>(classpath);
        if (Files.exists(clientJar)) fullClasspath.add(clientJar);
        return new InstalledVersion(versionDir, clientJar, fullClasspath, nativesDir, version);
    }

    /* ------------------------------------------------------------- pieces */

    private static VersionJson fetchVersionJson(VersionManifest.Entry entry, Path versionDir,
                                                Http.CancelToken cancel) throws Exception {
        if (cancel != null && cancel.cancelled()) throw new IOException("Cancelled");
        Path jsonFile = versionDir.resolve(entry.id() + ".json");
        if (Files.exists(jsonFile)) {
            if (entry.sha1() == null || entry.sha1().isBlank()
                    || Http.sha1(jsonFile).equalsIgnoreCase(entry.sha1())) {
                return VersionJson.parse(Files.readString(jsonFile));
            }
            Log.info("Version JSON changed on manifest, refreshing " + entry.id());
        }
        byte[] body = Http.get(entry.url());
        if (entry.sha1() != null && !entry.sha1().isBlank()) {
            String actual = Http.hex(java.security.MessageDigest.getInstance("SHA-1").digest(body));
            if (!actual.equalsIgnoreCase(entry.sha1()))
                throw new IOException("Version JSON hash mismatch for " + entry.id());
        }
        Files.write(jsonFile, body);
        return VersionJson.parse(new String(body, java.nio.charset.StandardCharsets.UTF_8));
    }

    private static void fetchIfMissing(String url, Path dest, String sha1, Http.CancelToken cancel)
            throws Exception {
        if (Files.exists(dest)) {
            if (sha1 == null || sha1.isBlank() || Http.sha1(dest).equalsIgnoreCase(sha1)) return;
        }
        Http.downloadToFile(url, dest, sha1, null, cancel);
    }

    /** com.google:guava:31.1-jre → com/google/guava/guava/31.1-jre/guava-31.1-jre.jar */
    private static String libPathFromName(String name) {
        String[] parts = name.split(":", -1);
        if (parts.length != 3) return name.replace(':', '/');
        String group = parts[0].replace('.', '/');
        String artifact = parts[1];
        String version = parts[2];
        int afterCoords = parts[0].length() + artifact.length() + version.length() + 2;
        String suffix = name.length() > afterCoords ? name.substring(afterCoords) : "";
        return group + "/" + artifact + "/" + version + "/" + artifact + "-" + version + suffix + ".jar";
    }

    private static void extractNatives(List<VersionJson.Download> nativesJars, Path nativesDir)
            throws IOException {
        Files.createDirectories(nativesDir);
        for (VersionJson.Download n : nativesJars) {
            Path jar = Path.of(n.path());
            if (!Files.exists(jar)) continue;
            String markerName = ".done-" + n.sha1();
            if (n.sha1() != null && Files.exists(nativesDir.resolve(markerName))) continue;
            try (ZipFile zip = new ZipFile(jar.toFile())) {
                var entries = zip.entries();
                byte[] buf = new byte[64 * 1024];
                while (entries.hasMoreElements()) {
                    ZipEntry e = entries.nextElement();
                    if (e.isDirectory()) continue;
                    String name = e.getName();
                    if (name.startsWith("META-INF")) continue;
                    Path out = nativesDir.resolve(name.replace('/', '_'));
                    try (var in = zip.getInputStream(e); var fout = Files.newOutputStream(out)) {
                        int n2;
                        while ((n2 = in.read(buf)) > 0) fout.write(buf, 0, n2);
                    }
                }
            }
            if (n.sha1() != null) Files.writeString(nativesDir.resolve(markerName), n.sha1());
        }
    }

    /** Copies stored objects into a legacy mirror directory (virtual assets / resources). */
    private static void mirrorAssets(Map<String, Object> assetObjects, Path mirrorRoot) throws IOException {
        for (Map.Entry<String, Object> e : assetObjects.entrySet()) {
            var m = com.omninode.omnilauncher.util.Json.asMap(e.getValue());
            if (m == null) continue;
            String key = e.getKey();
            String hash = com.omninode.omnilauncher.util.Json.str(m, "hash", "");
            if (key.isEmpty() || hash.length() < 3) continue;
            Path src = Os.assetsDir().resolve("objects").resolve(hash.substring(0, 2)).resolve(hash);
            Path dst = mirrorRoot.resolve(key);
            if (Files.exists(src) && !Files.exists(dst)) {
                Files.createDirectories(dst.getParent());
                try {
                    Files.copy(src, dst);
                } catch (IOException ignored) {}
            }
        }
    }
}
