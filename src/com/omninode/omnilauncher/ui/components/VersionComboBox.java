package com.omninode.omnilauncher.ui.components;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Component;
import java.awt.Cursor;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Image;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

import javax.swing.DefaultListModel;
import javax.swing.JList;
import javax.swing.JPopupMenu;
import javax.swing.JScrollPane;
import javax.swing.ListCellRenderer;
import javax.swing.ListSelectionModel;

import com.omninode.omnilauncher.api.VersionManifest;
import com.omninode.omnilauncher.ui.Theme;

/**
 * The version picker: shows the currently selected version and opens a
 * searchable popup with releases / snapshots / classics.
 */
public class VersionComboBox extends javax.swing.JComponent {

    private VersionManifest.Entry selected;
    private Consumer<VersionManifest.Entry> onSelect;
    private final PopupPanel popupPanel = new PopupPanel();
    private final JPopupMenu popup = new JPopupMenu();

    public VersionComboBox() {
        setOpaque(false);
        setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        popup.setLayout(new BorderLayout());
        popup.add(popupPanel);
        popup.setFocusable(true);
        addMouseListener(new MouseAdapter() {
            @Override public void mouseReleased(MouseEvent e) {
                if (contains(e.getPoint())) showPopup();
            }
        });
        popupPanel.onSelect = entry -> {
            popup.setVisible(false);
            setSelected(entry, true);
        };
    }

    public void setOnSelect(Consumer<VersionManifest.Entry> c) { onSelect = c; }

    public void setSelected(VersionManifest.Entry e, boolean fire) {
        selected = e;
        repaint();
        if (fire && onSelect != null && e != null) onSelect.accept(e);
    }

    public VersionManifest.Entry getSelected() { return selected; }

    private void showPopup() {
        popupPanel.refresh();
        popup.setPopupSize(new Dimension(Math.max(380, getWidth()), 380));
        popup.show(this, 0, getHeight() + 4);
        popupPanel.focusSearch();
    }

    @Override public Dimension getPreferredSize() { return new Dimension(360, 50); }

    @Override protected void paintComponent(Graphics g0) {
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        int w = getWidth(), h = getHeight();
        g.setColor(Theme.CARD);
        g.fillRoundRect(0, 0, w, h, 10, 10);
        g.setColor(Theme.STROKE_SOFT);
        g.drawRoundRect(0, 0, w - 1, h - 1, 10, 10);

        String line1, line2;
        if (selected == null) {
            line1 = "LATEST RELEASE";
            line2 = VersionManifest.latestRelease().isEmpty() ? "Loading versions…" : VersionManifest.latestRelease();
        } else {
            boolean latest = selected.isRelease() && selected.id().equals(VersionManifest.latestRelease());
            line1 = (latest ? "Latest release" : typeLabel(selected.type())).toUpperCase();
            line2 = selected.id();
        }
        g.setFont(Theme.medium(10.5f));
        g.setColor(Theme.FAINT);
        g.drawString(line1, 14, 17);
        g.setFont(Theme.semi(13.5f));
        g.setColor(Theme.TEXT);
        g.drawString(line2, 14, 35);

        // chevron
        Image chev = com.omninode.omnilauncher.ui.Icons.glyph(
                com.omninode.omnilauncher.ui.Icons.Glyph.CHEVRON_DOWN, 14, Theme.DIM);
        g.drawImage(chev, w - 26, h / 2 - 7, 14, 14, null);
    }

    static String typeLabel(String type) {
        return switch (type) {
            case "snapshot" -> "Snapshot";
            case "old_beta" -> "Beta";
            case "old_alpha" -> "Alpha";
            default -> "Release";
        };
    }

    static Color typeColor(String type) {
        return switch (type) {
            case "snapshot" -> Theme.CHIP_SNAPSHOT;
            case "old_beta", "old_alpha" -> Theme.CHIP_OLD;
            default -> Theme.CHIP_RELEASE;
        };
    }

    /* ------------------------------------------------------------- popup */

    /** Standalone popup content for the headless UI preview. */
    public javax.swing.JComponent popupForPreview() {
        PopupPanel p = new PopupPanel();
        p.refresh();
        return p;
    }

