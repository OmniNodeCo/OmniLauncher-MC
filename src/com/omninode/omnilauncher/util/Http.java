package com.omninode.omnilauncher.util;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.BiConsumer;

/**
 * Central HTTP client used for every API call and download.
 * Includes retries, SHA-1 verification and streamed downloads with progress.
 */
public final class Http {

    public static final String USER_AGENT = "OmniLauncher/2.0 (github.com/OmniNodeCo/OmniLauncher-MC)";

    private static final HttpClient CLIENT = HttpClient.newBuilder()
            .followRedirects(HttpClient.Redirect.NORMAL)
            .connectTimeout(Duration.ofSeconds(15))
            .build();

    private Http() {}

    /* ------------------------------------------------------------ GET -- */

    public static byte[] get(String url) throws IOException, InterruptedException {
        return get(url, Map.of());
    }

    public static byte[] get(String url, Map<String, String> headers) throws IOException, InterruptedException {
        IOException last = null;
        for (int attempt = 0; attempt < 3; attempt++) {
            try {
                HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(url))
                        .timeout(Duration.ofSeconds(30))
                        .header("User-Agent", USER_AGENT)
                        .GET();
                headers.forEach(b::header);
                HttpResponse<byte[]> resp = CLIENT.send(b.build(), HttpResponse.BodyHandlers.ofByteArray());
                if (resp.statusCode() / 100 != 2)
                    throw new IOException("HTTP " + resp.statusCode() + " for " + url);
                return resp.body();
            } catch (IOException e) {
                last = e;
                if (attempt < 2) Thread.sleep(400L * (attempt + 1));
            }
        }
        throw last != null ? last : new IOException("GET failed: " + url);
    }

    /** GET returning the raw body; returns empty when the server answers 304 Not Modified. */
    public static byte[] getIfChanged(String url, String etag, Map<String, List<String>> responseHeadersOut)
            throws IOException, InterruptedException {
        HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(30))
                .header("User-Agent", USER_AGENT)
                .GET();
        if (etag != null && !etag.isBlank()) b.header("If-None-Match", etag);
        HttpResponse<byte[]> resp = CLIENT.send(b.build(), HttpResponse.BodyHandlers.ofByteArray());
        if (resp.statusCode() == 304) return null;
        if (resp.statusCode() / 100 != 2) throw new IOException("HTTP " + resp.statusCode() + " for " + url);
        responseHeadersOut.put("etag", resp.headers().allValues("etag"));
        return resp.body();
    }

    /* ----------------------------------------------------------- POST -- */

    public static byte[] post(String url, byte[] body, Map<String, String> headers)
            throws IOException, InterruptedException {
        HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(30))
                .header("User-Agent", USER_AGENT)
                .POST(HttpRequest.BodyPublishers.ofByteArray(body));
        headers.forEach(b::header);
        HttpResponse<byte[]> resp = CLIENT.send(b.build(), HttpResponse.BodyHandlers.ofByteArray());
        if (resp.statusCode() / 100 != 2)
            throw new IOException("HTTP " + resp.statusCode() + " for " + url + ": "
                    + new String(resp.body(), StandardCharsets.UTF_8));
        return resp.body();
    }

    public static byte[] postJson(String url, String json) throws IOException, InterruptedException {
        return post(url, json.getBytes(StandardCharsets.UTF_8),
                Map.of("Content-Type", "application/json", "Accept", "application/json"));
    }

    public static byte[] postJson(String url, String json, String bearer) throws IOException, InterruptedException {
        return post(url, json.getBytes(StandardCharsets.UTF_8), Map.of(
                "Content-Type", "application/json",
                "Accept", "application/json",
                "Authorization", "Bearer " + bearer));
    }

    /** POST JSON that does NOT throw on non-2xx (Xbox XSTS errors arrive as 401 + XErr JSON). */
    public static Response postJsonRaw(String url, String json) throws IOException, InterruptedException {
        HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(30))
                .header("User-Agent", USER_AGENT)
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json, StandardCharsets.UTF_8))
                .build();
        HttpResponse<byte[]> resp = CLIENT.send(req, HttpResponse.BodyHandlers.ofByteArray());
        return new Response(resp.statusCode(), resp.body());
    }


    public static byte[] postForm(String url, Map<String, String> form) throws IOException, InterruptedException {
        StringBuilder sb = new StringBuilder();
        boolean first = true;
        for (Map.Entry<String, String> e : form.entrySet()) {
            if (!first) sb.append('&');
            first = false;
            sb.append(java.net.URLEncoder.encode(e.getKey(), StandardCharsets.UTF_8))
              .append('=')
              .append(java.net.URLEncoder.encode(e.getValue(), StandardCharsets.UTF_8));
        }
        return post(url, sb.toString().getBytes(StandardCharsets.UTF_8),
                Map.of("Content-Type", "application/x-www-form-urlencoded"));
    }

    /** POST that does NOT throw on non-2xx — OAuth endpoints signal pending/declined via status codes. */
    public record Response(int status, byte[] body) {
        public String text() { return new String(body, StandardCharsets.UTF_8); }
        public boolean ok() { return status / 100 == 2; }
    }

    public static Response postFormRaw(String url, Map<String, String> form) throws IOException, InterruptedException {
        StringBuilder sb = new StringBuilder();
        boolean first = true;
        for (Map.Entry<String, String> e : form.entrySet()) {
            if (!first) sb.append('&');
            first = false;
            sb.append(java.net.URLEncoder.encode(e.getKey(), StandardCharsets.UTF_8))
              .append('=')
              .append(java.net.URLEncoder.encode(e.getValue(), StandardCharsets.UTF_8));
        }
        HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(30))
                .header("User-Agent", USER_AGENT)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(sb.toString()))
                .build();
        HttpResponse<byte[]> resp = CLIENT.send(req, HttpResponse.BodyHandlers.ofByteArray());
        return new Response(resp.statusCode(), resp.body());
    }


    /* ------------------------------------------------------ downloads -- */

    /** Progress snapshot passed to listeners. */
    public record Progress(long bytesDone, long bytesTotal) {}

    /** Mutable cancellation flag shared between UI and download loops. */
    public static final class CancelToken {
        private final AtomicBoolean flag = new AtomicBoolean(false);
        public boolean cancelled() { return flag.get(); }
        public void cancel() { flag.set(true); }
    }

    public static CancelToken newCancelToken() {
        return new CancelToken();
    }

    /**
     * Streams a URL to {@code dest}, verifying SHA-1 when {@code sha1} is non-null.
     * Downloads to a {@code .part} sibling then atomically moves into place.
     *
     * @param progress called roughly every 256 KB with (bytesDone, bytesTotal) for THIS file
     */
    public static void downloadToFile(String url, Path dest, String sha1,
                                      BiConsumer<Long, Long> progress, CancelToken cancel)
            throws IOException, InterruptedException {
        Files.createDirectories(dest.getParent());
        Path part = dest.resolveSibling(dest.getFileName() + ".part");
        IOException last = null;
        for (int attempt = 0; attempt < 3; attempt++) {
            if (cancel != null && cancel.cancelled()) throw new IOException("Cancelled");
            try {
                Files.deleteIfExists(part);
                HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                        .timeout(Duration.ofSeconds(30))
                        .header("User-Agent", USER_AGENT)
                        .GET()
                        .build();
                HttpResponse<InputStream> resp =
                        CLIENT.send(req, HttpResponse.BodyHandlers.ofInputStream());
                if (resp.statusCode() / 100 != 2) {
                    try (InputStream ignored = resp.body()) {}
                    throw new IOException("HTTP " + resp.statusCode() + " for " + url);
                }
                long total = resp.headers().firstValueAsLong("Content-Length").orElse(-1);
                MessageDigest digest = sha1 != null ? MessageDigest.getInstance("SHA-1") : null;
                long done = 0;
                long nextTick = 262144;
                try (InputStream in = resp.body(); var out = Files.newOutputStream(part)) {
                    byte[] buf = new byte[64 * 1024];
                    while (true) {
                        if (cancel != null && cancel.cancelled()) throw new IOException("Cancelled");
                        int n = in.read(buf);
                        if (n < 0) break;
                        out.write(buf, 0, n);
                        if (digest != null) digest.update(buf, 0, n);
                        done += n;
                        if (progress != null && done >= nextTick) {
                            progress.accept(done, total);
                            nextTick = done + 262144;
                        }
                    }
                }
                if (sha1 != null) {
                    String actual = hex(digest.digest());
                    if (!actual.equalsIgnoreCase(sha1))
                        throw new IOException("SHA-1 mismatch for " + url + " (expected " + sha1 + ", got " + actual + ")");
                }
                if (total >= 0 && done != total)
                    throw new IOException("Truncated download for " + url + " (" + done + "/" + total + ")");
                Files.move(part, dest, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
                if (progress != null) progress.accept(done, done);
                return;
            } catch (IOException e) {
                last = e;
                if (cancel != null && cancel.cancelled()) throw e;
                if (attempt < 2) Thread.sleep(500L * (attempt + 1));
            } catch (InterruptedException e) {
                throw e;
            } catch (Exception e) {
                last = new IOException(e);
            }
        }
        throw last != null ? last : new IOException("Download failed: " + url);
    }

    public static String hex(byte[] bytes) {
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) sb.append(Character.forDigit((b >> 4) & 0xF, 16)).append(Character.forDigit(b & 0xF, 16));
        return sb.toString();
    }

    /** SHA-1 of a file on disk (streamed). */
    public static String sha1(Path file) throws IOException {
        try (InputStream in = Files.newInputStream(file)) {
            MessageDigest md = MessageDigest.getInstance("SHA-1");
            byte[] buf = new byte[64 * 1024];
            int n;
            while ((n = in.read(buf)) > 0) md.update(buf, 0, n);
            return hex(md.digest());
        } catch (Exception e) {
            throw new IOException("Hashing failed: " + file, e);
        }
    }
}
