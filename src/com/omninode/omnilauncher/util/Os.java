package com.omninode.omnilauncher.util;

import java.awt.Desktop;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Operating-system detection and per-platform launcher directories. */
public final class Os {

    public enum Family { WINDOWS, MACOS, LINUX }

    public final Family family;
    public final String arch; // "x64" or "arm64"

    private Os(Family family, String arch) {
        this.family = family;
        this.arch = arch;
    }

    private static volatile Os current;

    public static Os get() {
        Os o = current;
        if (o == null) {
            synchronized (Os.class) {
                o = current;
                if (o == null) current = o = detect();
            }
        }
        return o;
    }

    private static Os detect() {
        String osProp = System.getProperty("os.name", "").toLowerCase(Locale.ROOT);
        Family f;
        if (osProp.contains("win")) f = Family.WINDOWS;
        else if (osProp.contains("mac") || osProp.contains("darwin")) f = Family.MACOS;
        else f = Family.LINUX;
        String a = System.getProperty("os.arch", "x86").toLowerCase(Locale.ROOT);
        String arch = a.contains("aarch64") || a.contains("arm64") ? "arm64" : "x64";
        return new Os(f, arch);
    }

    /** Explicit platform descriptor (used by self-tests and fixtures). */
    public static Os of(Family family, String arch) {
        return new Os(family, arch);
    }

    /* ---------------------------------- names used by Mojang manifests -- */

    /** Mojang "os name" token: windows / linux / osx. */
    public String mojangName() {
        return switch (family) {
            case WINDOWS -> "windows";
            case MACOS -> "osx";
            case LINUX -> "linux";
        };
    }

    /** Library path token used inside Mojang library names: windows/linux/macos. */
    public String nativesKey() {
        return switch (family) {
            case WINDOWS -> "natives-windows";
            case MACOS -> "natives-macos";
            case LINUX -> "natives-linux";
        };
    }

    public String classpathSeparator() {
        return family == Family.WINDOWS ? ";" : ":";
    }

    public boolean isWindows() { return family == Family.WINDOWS; }

    /* ----------------------------------------------- launcher data dirs -- */

    private static Path dataDir;

    public static Path dataDir() {
        Path d = dataDir;
        if (d != null) return d;
        String override = System.getProperty("omnilauncher.data");
        if (override != null && !override.isBlank()) {
            d = Paths.get(override);
        } else if (get().family == Family.WINDOWS) {
            String appData = System.getenv("APPDATA");
            d = Paths.get(appData != null ? appData : System.getProperty("user.home"), "OmniLauncher");
        } else if (get().family == Family.MACOS) {
            d = Paths.get(System.getProperty("user.home"), "Library", "Application Support", "OmniLauncher");
        } else {
            String xdg = System.getenv("XDG_CONFIG_HOME");
            d = Paths.get(xdg != null && !xdg.isBlank() ? xdg : Paths.get(System.getProperty("user.home"), ".config").toString(), "omnilauncher");
        }
        dataDir = d;
        return d;
    }

    /** Only used by the headless preview/self-test modes to sandbox data. */
    public static void setDataDirForTests(Path p) { dataDir = p; }

    public static Path versionsDir() { return dir(dataDir(), "versions"); }
    public static Path assetsDir() { return dir(dataDir(), "assets"); }
    public static Path librariesDir() { return dir(dataDir(), "libraries"); }
    public static Path cacheDir() { return dir(dataDir(), "cache"); }
    public static Path logsDir() { return dir(dataDir(), "logs"); }
    public static Path accountsFile() { return dataDir().resolve("accounts.json"); }
    public static Path settingsFile() { return dataDir().resolve("settings.json"); }

    /**
     * Writes text atomically: to a sibling temp file first, then moved into
     * place. A crash mid-write can no longer truncate settings or accounts.
     */
    public static void atomicWriteString(Path target, String content) throws IOException {
        Files.createDirectories(target.getParent());
        Path tmp = target.resolveSibling(target.getFileName() + ".tmp");
        Files.writeString(tmp, content);
        try {
            Files.move(tmp, target, java.nio.file.StandardCopyOption.REPLACE_EXISTING,
                    java.nio.file.StandardCopyOption.ATOMIC_MOVE);
        } catch (java.nio.file.AtomicMoveNotSupportedException amnse) {
            Files.move(tmp, target, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        }
    }

    private static Path dir(Path base, String child) {
        Path p = base.resolve(child);
        try { Files.createDirectories(p); } catch (IOException ignored) {}
        return p;
    }

    /* --------------------------------------------------------- helpers -- */

    /** Opens a URI in the system browser; no-op when unsupported. */
    public static void openUri(String uri) {
        try {
            if (Desktop.isDesktopSupported() && Desktop.getDesktop().isSupported(Desktop.Action.BROWSE)) {
                Desktop.getDesktop().browse(URI.create(uri));
                return;
            }
        } catch (Throwable ignored) {}
        try {
            List<String> cmd = new ArrayList<>();
            switch (get().family) {
                case WINDOWS -> { cmd.add("rundll32"); cmd.add("url.dll,FileProtocolHandler"); cmd.add(uri); }
                case MACOS -> { cmd.add("open"); cmd.add(uri); }
                default -> { cmd.add("xdg-open"); cmd.add(uri); }
            }
            new ProcessBuilder(cmd).start();
        } catch (Throwable t) {
            Log.warn("Could not open browser for " + uri);
        }
    }

    /** Default game directory (.minecraft) per platform. */
    public static Path defaultGameDir() {
        if (get().isWindows()) {
            String appData = System.getenv("APPDATA");
            return Paths.get(appData != null ? appData : System.getProperty("user.home"), ".minecraft");
        }
        if (get().family == Family.MACOS)
            return Paths.get(System.getProperty("user.home"), "Library", "Application Support", "minecraft");
        return Paths.get(System.getProperty("user.home"), ".minecraft");
    }
}
