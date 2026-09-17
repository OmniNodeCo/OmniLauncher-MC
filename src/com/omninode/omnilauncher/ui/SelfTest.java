package com.omninode.omnilauncher.ui;

import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import com.omninode.omnilauncher.api.MicrosoftAuth;
import com.omninode.omnilauncher.api.NewsService;
import com.omninode.omnilauncher.api.VersionManifest;
import com.omninode.omnilauncher.core.RuntimeManager;
import com.omninode.omnilauncher.core.Settings;
import com.omninode.omnilauncher.core.VersionInstaller;
import com.omninode.omnilauncher.core.VersionJson;
import com.omninode.omnilauncher.core.GameLauncher;
import com.omninode.omnilauncher.util.Http;
import com.omninode.omnilauncher.model.Account;
import com.omninode.omnilauncher.util.Json;
import com.omninode.omnilauncher.util.Os;

/**
 * Offline test suite: exercises the JSON parser, Mojang rule engine,
 * version metadata parsing, argument substitution, manifest/news models,
 * the Microsoft auth response shapes and the settings store.
 * Run with: java -jar OmniLauncher.jar --selftest
 */
public final class SelfTest {

    private static int passed, failed;

    private SelfTest() {}

    /* ------------------------------------------------------------ fixtures */

    private static final String VERSION_JSON = """
    {
      "id": "1.21.9", "type": "release",
      "mainClass": "net.minecraft.client.main.Main",
      "releaseTime": "2026-07-28T09:41:00+00:00",
      "arguments": {
        "jvm": [
          "-Djava.library.path=${natives_directory}",
          { "rules": [ { "action": "allow", "os": { "name": "osx" } } ], "value": "-XstartOnFirstThread" },
          "-Dminecraft.launcher.brand=${launcher_name}",
          "-Dminecraft.launcher.version=${launcher_version}",
          "-cp", "${classpath}"
        ],
        "game": [
          "--username", "${auth_player_name}", "--version", "${version_name}",
          "--gameDir", "${game_directory}", "--assetsDir", "${assets_root}",
          "--assetIndex", "${assets_index_name}", "--uuid", "${auth_uuid}",
          "--accessToken", "${auth_access_token}", "--clientId", "${clientid}",
          "--xuid", "${auth_xuid}", "--userType", "${user_type}",
          "--versionType", "${version_type}",
          { "rules": [ { "action": "allow", "features": { "has_custom_resolution": true } } ],
            "value": [ "--width", "${resolution_width}", "--height", "${resolution_height}" ] }
        ]
      },
      "javaVersion": { "component": "java-runtime-gamma", "majorVersion": 21 },
      "assetIndex": { "id": "17", "url": "https://piston-meta.mojang.com/v1/packages/aa/17.json", "sha1": "aabbccddeeff00112233445566778899aabbccdd", "totalSize": 409600, "virtual": false },
      "downloads": {
        "client": { "sha1": "1111111111111111111111111111111111111111", "size": 26342400,
                    "url": "https://piston-data.mojang.com/v1/objects/11/client.jar" }
      },
      "logging": {
        "client": { "argument": "-Dlog4j.configurationFile=${path}",
          "file": { "id": "client-1.12.xml", "sha1": "2222222222222222222222222222222222222222", "size": 905,
                    "url": "https://piston-data.mojang.com/v1/objects/22/client-1.12.xml" } }
      },
      "libraries": [
        { "name": "com.google.guava:guava:32.1.2-jre",
          "downloads": { "artifact": { "path": "com/google/guava/guava/32.1.2-jre/guava-32.1.2-jre.jar",
            "sha1": "3333333333333333333333333333333333333333", "size": 100,
            "url": "https://libraries.minecraft.net/com/google/guava/guava/32.1.2-jre/guava-32.1.2-jre.jar" } } },
        { "name": "org.lwjgl:lwjgl:3.3.3",
          "downloads": { "artifact": { "path": "org/lwjgl/lwjgl/3.3.3/lwjgl-3.3.3.jar",
            "sha1": "4444444444444444444444444444444444444444", "size": 100,
            "url": "https://libraries.minecraft.net/org/lwjgl/lwjgl/3.3.3/lwjgl-3.3.3.jar" },
            "classifiers": {
              "natives-linux":   { "sha1": "5555555555555555555555555555555555555555", "size": 100, "url": "https://libraries.minecraft.net/lwjgl-linux.jar" },
              "natives-windows": { "sha1": "6666666666666666666666666666666666666666", "size": 100, "url": "https://libraries.minecraft.net/lwjgl-windows.jar" },
              "natives-macos":   { "sha1": "7777777777777777777777777777777777777777", "size": 100, "url": "https://libraries.minecraft.net/lwjgl-macos.jar" } } },
          "rules": [ { "action": "allow" }, { "action": "disallow", "os": { "name": "linux", "arch": "arm64" } } ],
          "natives": { "linux": "natives-linux", "windows": "natives-windows", "osx": "natives-macos" } },
        { "name": "ca.weblite:java-objc-bridge:1.0.0",
          "downloads": { "artifact": { "path": "ca/weblite/java-objc-bridge/1.0.0/java-objc-bridge-1.0.0.jar",
            "sha1": "8888888888888888888888888888888888888888", "size": 100,
            "url": "https://libraries.minecraft.net/objc.jar" } },
          "rules": [ { "action": "allow", "os": { "name": "osx" } } ] },
        { "name": "com.mojang:text2speech:1.17.9",
          "downloads": { "artifact": { "path": "com/mojang/text2speech/1.17.9/text2speech-1.17.9.jar",
            "sha1": "9999999999999999999999999999999999999999", "size": 100,
            "url": "https://libraries.minecraft.net/t2s.jar" },
            "classifiers": {
              "natives-windows": { "sha1": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "size": 100, "url": "https://libraries.minecraft.net/t2s-win.jar" },
              "n-windows-${arch}": { "sha1": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "size": 100, "url": "https://libraries.minecraft.net/t2s-win-arch.jar" } } },
          "natives": "n-windows-${arch}" }
      ]
    }
    """;