    class PopupPanel extends javax.swing.JPanel {
        final javax.swing.JTextField search = new RTextField("Search versions…");
        final DefaultListModel<VersionManifest.Entry> model = new DefaultListModel<>();
        final JList<VersionManifest.Entry> list = new JList<>(model);
        Consumer<VersionManifest.Entry> onSelect;

        PopupPanel() {
            setLayout(new BorderLayout());
            setBackground(Theme.PANEL);
            setPreferredSize(new Dimension(420, 380));
            search.setBorder(javax.swing.BorderFactory.createEmptyBorder(10, 12, 10, 12));
            search.setFont(Theme.medium(13f));
            search.getDocument().addDocumentListener(new javax.swing.event.DocumentListener() {
                public void insertUpdate(javax.swing.event.DocumentEvent e) { refresh(); }
                public void removeUpdate(javax.swing.event.DocumentEvent e) { refresh(); }
                public void changedUpdate(javax.swing.event.DocumentEvent e) { refresh(); }
            });
            add(search, BorderLayout.NORTH);

            list.setCellRenderer(new RowRenderer());
            list.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
            list.setFixedCellHeight(44);
            list.addMouseListener(new MouseAdapter() {
                @Override public void mouseReleased(MouseEvent e) {
                    int i = list.locationToIndex(e.getPoint());
                    if (i >= 0 && list.getCellBounds(i, i).contains(e.getPoint()) && onSelect != null) {
                        onSelect.accept(model.get(i));
                    }
                }
            });
            list.addListSelectionListener(e -> {
                if (!e.getValueIsAdjusting() && onSelect != null) {
                    VersionManifest.Entry en = list.getSelectedValue();
                    if (en != null) { onSelect.accept(en); }
                }
            });
            add(Theme.scroll(list), BorderLayout.CENTER);
        }

        void focusSearch() { search.requestFocusInWindow(); }

        void refresh() {
            String q = search.getText() == null ? "" : search.getText().trim().toLowerCase();
            List<VersionManifest.Entry> all = VersionManifest.visibleEntries(
                    com.omninode.omnilauncher.core.Settings.get().showSnapshots,
                    com.omninode.omnilauncher.core.Settings.get().showHistorical);
            List<VersionManifest.Entry> out = new ArrayList<>();
            for (VersionManifest.Entry e : all) {
                if (q.isEmpty() || e.id().toLowerCase().contains(q)) out.add(e);
            }
            model.clear();
            for (VersionManifest.Entry e : out) model.addElement(e);
            if (selected != null) list.setSelectedValue(selected, false);
        }
    }

    private static class RowRenderer implements ListCellRenderer<VersionManifest.Entry> {
        @Override public Component getListCellRendererComponent(
                JList<? extends VersionManifest.Entry> list, VersionManifest.Entry value,
                int index, boolean isSelected, boolean cellHasFocus) {
            javax.swing.JPanel p = new javax.swing.JPanel(null) {
                @Override protected void paintComponent(Graphics g0) {
                    Graphics2D g = (Graphics2D) g0;
                    g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                    g.setColor(isSelected ? Theme.CARD_HOVER : Theme.PANEL);
                    g.fillRect(0, 0, getWidth(), getHeight());
                    g.setFont(Theme.semi(13f));
                    g.setColor(Theme.TEXT);
                    g.drawString(value.id(), 14, 19);
                    String label = typeLabel(value.type());
                    g.setFont(Theme.semi(10f));
                    int lw = g.getFontMetrics().stringWidth(label);
                    g.setColor(typeColor(value.type()));
                    g.drawString(label, getWidth() - lw - 16, 19);
                    g.setFont(Theme.regular(10.5f));
                    g.setColor(Theme.FAINT);
                    String date = value.releaseTime();
                    if (date.length() >= 10) date = date.substring(0, 10);
                    g.drawString(date, 14, 36);
                    if (!isSelected) {
                        g.setColor(Theme.withAlpha(Theme.STROKE_SOFT, 120));
                        g.drawLine(0, getHeight() - 1, getWidth(), getHeight() - 1);
                    }
                }
            };
            p.setPreferredSize(new Dimension(100, 44));
            return p;
        }
    }
}
