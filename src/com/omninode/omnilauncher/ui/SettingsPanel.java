package com.omninode.omnilauncher.ui;

import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.io.File;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JFileChooser;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JComponent;
import javax.swing.JScrollPane;
import javax.swing.Timer;

import com.omninode.omnilauncher.core.GameLauncher;
import com.omninode.omnilauncher.core.Settings;
import com.omninode.omnilauncher.ui.components.HoverCard;
import com.omninode.omnilauncher.ui.components.RButton;
import com.omninode.omnilauncher.ui.components.RSlider;
import com.omninode.omnilauncher.ui.components.RTextField;
import com.omninode.omnilauncher.ui.components.Toggle;

/** SETTINGS page: Java, game, content filters, accounts, about. */
public class SettingsPanel extends JPanel {

    private final Settings s = Settings.get();
    private final Timer saveDebounce;

    public SettingsPanel(Runnable openAccounts) {
        setLayout(new BorderLayout());
        setBackground(Theme.BG);

        saveDebounce = new Timer(500, e -> s.save());
        saveDebounce.setRepeats(false);

        JPanel column = new JPanel();
        column.setOpaque(false);
        column.setLayout(new BoxLayout(column, BoxLayout.Y_AXIS));
        column.setBorder(BorderFactory.createEmptyBorder(18, 28, 24, 28));

        column.add(sectionTitle("LAUNCHER"));
        column.add(Box.createVerticalStrut(10));

        // ---------------------------------------------------- Java section
        HoverCard javaCard = section();
        column.add(javaCard);
        addRow(javaCard, 0, "Java runtime",
                "Path to the java executable used to start the game. Leave empty to auto-detect.");
        RTextField javaPath = text(javaCard, s.javaPath, 1);
        javaPath.getDocument().addDocumentListener(simple(() -> {
            s.javaPath = javaPath.getText().trim();
            GameLauncher.clearCache();
            touch();
        }));
        addButtons(javaCard, 2,
                new String[]{"Browse…", "Auto-detect"},
                new Runnable[]{
                        () -> {
                            JFileChooser fc = new JFileChooser(s.javaPath.isBlank()
                                    ? new File(System.getProperty("java.home")) : new File(s.javaPath));
                            fc.setFileSelectionMode(JFileChooser.FILES_ONLY);
                            if (fc.showOpenDialog(this) == JFileChooser.APPROVE_OPTION) {
                                javaPath.setText(fc.getSelectedFile().getAbsolutePath());
                            }
                        },
                        () -> {
                            GameLauncher.clearCache();
                            GameLauncher.JavaRuntime rt = GameLauncher.findJava();
                            if (rt != null) {
                                javaPath.setText(rt.javaExe().toString());
                                status(javaCard, "Found Java " + rt.major() + " — " + rt.javaExe());
                            } else {
                                status(javaCard, "No Java runtime found. Install Java 21+ and try again.");
                            }
                        }});
        addRow(javaCard, 3, "Memory", "Maximum RAM (−Xmx) given to the game.");
        RSlider memSlider = new RSlider(1024, 16384, 256, s.memoryMb);
        memSlider.setLabelFn(v -> (v / 1024) + " GB");
        JLabel memLabel = valueLabel(javaCard, (s.memoryMb / 1024) + " GB", 4);
        memSlider.onChange(v -> { memLabel.setText((v / 1024) + " GB"); s.memoryMb = v; touch(); });
        place(javaCard, memSlider, 5);
        addRow(javaCard, 6, "Extra JVM arguments", "Added before the game arguments (quotes supported).");
        RTextField jvmArgs = text(javaCard, s.extraJvmArgs, 7);
        jvmArgs.getDocument().addDocumentListener(simple(() -> { s.extraJvmArgs = jvmArgs.getText(); touch(); }));
        addToggle(javaCard, 8, "Download the right Java automatically",
                "Fetch Mojang's matching runtime (java-runtime-*) for each version on first play.",
                s.autoDownloadJava, v -> s.autoDownloadJava = v);

        // ---------------------------------------------------- Game section
        column.add(Box.createVerticalStrut(14));
        column.add(sectionTitle("GAME"));
        column.add(Box.createVerticalStrut(10));
        HoverCard gameCard = section();
        column.add(gameCard);
        addRow(gameCard, 0, "Game directory",
                "Where worlds, resource packs and screenshots live (.minecraft).");
        RTextField gameDir = text(gameCard, s.gameDir, 1);
        gameDir.getDocument().addDocumentListener(simple(() -> { s.gameDir = gameDir.getText().trim(); touch(); }));
        addButtons(gameCard, 2, new String[]{"Browse…", "Use default"}, new Runnable[]{
                () -> {
                    JFileChooser fc = new JFileChooser(s.resolveGameDir().toFile());
                    fc.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
                    if (fc.showOpenDialog(this) == JFileChooser.APPROVE_OPTION)
                        gameDir.setText(fc.getSelectedFile().getAbsolutePath());
                },
                () -> gameDir.setText("")});
        addRow(gameCard, 3, "Window size", "In-game window size on launch.");
        RTextField w = text(gameCard, String.valueOf(s.gameWidth), 4);
        RTextField h = text(gameCard, String.valueOf(s.gameHeight), 4);
        w.setColumns(6); h.setColumns(6);
        JPanel res = new JPanel(new java.awt.FlowLayout(java.awt.FlowLayout.LEFT, 8, 0));
        res.setOpaque(false);
        res.add(w); res.add(new JLabel("×")); res.add(h);
        ((JLabel) res.getComponent(1)).setForeground(Theme.DIM);
        place(gameCard, res, 4);
        w.getDocument().addDocumentListener(simple(() -> { s.gameWidth = parseInt(w.getText(), 854); touch(); }));
        h.getDocument().addDocumentListener(simple(() -> { s.gameHeight = parseInt(h.getText(), 480); touch(); }));
        addToggle(gameCard, 5, "Fullscreen", "Launch the game in fullscreen mode.", s.fullscreen,
                v -> s.fullscreen = v);
        addRow(gameCard, 6, "Extra game arguments", "Passed straight to the Minecraft client.");
        RTextField gameArgs = text(gameCard, s.extraGameArgs, 7);
        gameArgs.getDocument().addDocumentListener(simple(() -> { s.extraGameArgs = gameArgs.getText(); touch(); }));

        // ------------------------------------------------- Content section
        column.add(Box.createVerticalStrut(14));
        column.add(sectionTitle("VERSIONS"));
        column.add(Box.createVerticalStrut(10));
        HoverCard contentCard = section();
        column.add(contentCard);
        addToggle(contentCard, 0, "Show snapshots", "List experimental snapshot versions.", s.showSnapshots,
                v -> s.showSnapshots = v);
        addToggle(contentCard, 1, "Show beta & alpha versions", "List historical (2010–2013) versions.",
                s.showHistorical, v -> s.showHistorical = v);

        // ------------------------------------------------ Launcher section
        column.add(Box.createVerticalStrut(14));
        column.add(sectionTitle("ACCOUNTS & DOWNLOADS"));
        column.add(Box.createVerticalStrut(10));
        HoverCard accCard = section();
        column.add(accCard);
        addRow(accCard, 0, "Microsoft client ID",
                "Azure app ID used for Microsoft sign-in. See the README for a 2-minute setup guide.");
        RTextField clientId = text(accCard, s.msaClientId, 1);
        clientId.getDocument().addDocumentListener(simple(() -> { s.msaClientId = clientId.getText().trim(); touch(); }));
        addButtons(accCard, 2, new String[]{"Manage accounts"}, new Runnable[]{openAccounts});
        addRow(accCard, 3, "Download threads", "Parallel connections used when installing files.");
        RSlider concSlider = new RSlider(2, 16, 1, s.concurrency);
        JLabel concLabel = valueLabel(accCard, s.concurrency + " threads", 4);
        concSlider.onChange(v -> { concLabel.setText(v + " threads"); s.concurrency = v; touch(); });
        place(accCard, concSlider, 5);
        addToggle(accCard, 6, "Keep launcher open", "Keep this window visible while the game runs.",
                s.keepLauncherOpen, v -> s.keepLauncherOpen = v);

        // ------------------------------------------------------- About box
        column.add(Box.createVerticalStrut(14));
        column.add(sectionTitle("ABOUT"));
        column.add(Box.createVerticalStrut(10));
        HoverCard about = section();
        column.add(about);
        JLabel logo = new JLabel(new javax.swing.ImageIcon(Icons.grassBlock(44)));
        place(about, logo, 0);
        JLabel aboutText = new JLabel("<html><div style='width:560px'>"
                + "<b>OmniLauncher 2.0</b> — a native, dependency-free Minecraft launcher.<br>"
                + "Pure Java 17. No Electron, no HTML, no Python. <br><br>"
                + "<span style='color:#6b7280'>Not an official Minecraft product. "
                + "Not approved by or associated with Mojang or Microsoft.</span></div></html>");
        aboutText.setFont(Theme.regular(12.5f));
        aboutText.setForeground(Theme.DIM);
        place(about, aboutText, 1);

        JScrollPane scroll = Theme.scroll(column);
        add(scroll, BorderLayout.CENTER);
    }

