package com.omninode.omnilauncher.core;

import java.util.LinkedHashMap;
import java.util.Map;

import com.omninode.omnilauncher.util.Json;
import com.omninode.omnilauncher.util.Os;

/**
 * A named launcher instance: one pinned Minecraft version with its own game
 * folder (saves, configs, screenshots), like MultiMC/Prism instances. Game
 * files (jar/libraries/assets) are shared between instances to save disk.
 */
public final class Instance {

    public final String id;
    public String name;
    public String versionId;
    public long created;
    public long lastPlayed;

    public Instance(String id, String name, String versionId, long created, long lastPlayed) {
        this.id = id;
        this.name = name;
        this.versionId = versionId;
        this.created = created;
        this.lastPlayed = lastPlayed;
    }

    /** The instance's isolated game folder (saves/configs/screenshots). */
    public java.nio.file.Path gameDir() {
        return Os.instancesDir().resolve(id).resolve("game");
    }

    public Map<String, Object> toMap() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", id);
        m.put("name", name);
        m.put("versionId", versionId);
        m.put("created", created);
        m.put("lastPlayed", lastPlayed);
        return m;
    }

    public static Instance fromMap(Map<String, Object> m) {
        if (m == null) return null;
        String id = Json.str(m, "id", null);
        String name = Json.str(m, "name", null);
        if (id == null || id.isBlank() || name == null || name.isBlank()) return null;
        return new Instance(id, name,
                Json.str(m, "versionId", ""),
                Json.num(m, "created", 0L),
                Json.num(m, "lastPlayed", 0L));
    }

    @Override public String toString() { return name + " (" + versionId + ")"; }
}