    private static final String LEGACY_VERSION_JSON = """
    {
      "id": "1.5.2", "type": "release", "mainClass": "net.minecraft.client.Minecraft",
      "minecraftArguments": "${auth_player_name} ${auth_session} --gameDir ${game_directory} --version ${version_name}",
      "minimumLauncherVersion": 2,
      "assets": "pre-1.6",
      "libraries": [
        { "name": "net.java.jinput:jinput:2.0.5",
          "downloads": { "artifact": { "path": "net/java/jinput/jinput/2.0.5/jinput-2.0.5.jar",
            "sha1": "39c7796b469a600f72380316f6b1f11db6c2c7c4", "size": 100,
            "url": "https://libraries.minecraft.net/jinput.jar" } } }
      ]
    }
    """;

    private static final String MANIFEST_JSON = """
    {
      "latest": { "release": "1.21.9", "snapshot": "25w45a" },
      "versions": [
        { "id": "25w45a", "type": "snapshot", "url": "u3", "time": "t", "releaseTime": "2026-08-05T00:00:00+00:00" },
        { "id": "1.21.9", "type": "release", "url": "u2", "time": "t", "releaseTime": "2026-07-28T00:00:00+00:00", "sha1": "abc" },
        { "id": "1.5.2", "type": "release", "url": "u1", "time": "t", "releaseTime": "2013-04-25T00:00:00+00:00" },
        { "id": "b1.7.3", "type": "old_beta", "url": "u0", "time": "t", "releaseTime": "2011-07-08T00:00:00+00:00" }
      ]
    }
    """;

    private static final String NEWS_JSON = """
    [
      { "title": "Big Update", "date": "2026-07-28T09:41:00+00:00", "category": "release",
        "shortText": "Short", "longText": "<p>Long body</p>",
        "image": { "url": "https://launchercontent.mojang.com/v2/images/x.jpg" } },
      { "title": "Relative Image", "date": "2026-08-01T00:00:00+00:00", "category": "snapshot",
        "shortText": "s2", "longText": "l2", "image": "/v2/images/y.jpg" }
    ]
    """;

    /* --------------------------------------------------------------- run */

    public static int run() {
        long t0 = System.currentTimeMillis();
        System.out.println("OmniLauncher self-test");
        System.out.println("======================");

        jsonTests();
        substitutionTests();
        rulesTests();
        versionJsonTests();
        manifestTests();
        newsTests();
        authShapeTests();
        accountTests();
        settingsTests();
        argSplitTests();
        try {
            installPipelineTests();
            gameCommandTests();
            runtimeTests();
        } catch (Throwable t) {
            failed++;
            System.out.println("FAIL  install pipeline threw: " + t);
            t.printStackTrace(System.out);
        }

        System.out.println();
        System.out.printf("%d passed, %d failed (%d ms)%n", passed, failed,
                System.currentTimeMillis() - t0);
        return failed == 0 ? 0 : 1;
    }

    /* ------------------------------------------------------------- tests */

    private static void jsonTests() {
        var m = Json.parseObject("""
            {"a":1, "b":2.5, "c":[1,"two",{"d":null}], "e":"x\\ny\\u00e9", "f":true, "g":-17}""");
        eq(1L, Json.num(m, "a", 0), "json int");
        eq(2.5, Json.dbl(m, "b", 0), "json double");
        eq(true, Json.bool(m, "f", false), "json bool");
        eq(-17L, Json.num(m, "g", 0), "json negative");
        eq("x\ny\u00e9", Json.str(m, "e", ""), "json escapes");
        var arr = Json.arr(m, "c");
        eq(3, arr.size(), "json array size");
        eq(null, arr.get(2) instanceof Map ? null : "notmap", "json nested map");
        var ordered = new LinkedHashMap<String, Object>();
        ordered.put("a", 1L);
        ordered.put("e", "x\ny\u00e9");
        eq("{\"a\":1,\"e\":\"x\\ny\u00e9\"}",
                Json.write(ordered), "json serialize");
        // tolerate unquoted parses failing: parser must throw on garbage
        try { Json.parse("{nope}"); fail("json rejects garbage"); }
        catch (Exception ok) { pass("json rejects garbage"); }
    }

