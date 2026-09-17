package com.omninode.omnilauncher.api;

import java.util.LinkedHashMap;
import java.util.Map;

import com.omninode.omnilauncher.model.Account;
import com.omninode.omnilauncher.util.Http;
import com.omninode.omnilauncher.util.Json;

/**
 * Microsoft account sign-in via the OAuth 2.0 device-code flow:
 *
 *   Microsoft → Xbox Live (XBL) → XSTS → minecraftservices.com → profile
 *
 * The user only needs to supply an Azure application (client) ID in
 * Settings → Accounts; the flow then runs entirely inside the launcher.
 */
public class MicrosoftAuth {

    /** Endpoints are mutable so tests can point the whole chain at a local fake. */
    public static volatile String DEVICE_CODE_URL =
            "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode";
    public static volatile String TOKEN_URL =
            "https://login.microsoftonline.com/consumers/oauth2/v2.0/token";
    private static final String SCOPE = "XboxLive.signin offline_access";

    public static volatile String XBL_AUTH_URL = "https://user.auth.xboxlive.com/user/authenticate";
    public static volatile String XSTS_AUTH_URL = "https://xsts.auth.xboxlive.com/xsts/authorize";
    public static volatile String MC_LOGIN_URL = "https://api.minecraftservices.com/authentication/login_with_xbox";
    public static volatile String MC_PROFILE_URL = "https://api.minecraftservices.com/minecraft/profile";

    /** Result of starting the device-code flow. */
    public record DeviceCode(String userCode, String verificationUri, String deviceCode, long interval, long expiresAt) {}

    /** States while polling for the user finishing sign-in in their browser. */
    public enum PollState { PENDING, SLOW_DOWN, EXPIRED, DECLINED, SUCCESS, FAILED }

    public record PollResult(PollState state, Account account, String errorDetail) {
        static PollResult pending() { return new PollResult(PollState.PENDING, null, null); }
        static PollResult failed(String detail) { return new PollResult(PollState.FAILED, null, detail); }
    }

    /* ------------------------------------------------------ device flow -- */

    public static DeviceCode startDeviceCode(String clientId) throws Exception {
        byte[] resp = Http.postForm(DEVICE_CODE_URL, Map.of("client_id", clientId, "scope", SCOPE));
        var m = Json.parseObject(new String(resp, java.nio.charset.StandardCharsets.UTF_8));
        if (m.containsKey("error"))
            throw new IllegalStateException("Microsoft: " + Json.str(m, "error_description", Json.str(m, "error", "error")));
        long interval = Json.num(m, "interval", 5);
        long expiresIn = Json.num(m, "expires_in", 900);
        return new DeviceCode(Json.str(m, "user_code", ""), Json.str(m, "verification_uri", "https://www.microsoft.com/link"),
                Json.str(m, "device_code", ""), interval, System.currentTimeMillis() + expiresIn * 1000);
    }

    public static PollResult pollDeviceCode(String clientId, DeviceCode dc) {
        try {
            Http.Response resp = Http.postFormRaw(TOKEN_URL, Map.of(
                    "grant_type", "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id", clientId,
                    "device_code", dc.deviceCode()));
            var m = Json.parseObject(resp.text());
            if (resp.ok()) {
                String msAccessToken = Json.str(m, "access_token", "");
                String refreshToken = Json.str(m, "refresh_token", "");
                long expiresIn = Json.num(m, "expires_in", 3600);
                Account acc = completeSignIn(msAccessToken, refreshToken, expiresIn);
                return new PollResult(PollState.SUCCESS, acc, null);
            }
            String err = Json.str(m, "error", "");
            return switch (err) {
                case "authorization_pending" -> PollResult.pending();
                case "slow_down" -> new PollResult(PollState.SLOW_DOWN, null, null);
                case "expired_token" -> new PollResult(PollState.EXPIRED, null, "The sign-in code expired — try again.");
                case "authorization_declined" -> new PollResult(PollState.DECLINED, null, "Sign-in was declined.");
                default -> PollResult.failed("Microsoft: " + Json.str(m, "error_description", err));
            };
        } catch (Exception e) {
            return PollResult.failed(e.getMessage());
        }
    }

    /** Refresh an existing Microsoft account's tokens. */
    public static Account refresh(Account old) throws Exception {
        String clientId = com.omninode.omnilauncher.core.Settings.get().msaClientId;
        if (clientId == null || clientId.isBlank())
            throw new IllegalStateException("No Microsoft client ID configured (Settings → Accounts).");
        Http.Response resp = Http.postFormRaw(TOKEN_URL, Map.of(
                "grant_type", "refresh_token",
                "client_id", clientId,
                "refresh_token", old.getRefreshToken(),
                "scope", SCOPE));
        var m = Json.parseObject(resp.text());
        if (!resp.ok())
            throw new IllegalStateException("Token refresh failed: " + Json.str(m, "error_description", "HTTP " + resp.status()));
        String msAccessToken = Json.str(m, "access_token", "");
        String refreshToken = Json.str(m, "refresh_token", old.getRefreshToken());
        long expiresIn = Json.num(m, "expires_in", 3600);
        return completeSignIn(msAccessToken, refreshToken, expiresIn);
    }

