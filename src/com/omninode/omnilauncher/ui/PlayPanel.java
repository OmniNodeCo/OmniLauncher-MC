package com.omninode.omnilauncher.ui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Cursor;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Image;
import java.awt.Insets;
import java.awt.RenderingHints;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayDeque;
import java.util.Deque;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JComponent;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.Timer;

import com.omninode.omnilauncher.api.NewsService;
import com.omninode.omnilauncher.api.VersionManifest;
import com.omninode.omnilauncher.core.LaunchController;
import com.omninode.omnilauncher.core.Settings;
import com.omninode.omnilauncher.util.Log;
import com.omninode.omnilauncher.ui.Icons.Glyph;
import com.omninode.omnilauncher.ui.components.HoverCard;
import com.omninode.omnilauncher.ui.components.RButton;
import com.omninode.omnilauncher.ui.components.VersionComboBox;

/** The PLAY page: version picker, hero, PLAY button, status and news column. */
public class PlayPanel extends JPanel {

    public interface Host {
        void openAccounts();
        void showNews(NewsService.Item item);
        void showNewsPage();
    }

    private final VersionComboBox versionBox = new VersionComboBox();
    private final RButton refreshBtn = new RButton("", RButton.Kind.GHOST);
    private final RButton cancelBtn = new RButton("CANCEL", RButton.Kind.GHOST);
    private final PlayButton playButton = new PlayButton();
    private final javax.swing.JLabel statusDot = new javax.swing.JLabel();
    private final javax.swing.JLabel statusText = new javax.swing.JLabel("Loading versions…");
    private final JTextArea outputArea = new JTextArea();
    private final javax.swing.JPanel outputDrawer = new javax.swing.JPanel(new BorderLayout());
    private final RButton outputToggle = new RButton("GAME OUTPUT", RButton.Kind.GHOST);
    private final NewsColumn newsColumn;
    private final Host host;
    private boolean outputOpen;
    private final Deque<String> pendingOutput = new ArrayDeque<>();
    private final Timer outputPump;

