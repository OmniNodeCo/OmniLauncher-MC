package com.omninode.omnilauncher.core;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import com.omninode.omnilauncher.model.Account;
import com.omninode.omnilauncher.util.Log;
import com.omninode.omnilauncher.util.Os;

/** Builds the java command line and starts the Minecraft client process. */
public class GameLauncher {

    public static final String LAUNCHER_NAME = "OmniLauncher";
    public static final String LAUNCHER_VERSION = "2.0.0";

    public record JavaRuntime(Path javaExe, int major) {}

    public interface RunListener {
        /** Called once the process starts (never null process). */
        void started(Process process);
        /** Called when the game exits. */
        void exited(int exitCode);
        /** Called for every game output line. */
        void outputLine(String line);
        /** Called on launch failure (process never started). */
        void failed(String message);
    }

    /**
     * Constructs the full java command for the given installed version and
     * account (pure function of settings + version metadata — unit tested).
     */
    public static List<String> buildCommand(VersionInstaller.InstalledVersion v,
                                            Account account, JavaRuntime rt) {
        Settings s = Settings.get();
        Os os = Os.get();

        // ------------------------------------------------------ variables
        Map<String, String> vars = new LinkedHashMap<>();
        vars.put("natives_directory", v.nativesDir().toString());
        vars.put("launcher_name", LAUNCHER_NAME);
        vars.put("launcher_version", LAUNCHER_VERSION);
        vars.put("classpath_separator", os.classpathSeparator());
        vars.put("library_directory", Os.librariesDir().toString());
        vars.put("classpath", joinClasspath(v.classpath(), os.classpathSeparator()));

        Map<String, String> gameVars = new LinkedHashMap<>(vars);
        gameVars.put("auth_player_name", account.getName());
        gameVars.put("version_name", v.json().id);
        gameVars.put("game_directory", s.resolveGameDir().toString());
        gameVars.put("assets_root", Os.assetsDir().toString());
        gameVars.put("assets_index_name",
                v.json().assetIndex != null ? v.json().assetIndex.id() : "legacy");
        gameVars.put("auth_uuid", account.getUuid());
        gameVars.put("auth_access_token", account.getAccessToken());
        gameVars.put("user_type", account.isMicrosoft() ? "msa" : "legacy");
        gameVars.put("version_type", v.json().type);
        gameVars.put("clientid", LAUNCHER_NAME.toLowerCase());
        gameVars.put("auth_xuid", "0");
        gameVars.put("user_properties", "{}");
        if (!s.fullscreen && s.gameWidth > 0) {
            gameVars.put("resolution_width", String.valueOf(s.gameWidth));
            gameVars.put("resolution_height", String.valueOf(s.gameHeight));
        }

        var features = new java.util.HashSet<String>();
        if (!s.fullscreen && s.gameWidth > 0) features.add("has_custom_resolution");

        // ------------------------------------------------------ command
        List<String> cmd = new ArrayList<>();
        cmd.add(rt.javaExe().toString());
        cmd.add("-Xmx" + s.memoryMb + "M");
        if (rt.major() >= 10) cmd.add("-XX:+UseG1GC");
        for (String a : splitArgs(s.extraJvmArgs)) cmd.add(a);

        cmd.addAll(v.json().resolveJvmArgs(os, features, vars));
        if (!v.json().isModern()) {
            // legacy versions: synthesize the JVM setup the old launcher used
            cmd.add("-Djava.library.path=" + v.nativesDir());
            cmd.add("-cp");
            cmd.add(joinClasspath(v.classpath(), os.classpathSeparator()));
        }

        // logging configuration (log4j config shipped per-version)
        if (v.json().logging != null && v.json().logging.id() != null) {
            Path logCfg = Os.assetsDir().resolve("log_configs").resolve(v.json().logging.id());
            if (Files.exists(logCfg)) {
                cmd.add(VersionJson.substitute(v.json().logging.argument(),
                        Map.of("path", logCfg.toString())));
            }
        }

        cmd.add(v.json().mainClass);
        cmd.addAll(v.json().resolveGameArgs(os, features, gameVars));
        for (String a : splitArgs(s.extraGameArgs)) cmd.add(a);
        return cmd;
    }