    private static void substitutionTests() {
        var vars = Map.of("classpath", "/a.jar:/b.jar", "version_name", "1.21.9");
        eq("-cp -Dx=/a.jar:/b.jar",
                VersionJson.substitute("-cp -Dx=${classpath}", vars).replace("${missing}", ""),
                "substitute basic");
        eq("${unknown}", VersionJson.substitute("${unknown}", vars), "substitute keeps unknown");
    }

    private static void rulesTests() {
        Os linuxX64 = Os.of(Os.Family.LINUX, "x64");
        Os osxArm = Os.of(Os.Family.MACOS, "arm64");
        Os linuxArm = Os.of(Os.Family.LINUX, "arm64");

        var osxOnly = List.of(
                Map.of("action", "allow", "os", Map.of("name", "osx")));
        eq(false, VersionJson.rulesAllow(osxOnly, linuxX64, Set.of()), "rule osx vs linux");
        eq(true, VersionJson.rulesAllow(osxOnly, osxArm, Set.of()), "rule osx vs osx");

        var notLinuxArm = List.of(
                Map.of("action", "allow"),
                Map.of("action", "disallow", "os", Map.of("name", "linux", "arch", "arm64")));
        eq(true, VersionJson.rulesAllow(notLinuxArm, linuxX64, Set.of()), "rule disallow arm keeps x64");
        eq(false, VersionJson.rulesAllow(notLinuxArm, linuxArm, Set.of()), "rule disallow arm blocks arm");

        var resolution = List.of(
                Map.of("action", "allow", "features", Map.of("has_custom_resolution", true)));
        eq(false, VersionJson.rulesAllow(resolution, linuxX64, Set.of()), "feature absent → no match");
        eq(true, VersionJson.rulesAllow(resolution, linuxX64, Set.of("has_custom_resolution")),
                "feature present → match");
    }

    private static void versionJsonTests() {
        VersionJson v = VersionJson.parse(VERSION_JSON);
        eq("1.21.9", v.id, "version id");
        eq("net.minecraft.client.main.Main", v.mainClass, "main class");
        eq(21, v.javaMajor, "java major");
        eq(4, v.libraries.size(), "library count");
        eq("1111111111111111111111111111111111111111", v.client.sha1(), "client sha1");
        eq(true, v.isModern(), "modern version has arguments");

        Os linux = Os.of(Os.Family.LINUX, "x64");
        var features = Set.of("has_custom_resolution");
        var vars = new LinkedHashMap<String, String>();
        vars.put("classpath", "/client.jar");
        vars.put("natives_directory", "/tmp/natives");
        vars.put("launcher_name", "OmniLauncher");
        vars.put("launcher_version", "2.0.0");

        List<String> jvm = v.resolveJvmArgs(linux, Set.of(), vars);
        eq(true, jvm.contains("-Djava.library.path=/tmp/natives"), "jvm natives dir");
        eq(false, jvm.contains("-XstartOnFirstThread"), "jvm osx-only excluded on linux");
        eq(true, jvm.contains("-Dminecraft.launcher.brand=OmniLauncher"), "jvm brand substitution");
        eq(true, jvm.contains("/client.jar"), "jvm classpath entry");

        List<String> game = v.resolveGameArgs(linux, features, Map.of(
                "auth_player_name", "Steve", "resolution_width", "854", "resolution_height", "480"));
        eq(true, game.contains("Steve"), "game player name");
        eq(true, game.contains("--width") && game.contains("854"), "game resolution feature");

        Os osx = Os.of(Os.Family.MACOS, "arm64");
        List<String> jvmOsx = v.resolveJvmArgs(osx, Set.of(), vars);
        eq(true, jvmOsx.contains("-XstartOnFirstThread"), "jvm osx-only allowed on osx");

        // natives classifier per OS
        Os win = Os.of(Os.Family.WINDOWS, "x64");
        VersionJson.Library lwjgl = v.libraries.get(1);
        eq("natives-windows", lwjgl.nativesKey(win), "windows natives key");
        eq("natives-linux", lwjgl.nativesKey(linux), "linux natives key");
        eq("natives-macos", lwjgl.nativesKey(osx), "macos natives key");
        eq(true, lwjgl.allowedByRules(win, Set.of()), "lwjgl allowed on windows");
        eq(true, lwjgl.allowedByRules(linux, Set.of()), "lwjgl allowed on linux x64");
        eq(false, lwjgl.allowedByRules(Os.of(Os.Family.LINUX, "arm64"), Set.of()), "lwjgl blocked linux-arm64");

        VersionJson.Library t2s = v.libraries.get(3);
        eq("n-windows-64", t2s.nativesKey(win), "${arch} resolves to 64");
        eq(true, t2s.allowedByRules(win, Set.of()), "unruly lib allowed");
        eq(true, lwjgl.allowedByRules(Os.of(Os.Family.LINUX, "x64"), Set.of()), "lwjgl linux x64 allowed");

        // legacy path
        VersionJson legacy = VersionJson.parse(LEGACY_VERSION_JSON);
        eq(false, legacy.isModern(), "legacy detection");
        eq(true, legacy.resolveGameArgs(linux, Set.of(), Map.of("auth_player_name", "X")).contains("X"),
                "legacy args split");
    }

