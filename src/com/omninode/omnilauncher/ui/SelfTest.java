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
import com.omninode.omnilauncher.ui.components.VersionComboBox;
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
    { "version": 1, "entries": [
      { "title": "Brave a new dimension in Dungeons II", "tag": "news",
        "category": "Minecraft Dungeons", "date": "2026-08-20",
        "text": "Journey into the Sift to explore uncharted lands and fight unfamiliar threats.",
        "playPageImage": { "title": "MCD2_MinecraftLauncher_700x466.png",
                           "url": "/v2/images/MCD2MinecraftLauncher700x466.png" },
        "newsPageImage": { "title": "MCD2_MinecraftLauncher_772x350.png",
                           "url": "/v2/images/MCD2MinecraftLauncher772x350.png",
                           "dimensions": { "width": 772, "height": 350 } },
        "readMoreLink": "https://www.minecraft.net/about-dungeons-ii?OCID=Launcher",
        "cardBorder": false, "articleBody": "", "newsType": ["Dungeons", "News page"],
        "id": "65e0c5c5", "needsTranslation": true },
      { "title": "Legacy image entry", "tag": "news", "category": "Minecraft for Windows",
        "date": "2026-08-01",
        "text": "The copper golem sorts your chests while the shelf stores your leftovers and this gentle news body keeps drifting well past the one hundred and fifty character summary cut so truncation is genuinely exercised.",
        "image": { "url": "/v2/images/y.jpg" },
        "articleBody": "", "newsType": ["News page", "Bedrock"], "id": "12b600e8" }
    ] }
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
        comboGuardTests();
        newsTests();
        authShapeTests();
        accountTests();
        settingsTests();
        argSplitTests();
        try {
            installPipelineTests();
            gameCommandTests();
            runtimeTests();
            authFlowTests();
            iconTests();
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

    private static void comboGuardTests() {
        com.omninode.omnilauncher.ui.Theme.init();
        // regression: opening the popup ran refresh() which re-selected the
        // current entry and fired onSelect -> close/save/reopen storm that
        // wedged the EDT on the second open
        var box = new VersionComboBox();
        var panel = box.new PopupPanel();
        int[] fired = {0};
        panel.onSelect = e -> { fired[0]++; box.setSelected(e, false); };
        var vis = VersionManifest.visibleEntries(Settings.get().showSnapshots,
                Settings.get().showHistorical);
        eq(true, vis.size() >= 2, "combo: fixture has visible entries");
        var a = vis.get(0);
        var b = vis.get(1);
        box.setSelected(a, false);
        eq(false, box.isPopupVisible(), "combo: popup starts hidden");
        panel.refresh();
        eq(0, fired[0], "combo: refresh selection is guarded");
        panel.list.setSelectedValue(b, false);
        eq(1, fired[0], "combo: user selection fires once");
        eq(b.id(), box.getSelected().id(), "combo: selection propagates");
        panel.refresh();
        eq(1, fired[0], "combo: second refresh still guarded");
    }

    private static void newsTests() {
        // fixture mirrors the real launchercontent.mojang.com/v2/news.json shape
        NewsService.parse(NEWS_JSON);
        eq(2, NewsService.items().size(), "news count");
        eq("Brave a new dimension in Dungeons II", NewsService.items().get(0).title(), "news title");
        eq("Journey into the Sift to explore uncharted lands and fight unfamiliar threats.",
                NewsService.items().get(0).shortText(), "news shortText from text");
        eq("Journey into the Sift to explore uncharted lands and fight unfamiliar threats.",
                NewsService.items().get(0).longText(), "news longText falls back to text");
        eq("Minecraft Dungeons", NewsService.items().get(0).category(), "news category is the game name");
        eq("https://launchercontent.mojang.com/v2/images/MCD2MinecraftLauncher700x466.png",
                NewsService.items().get(0).imageUrl(), "news card image from playPageImage");
        eq("https://launchercontent.mojang.com/v2/images/MCD2MinecraftLauncher772x350.png",
                NewsService.items().get(0).detailImageUrl(), "news banner image from newsPageImage");
        eq("https://www.minecraft.net/about-dungeons-ii?OCID=Launcher",
                NewsService.items().get(0).readMoreUrl(), "news readMoreLink parsed");
        eq(true, NewsService.items().get(0).formattedDate().startsWith("August")
                && NewsService.items().get(0).formattedDate().contains("2026"), "news date format");
        eq("https://launchercontent.mojang.com/v2/images/y.jpg",
                NewsService.items().get(1).imageUrl(), "news legacy image map resolved");
        eq("https://launchercontent.mojang.com/v2/images/y.jpg",
                NewsService.items().get(1).detailImageUrl(), "news detail falls back to card image");
        var blurb = NewsService.items().get(1).shortText();
        eq(true, blurb.length() <= 151 && blurb.endsWith("…"), "news blurb truncated at word boundary");
        // full-blog article document: plain text becomes paragraphs + read-more link
        var doc = NewsService.buildArticleHtml(NewsService.items().get(0));
        eq(true, doc.startsWith("<html><body><p>Journey into the Sift")
                && doc.contains("fight unfamiliar threats.</p>"), "article plain text becomes a paragraph");
        eq(true, doc.contains("<a href=\"https://www.minecraft.net/about-dungeons-ii?OCID=Launcher\">")
                && doc.contains("Read the full article on minecraft.net"), "article has read-more link");
        eq(true, doc.endsWith("</body></html>"), "article document is well formed");
        eq("Journey into the Sift to explore uncharted lands and fight unfamiliar threats.",
                NewsService.articlePlainText(NewsService.items().get(0)), "article plain text of plain entry");
        // plain text with stray inline markup stays plain: escaped, newlines kept,
        // blank lines split paragraphs, no link when the entry has none
        NewsService.parse("""
            { "entries": [ { "title": "Esc", "date": "2026-08-02", "category": "Minecraft: Java Edition",
              "text": "A & B <br> real newline kept\nsecond line\n\nsecond paragraph" } ] }
            """);
        var escDoc = NewsService.buildArticleHtml(NewsService.items().get(0));
        eq(true, escDoc.contains("A &amp; B &lt;br&gt; real newline kept<br>second line</p>"),
                "article escapes tags and keeps single newlines");
        eq(true, escDoc.contains("<p>second paragraph</p>"), "article splits blank-line paragraphs");
        eq(false, escDoc.contains("Read the full article"), "article omits link when absent");
        // rich articleBody is preferred and passed through untouched
        NewsService.parse("""
            { "entries": [ { "title": "Rich", "date": "2026-08-02", "category": "Minecraft: Java Edition",
              "text": "plain", "articleBody": "<p>rich body</p>" } ] }
            """);
        eq("<p>rich body</p>", NewsService.items().get(0).longText(), "news articleBody preferred");
        eq(true, NewsService.buildArticleHtml(NewsService.items().get(0)).contains("<p>rich body</p>"),
                "article keeps rich HTML verbatim");

        javaLookupTests();
        NewsService.parse("""
            { "entries": [ { "title": "Fmt", "date": "2026-08-03", "category": "Minecraft: Java Edition",
              "articleBody": "<p>one</p><p>two</p><ul><li>bullet</li></ul>" } ] }
            """);
        eq("one\n\ntwo\n\n\u2022 bullet",
                NewsService.articlePlainText(NewsService.items().get(0)), "article plain text keeps paragraphs and bullets");
        eq("a b", NewsService.summarize("<p>a</p><p>b</p>", 150), "card blurb stays single-line");
        // legacy bare-array payloads still parse
        NewsService.parse("[{ \"title\": \"Bare\", \"date\": \"2026-08-02\", \"text\": \"<b>hi</b> &amp; bye\" }]");
        eq(1, NewsService.items().size(), "news bare array accepted");
        eq("hi & bye", NewsService.items().get(0).shortText(), "news bare array text stripped");
        eq("news", NewsService.items().get(0).category(), "news bare array category default");
        // ImageLoader cache names: stable, safe, distinct per URL
        var a = ImageLoader.cacheFileFor("https://launchercontent.mojang.com/v2/images/MCD2_700x466.png");
        var b = ImageLoader.cacheFileFor("https://launchercontent.mojang.com/v2/images/MCD2_700x466.png");
        var c = ImageLoader.cacheFileFor("https://launchercontent.mojang.com/v2/images/other.jpg?q=1&x=2");
        eq(a.toString(), b.toString(), "image cache name stable");
        eq(true, !a.toString().equals(c.toString()), "image cache names distinct");
        eq(true, a.getFileName().toString().matches("[0-9a-f]+-MCD2_700x466\\.png"), "image cache name safe");
        eq(true, c.getFileName().toString().matches("[0-9a-f]+-[A-Za-z0-9._-]+"), "image cache strips query chars");
        NewsService.parse(NEWS_JSON); // restore wrapped fixture for any later readers
    }

    private static void javaLookupTests() {
        var os = Os.of(Os.Family.LINUX, "x64");
        var sep = java.io.File.pathSeparator;
        // PATH entries are now searched explicitly (the old lookup probed the
        // bare name against the current directory, missing PATH installs)
        var cands = GameLauncher.javaCandidates(null, "/jh", "/a" + sep + "/b" + sep + sep + "/c",
                os, "/runner/jre", null);
        eq("/jh/bin/java", cands.get(0).toString(), "java candidate: JAVA_HOME first");
        eq(true, cands.contains(Path.of("/a/java")) && cands.contains(Path.of("/b/java"))
                && cands.contains(Path.of("/c/java")), "java candidate: PATH dirs expanded");
        eq(true, cands.contains(Path.of("/runner/jre/bin/java")), "java candidate: launcher runtime");
        eq(true, cands.contains(Path.of("/usr/lib/jvm")) == false, "java candidate: dirs not added raw");
        // bundled runtime layout per OS (jpackage app-path)
        var win = GameLauncher.javaCandidates(null, null, "", Os.of(Os.Family.WINDOWS, "x64"), null,
                "/install/OmniLauncher.exe");
        eq(true, win.contains(Path.of("/install/runtime/bin/java.exe")),
                "java candidate: windows bundled runtime");
        var mac = GameLauncher.javaCandidates(null, null, "", Os.of(Os.Family.MACOS, "x64"), null,
                "/Applications/OmniLauncher.app/Contents/MacOS/OmniLauncher");
        eq(true, mac.contains(Path.of("/Applications/OmniLauncher.app/Contents/PlugIns/runtime/Contents/Home/bin/java")),
                "java candidate: mac bundled runtime");
        // explicit override: an existing directory resolves to its java binary
        Path tmpJdk;
        try { tmpJdk = java.nio.file.Files.createTempDirectory("omni-jdk-test"); }
        catch (java.io.IOException e) { throw new RuntimeException(e); }
        var ov = GameLauncher.javaCandidates(tmpJdk.toString(), null, "", os, null, null);
        eq(tmpJdk.resolve("bin").resolve("java").toString(), ov.get(0).toString(),
                "java candidate: dir override resolved");
        // a selected javaw.exe is swapped for the console java next to it
        var ovw = GameLauncher.javaCandidates("/c/Java/javaw.exe", null, "",
                Os.of(Os.Family.WINDOWS, "x64"), null, null);
        eq("/c/Java/java.exe", ovw.get(0).toString(), "java candidate: javaw swapped to java");
        // best runtime wins (an old PATH entry must not shadow a newer install)
        eq(null, GameLauncher.pickBest(List.of()), "java pick: empty");
        eq(21, GameLauncher.pickBest(List.of(new GameLauncher.JavaRuntime(Path.of("/a"), 17),
                new GameLauncher.JavaRuntime(Path.of("/b"), 21))).major(), "java pick: highest major");
        eq("/first", GameLauncher.pickBest(List.of(new GameLauncher.JavaRuntime(Path.of("/first"), 17),
                new GameLauncher.JavaRuntime(Path.of("/second"), 17))).javaExe().toString(),
                "java pick: tie keeps first");
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

    /* ---------------------------------------------------- Microsoft chain */

    /**
     * Walks the full device-code chain (devicecode -> token -> XBL -> XSTS ->
     * minecraftservices -> profile) against a local fake of every endpoint,
     * asserting request shapes, the pending->success poll rhythm and the
     * resulting Account. Also covers the XSTS XErr path.
     */
    private static void authFlowTests() throws Exception {
        Path sandbox = Files.createTempDirectory("omni-auth");
        Os.setDataDirForTests(sandbox);
        java.util.concurrent.atomic.AtomicInteger tokenCalls =
                new java.util.concurrent.atomic.AtomicInteger();
        java.util.concurrent.atomic.AtomicBoolean xstsDeny =
                new java.util.concurrent.atomic.AtomicBoolean(false);
        java.util.concurrent.atomic.AtomicReference<String> lastProfileAuth =
                new java.util.concurrent.atomic.AtomicReference<>();

        var server = com.sun.net.httpserver.HttpServer.create(
                new java.net.InetSocketAddress("127.0.0.1", 0), 0);
        server.start();
        final String base = "http://127.0.0.1:" + server.getAddress().getPort();
        server.createContext("/devicecode", exchange -> {
            byte[] body = ("{\"device_code\":\"dc-123\",\"user_code\":\"ABCD EFGH\","
                    + "\"verification_uri\":\"" + base + "/link\",\"interval\":1,\"expires_in\":900}")
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, body.length);
            try (var out = exchange.getResponseBody()) { out.write(body); }
        });
        server.createContext("/token", exchange -> {
            boolean pending = tokenCalls.incrementAndGet() == 1;
            // real Azure AD answers authorization_pending with HTTP 400
            byte[] b = (pending
                    ? "{\"error\":\"authorization_pending\",\"error_description\":\"waiting\"}"
                    : "{\"access_token\":\"ms-token\",\"refresh_token\":\"ms-refresh\","
                      + "\"expires_in\":3600}").getBytes(java.nio.charset.StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(pending ? 400 : 200, b.length);
            try (var out = exchange.getResponseBody()) { out.write(b); }
        });
        server.createContext("/xbl", exchange -> {
            byte[] b = ("{\"Token\":\"xbl-token\",\"DisplayClaims\":{\"xui\":[{\"uhs\":\"uhs-1\"}]}}")
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(200, b.length);
            try (var out = exchange.getResponseBody()) { out.write(b); }
        });
        server.createContext("/xsts", exchange -> {
            if (xstsDeny.get()) {
                byte[] b = "{\"XErr\":2148916233,\"Identity\":\"0\"}"
                        .getBytes(java.nio.charset.StandardCharsets.UTF_8);
                exchange.sendResponseHeaders(401, b.length);
                try (var out = exchange.getResponseBody()) { out.write(b); }
                return;
            }
            byte[] b = ("{\"Token\":\"xsts-token\",\"DisplayClaims\":{\"xui\":[{\"uhs\":\"uhs-2\"}]}}")
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(200, b.length);
            try (var out = exchange.getResponseBody()) { out.write(b); }
        });
        server.createContext("/login", exchange -> {
            byte[] b = "{\"access_token\":\"mc-token\",\"expires_in\":86400}"
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(200, b.length);
            try (var out = exchange.getResponseBody()) { out.write(b); }
        });
        server.createContext("/profile", exchange -> {
            lastProfileAuth.set(exchange.getRequestHeaders().getFirst("Authorization"));
            byte[] b = ("{\"id\":\"770c88d14dac553db02f99e9a488f83e\",\"name\":\"Alex\","
                    + "\"skins\":[{\"id\":\"s\",\"state\":\"ACTIVE\","
                    + "\"url\":\"http://textures/skin.png\"}]}")
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(200, b.length);
            try (var out = exchange.getResponseBody()) { out.write(b); }
        });
        String oldDevice = MicrosoftAuth.DEVICE_CODE_URL;
        String oldToken = MicrosoftAuth.TOKEN_URL;
        String oldXbl = MicrosoftAuth.XBL_AUTH_URL;
        String oldXsts = MicrosoftAuth.XSTS_AUTH_URL;
        String oldLogin = MicrosoftAuth.MC_LOGIN_URL;
        String oldProfile = MicrosoftAuth.MC_PROFILE_URL;
        MicrosoftAuth.DEVICE_CODE_URL = base + "/devicecode";
        MicrosoftAuth.TOKEN_URL = base + "/token";
        MicrosoftAuth.XBL_AUTH_URL = base + "/xbl";
        MicrosoftAuth.XSTS_AUTH_URL = base + "/xsts";
        MicrosoftAuth.MC_LOGIN_URL = base + "/login";
        MicrosoftAuth.MC_PROFILE_URL = base + "/profile";

        try {
            // start: device code fields parse
            var dc = MicrosoftAuth.startDeviceCode("client-id");
            eq("ABCD EFGH", dc.userCode(), "auth: user code");
            eq("dc-123", dc.deviceCode(), "auth: device code");
            eq(1L, dc.interval(), "auth: poll interval");
            eq(base + "/link", dc.verificationUri(), "auth: verification uri");

            // poll 1 -> pending; poll 2 -> full chain -> account
            var pending = MicrosoftAuth.pollDeviceCode("client-id", dc);
            eq(MicrosoftAuth.PollState.PENDING, pending.state(), "auth: first poll pending");
            var done = MicrosoftAuth.pollDeviceCode("client-id", dc);
            eq(MicrosoftAuth.PollState.SUCCESS, done.state(), "auth: second poll success");
            var acc = done.account();
            eq(true, acc != null, "auth: account produced");
            eq("Alex", acc.getName(), "auth: profile name");
            eq("770c88d1-4dac-553d-b02f-99e9a488f83e", acc.getUuid(), "auth: profile uuid dashed");
            eq(true, acc.isMicrosoft(), "auth: account type");
            eq("ms-refresh", acc.getRefreshToken(), "auth: refresh token kept");
            eq("http://textures/skin.png", acc.getSkinUrl(), "auth: active skin captured");
            eq("Bearer mc-token", lastProfileAuth.get(), "auth: profile bearer header");
            eq(true, acc.getExpiresAt() > System.currentTimeMillis(), "auth: expiry in future");

            // XSTS denial: poll surfaces the friendly XErr message as a failure
            xstsDeny.set(true);
            tokenCalls.set(10); // next poll returns tokens again
            var denied = MicrosoftAuth.pollDeviceCode("client-id", dc);
            eq(MicrosoftAuth.PollState.FAILED, denied.state(), "auth: xsts denial fails the poll");
            eq(true, String.valueOf(denied.errorDetail()).contains("no Xbox profile"),
                    "auth: xerr friendly message");
            // and completeSignIn directly throws the same friendly error
            try {
                MicrosoftAuth.completeSignIn("ms-token", "r", 60);
                fail("auth: xsts denial should throw from completeSignIn");
            } catch (IllegalStateException e) {
                eq(true, String.valueOf(e.getMessage()).contains("no Xbox profile"),
                        "auth: completeSignIn throws friendly message");
            }
        } finally {
            server.stop(0);
            MicrosoftAuth.DEVICE_CODE_URL = oldDevice;
            MicrosoftAuth.TOKEN_URL = oldToken;
            MicrosoftAuth.XBL_AUTH_URL = oldXbl;
            MicrosoftAuth.XSTS_AUTH_URL = oldXsts;
            MicrosoftAuth.MC_LOGIN_URL = oldLogin;
            MicrosoftAuth.MC_PROFILE_URL = oldProfile;
            Os.setDataDirForTests(null);
        }
    }

    /* ---------------------------------------------------- icons & version */

    private static void iconTests() throws Exception {
        eq("0.3.7", GameLauncher.LAUNCHER_VERSION, "version is 0.3.7");
        Path dir = Files.createTempDirectory("omni-icons");
        var written = com.omninode.omnilauncher.ui.IconExporter.exportAll(dir);
        Path png = dir.resolve("icon-256.png");
        eq(true, Files.exists(png), "icon: 256px png written");
        byte[] pngBytes = Files.readAllBytes(png);
        eq(true, pngBytes.length > 0
                && (pngBytes[0] & 0xFF) == 0x89 && pngBytes[1] == 'P' && pngBytes[2] == 'N',
                "icon: png signature");
        byte[] ico = Files.readAllBytes(dir.resolve("OmniLauncher.ico"));
        eq(true, ico.length > 4 && ico[0] == 0 && ico[1] == 0 && ico[2] == 1 && ico[3] == 0,
                "icon: ico header (type=1)");
        byte[] icns = Files.readAllBytes(dir.resolve("OmniLauncher.icns"));
        eq(true, icns.length > 8 && icns[0] == 'i' && icns[1] == 'c' && icns[2] == 'n' && icns[3] == 's',
                "icon: icns magic");
        int declared = ((icns[4] & 0xFF) << 24) | ((icns[5] & 0xFF) << 16)
                | ((icns[6] & 0xFF) << 8) | (icns[7] & 0xFF);
        eq(icns.length, declared, "icon: icns declared size matches");
        eq(11, written.size(), "icon: export map size");
        String svg = Files.readString(written.get("svg"));
        eq(true, svg.startsWith("<svg") && svg.contains("</svg>"), "icon: svg document");
        eq(true, svg.contains("viewBox=\"0 0 512 512\"") && svg.contains("#7cb342"),
                "icon: svg brand geometry");
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