    public static Process launch(VersionInstaller.InstalledVersion v, Account account, RunListener listener)
            throws IOException {
        JavaRuntime rt = findJava();
        if (rt == null) {
            listener.failed("No Java runtime found. Install Java and set its path in Settings → Java.");
            return null;
        }
        int required = v.json().javaMajor > 0 ? v.json().javaMajor : 8;
        if (rt.major() > 0 && rt.major() < required) {
            listener.failed("Minecraft " + v.json().id + " requires Java " + required
                    + " but the configured runtime is Java " + rt.major()
                    + ". Install Java " + required + " and select it in Settings → Java.");
            return null;
        }

        List<String> cmd = buildCommand(v, account, rt);
        Path gameDir = Settings.get().resolveGameDir();
        Files.createDirectories(gameDir);

        Log.info("Launching Minecraft " + v.json().id + " with " + rt.javaExe());
        Log.info("Command: " + String.join(" ", cmd));

        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.directory(gameDir.toFile());
        pb.redirectErrorStream(true);
        try {
            Process process = pb.start();
            Thread t = new Thread(() -> {
                try (var reader = new java.io.BufferedReader(
                        new java.io.InputStreamReader(process.getInputStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        Log.info("[game] " + line);
                        listener.outputLine(line);
                    }
                } catch (IOException ignored) {
                } finally {
                    int code = -1;
                    try { code = process.waitFor(); } catch (InterruptedException ignored) {}
                    listener.exited(code);
                }
            }, "omni-game-log");
            t.setDaemon(true);
            t.start();
            listener.started(process);
            return process;
        } catch (IOException e) {
            listener.failed("Could not start the game: " + e.getMessage());
            return null;
        }
    }

    private static String joinClasspath(List<Path> files, String sep) {
        StringBuilder sb = new StringBuilder();
        for (Path p : files) {
            if (sb.length() > 0) sb.append(sep);
            sb.append(p.toString());
        }
        return sb.toString();
    }

    /** Splits arguments respecting double quotes. */
    public static List<String> splitArgs(String raw) {
        List<String> out = new ArrayList<>();
        if (raw == null || raw.isBlank()) return out;
        StringBuilder cur = new StringBuilder();
        boolean inQuote = false;
        for (int i = 0; i < raw.length(); i++) {
            char c = raw.charAt(i);
            if (c == '"') { inQuote = !inQuote; }
            else if (c == ' ' && !inQuote) {
                if (cur.length() > 0) { out.add(cur.toString()); cur.setLength(0); }
            } else cur.append(c);
        }
        if (cur.length() > 0) out.add(cur.toString());
        return out;
    }

    /* ----------------------------------------------------- java lookup -- */

    private static volatile JavaRuntime cached;

    public static JavaRuntime findJava() {
        JavaRuntime c = cached;
        if (c != null) return c;
        Settings s = Settings.get();
        List<Path> candidates = new ArrayList<>();
        if (s.javaPath != null && !s.javaPath.isBlank()) {
            Path p = Path.of(s.javaPath);
            if (Files.isDirectory(p)) p = p.resolve(javaBinary());
            candidates.add(p);
        }
        String javaHome = System.getenv("JAVA_HOME");
        if (javaHome != null && !javaHome.isBlank())
            candidates.add(Path.of(javaHome, "bin", javaBinary()));
        candidates.add(Path.of(javaBinary())); // PATH
        if (Os.get().family == Os.Family.MACOS) {
            for (String home : new String[]{"/Library/Java/JavaVirtualMachines",
                    System.getProperty("user.home") + "/Library/Java/JavaVirtualMachines"}) {
                candidates.addAll(globJavaCandidates(Path.of(home), "*/Contents/Home/bin/" + javaBinary()));
            }
        }
        if (Os.get().isWindows()) {
            for (String dir : new String[]{"C:/Program Files/Java", "C:/Program Files (x86)/Java",
                    "C:/Program Files/Eclipse Adoptium", System.getenv("LOCALAPPDATA") + "/Programs/Java"}) {
                if (dir == null) continue;
                candidates.addAll(globJavaCandidates(Path.of(dir), "*/bin/" + javaBinary()));
            }
        } else {
            for (String dir : new String[]{"/usr/lib/jvm", "/opt", System.getProperty("user.home") + "/.sdkman/candidates/java"}) {
                candidates.addAll(globJavaCandidates(Path.of(dir), "*/bin/" + javaBinary()));
            }
        }
        for (Path p : candidates) {
            if (p == null || !Files.isExecutable(p)) continue;
            int major = probeJavaMajor(p);
            if (major >= 8) {
                JavaRuntime rt = new JavaRuntime(p, major);
                cached = rt;
                return rt;
            }
        }
        return null;
    }

    private static String javaBinary() {
        return Os.get().isWindows() ? "java.exe" : "java";
    }

    private static List<Path> globJavaCandidates(Path dir, String glob) {
        List<Path> out = new ArrayList<>();
        try (var stream = Files.newDirectoryStream(dir, glob)) {
            stream.forEach(out::add);
        } catch (IOException ignored) {}
        return out;
    }

    /** Runs `java -version` and parses the major version from stderr/stdout. */
    public static int probeJavaMajor(Path javaExe) {
        try {
            Process p = new ProcessBuilder(javaExe.toString(), "-version").start();
            String out;
            try (var in = p.getInputStream()) {
                out = new String(in.readAllBytes());
            }
            p.waitFor(10, TimeUnit.SECONDS);
            var m = java.util.regex.Pattern.compile("version \"(\\d+)").matcher(out);
            if (m.find()) {
                int major = Integer.parseInt(m.group(1));
                if (major == 1) { // legacy "1.8.0_x" scheme
                    var m2 = java.util.regex.Pattern.compile("version \"1\\.(\\d+)").matcher(out);
                    if (m2.find()) return Integer.parseInt(m2.group(1));
                }
                return major;
            }
            return -1;
        } catch (Exception e) {
            return -1;
        }
    }

    public static void clearCache() { cached = null; }
}