    private static void manifestTests() {
        VersionManifest.parse(MANIFEST_JSON);
        eq(4, VersionManifest.entries().size(), "manifest count");
        eq("1.21.9", VersionManifest.latestRelease(), "manifest latest release");
        eq("25w45a", VersionManifest.latestSnapshot(), "manifest latest snapshot");
        eq("25w45a", VersionManifest.entries().get(0).id(), "manifest sorted newest first");
        eq("abc", VersionManifest.byId("1.21.9").sha1(), "manifest sha1");
        var visible = VersionManifest.visibleEntries(true, false);
        eq(3, visible.size(), "visible without historical");
        var withOld = VersionManifest.visibleEntries(true, true);
        eq(4, withOld.size(), "visible with historical");
        eq("1.21.9", VersionManifest.resolveSelected("").id(), "resolve default → latest release");
        eq("1.5.2", VersionManifest.resolveSelected("1.5.2").id(), "resolve by id");
    }

    private static void newsTests() {
        NewsService.parse(NEWS_JSON);
        eq(2, NewsService.items().size(), "news count");
        eq("Big Update", NewsService.items().get(0).title(), "news title");
        eq("https://launchercontent.mojang.com/v2/images/y.jpg",
                NewsService.items().get(1).imageUrl(), "news relative image resolved");
        eq(true, NewsService.items().get(0).formattedDate().contains("2026"), "news date format");
    }

    private static void authShapeTests() {
        // device-code response shape
        var dc = Json.parseObject("""
            {"user_code":"ABCD-EFGH","device_code":"xyz","verification_uri":"https://www.microsoft.com/link",
             "expires_in":900,"interval":5,"message":"msg"}""");
        eq("ABCD-EFGH", Json.str(dc, "user_code", ""), "device code user_code");

        // pending poll shape
        var pending = Json.parseObject("{\"error\":\"authorization_pending\"}");
        eq("authorization_pending", Json.str(pending, "error", ""), "poll pending");

        // XBL response shape
        var xbl = Json.parseObject("""
            {"IssueInstant":"2026","NotAfter":"2026","Token":"tkt",
             "DisplayClaims":{"xui":[{"uhs":"12345"}]}}""");
        eq("tkt", Json.str(xbl, "Token", ""), "xbl token");
        var xui = Json.arr(Json.map(xbl, "DisplayClaims"), "xui");
        eq("12345", Json.str(Json.asMap(xui.get(0)), "uhs", ""), "xbl uhs");

        // XSTS error shape
        var xstsErr = Json.parseObject("{\"XErr\":2148916233,\"Redirect\":\"xbox\",\"Identity\":\"0\"}");
        eq(2148916233L, Json.num(xstsErr, "XErr", 0), "xsts XErr as long");

        // MC login + profile shapes
        var mc = Json.parseObject("{\"access_token\":\"mc.tok\",\"expires_in\":86400}");
        eq("mc.tok", Json.str(mc, "access_token", ""), "mc token");
        var profile = Json.parseObject("""
            {"id":"770c88d14dac553db02f99e9a488f83e","name":"Steve",
             "skins":[{"id":"s","state":"ACTIVE","url":"https://textures.minecraft.net/x.png"}]}""");
        eq("Steve", Json.str(profile, "name", ""), "profile name");
        eq("770c88d1-4dac-553d-b02f-99e9a488f83e",
                Account.dashed(Json.str(profile, "id", "")), "profile uuid dashed");

        eq(MicrosoftAuth.PollState.PENDING,
                new MicrosoftAuth.PollResult(MicrosoftAuth.PollState.PENDING, null, null).state(),
                "poll state passthrough");
    }

