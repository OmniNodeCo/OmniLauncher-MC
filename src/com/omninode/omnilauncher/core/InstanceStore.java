package com.omninode.omnilauncher.core;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.omninode.omnilauncher.util.Json;
import com.omninode.omnilauncher.util.Log;
import com.omninode.omnilauncher.util.Os;

/**
 * Creates, lists and removes launcher instances. Persisted atomically in
 * {@code <data>/instances.json}; each instance's game folder lives at
 * {@code <data>/instances/<id>/game}.
 */
public final class InstanceStore {

    private static volatile List<Instance> cache;

    private InstanceStore() {}

    private static Path file() { return Os.dataDir().resolve("instances.json"); }

    /** All instances, newest-created last. */
    public static List<Instance> all() {
        List<Instance> c = cache;
        if (c != null) return c;
        synchronized (InstanceStore.class) {
            if (cache == null) load();
            return cache;
        }
    }

    public static Instance get(String id) {
        if (id == null) return null;
        for (Instance i : all()) if (i.id.equals(id)) return i;
        return null;
    }

    /**
     * Creates an instance; {@code name} must be non-blank and unique.
     * Returns the new instance or {@code null} when invalid/duplicate.
     */
    public static synchronized Instance create(String name, String versionId) {
        String n = name == null ? "" : name.trim();
        if (n.isEmpty() || n.length() > 40) return null;
        if (findByName(n) != null) return null;
        String id = slug(n) + "-" + Long.toHexString(System.currentTimeMillis() & 0xFFFF);
        Instance inst = new Instance(id, n, versionId == null ? "" : versionId,
                System.currentTimeMillis(), 0L);
        List<Instance> next = new ArrayList<>(all());
        next.add(inst);
        if (persist(next)) {
            cache = List.copyOf(next);
            Log.info("Instance created: " + inst + " [" + id + "] -> " + inst.gameDir());
            return inst;
        }
        return null;
    }

    /** Removes the instance from the store; its files are left on disk. */
    public static synchronized boolean remove(String id) {
        Instance target = get(id);
        if (target == null) return false;
        List<Instance> next = new ArrayList<>();
        for (Instance i : all()) if (!i.id.equals(id)) next.add(i);
        if (!persist(next)) return false;
        cache = List.copyOf(next);
        Log.info("Instance removed: " + target + " [" + id + "] (files kept at "
                + target.gameDir() + ")");
        return true;
    }

    /** Marks the instance as played now (also creates its game folder). */
    public static synchronized void touch(String id) {
        Instance i = get(id);
        if (i == null) return;
        List<Instance> next = new ArrayList<>();
        for (Instance x : all()) {
            if (x.id.equals(id)) {
                x.lastPlayed = System.currentTimeMillis();
                try {
                    Files.createDirectories(x.gameDir());
                } catch (Exception e) {
                    Log.warn("Could not create instance dir: " + e.getMessage());
                }
            }
            next.add(x);
        }
        if (persist(next)) cache = List.copyOf(next);
    }

    /** Case-insensitive unique-name lookup (used to reject duplicates). */
    public static Instance findByName(String name) {
        String n = name == null ? "" : name.trim().toLowerCase();
        for (Instance i : all()) if (i.name.toLowerCase().equals(n)) return i;
        return null;
    }

    /** Reloads from disk (also used by tests to verify persistence). */
    public static synchronized void reload() {
        synchronized (InstanceStore.class) {
            cache = null;
        }
        load();
    }

    private static void load() {
        List<Instance> out = new ArrayList<>();
        try {
            Path f = file();
            if (Files.exists(f)) {
                Map<String, Object> root = Json.parseObject(Files.readString(f));
                List<Object> arr = root == null ? null : Json.arr(root, "instances");
                if (arr != null) {
                    for (Object o : arr) {
                        Instance i = Instance.fromMap(Json.asMap(o));
                        if (i != null) out.add(i);
                    }
                }
            }
        } catch (Exception e) {
            Log.error("Could not read instances.json", e);
        }
        cache = List.copyOf(out);
    }

    private static boolean persist(List<Instance> list) {
        try {
            List<Object> arr = new ArrayList<>();
            for (Instance i : list) arr.add(i.toMap());
            Map<String, Object> root = new LinkedHashMap<>();
            root.put("version", 1);
            root.put("instances", arr);
            Os.atomicWriteString(file(), Json.write(root));
            return true;
        } catch (Exception e) {
            Log.error("Could not save instances.json", e);
            return false;
        }
    }

    /** Filesystem-safe, readable id from the display name. */
    public static String slug(String name) {
        StringBuilder sb = new StringBuilder();
        for (char c : name.toLowerCase().toCharArray()) {
            if (Character.isLetterOrDigit(c)) sb.append(c);
            else if (sb.length() > 0 && sb.charAt(sb.length() - 1) != '-') sb.append('-');
        }
        String s = sb.toString();
        while (s.startsWith("-")) s = s.substring(1);
        while (s.endsWith("-")) s = s.substring(0, s.length() - 1);
        return s.isEmpty() ? "instance" : s;
    }
}
