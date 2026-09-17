package com.omninode.omnilauncher.core;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.omninode.omnilauncher.util.Json;
import com.omninode.omnilauncher.util.Os;

/**
 * Parsed Mojang version metadata (the per-version JSON from piston-meta).
 *
 * Handles both the modern "arguments" format and the legacy
 * "minecraftArguments" format, library rule evaluation, natives classifiers
 * (including the ${arch} placeholder) and variable substitution.
 */
public class VersionJson {

    /* ------------------------------------------------------------ types */

    public record Download(String url, String sha1, long size, String path) {}

    public record AssetIndexRef(String id, String url, String sha1, long totalSize,
                                boolean virtual, boolean mapToResources) {}

    public record LogConfigRef(String argument, String id, String url, String sha1, long size) {}

    public static final class Library {
        public String name;
        public List<Object> rulesRaw;
        public Download artifact;                    // main artifact
        public Map<String, Download> classifiers;    // natives variants
        /** os name (windows/linux/osx) → classifier pattern, e.g. "natives-windows-${arch}". */
        public Map<String, String> nativesMap;
        public List<String> extractExcludes = List.of();

        public boolean allowedByRules(Os os, Set<String> features) {
            return rulesAllow(rulesRaw, os, features);
        }

        /** Classifier key for this OS with ${arch} resolved. */
        public String nativesKey(Os os) {
            if (nativesMap == null) return null;
            String pattern = nativesMap.get(os.mojangName());
            if (pattern == null) return null;
            return pattern.replace("${arch}", os.arch.equals("x64") ? "64" : "32");
        }
    }

    public static final class ArgEntry {
        List<Object> rulesRaw;
        final List<String> values = new ArrayList<>();

        static ArgEntry from(Object o) {
            ArgEntry e = new ArgEntry();
            if (o instanceof String s) {
                e.values.add(s);
            } else {
                Map<String, Object> m = Json.asMap(o);
                if (m == null) return null;
                e.rulesRaw = Json.asList(m.get("rules"));
                Object value = m.get("value");
                if (value instanceof String s) e.values.add(s);
                else if (value instanceof List<?> l) for (Object v : l) if (v != null) e.values.add(String.valueOf(v));
            }
            return e.values.isEmpty() ? null : e;
        }

        public boolean allowed(Os os, Set<String> features) {
            return rulesAllow(rulesRaw, os, features);
        }
    }

    /* ---------------------------------------------------------- fields */

    public String id;
    public String type = "release";
    public String mainClass;
    public Download client;
    public AssetIndexRef assetIndex;
    public LogConfigRef logging;
    public List<Library> libraries = new ArrayList<>();
    public List<ArgEntry> jvmArgs = new ArrayList<>();
    public List<ArgEntry> gameArgs = new ArrayList<>();
    public String legacyMinecraftArguments;
    public int javaMajor;
    /** Mojang bundled JVM component, e.g. "java-runtime-gamma" (null on ancient versions). */
    public String javaComponent;

    public boolean isModern() { return legacyMinecraftArguments == null; }

    /* ---------------------------------------------------------- parsing */

    public static VersionJson parse(String json) {
        Map<String, Object> root = Json.parseObject(json);
        VersionJson v = new VersionJson();
        v.id = Json.str(root, "id", "?");
        v.type = Json.str(root, "type", "release");
        v.mainClass = Json.str(root, "mainClass", "");
        var downloads = Json.map(root, "downloads");
        if (downloads != null) v.client = readDownload(Json.map(downloads, "client"));
        var assetIndex = Json.map(root, "assetIndex");
        if (assetIndex != null) {
            v.assetIndex = new AssetIndexRef(Json.str(assetIndex, "id", "legacy"),
                    Json.str(assetIndex, "url", ""), Json.str(assetIndex, "sha1", null),
                    Json.num(assetIndex, "totalSize", 0),
                    Json.bool(assetIndex, "virtual", false),
                    Json.bool(assetIndex, "map_to_resources", false));
        }
        var logging = Json.map(root, "logging");
        if (logging != null) {
            var clientLog = Json.map(logging, "client");
            if (clientLog != null) {
                var file = Json.map(clientLog, "file");
                if (file != null)
                    v.logging = new LogConfigRef(Json.str(clientLog, "argument", "-Dlog4j.configurationFile=${path}"),
                            Json.str(file, "id", ""), Json.str(file, "url", ""),
                            Json.str(file, "sha1", null), Json.num(file, "size", 0));
            }
        }
        var javaVersion = Json.map(root, "javaVersion");
        if (javaVersion != null) {
            v.javaMajor = (int) Json.num(javaVersion, "majorVersion", 0);
            v.javaComponent = Json.str(javaVersion, "component", null);
        }

        for (Object o : Json.arr(root, "libraries")) {
            Library lib = parseLibrary(o);
            if (lib != null) v.libraries.add(lib);
        }

        var arguments = Json.map(root, "arguments");
        if (arguments != null) {
            readArgs(Json.arr(arguments, "jvm"), v.jvmArgs);
            readArgs(Json.arr(arguments, "game"), v.gameArgs);
        }
        v.legacyMinecraftArguments = Json.str(root, "minecraftArguments", null);
        if (v.legacyMinecraftArguments != null && v.gameArgs.isEmpty()) {
            for (String part : v.legacyMinecraftArguments.split("\\s+")) {
                ArgEntry e = new ArgEntry();
                e.values.add(part);
                v.gameArgs.add(e);
            }
        }
        return v;
    }