    private static void accountTests() {
        Account a = Account.offline("Steve");
        eq("5627dd98-e6be-3c21-b8a8-e92344183641", a.getUuid(), "offline uuid (OfflinePlayer:Steve)");
        eq("OFFLINE", a.getType().name(), "offline type");
        eq(false, a.isMicrosoft(), "not microsoft");

        Account m = Account.microsoft("Alex", "770c88d14dac553db02f99e9a488f83e",
                "tok", "ref", System.currentTimeMillis() + 100000, null);
        eq("770c88d1-4dac-553d-b02f-99e9a488f83e", m.getUuid(), "msa dashed uuid");
        var roundtrip = Account.fromMap(m.toMap());
        eq(m.getUuid(), roundtrip.getUuid(), "account roundtrip");
        eq("ref", roundtrip.getRefreshToken(), "account roundtrip refresh");

        Account shortOne = Account.offline("bob");
        eq("bob", shortOne.getName(), "offline name");
    }

    private static void settingsTests() {
        Settings s = new Settings();
        s.memoryMb = 8192;
        s.showSnapshots = false;
        s.msaClientId = "00000000-0000-0000-0000-000000000000";
        Settings s2 = new Settings();
        s2.fromMap(s.toMap());
        eq(8192, s2.memoryMb, "settings roundtrip memory");
        eq(false, s2.showSnapshots, "settings roundtrip flag");
        eq("00000000-0000-0000-0000-000000000000", s2.msaClientId, "settings roundtrip client id");
        s2.fromMap(Map.of("memoryMb", 999999));
        eq(32768, s2.memoryMb, "settings clamp max");
        s2.fromMap(Map.of("memoryMb", 1));
        eq(512, s2.memoryMb, "settings clamp min");
    }

    private static void argSplitTests() {
        var parts = GameLauncher.splitArgs("-Xmx2G -Dfoo=\"two words\" --end");
        eq(3, parts.size(), "arg split count");
        eq("-Dfoo=two words", parts.get(1), "arg split quoted");
    }

    /* ---------------------------------------------- integration pipeline */