    public PlayPanel(Host host) {
        this.host = host;
        setLayout(new BorderLayout());
        setBackground(Theme.BG);

        this.newsColumn = new NewsColumn();
        outputPump = new Timer(200, this::pumpOutput);
        outputPump.start();

        // ------------------------------------------------------ left column
        JPanel left = new JPanel(new GridBagLayout());
        left.setOpaque(false);

        JPanel pickerRow = new JPanel();
        pickerRow.setOpaque(false);
        pickerRow.setLayout(new BoxLayout(pickerRow, BoxLayout.X_AXIS));
        versionBox.setAlignmentY(0.5f);
        pickerRow.add(versionBox);
        pickerRow.add(Box.createHorizontalStrut(10));
        refreshBtn.setIcon(Icons.glyph(Glyph.REFRESH, 14, Theme.DIM));
        refreshBtn.setOverrideBg(null);
        refreshBtn.setPreferredSize(new Dimension(34, 50));
        refreshBtn.onClick(this::refreshManifest);
        refreshBtn.setAlignmentY(0.5f);
        pickerRow.add(refreshBtn);

        GridBagConstraints gc = new GridBagConstraints();
        gc.gridx = 0; gc.gridy = 0;
        gc.weightx = 1;
        gc.fill = GridBagConstraints.HORIZONTAL;
        gc.insets = new Insets(20, 28, 0, 24);
        left.add(pickerRow, gc);

        // hero block
        JPanel hero = new JPanel();
        hero.setOpaque(false);
        hero.setLayout(new BoxLayout(hero, BoxLayout.Y_AXIS));
        hero.setAlignmentX(0f);

        javax.swing.JLabel blockIcon = new javax.swing.JLabel(new javax.swing.ImageIcon(Icons.grassBlock(72)));
        blockIcon.setAlignmentX(0f);
        blockIcon.setBorder(BorderFactory.createEmptyBorder(26, 0, 18, 0));
        blockIcon.setMaximumSize(blockIcon.getPreferredSize());
        hero.add(blockIcon);

        hero.add(heroLabel("MINECRAFT", Theme.xbold(34f), Theme.TEXT));
        hero.add(heroLabel("J A V A   E D I T I O N", Theme.semi(12.5f), Theme.DIM));

        javax.swing.Box buttonRow = Box.createHorizontalBox();
        buttonRow.setAlignmentX(0f);
        buttonRow.setBorder(BorderFactory.createEmptyBorder(30, 0, 12, 0));
        buttonRow.setMaximumSize(new Dimension(Integer.MAX_VALUE, 104));
        playButton.setMaximumSize(new Dimension(300, 62));
        playButton.setMinimumSize(new Dimension(300, 62));
        buttonRow.add(playButton);
        buttonRow.add(javax.swing.Box.createHorizontalStrut(12));
        cancelBtn.setVisible(false);
        cancelBtn.setPreferredSize(new Dimension(96, 62));
        cancelBtn.setMaximumSize(new Dimension(96, 62));
        cancelBtn.setMinimumSize(new Dimension(96, 62));
        cancelBtn.setFont2(Theme.semi(12f));
        cancelBtn.onClick(() -> LaunchController.get().cancel());
        buttonRow.add(cancelBtn);
        hero.add(buttonRow);

        JPanel statusRow = new JPanel();
        statusRow.setOpaque(false);
        statusRow.setLayout(new BoxLayout(statusRow, BoxLayout.X_AXIS));
        statusRow.setAlignmentX(0f);
        statusRow.setMaximumSize(new Dimension(Integer.MAX_VALUE, 20));
        statusDot.setOpaque(true);
        statusDot.setPreferredSize(new Dimension(9, 9));
        statusDot.setMinimumSize(new Dimension(9, 9));
        statusDot.setMaximumSize(new Dimension(9, 9));
        statusDot.setBackground(Theme.STROKE);
        statusText.setFont(Theme.medium(12.5f));
        statusText.setForeground(Theme.DIM);
        statusRow.add(statusDot);
        statusRow.add(Box.createHorizontalStrut(9));
        statusRow.add(statusText);
        hero.add(statusRow);

        gc.gridy = 1;
        gc.weighty = 1;
        gc.fill = GridBagConstraints.BOTH;
        gc.insets = new Insets(0, 28, 0, 24);
        left.add(hero, gc);

        // output drawer
        outputDrawer.setOpaque(false);
        outputDrawer.setVisible(false);
        outputToggle.setIcon(Icons.glyph(Glyph.CHEVRON_DOWN, 12, Theme.DIM));
        outputToggle.setFont2(Theme.semi(10.5f));
        outputToggle.setPreferredSize(new Dimension(120, 26));
        outputToggle.onClick(() -> {
            outputOpen = !outputOpen;
            outputDrawer.setVisible(outputOpen);
            outputToggle.setIcon(Icons.glyph(Glyph.CHEVRON_DOWN, 12, Theme.DIM));
            revalidate();
        });
        outputArea.setEditable(false);
        outputArea.setBackground(new Color(0x141519));
        outputArea.setForeground(new Color(0xa8d5a2));
        outputArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 11));
        outputArea.setBorder(BorderFactory.createEmptyBorder(8, 10, 8, 10));
        JScrollPane outputScroll = Theme.scroll(outputArea);
        outputScroll.setBorder(BorderFactory.createMatteBorder(1, 0, 0, 0, Theme.STROKE_SOFT));
        outputDrawer.add(outputToggle, BorderLayout.NORTH);
        outputDrawer.add(outputScroll, BorderLayout.CENTER);
        outputDrawer.setPreferredSize(new Dimension(100, 170));

        gc.gridy = 2;
        gc.weighty = 0;
        gc.insets = new Insets(0, 28, 0, 0);
        left.add(outputDrawer, gc);

        add(left, BorderLayout.CENTER);
        add(newsColumn, BorderLayout.EAST);

        // wiring
        versionBox.setOnSelect(e -> {
            Settings.get().lastVersionId = e != null ? e.id() : "";
            Settings.get().save();
            playButton.repaint();
        });
        playButton.addActionListener(this::onPlayClicked);
        Log.addSink(line -> {
            synchronized (pendingOutput) { pendingOutput.add(line); }
        });
        AppState.get().listen(this::onStateChanged);
        VersionManifest.loadAsync(this::syncVersionBox, err ->
                AppState.get().setStatus("Could not load versions — offline?"));
        refreshNews();
        if (!VersionManifest.entries().isEmpty()) syncVersionBox();
        if (!NewsService.items().isEmpty()) newsColumn.refresh(null);
        onStateChanged();
    }

    /** Re-syncs data when the page becomes visible. */
    public void onShown() {
        if (VersionManifest.entries().isEmpty()) VersionManifest.loadAsync(this::syncVersionBox, null);
        else syncVersionBox();
        if (NewsService.items().isEmpty()) NewsService.loadAsync(() -> newsColumn.refresh(null), null);
        onStateChanged();
    }

    private javax.swing.JLabel heroLabel(String text, Font font, Color color) {
        javax.swing.JLabel l = new javax.swing.JLabel(text);
        l.setFont(font);
        l.setForeground(color);
        l.setAlignmentX(0f);
        l.setMaximumSize(new Dimension(Integer.MAX_VALUE, l.getPreferredSize().height));
        return l;
    }

    private void onPlayClicked(ActionEvent e) {
        LaunchController.get().play(currentEntry());
    }

    private VersionManifest.Entry currentEntry() {
        VersionManifest.Entry e = versionBox.getSelected();
        if (e != null) return e;
        return VersionManifest.resolveSelected(Settings.get().lastVersionId);
    }

    private void refreshManifest() {
        versionBox.setSelected(null, false);
        VersionManifest.loadAsync(this::syncVersionBox, null);
    }

    private void syncVersionBox() {
        VersionManifest.Entry selected = VersionManifest.resolveSelected(Settings.get().lastVersionId);
        versionBox.setSelected(selected, false);
        if (AppState.get().getPhase() == com.omninode.omnilauncher.ui.AppState.Phase.IDLE) {
            if (VersionManifest.isStaleCache())
                AppState.get().set(AppState.Phase.IDLE,
                        "Offline — showing the cached version list");
            else
                AppState.get().set(AppState.Phase.IDLE, "Ready to play");
        }
        playButton.repaint();
    }

    private void refreshNews() {
        NewsService.loadAsync(() -> newsColumn.refresh(null), null);
    }

    /* --------------------------------------------------------- reactions */

    private void onStateChanged() {
        AppState st = AppState.get();
        statusText.setText(st.getStatusText());
        Color dot = switch (st.getPhase()) {
            case IDLE -> Theme.STROKE;
            case PREPARING, INSTALLING, LAUNCHING -> Theme.AMBER;
            case RUNNING -> Theme.GREEN_HOVER;
            case ERROR -> Theme.RED;
        };
        statusDot.setBackground(dot);
        cancelBtn.setVisible(st.busy());
        playButton.repaint();
    }

    private void pumpOutput(ActionEvent e) {
        if (!outputOpen && outputDrawer.getWidth() == 0) {
            synchronized (pendingOutput) {
                boolean any = !pendingOutput.isEmpty();
                pendingOutput.clear();
                if (!any) return;
            }
            return;
        }
        StringBuilder sb = null;
        synchronized (pendingOutput) {
            while (!pendingOutput.isEmpty()) {
                if (sb == null) sb = new StringBuilder();
                sb.append(pendingOutput.poll()).append('\n');
            }
        }
        if (sb != null) {
            outputArea.append(sb.toString());
            if (outputArea.getLineCount() > 500) {
                try {
                    int end = outputArea.getLineEndOffset(Math.min(200, outputArea.getLineCount() - 1));
                    outputArea.getDocument().remove(0, end);
                } catch (Exception ignored) {}
            }
            outputArea.setCaretPosition(outputArea.getDocument().getLength());
        }
    }

    /* ------------------------------------------------------- play button */

    private class PlayButton extends JComponent {
        private final java.util.List<ActionListener> listeners = new java.util.ArrayList<>();

        PlayButton() {
            setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            setOpaque(false);
            AppState.get().listen(PlayButton.this::repaint);
            addMouseListener(new java.awt.event.MouseAdapter() {
                @Override public void mouseReleased(java.awt.event.MouseEvent e) {
                    if (contains(e.getPoint()) && AppState.get().getPhase() == AppState.Phase.IDLE
                            || (contains(e.getPoint()) && AppState.get().getPhase() == AppState.Phase.ERROR)) {
                        ActionEvent ev = new ActionEvent(PlayButton.this, ActionEvent.ACTION_PERFORMED, "play");
                        for (ActionListener l : listeners) l.actionPerformed(ev);
                    }
                }
            });
        }

        void addActionListener(ActionListener l) { listeners.add(l); }

        @Override public Dimension getPreferredSize() { return new Dimension(300, 62); }
        @Override public Dimension getMinimumSize() { return new Dimension(300, 62); }
        @Override public Dimension getMaximumSize() { return new Dimension(300, 62); }

        @Override protected void paintComponent(Graphics g0) {
            Graphics2D g = (Graphics2D) g0;
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            int w = getWidth(), h = getHeight();
            AppState st = AppState.get();
            var phase = st.getPhase();

            if (phase == AppState.Phase.PREPARING || phase == AppState.Phase.INSTALLING
                    || phase == AppState.Phase.LAUNCHING) {
                // morph into a progress bar
                g.setColor(new Color(0x17181c));
                g.fillRoundRect(0, 0, w, h, 12, 12);
                if (st.getProgress() >= 0) {
                    g.setColor(Theme.GREEN);
                    g.fillRoundRect(0, 0, Math.max(h, Math.round(w * st.getProgress())), h, 12, 12);
                    g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_OFF);
                }
                String label = st.getStatusText();
                if (st.getProgress() >= 0) label += " · " + Math.round(st.getProgress() * 100) + "%";
                g.setFont(Theme.semi(12.5f));
                var fm = g.getFontMetrics();
                while (fm.stringWidth(label) > w - 28 && label.length() > 4)
                    label = label.substring(0, label.length() - 5).trim() + "…";
                g.setColor(Theme.withAlpha(new Color(0x000000), 120));
                g.drawString(label, (w - fm.stringWidth(label)) / 2f + 1, (h + fm.getAscent()) / 2f - 1);
                g.setColor(Theme.TEXT);
                g.drawString(label, (w - fm.stringWidth(label)) / 2f, (h + fm.getAscent()) / 2f - 2);
            } else {
                boolean running = phase == AppState.Phase.RUNNING;
                Color fill = running ? Theme.CARD_HOVER : Theme.GREEN;
                g.setColor(Theme.withAlpha(new Color(0x000000), 80));
                g.fillRoundRect(2, 4, w - 4, h - 4, 12, 12);
                g.setColor(fill);
                g.fillRoundRect(0, 0, w, h, 12, 12);
                g.setColor(Theme.withAlpha(new Color(0xffffff), 26));
                g.fillRoundRect(0, 0, w, h / 2, 12, 12);
                String label = running ? "RUNNING" : "PLAY";
                g.setColor(running ? Theme.GREEN_TEXT : Color.WHITE);
                g.setFont(Theme.xbold(running ? 15f : 21f));
                var fm = g.getFontMetrics();
                if (!running) {
                    Image tri = Icons.glyph(Glyph.PLAY, 18, Color.WHITE);
                    int total = fm.stringWidth(label) + 34;
                    g.drawImage(tri, (w - total) / 2, (h - 18) / 2 + 1, 18, 18, null);
                    g.drawString(label, (w + 16 - total) / 2 + 16, (h + fm.getAscent()) / 2 - 2);
                } else {
                    g.drawString(label, (w - fm.stringWidth(label)) / 2f, (h + fm.getAscent()) / 2f - 2);
                }
            }
        }
    }

    /* ------------------------------------------------------- news column */

    public class NewsColumn extends JPanel {
        NewsColumn() {
            setLayout(new BoxLayout(this, BoxLayout.Y_AXIS));
            setBackground(Theme.BG);
            setBorder(BorderFactory.createEmptyBorder(0, 0, 0, 0));
            setPreferredSize(new Dimension(372, 100));
        }

        void refresh(NewsService.Item highlight) {
            removeAll();
            var header = javax.swing.Box.createHorizontalBox();
            header.setBorder(BorderFactory.createEmptyBorder(20, 24, 12, 24));
            javax.swing.JLabel t = new javax.swing.JLabel("NEWS");
            t.setFont(Theme.bold(12.5f));
            t.setForeground(Theme.TEXT);
            header.add(t);
            header.add(Box.createHorizontalGlue());
            RButton all = new RButton("View all", RButton.Kind.GHOST);
            all.setFont2(Theme.medium(11.5f));
            all.onClick(() -> host.showNewsPage());
            header.add(all);
            add(header);

            var items = NewsService.items();
            int count = Math.min(3, items.size());
            for (int i = 0; i < count; i++) {
                NewsService.Item item = items.get(i);
                add(makeCard(item, false));
                if (i < count - 1) add(javax.swing.Box.createVerticalStrut(10));
            }
            if (count == 0) {
                javax.swing.JLabel none = new javax.swing.JLabel(
                        items.isEmpty() ? "News will appear here." : "Loading news…");
                none.setFont(Theme.medium(12.5f));
                none.setForeground(Theme.FAINT);
                none.setBorder(BorderFactory.createEmptyBorder(8, 24, 0, 24));
                none.setAlignmentX(0f);
                add(none);
            }
            add(Box.createVerticalGlue());
            revalidate();
            repaint();
        }

        HoverCard makeCard(NewsService.Item item, boolean wide) {
            HoverCard card = new HoverCard();
            card.setLayout(new BorderLayout());
            card.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 14));
            card.onClick(() -> host.showNews(item));
            card.add(new ThumbLabel(item), BorderLayout.WEST);

            var textCol = Box.createVerticalBox();
            textCol.setBorder(BorderFactory.createEmptyBorder(2, 12, 2, 0));
            javax.swing.JLabel date = new javax.swing.JLabel(item.formattedDate().toUpperCase());
            date.setFont(Theme.semi(9.5f));
            date.setForeground(Theme.GREEN_TEXT);
            date.setAlignmentX(0f);
            textCol.add(date);
            javax.swing.JLabel title = new javax.swing.JLabel(
                    "<html><div style='width:172px'>" + escape(shorten(item.title(), 80)) + "</div></html>");
            title.setFont(Theme.semi(13f));
            title.setForeground(Theme.TEXT);
            title.setAlignmentX(0f);
            textCol.add(title);
            javax.swing.JLabel snippet = new javax.swing.JLabel(
                    "<html><div style='width:172px;color:#9aa1ad'>" + escape(shorten(item.shortText(), 74)) + "</div></html>");
            snippet.setFont(Theme.regular(11.5f));
            snippet.setAlignmentX(0f);
            textCol.add(snippet);
            card.add(textCol, BorderLayout.CENTER);
            return card;
        }
    }

    static String shorten(String s, int max) {
        if (s == null) return "";
        String clean = s.replaceAll("<[^>]+>", " ").replaceAll("\\s+", " ").trim();
        return clean.length() <= max ? clean : clean.substring(0, max - 1) + "…";
    }

    static String escape(String s) {
        return s == null ? "" : s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }

    /** Rounded news thumbnail that loads its image asynchronously. */
    static class ThumbLabel extends JComponent {
        private final NewsService.Item item;
        private Image image;

        ThumbLabel(NewsService.Item item) {
            this.item = item;
            setOpaque(false);
            setPreferredSize(new Dimension(128, 84));
            ImageLoader.load(item.imageUrl(), img -> {
                image = img;
                repaint();
            });
        }

        @Override protected void paintComponent(Graphics g0) {
            Graphics2D g = (Graphics2D) g0;
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            var shape = new java.awt.geom.RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 10, 10);
            g.setClip(shape);
            Image img = image != null ? image : Icons.newsPlaceholder(getWidth(), getHeight(), item.title());
            int iw = img.getWidth(null), ih = img.getHeight(null);
            if (iw > 0 && ih > 0) {
                double scale = Math.max(getWidth() / (double) iw, getHeight() / (double) ih);
                int dw = (int) (iw * scale), dh = (int) (ih * scale);
                g.drawImage(img, (getWidth() - dw) / 2, (getHeight() - dh) / 2, dw, dh, null);
            }
            g.setClip(null);
            g.setColor(Theme.withAlpha(Theme.STROKE_SOFT, 140));
            g.draw(shape);
        }
    }
}