    private void touch() { saveDebounce.restart(); }

    private int parseInt(String v, int def) {
        try { return Integer.parseInt(v.trim()); } catch (Exception e) { return def; }
    }

    private javax.swing.event.DocumentListener simple(Runnable r) {
        return new javax.swing.event.DocumentListener() {
            public void insertUpdate(javax.swing.event.DocumentEvent e) { r.run(); }
            public void removeUpdate(javax.swing.event.DocumentEvent e) { r.run(); }
            public void changedUpdate(javax.swing.event.DocumentEvent e) { r.run(); }
        };
    }

    /* ------------------------------------------------------- scaffolding */

    private JLabel sectionTitle(String text) {
        JLabel l = new JLabel(text);
        l.setFont(Theme.bold(12.5f));
        l.setForeground(Theme.TEXT);
        l.setAlignmentX(0f);
        return l;
    }

    private HoverCard section() {
        HoverCard card = new HoverCard(false);
        card.setLayout(new GridBagLayout());
        card.setAlignmentX(0f);
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, Integer.MAX_VALUE));
        return card;
    }

    private GridBagConstraints gc(int row, boolean span, int padTop) {
        GridBagConstraints g = new GridBagConstraints();
        g.gridx = span ? 0 : 1;
        g.gridy = row;
        g.weightx = span ? 1 : 0;
        g.fill = span ? GridBagConstraints.HORIZONTAL : GridBagConstraints.NONE;
        g.anchor = span ? GridBagConstraints.WEST : GridBagConstraints.NORTHWEST;
        g.insets = new Insets(padTop, 18, 8, 18);
        return g;
    }

    private void addRow(HoverCard card, int row, String title, String hint) {
        var box = Box.createVerticalBox();
        JLabel t = new JLabel(title);
        t.setFont(Theme.semi(13f));
        t.setForeground(Theme.TEXT);
        t.setAlignmentX(0f);
        JLabel hh = new JLabel("<html><div style='width:520px'>" + hint + "</div></html>");
        hh.setFont(Theme.regular(11f));
        hh.setForeground(Theme.FAINT);
        hh.setAlignmentX(0f);
        box.add(t);
        box.add(hh);
        card.add(box, gc(row, true, 16));
    }

    private RTextField text(HoverCard card, String initial, int row) {
        RTextField f = new RTextField();
        f.setText(initial);
        f.setFont(Theme.medium(13f));
        f.setPreferredSize(new Dimension(420, 38));
        place(card, f, row);
        return f;
    }

    private void place(HoverCard card, JComponent c, int row) {
        card.add(c, gc(row, true, 8));
    }

    private JLabel valueLabel(HoverCard card, String initial, int row) {
        JLabel l = new JLabel(initial);
        l.setFont(Theme.semi(12.5f));
        l.setForeground(Theme.GREEN_TEXT);
        l.setHorizontalAlignment(JLabel.RIGHT);
        GridBagConstraints g = gc(row, false, 8);
        g.anchor = GridBagConstraints.NORTHEAST;
        card.add(l, g);
        return l;
    }

    private void addButtons(HoverCard card, int row, String[] labels, Runnable[] actions) {
        JPanel p = new JPanel(new java.awt.FlowLayout(java.awt.FlowLayout.LEFT, 10, 0));
        p.setOpaque(false);
        for (int i = 0; i < labels.length; i++) {
            RButton b = new RButton(labels[i], RButton.Kind.NEUTRAL);
            final Runnable r = actions[i];
            b.onClick(r);
            p.add(b);
        }
        place(card, p, row);
    }

    private void addToggle(HoverCard card, int row, String title, String hint, boolean value,
                           java.util.function.Consumer<Boolean> setter) {
        addRow(card, row, title, hint);
        Toggle t = new Toggle(value);
        t.onChange(v -> { setter.accept(v); touch(); });
        GridBagConstraints g = gc(row, false, 20);
        g.anchor = GridBagConstraints.NORTHEAST;
        card.add(t, g);
    }

    private void status(HoverCard card, String text) {
        JLabel existing = null;
        for (Component c : card.getComponents()) {
            if (c instanceof JLabel l && "status".equals(l.getName())) { existing = l; break; }
        }
        if (existing != null) card.remove(existing);
        JLabel l = new JLabel(text);
        l.setName("status");
        l.setFont(Theme.medium(11.5f));
        l.setForeground(Theme.GREEN_TEXT);
        GridBagConstraints g = gc(card.getComponentCount(), true, 0);
        g.insets = new Insets(0, 18, 14, 18);
        card.add(l, g);
        card.revalidate();
        card.repaint();
    }
}