    /** End-to-end: manifest entry → version json → downloads → natives → assets. */
    private static void installPipelineTests() throws Exception {
        Path sandbox = Files.createTempDirectory("omni-it");
        Os.setDataDirForTests(sandbox);
        Path www = Files.createDirectories(sandbox.resolve("www"));

        // ---- binary fixtures ----
        byte[] clientJar = zipBytes(Map.of("net/minecraft/Main.class", "fake client".getBytes()));
        byte[] libJar = zipBytes(Map.of("test/Lib.class", "fake lib".getBytes()));
        Map<String, byte[]> natEntries = new LinkedHashMap<>();
        natEntries.put("META-INF/MANIFEST.MF", "manifest".getBytes());
        natEntries.put("lwjgl.dll", "win-native".getBytes());
        natEntries.put("liblwjgl.so", "linux-native".getBytes());
        byte[] nativesJar = zipBytes(natEntries);
        byte[] logXml = "<Configuration/>".getBytes();

        String hClient = sha1(clientJar), hLib = sha1(libJar), hNat = sha1(nativesJar), hLog = sha1(logXml);
        Files.write(www.resolve("client.jar"), clientJar);
        Files.write(www.resolve("lib.jar"), libJar);
        Files.write(www.resolve("natives.jar"), nativesJar);
        Files.write(www.resolve("log.xml"), logXml);

        byte[] a1 = "asset-one".getBytes(), a2 = "asset-two-bytes!!".getBytes();
        String hA1 = sha1(a1), hA2 = sha1(a2);
        Files.createDirectories(www.resolve(hA1.substring(0, 2)));
        Files.createDirectories(www.resolve(hA2.substring(0, 2)));
        Files.write(www.resolve(hA1.substring(0, 2)).resolve(hA1), a1);
        Files.write(www.resolve(hA2.substring(0, 2)).resolve(hA2), a2);

        String indexJson = "{\"objects\":{"
                + "\"hero.png\":{\"hash\":\"" + hA1 + "\",\"size\":" + a1.length + "},"
                + "\"pack.mcmeta\":{\"hash\":\"" + hA2 + "\",\"size\":" + a2.length + "}}}";
        Files.write(www.resolve("index.json"), indexJson.getBytes());

        // ---- local HTTP server posing as Mojang ----
        var server = com.sun.net.httpserver.HttpServer.create(
                new java.net.InetSocketAddress("127.0.0.1", 0), 0);
        var hits = new java.util.concurrent.ConcurrentHashMap<String, Integer>();
        server.createContext("/", exchange -> {
            String path = exchange.getRequestURI().getPath();
            if (path.startsWith("/")) path = path.substring(1);
            hits.merge(path, 1, Integer::sum);
            byte[] body;
            try {
                body = Files.readAllBytes(www.resolve(path));
            } catch (Exception e) {
                exchange.sendResponseHeaders(404, -1);
                return;
            }
            exchange.getResponseHeaders().add("Content-Type", "application/octet-stream");
            exchange.sendResponseHeaders(200, body.length);
            try (var out = exchange.getResponseBody()) { out.write(body); }
        });
        server.start();
        String base = "http://127.0.0.1:" + server.getAddress().getPort();
        VersionInstaller.assetBaseUrl = base;

        try {
            String versionJson = """
                {
                  "id": "it.1.0", "type": "release", "mainClass": "test.Main",
                  "javaVersion": { "majorVersion": 17 },
                  "downloads": { "client": { "url": "%B%/client.jar", "sha1": "%HC%", "size": %SC% } },
                  "assetIndex": { "id": "it", "url": "%B%/index.json", "sha1": "%HIDX%", "totalSize": 0, "virtual": false },
                  "logging": { "client": { "argument": "-Dlog4j.configurationFile=${path}",
                      "file": { "id": "log.xml", "url": "%B%/log.xml", "sha1": "%HL%", "size": %SL% } } },
                  "arguments": { "jvm": ["-Dhello=world"], "game": ["--x"] },
                  "libraries": [
                    { "name": "test:lib:1",
                      "downloads": { "artifact": { "url": "%B%/lib.jar", "sha1": "%HLIB%", "size": %SLIB% } } },
                    { "name": "test:nat:1",
                      "natives": { "linux": "natives-linux", "windows": "natives-windows", "osx": "natives-macos" },
                      "downloads": {
                        "artifact": { "url": "%B%/lib.jar", "sha1": "%HLIB%", "size": %SLIB% },
                        "classifiers": {
                          "natives-linux":   { "url": "%B%/natives.jar", "sha1": "%HN%", "size": %SN% },
                          "natives-windows": { "url": "%B%/natives.jar", "sha1": "%HN%", "size": %SN% },
                          "natives-macos":   { "url": "%B%/natives.jar", "sha1": "%HN%", "size": %SN% } } } }
                  ]
                }
                """
                    .replace("%B%", base).replace("%HC%", hClient)
                    .replace("%SC%", String.valueOf(clientJar.length))
                    .replace("%HIDX%", sha1(indexJson.getBytes()))
                    .replace("%HL%", hLog).replace("%SL%", String.valueOf(logXml.length))
                    .replace("%HLIB%", hLib).replace("%SLIB%", String.valueOf(libJar.length))
                    .replace("%HN%", hNat).replace("%SN%", String.valueOf(nativesJar.length));
            Files.write(www.resolve("version.json"), versionJson.getBytes());

            var entry = new VersionManifest.Entry("it.1.0", "release", base + "/version.json",
                    sha1(versionJson.getBytes()), "2026-01-01T00:00:00+00:00");

            var installed = VersionInstaller.install(entry, s -> {}, f -> {},
                    new Http.CancelToken());

            // client jar downloaded + verified
            eq(true, Files.exists(Os.versionsDir().resolve("it.1.0").resolve("it.1.0.jar")),
                    "it: client jar in versions dir");
            eq(hClient, Http.sha1(Os.versionsDir().resolve("it.1.0").resolve("it.1.0.jar")),
                    "it: client sha1 verified");
            eq(Os.versionsDir().resolve("it.1.0").resolve("it.1.0.jar"), installed.clientJar(),
                    "it: InstalledVersion client path");

            // library downloaded to library path layout
            eq(true, Files.exists(Os.librariesDir().resolve("test/lib/1/lib-1.jar")),
                    "it: library at maven layout");

            // natives extracted, META-INF skipped, marker written
            eq(true, Files.exists(installed.nativesDir().resolve("lwjgl.dll")), "it: native .dll extracted");
            eq(true, Files.exists(installed.nativesDir().resolve("liblwjgl.so")), "it: native .so extracted");
            eq(false, Files.exists(installed.nativesDir().resolve("META-INF_MANIFEST.MF")),
                    "it: META-INF skipped");
            eq(true, Files.exists(installed.nativesDir().resolve(".done-" + hNat)), "it: extraction marker");

            // assets + log config
            eq(true, Files.exists(Os.assetsDir().resolve("objects")
                    .resolve(hA1.substring(0, 2)).resolve(hA1)), "it: asset object 1");
            eq(true, Files.exists(Os.assetsDir().resolve("objects")
                    .resolve(hA2.substring(0, 2)).resolve(hA2)), "it: asset object 2");
            eq(true, Files.exists(Os.assetsDir().resolve("log_configs").resolve("log.xml")),
                    "it: log config downloaded");

            // classpath contains library + client
            eq(true, installed.classpath().contains(Os.librariesDir().resolve("test/lib/1/lib-1.jar")),
                    "it: classpath has library");
            eq(true, installed.classpath().contains(installed.clientJar()), "it: classpath has client");

            // re-install must skip everything (fast path, zero new downloads)
            int clientHitsBefore = hits.getOrDefault("client.jar", 0);
            VersionInstaller.install(entry, s -> {}, f -> {}, new Http.CancelToken());
            eq(clientHitsBefore, hits.getOrDefault("client.jar", 0), "it: second run skips downloads");
        } finally {
            server.stop(0);
            VersionInstaller.assetBaseUrl = "https://resources.download.minecraft.net";
            Os.setDataDirForTests(null);
        }
    }

