package com.omninode.omnilauncher.ui;

import java.awt.Component;
import java.awt.Container;
import java.awt.image.BufferedImage;
import java.nio.file.Files;
import java.nio.file.Path;

import javax.imageio.ImageIO;

import com.omninode.omnilauncher.api.NewsService;
import com.omninode.omnilauncher.api.VersionManifest;
import com.omninode.omnilauncher.util.Os;

/**
 * Headless UI renderer used for design iteration and documentation
 * screenshots: builds the real launcher shell with sample data and
 * paints it to a PNG without any display server.
 */
public final class Preview {

    private Preview() {}

    public static int run(String[] args) {
        String out = args.length > 1 ? args[1] : "preview.png";
        String page = args.length > 2 ? args[2] : "play";
        int w = args.length > 3 ? Integer.parseInt(args[3]) : 1200;
        int h = args.length > 4 ? Integer.parseInt(args[4]) : 740;
        try {
            render(Path.of(out), page, w, h);
            System.out.println("Preview written: " + out);
            return 0;
        } catch (Exception e) {
            System.err.println("Preview failed: " + e);
            e.printStackTrace();
            return 1;
        }
    }

    static void render(Path out, String page, int w, int h) throws Exception {
        // run async UI completions inline so headless rendering sees final state
        com.omninode.omnilauncher.util.Async.synchronousUi = true;
        // sandbox data dir so the preview never touches real user data
        Os.setDataDirForTests(Files.createTempDirectory("omni-preview"));
        PreviewData.install();
        Theme.init();

        LauncherShell shell = new LauncherShell(null);

        javax.swing.JComponent overlay = null;
        java.awt.Point overlayAt = null;
        switch (page) {
            case "play" -> shell.navigate(NavRail.Page.PLAY);
            case "installing" -> {
                shell.navigate(NavRail.Page.PLAY);
                AppState.get().set(AppState.Phase.INSTALLING, "Downloading assets — 1,204 / 3,412 files");
                AppState.get().setProgress(0.42f);
            }
            case "running" -> {
                shell.navigate(NavRail.Page.PLAY);
                AppState.get().set(AppState.Phase.RUNNING, "Minecraft 1.21.9 is running");
            }
            case "error" -> {
                shell.navigate(NavRail.Page.PLAY);
                AppState.get().set(AppState.Phase.ERROR,
                        "Minecraft 1.21.9 requires Java 21 — set it in Settings → Java");
            }
            case "instances" -> {
                shell.navigate(NavRail.Page.INSTANCES);
                com.omninode.omnilauncher.core.InstanceStore.reload();
                var a = com.omninode.omnilauncher.core.InstanceStore.create("Survival 1.21", "1.21.9");
                if (a != null) a.lastPlayed = System.currentTimeMillis() - 3_600_000;
                com.omninode.omnilauncher.core.InstanceStore.create("Snapshot testing", "25w45a");
                shell.instances.refresh();
            }
            case "news" -> shell.navigate(NavRail.Page.NEWS);
            case "detail" -> {
                shell.navigate(NavRail.Page.NEWS);
                if (!NewsService.items().isEmpty()) shell.news.showDetail(NewsService.items().get(0));
            }
            case "settings" -> shell.navigate(NavRail.Page.SETTINGS);
            case "accounts" -> {
                shell.navigate(NavRail.Page.PLAY);
                overlay = new AccountsPanel(() -> {});
                overlayAt = new java.awt.Point((w - 500) / 2, (h - 480) / 2);
            }
            case "versions" -> {
                shell.navigate(NavRail.Page.PLAY);
                var box = new com.omninode.omnilauncher.ui.components.VersionComboBox();
                box.setSelected(VersionManifest.resolveSelected(""), false);
                overlay = box.popupForPreview();
                overlayAt = new java.awt.Point(84, 70);
            }
            default -> throw new IllegalArgumentException("Unknown preview page: " + page);
        }

        shell.setSize(w, h);
        layoutTree(shell);
        layoutTree(shell);
        layoutTree(shell);

        BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_RGB);
        var g2 = img.createGraphics();
        g2.setColor(Theme.BG);
        g2.fillRect(0, 0, w, h);
        shell.printAll(g2);

        if (overlay != null) {
            var ps = overlay.getPreferredSize();
            overlay.setSize(ps);
            layoutTree(overlay);
            layoutTree(overlay);
            var oi = new BufferedImage(ps.width, ps.height, BufferedImage.TYPE_INT_ARGB);
            var og = oi.createGraphics();
            og.setRenderingHint(java.awt.RenderingHints.KEY_ANTIALIASING,
                    java.awt.RenderingHints.VALUE_ANTIALIAS_ON);
            overlay.printAll(og);
            og.dispose();
            g2.setColor(new java.awt.Color(0, 0, 0, 90));
            g2.fillRoundRect(overlayAt.x + 5, overlayAt.y + 9, ps.width, ps.height, 16, 16);
            g2.drawImage(oi, overlayAt.x, overlayAt.y, null);
            g2.setColor(Theme.STROKE);
            g2.drawRoundRect(overlayAt.x, overlayAt.y, ps.width - 1, ps.height - 1, 4, 4);
        }

        g2.dispose();
        ImageIO.write(img, "png", out.toFile());
    }

    /** Layout the component tree without a display (top-down, then a settling pass). */
    static void layoutTree(Container c) {
        synchronized (c.getTreeLock()) {
            c.doLayout();
            for (Component ch : c.getComponents()) {
                if (ch instanceof Container cc) layoutTree(cc);
            }
        }
    }
}
