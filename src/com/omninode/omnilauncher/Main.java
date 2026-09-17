package com.omninode.omnilauncher;

import java.nio.file.Path;


import com.omninode.omnilauncher.api.VersionManifest;
import com.omninode.omnilauncher.core.AccountStore;
import com.omninode.omnilauncher.core.GameLauncher;
import com.omninode.omnilauncher.core.Settings;
import com.omninode.omnilauncher.core.VersionInstaller;
import com.omninode.omnilauncher.model.Account;
import com.omninode.omnilauncher.ui.LauncherWindow;
import com.omninode.omnilauncher.ui.Preview;
import com.omninode.omnilauncher.ui.SelfTest;
import com.omninode.omnilauncher.util.Log;
import com.omninode.omnilauncher.util.Os;

/** Entry point: GUI by default, plus headless CLI modes. */
public class Main {

    public static void main(String[] args) {
        Thread.setDefaultUncaughtExceptionHandler((t, e) ->
                Log.error("Uncaught on " + t.getName(), e));

        if (args.length > 0) {
            switch (args[0]) {
                case "--version", "-v" -> {
                    System.out.println("OmniLauncher " + GameLauncher.LAUNCHER_VERSION);
                    return;
                }
                case "--selftest" -> { System.exit(SelfTest.run()); return; }
                case "--preview" -> {
                    System.exit(Preview.run(args));
                    return;
                }
                case "--export-icon" -> { System.exit(exportIcon(argOf(args, 1))); return; }
                case "--install" -> { System.exit(headlessInstall(argOf(args, 1))); return; }
                case "--launch" -> { System.exit(headlessLaunch(args)); return; }
                case "--list" -> { System.exit(headlessList()); return; }
                case "--help", "-h" -> { printHelp(); return; }
                default -> {
                    System.err.println("Unknown option: " + args[0]);
                    printHelp();
                    System.exit(2);
                    return;
                }
            }
        }

        launchGui();
    }

    private static int exportIcon(String dirArg) {
        try {
            if (dirArg == null || dirArg.isBlank()) {
                System.err.println("Usage: --export-icon <output-dir>");
                return 2;
            }
            var written = com.omninode.omnilauncher.ui.IconExporter.exportAll(Path.of(dirArg));
            written.forEach((k, p) -> System.out.println("  " + p));
            System.out.println("Icons written to " + dirArg);
            return 0;
        } catch (Exception e) {
            System.err.println("Icon export failed: " + e.getMessage());
            return 1;
        }
    }

    private static String argOf(String[] args, int i) {
        return i < args.length ? args[i] : null;
    }

    private static void printHelp() {
        System.out.println("""
                OmniLauncher %s — native Minecraft launcher

                Usage:
                  OmniLauncher                       open the launcher window
                  OmniLauncher --install <version>   install a version, headless
                  OmniLauncher --launch <version> [--name <player>]
                                                     install & launch, headless
                  OmniLauncher --list                print available versions
                  OmniLauncher --preview <out.png> [page] [width] [height]
                                                     render UI preview (headless)
                  OmniLauncher --export-icon <dir>   write PNG/ICO/ICNS icons
                                                     (used by scripts/package.sh)
                  OmniLauncher --selftest            run the built-in test suite
                  OmniLauncher --version             print version
                """.formatted(GameLauncher.LAUNCHER_VERSION));
    }

    private static java.nio.channels.FileLock instanceLock;
    private static java.nio.channels.FileChannel instanceChannel;

    private static void launchGui() {
        System.setProperty("apple.application.name", "OmniLauncher");
        if (!acquireInstanceLock()) {
            System.err.println("OmniLauncher is already running.");
            System.exit(4);
            return;
        }
        Log.init(Os.logsDir());
        Log.info("OmniLauncher " + GameLauncher.LAUNCHER_VERSION + " starting — " + Os.get().family
                + "/" + Os.get().arch + ", data: " + Os.dataDir());
        Settings.get();
        AccountStore.load();
        LauncherWindow.showWindow();
    }