    /** Command construction for modern + legacy version metadata. */
    private static void gameCommandTests() {
        String sep = Os.get().classpathSeparator();
        Os.setDataDirForTests(Path.of(System.getProperty("java.io.tmpdir"), "omni-it-cmd"
                + System.nanoTime()));
        var modern = VersionJson.parse(VERSION_JSON);
        var v = new VersionInstaller.InstalledVersion(Path.of("/vd"), Path.of("/vd/client.jar"),
                List.of(Path.of("/libs/a.jar"), Path.of("/vd/client.jar")),
                Path.of("/vd/natives"), modern);
        var cmd = GameLauncher.buildCommand(v, Account.offline("Steve"),
                new GameLauncher.JavaRuntime(Path.of("/usr/bin/java"), 17));
        eq("/usr/bin/java", cmd.get(0), "cmd: java executable");
        eq(true, cmd.contains("-Xmx2048M"), "cmd: memory flag");
        eq(true, cmd.contains("-Dminecraft.launcher.brand=OmniLauncher"), "cmd: jvm template argument");
        eq(true, cmd.contains("-Djava.library.path=/vd/natives"), "cmd: natives via template");
        int cp = cmd.indexOf("-cp");
        eq(true, cp >= 0, "cmd: has -cp");
        eq("/libs/a.jar" + sep + "/vd/client.jar", cmd.get(cp + 1), "cmd: classpath joined");
        eq(true, cmd.contains("net.minecraft.client.main.Main"), "cmd: main class");
        int u = cmd.indexOf("--username");
        eq(true, u >= 0 && "Steve".equals(cmd.get(u + 1)), "cmd: username");
        eq(true, cmd.contains("--width") && cmd.contains("854"), "cmd: resolution feature");
        eq(true, cmd.indexOf("net.minecraft.client.main.Main") > cp, "cmd: main class after jvm args");

        var legacy = VersionJson.parse(LEGACY_VERSION_JSON);
        var lv = new VersionInstaller.InstalledVersion(Path.of("/vl"), Path.of("/vl/c.jar"),
                List.of(Path.of("/libs/old.jar")), Path.of("/vl/natives"), legacy);
        var lcmd = GameLauncher.buildCommand(lv, Account.offline("Alex"),
                new GameLauncher.JavaRuntime(Path.of("/usr/bin/java"), 8));
        eq(true, lcmd.contains("-Djava.library.path=/vl/natives"), "cmd: legacy natives property");
        int lcp = lcmd.indexOf("-cp");
        eq("/libs/old.jar", lcmd.get(lcp + 1), "cmd: legacy classpath");
        eq(true, lcmd.contains("--gameDir"), "cmd: legacy game args");
        eq(true, lcmd.indexOf("net.minecraft.client.Minecraft") < lcmd.indexOf("--gameDir"),
                "cmd: legacy main class before game args");
    }

    private static byte[] zipBytes(Map<String, byte[]> entries) throws Exception {
        var bos = new ByteArrayOutputStream();
        try (var zos = new ZipOutputStream(bos)) {
            for (Map.Entry<String, byte[]> e : entries.entrySet()) {
                zos.putNextEntry(new ZipEntry(e.getKey()));
                zos.write(e.getValue());
                zos.closeEntry();
            }
        }
        return bos.toByteArray();
    }

    private static String sha1(byte[] data) throws Exception {
        return Http.hex(java.security.MessageDigest.getInstance("SHA-1").digest(data));
    }

    /* ----------------------------------------------------- Mojang runtime */