    private static Library parseLibrary(Object o) {
        Map<String, Object> m = Json.asMap(o);
        if (m == null) return null;
        Library lib = new Library();
        lib.name = Json.str(m, "name", "?");
        lib.rulesRaw = Json.asList(m.get("rules"));
        var downloads = Json.map(m, "downloads");
        if (downloads != null) {
            lib.artifact = readDownload(Json.map(downloads, "artifact"));
            var classifiers = Json.map(downloads, "classifiers");
            if (classifiers != null) {
                lib.classifiers = new LinkedHashMap<>();
                for (Map.Entry<String, Object> e : classifiers.entrySet()) {
                    Download d = readDownload(Json.asMap(e.getValue()));
                    if (d != null) lib.classifiers.put(e.getKey(), d);
                }
            }
        }
        Object natives = m.get("natives");
        if (natives instanceof Map) {
            Map<String, Object> nm = Json.asMap(natives);
            Map<String, String> out = new LinkedHashMap<>();
            for (Map.Entry<String, Object> e : nm.entrySet())
                out.put(e.getKey(), String.valueOf(e.getValue()));
            lib.nativesMap = out;
        } else if (natives instanceof String s) {
            lib.nativesMap = Map.of("windows", s, "linux", s, "osx", s);
        }
        var extract = Json.map(m, "extract");
        if (extract != null) {
            List<String> ex = new ArrayList<>();
            for (Object x : Json.arr(extract, "exclude")) ex.add(String.valueOf(x));
            lib.extractExcludes = ex;
        }
        return lib;
    }

    private static Download readDownload(Map<String, Object> m) {
        if (m == null) return null;
        return new Download(Json.str(m, "url", ""), Json.str(m, "sha1", null),
                Json.num(m, "size", -1), Json.str(m, "path", null));
    }

    private static void readArgs(List<Object> raw, List<ArgEntry> out) {
        if (raw == null) return;
        for (Object o : raw) {
            ArgEntry e = ArgEntry.from(o);
            if (e != null) out.add(e);
        }
    }

    /* ----------------------------------------------------------- rules */

    /** Mojang rule semantics: walk in order, last matching action wins. */
    public static boolean rulesAllow(List<?> rules, Os os, Set<String> features) {
        if (rules == null || rules.isEmpty()) return true;
        boolean result = false;
        for (Object r : rules) {
            Map<String, Object> m = Json.asMap(r);
            if (m == null) continue;
            if (!ruleMatches(m, os, features)) continue;
            result = "allow".equals(Json.str(m, "action", "allow"));
        }
        return result;
    }

    private static boolean ruleMatches(Map<String, Object> rule, Os os, Set<String> features) {
        Map<String, Object> osM = Json.map(rule, "os");
        if (osM != null) {
            String name = Json.str(osM, "name", null);
            if (name != null && !name.equals(os.mojangName())) return false;
            String arch = Json.str(osM, "arch", null);
            if (arch != null && !archMatches(arch, os)) return false;
        }
        Map<String, Object> feat = Json.map(rule, "features");
        if (feat != null) {
            for (Map.Entry<String, Object> e : feat.entrySet()) {
                boolean required = e.getValue() instanceof Boolean b && b;
                if (required && !features.contains(e.getKey())) return false;
                if (!required && features.contains(e.getKey())) return false;
            }
            // a feature-gated rule must not match when none of its features are active
            if (feat.isEmpty()) return false;
        }
        return true;
    }

    private static boolean archMatches(String arch, Os os) {
        return switch (arch) {
            case "arm64" -> os.arch.equals("arm64");
            case "x86" -> os.arch.equals("x86");
            case "x86_64", "x64" -> os.arch.equals("x64");
            default -> arch.equalsIgnoreCase(os.arch);
        };
    }

    /* ------------------------------------------------------ resolution */

    /** Resolves the modern JVM argument list with variables substituted. */
    public List<String> resolveJvmArgs(Os os, Set<String> features, Map<String, String> vars) {
        List<String> out = new ArrayList<>();
        for (ArgEntry e : jvmArgs) {
            if (!e.allowed(os, features)) continue;
            for (String v : e.values) out.add(substitute(v, vars));
        }
        return out;
    }

    /** Resolves the game argument list with variables substituted. */
    public List<String> resolveGameArgs(Os os, Set<String> features, Map<String, String> vars) {
        List<String> out = new ArrayList<>();
        for (ArgEntry e : gameArgs) {
            if (!e.allowed(os, features)) continue;
            for (String v : e.values) out.add(substitute(v, vars));
        }
        return out;
    }

    public static String substitute(String s, Map<String, String> vars) {
        if (s.indexOf("${") < 0) return s;
        StringBuilder sb = new StringBuilder(s.length() + 16);
        int i = 0;
        while (i < s.length()) {
            int start = s.indexOf("${", i);
            if (start < 0) { sb.append(s, i, s.length()); break; }
            int end = s.indexOf('}', start);
            if (end < 0) { sb.append(s, i, s.length()); break; }
            sb.append(s, i, start);
            String key = s.substring(start + 2, end);
            String val = vars.get(key);
            sb.append(val != null ? val : s.substring(start, end + 1));
            i = end + 1;
        }
        return sb.toString();
    }
}