    /** Prevents two launcher instances from racing on the same data directory. */
    private static boolean acquireInstanceLock() {
        try {
            instanceChannel = java.nio.channels.FileChannel.open(Os.dataDir().resolve("launcher.lock"),
                    java.nio.file.StandardOpenOption.CREATE,
                    java.nio.file.StandardOpenOption.WRITE);
            instanceLock = instanceChannel.tryLock();
            return instanceLock != null;
        } catch (Exception e) {
            Log.error("Instance lock failed", e);
            return true; // fail open rather than block the user
        }
    }

    private static int headlessInstall(String versionId) {
        try {
            Log.init(Os.logsDir());
            AccountStore.load();
            if (versionId == null || versionId.isBlank() || versionId.equals("latest"))
                versionId = VersionManifest.latestRelease().isEmpty() ? null : versionId;
            VersionManifest.loadBlocking();
            var entry = "latest".equals(versionId) || versionId == null
                    ? VersionManifest.byId(VersionManifest.latestRelease())
                    : VersionManifest.byId(versionId);
            if (entry == null) {
                System.err.println("Version not found: " + versionId);
                return 3;
            }
            System.out.println("Installing " + entry.id() + "…");
            VersionInstaller.install(entry,
                    s -> System.out.println("  " + s),
                    f -> { /* quiet */ }, com.omninode.omnilauncher.util.Http.newCancelToken());
            System.out.println("Installed " + entry.id() + " → " + Os.versionsDir().resolve(entry.id()));
            return 0;
        } catch (Exception e) {
            System.err.println("Install failed: " + e.getMessage());
            return 1;
        }
    }

    private static int headlessList() {
        try {
            VersionManifest.loadBlocking();
            for (var e : VersionManifest.visibleEntries(
                    Settings.get().showSnapshots, Settings.get().showHistorical)) {
                String date = e.releaseTime();
                if (date.length() >= 10) date = date.substring(0, 10);
                System.out.println(e.id() + "\t" + e.type() + "\t" + date);
            }
            return 0;
        } catch (Exception e) {
            System.err.println("Could not load the version list: " + e.getMessage());
            return 1;
        }
    }

    private static int headlessLaunch(String[] args) {
        String versionId = argOf(args, 1);
        String name = null;
        for (int i = 2; i < args.length - 1; i++)
            if ("--name".equals(args[i])) name = args[i + 1];
        try {
            Log.init(Os.logsDir());
            AccountStore.load();
            Account account = AccountStore.selected();
            if (name != null) {
                account = Account.offline(name);
                AccountStore.add(account);
            }
            if (account == null && versionId != null) {
                account = Account.offline("Player");
                AccountStore.add(account);
            }
            VersionManifest.loadBlocking();
            var entry = versionId == null || "latest".equals(versionId)
                    ? VersionManifest.byId(VersionManifest.latestRelease())
                    : VersionManifest.byId(versionId);
            if (entry == null) {
                System.err.println("Version not found: " + versionId);
                return 3;
            }
            System.out.println("Preparing " + entry.id() + "…");
            var installed = VersionInstaller.install(entry,
                    s -> System.out.println("  " + s),
                    f -> { /* quiet */ }, com.omninode.omnilauncher.util.Http.newCancelToken());
            Process p = GameLauncher.launch(installed, account, new GameLauncher.RunListener() {
                @Override public void started(Process process) { System.out.println("Minecraft started."); }
                @Override public void exited(int exitCode) {
                    System.out.println("Game exited with code " + exitCode);
                    System.exit(exitCode == 0 ? 0 : 1);
                }
                @Override public void outputLine(String line) { System.out.println("[mc] " + line); }
                @Override public void failed(String message) {
                    System.err.println("Launch failed: " + message);
                    System.exit(1);
                }
            });
            return p == null ? 1 : 0;
        } catch (Exception e) {
            System.err.println("Launch failed: " + e.getMessage());
            return 1;
        }
    }
}