    private static void runtimeTests() throws Exception {
        Path sandbox = Files.createTempDirectory("omni-rt");
        Os.setDataDirForTests(sandbox);
        Path www = Files.createDirectories(sandbox.resolve("rwww"));

        byte[] javaBin = "#!/bin/sh\necho fake-runtime-java\n".getBytes();
        byte[] rtJar = "runtime-jar-bytes".getBytes();
        String hBin = sha1(javaBin), hJar = sha1(rtJar);
        Files.write(www.resolve("bin-java"), javaBin);
        Files.write(www.resolve("rt-jar"), rtJar);

        var server = com.sun.net.httpserver.HttpServer.create(
                new java.net.InetSocketAddress("127.0.0.1", 0), 0);
        var hits = new java.util.concurrent.ConcurrentHashMap<String, Integer>();
        server.createContext("/", exchange -> {
            String path = exchange.getRequestURI().getPath();
            if (path.startsWith("/")) path = path.substring(1);
            hits.merge(path, 1, Integer::sum);
            byte[] body;
            try {
                body = Files.readAllBytes(www.resolve(path));
            } catch (Exception e) {
                exchange.sendResponseHeaders(404, -1);
                return;
            }
            exchange.sendResponseHeaders(200, body.length);
            try (var out = exchange.getResponseBody()) { out.write(body); }
        });
        server.start();
        String base = "http://127.0.0.1:" + server.getAddress().getPort();

        String manifestJson = """
            {
              "files": {
                "bin/java":   { "type": "file", "executable": true,
                                "downloads": { "raw": { "url": "%B%/bin-java", "sha1": "%HB%", "size": %SB% } } },
                "lib/rt.jar": { "type": "file", "executable": false,
                                "downloads": { "raw": { "url": "%B%/rt-jar", "sha1": "%HR%", "size": %SR% } } },
                "conf":       { "type": "directory" }
              }
            }
            """
                .replace("%B%", base)
                .replace("%HB%", hBin).replace("%SB%", String.valueOf(javaBin.length))
                .replace("%HR%", hJar).replace("%SR%", String.valueOf(rtJar.length));
        byte[] manifestBytes = manifestJson.getBytes();
        Files.write(www.resolve("rt-manifest.json"), manifestBytes);
        String checksum = sha1(manifestBytes);

        // products list: decoy first, jre_local second (must be preferred)
        String productsJson = """
            [
              { "component": "java-runtime-test", "version": "17.0.1", "availability": "jre",
                "manifest": { "type": "file", "url": "http://decoy.invalid/manifest.json" } },
              { "component": "java-runtime-test", "version": "17.0.9", "availability": "jre_local",
                "checksum": "%CK%",
                "manifest": { "type": "file", "url": "%U%/rt-manifest.json" } }
            ]
            """
                .replace("%CK%", checksum)
                .replace("%U%", base);
        RuntimeManager.productsBaseUrl = base + "/products";

        try {
            // product parsing: prefers jre_local over jre
            var product = RuntimeManager.parseProducts(productsJson, "java-runtime-test");
            eq("17.0.9", product.version(), "rt: prefers jre_local entry");
            eq(base + "/rt-manifest.json", product.manifestUrl(), "rt: manifest url");
            eq(checksum, product.checksum(), "rt: checksum passthrough");
            eq(null, RuntimeManager.parseProducts("[]", "x"), "rt: empty products → null");
            eq("17", String.valueOf(RuntimeManager.majorOfVersion("17.0.9")), "rt: version major parse");

            eq(true, RuntimeManager.productsUrl("java-runtime-gamma",
                    Os.of(Os.Family.LINUX, "x64")).endsWith("/java-runtime-gamma/linux/x64/all.json"),
                    "rt: products url shape");
            eq(true, RuntimeManager.productsUrl("java-runtime-gamma",
                    Os.of(Os.Family.WINDOWS, "arm64")).contains("/windows/x64/"),
                    "rt: windows arm falls back to x64");

            // install through the live local server
            RuntimeManager.ensure(product, s -> {}, f -> {}, new Http.CancelToken());
            Path javaExe = RuntimeManager.javaExecutable("java-runtime-test");
            eq(true, Files.exists(javaExe), "rt: bin/java downloaded");
            eq(true, Files.isExecutable(javaExe), "rt: executable bit set");
            eq(true, Files.exists(RuntimeManager.runtimeDir("java-runtime-test").resolve("lib/rt.jar")),
                    "rt: lib/rt.jar downloaded");
            eq(hJar, Http.sha1(RuntimeManager.runtimeDir("java-runtime-test").resolve("lib/rt.jar")),
                    "rt: runtime file sha1 verified");
            eq(true, Files.exists(RuntimeManager.runtimeDir("java-runtime-test")
                    .resolve(".done-" + checksum)), "rt: checksum marker");
            var handle = RuntimeManager.javaFor("java-runtime-test", 17);
            eq(true, handle != null && handle.major() == 17, "rt: javaFor handle");

            // second ensure: fast path, no re-downloads
            int hitsBefore = hits.getOrDefault("bin-java", 0);
            RuntimeManager.ensure(product, s -> {}, f -> {}, new Http.CancelToken());
            eq(hitsBefore, hits.getOrDefault("bin-java", 0), "rt: installed runtime not re-downloaded");

            // component plumbing through version metadata
            eq("java-runtime-gamma", VersionJson.parse(VERSION_JSON).javaComponent,
                    "rt: version json component");
        } finally {
            server.stop(0);
            RuntimeManager.productsBaseUrl = "https://piston-meta.mojang.com/v1/products/java-runtime";
            Os.setDataDirForTests(null);
        }
    }

    /* ------------------------------------------------------------ assert */

    private static void eq(Object expected, Object actual, String name) {
        boolean ok = expected == null ? actual == null : expected.equals(actual);
        if (ok) pass(name);
        else {
            failed++;
            System.out.println("FAIL  " + name + "\n      expected: " + expected + "\n      actual:   " + actual);
        }
    }

    private static void pass(String name) {
        passed++;
        System.out.println("PASS  " + name);
    }

    private static void fail(String name) {
        failed++;
        System.out.println("FAIL  " + name);
    }
}