    /* ------------------------------------------------- full auth chain -- */

    /** msAccessToken → XBL → XSTS → Minecraft token + profile → Account. */
    public static Account completeSignIn(String msAccessToken, String refreshToken, long expiresIn) throws Exception {
        Map<String, Object> xblProps = new LinkedHashMap<>();
        xblProps.put("AuthMethod", "RPS");
        xblProps.put("SiteName", "user.auth.xboxlive.com");
        xblProps.put("RpsTicket", "d=" + msAccessToken);
        Map<String, Object> xblBody = new LinkedHashMap<>();
        xblBody.put("Properties", xblProps);
        xblBody.put("RpsTicket", "d=" + msAccessToken);
        var xblResp = Json.parseObject(new String(Http.postJson(XBL_AUTH_URL, Json.write(xblBody))));
        String xblToken = Json.str(xblResp, "Token", "");
        String uhs = "";
        var displayClaims = Json.map(xblResp, "DisplayClaims");
        if (displayClaims != null) {
            var xui = Json.arr(displayClaims, "xui");
            if (xui != null && !xui.isEmpty()) {
                var first = Json.asMap(xui.get(0));
                if (first != null) uhs = Json.str(first, "uhs", "");
            }
        }
        if (xblToken.isBlank() || uhs.isBlank()) throw new IllegalStateException("Xbox Live authentication failed.");

        Map<String, Object> xstsProps = new LinkedHashMap<>();
        xstsProps.put("SandboxId", "RETAIL");
        xstsProps.put("UserTokens", java.util.List.of(xblToken));
        Map<String, Object> xstsBody = new LinkedHashMap<>();
        xstsBody.put("Properties", xstsProps);
        xstsBody.put("RpsTicket", "");
        Http.Response xstsRaw = Http.postJsonRaw(XSTS_AUTH_URL, Json.write(xstsBody));
        var xstsResp = Json.parseObject(xstsRaw.text());
        String xstsToken = Json.str(xstsResp, "Token", "");
        if (xstsToken.isBlank()) {
            long xerr = Json.num(xstsResp, "XErr", 0);
            String msg;
            if (xerr == 2148916233L) msg = "This Microsoft account has no Xbox profile. Create one at xbox.com first.";
            else if (xerr == 2148916235L) msg = "Xbox Live is not available in your country.";
            else if (xerr == 2148916236L || xerr == 2148916237L) msg = "Adult verification is required on this Xbox account.";
            else if (xerr == 2148916238L) msg = "This account is a child account and cannot play Minecraft.";
            else msg = "Xbox authentication failed (code " + xerr + ").";
            throw new IllegalStateException(msg);
        }
        var xstsClaims = Json.map(xstsResp, "DisplayClaims");
        if (xstsClaims != null) {
            var xui = Json.arr(xstsClaims, "xui");
            if (xui != null && !xui.isEmpty()) {
                var first = Json.asMap(xui.get(0));
                if (first != null) uhs = Json.str(first, "uhs", uhs);
            }
        }

        Map<String, Object> mcBody = new LinkedHashMap<>();
        mcBody.put("identityToken", "XBL3.0 x=" + uhs + ";" + xstsToken);
        var mcResp = Json.parseObject(new String(Http.postJson(MC_LOGIN_URL, Json.write(mcBody))));
        String mcToken = Json.str(mcResp, "access_token", "");
        long mcExpiresIn = Json.num(mcResp, "expires_in", 86400);
        if (mcToken.isBlank()) throw new IllegalStateException("Minecraft sign-in failed (no token).");

        byte[] profileRaw = Http.get(MC_PROFILE_URL, Map.of("Authorization", "Bearer " + mcToken));
        var profile = Json.parseObject(new String(profileRaw, java.nio.charset.StandardCharsets.UTF_8));
        String name = Json.str(profile, "name", null);
        String id = Json.str(profile, "id", null);
        if (name == null || id == null)
            throw new IllegalStateException("This Microsoft account does not own Minecraft: Java Edition.");
        String skinUrl = null;
        var skins = Json.arr(profile, "skins");
        if (skins != null && !skins.isEmpty()) {
            for (Object s : skins) {
                var sm = Json.asMap(s);
                if (sm != null && "ACTIVE".equalsIgnoreCase(Json.str(sm, "state", ""))) {
                    skinUrl = Json.str(sm, "url", null);
                    break;
                }
            }
        }
        long expiresAt = System.currentTimeMillis()
                + Math.min(mcExpiresIn, expiresIn) * 1000 - 60_000;
        return Account.microsoft(name, id, mcToken, refreshToken, expiresAt, skinUrl);
    }
}
