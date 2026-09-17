package com.omninode.omnilauncher.ui;

import javax.swing.JFrame;
import javax.swing.SwingUtilities;

import com.omninode.omnilauncher.core.Settings;
import com.omninode.omnilauncher.util.Log;

/** The undecorated launcher window with custom chrome and edge resizing. */
public class LauncherWindow extends JFrame {

    private final LauncherShell shell;

    public LauncherWindow() {
        super("OmniLauncher");
        Theme.init();
        Settings s = Settings.get();
        setUndecorated(true);
        setDefaultCloseOperation(DISPOSE_ON_CLOSE);
        setSize(Math.max(980, s.windowWidth), Math.max(600, s.windowHeight));
        setLocationRelativeTo(null);

        try {
            var icon = Icons.grassBlock(128);
            setIconImage(icon);
            if (java.awt.Taskbar.isTaskbarSupported() && java.awt.Taskbar.getTaskbar()
                    .isSupported(java.awt.Taskbar.Feature.ICON_IMAGE)) {
                java.awt.Taskbar.getTaskbar().setIconImage(icon);
            }
        } catch (Throwable ignored) {
        }

        shell = new LauncherShell(this);
        setContentPane(shell);
        new WindowResizer(this).install();

        addWindowListener(new java.awt.event.WindowAdapter() {
            @Override public void windowClosed(java.awt.event.WindowEvent e) { saveState(); }
        });

        // minimize while the game runs (if the user asked for it)
        AppState.get().listen(() -> {
            if (AppState.get().getPhase() == AppState.Phase.RUNNING && !Settings.get().keepLauncherOpen) {
                setState(ICONIFIED);
            }
        });
    }

    private void saveState() {
        try {
            Settings s = Settings.get();
            if (getExtendedState() == MAXIMIZED_BOTH) {
                s.windowMaximized = true;
            } else {
                s.windowMaximized = false;
                s.windowWidth = getWidth();
                s.windowHeight = getHeight();
            }
            s.save();
        } catch (Exception ex) {
            Log.error("Could not save window state", ex);
        }
    }

    public static void showWindow() {
        SwingUtilities.invokeLater(() -> {
            LauncherWindow w = new LauncherWindow();
            w.setVisible(true);
            if (Settings.get().windowMaximized) w.setExtendedState(MAXIMIZED_BOTH);
            w.shell.onWindowShown();
        });
    }
}
