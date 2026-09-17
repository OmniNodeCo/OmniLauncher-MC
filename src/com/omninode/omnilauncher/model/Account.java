package com.omninode.omnilauncher.model;

import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.UUID;

import com.omninode.omnilauncher.util.Json;

/** A player account, either offline or Microsoft-authenticated. */
public class Account {

    public enum Type { OFFLINE, MICROSOFT }

    private Type type;
    private String name;
    private String uuid;
    private String accessToken;
    private String refreshToken; // Microsoft accounts only
    private long expiresAt;      // epoch millis
    private String skinUrl;

    public static Account offline(String name) {
        Account a = new Account();
        a.type = Type.OFFLINE;
        a.name = name.trim();
        a.uuid = UUID.nameUUIDFromBytes(("OfflinePlayer:" + a.name).getBytes(StandardCharsets.UTF_8)).toString();
        a.accessToken = "0";
        a.expiresAt = Long.MAX_VALUE;
        return a;
    }

    public static Account microsoft(String name, String uuid, String accessToken, String refreshToken,
                                    long expiresAt, String skinUrl) {
        Account a = new Account();
        a.type = Type.MICROSOFT;
        a.name = name;
        a.uuid = dashed(uuid);
        a.accessToken = accessToken;
        a.refreshToken = refreshToken;
        a.expiresAt = expiresAt;
        a.skinUrl = skinUrl;
        return a;
    }

    public boolean isMicrosoft() { return type == Type.MICROSOFT; }

    public boolean needsRefresh() {
        return isMicrosoft() && refreshToken != null && System.currentTimeMillis() > expiresAt - 60_000;
    }

    /* -------------------------------------------------- serialization -- */

    public Map<String, Object> toMap() {
        Map<String, Object> m = new java.util.LinkedHashMap<>();
        m.put("type", type == Type.MICROSOFT ? "microsoft" : "offline");
        m.put("name", name);
        m.put("uuid", uuid);
        m.put("accessToken", accessToken);
        if (refreshToken != null) m.put("refreshToken", refreshToken);
        m.put("expiresAt", expiresAt);
        if (skinUrl != null) m.put("skinUrl", skinUrl);
        return m;
    }

    public static Account fromMap(Map<String, Object> m) {
        String type = Json.str(m, "type", "offline");
        if (type.equals("microsoft")) {
            return microsoft(Json.str(m, "name", "?"), Json.str(m, "uuid", ""),
                    Json.str(m, "accessToken", ""), Json.str(m, "refreshToken", null),
                    Json.num(m, "expiresAt", 0), Json.str(m, "skinUrl", null));
        }
        return offline(Json.str(m, "name", "Player"));
    }

    /* ------------------------------------------------------- helpers -- */

    public static String dashed(String uuid) {
        if (uuid == null || uuid.contains("-") || uuid.length() != 32) return uuid;
        return uuid.replaceFirst("(\\w{8})(\\w{4})(\\w{4})(\\w{4})(\\w{12})", "$1-$2-$3-$4-$5");
    }

    public static String undashed(String uuid) {
        return uuid == null ? null : uuid.replace("-", "");
    }

    /* ------------------------------------------------- getters/setters */

    public Type getType() { return type; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getUuid() { return uuid; }
    public String getAccessToken() { return accessToken; }
    public void setAccessToken(String accessToken) { this.accessToken = accessToken; }
    public String getRefreshToken() { return refreshToken; }
    public long getExpiresAt() { return expiresAt; }
    public void setExpiresAt(long expiresAt) { this.expiresAt = expiresAt; }
    public String getSkinUrl() { return skinUrl; }
    public void setSkinUrl(String skinUrl) { this.skinUrl = skinUrl; }
}
