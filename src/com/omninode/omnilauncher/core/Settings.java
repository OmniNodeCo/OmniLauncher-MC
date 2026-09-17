package com.omninode.omnilauncher.core;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

import com.omninode.omnilauncher.util.Json;
import com.omninode.omnilauncher.util.Log;
import com.omninode.omnilauncher.util.Os;

/** Launcher settings, persisted as JSON. */
public class Settings {

    private static volatile Settings instance;

    public static Settings get() {
        Settings s = instance;
        if (s == null) {
            synchronized (Settings.class) {
                s = instance;
                if (s == null) instance = s = load();
            }
        }
        return s;
    }

    /* Java */
    public String javaPath = "";                 // empty = auto-detect
    public int memoryMb = 2048;                  // -Xmx
    public String extraJvmArgs = "";

    /* Game */
    public String gameDir = "";                  // empty = platform default .minecraft
    public int gameWidth = 854;
    public int gameHeight = 480;
    public boolean fullscreen = false;
    public String extraGameArgs = "";

    /* Content filters */
    public boolean showSnapshots = true;
    public boolean showHistorical = false;       // beta / alpha

    /* Launcher */
    public int concurrency = 10;
    public boolean keepLauncherOpen = true;
    public String msaClientId = "";
    public boolean firstRunCompleted = false;

    /* Window state */
    public int windowWidth = 1200;
    public int windowHeight = 740;
    public boolean windowMaximized = false;

    /* Selection */
    public String lastVersionId = "";            // empty = latest release

    /* ---------------------------------------------------------------- */

    public Path resolveGameDir() {
        if (gameDir == null || gameDir.isBlank()) return Os.defaultGameDir();
        return Path.of(gameDir);
    }

    public Map<String, Object> toMap() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("version", 2);
        m.put("javaPath", javaPath);
        m.put("memoryMb", memoryMb);
        m.put("extraJvmArgs", extraJvmArgs);
        m.put("gameDir", gameDir);
        m.put("gameWidth", gameWidth);
        m.put("gameHeight", gameHeight);
        m.put("fullscreen", fullscreen);
        m.put("extraGameArgs", extraGameArgs);
        m.put("showSnapshots", showSnapshots);
        m.put("showHistorical", showHistorical);
        m.put("concurrency", concurrency);
        m.put("keepLauncherOpen", keepLauncherOpen);
        m.put("msaClientId", msaClientId);
        m.put("firstRunCompleted", firstRunCompleted);
        m.put("windowWidth", windowWidth);
        m.put("windowHeight", windowHeight);
        m.put("windowMaximized", windowMaximized);
        m.put("lastVersionId", lastVersionId);
        return m;
    }

    public void fromMap(Map<String, Object> m) {
        javaPath = Json.str(m, "javaPath", javaPath);
        memoryMb = (int) Json.num(m, "memoryMb", memoryMb);
        extraJvmArgs = Json.str(m, "extraJvmArgs", extraJvmArgs);
        gameDir = Json.str(m, "gameDir", gameDir);
        gameWidth = (int) Json.num(m, "gameWidth", gameWidth);
        gameHeight = (int) Json.num(m, "gameHeight", gameHeight);
        fullscreen = Json.bool(m, "fullscreen", fullscreen);
        extraGameArgs = Json.str(m, "extraGameArgs", extraGameArgs);
        showSnapshots = Json.bool(m, "showSnapshots", showSnapshots);
        showHistorical = Json.bool(m, "showHistorical", showHistorical);
        concurrency = (int) Json.num(m, "concurrency", concurrency);
        keepLauncherOpen = Json.bool(m, "keepLauncherOpen", keepLauncherOpen);
        msaClientId = Json.str(m, "msaClientId", msaClientId);
        firstRunCompleted = Json.bool(m, "firstRunCompleted", firstRunCompleted);
        windowWidth = (int) Json.num(m, "windowWidth", windowWidth);
        windowHeight = (int) Json.num(m, "windowHeight", windowHeight);
        windowMaximized = Json.bool(m, "windowMaximized", windowMaximized);
        lastVersionId = Json.str(m, "lastVersionId", lastVersionId);
        clamp();
    }

    private void clamp() {
        memoryMb = Math.max(512, Math.min(32768, memoryMb));
        concurrency = Math.max(2, Math.min(16, concurrency));
        gameWidth = Math.max(320, gameWidth);
        gameHeight = Math.max(240, gameHeight);
    }

    public void save() {
        try {
            Files.writeString(Os.settingsFile(), Json.write(toMap()));
        } catch (Exception e) {
            Log.error("Could not save settings", e);
        }
    }

    public static Settings load() {
        Settings s = new Settings();
        try {
            Path f = Os.settingsFile();
            if (Files.exists(f)) s.fromMap(Json.parseObject(Files.readString(f)));
        } catch (Exception e) {
            Log.error("Could not load settings, using defaults", e);
        }
        s.clamp();
        return s;
    }

    public static void reload() { instance = load(); }
}
