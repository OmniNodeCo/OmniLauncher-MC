package com.omninode.omnilauncher.ui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Image;
import java.awt.Insets;
import java.awt.RenderingHints;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JComponent;
import javax.swing.JEditorPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.SwingUtilities;

import com.omninode.omnilauncher.api.NewsService;
import com.omninode.omnilauncher.ui.components.HoverCard;
import com.omninode.omnilauncher.ui.components.RButton;
import com.omninode.omnilauncher.ui.components.RTextField;

/** PATCH NOTES page: list of official Mojang news with a detail reader. */
public class NewsPanel extends JPanel {

    private final JPanel listWrapper = new JPanel();
    private final JPanel listCard = new JPanel();
    private final JPanel detail = new JPanel(new BorderLayout());
    private final RTextField search = new RTextField("Search notes…");
    private final java.awt.CardLayout cards = new java.awt.CardLayout();
    private NewsService.Item currentDetail;

    public NewsPanel() {
        setLayout(new java.awt.CardLayout() == null ? null : cards);
        setBackground(Theme.BG);

        // ------------------------------------------------------------- list
        listWrapper.setOpaque(false);
        listWrapper.setLayout(new BorderLayout());
        listCard.setOpaque(false);
        listCard.setLayout(new BorderLayout());

        JPanel header = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 14));
        header.setOpaque(false);
        header.setBorder(BorderFactory.createEmptyBorder(6, 28, 2, 24));
        javax.swing.JLabel title = new javax.swing.JLabel("PATCH NOTES");
        title.setFont(Theme.xbold(17f));
        title.setForeground(Theme.TEXT);
        header.add(title);
        javax.swing.JLabel count = new javax.swing.JLabel("");
        count.setFont(Theme.medium(12f));
        count.setForeground(Theme.FAINT);
        header.add(count);
        header.add(Box.createHorizontalStrut(24));
        search.setPreferredSize(new Dimension(240, 36));
        search.getDocument().addDocumentListener(new javax.swing.event.DocumentListener() {
            public void insertUpdate(javax.swing.event.DocumentEvent e) { rebuildRows(); }
            public void removeUpdate(javax.swing.event.DocumentEvent e) { rebuildRows(); }
            public void changedUpdate(javax.swing.event.DocumentEvent e) { rebuildRows(); }
        });
        header.add(search);
        listCard.add(header, BorderLayout.NORTH);

        JPanel rows = new JPanel();
        rows.setOpaque(false);
        rows.setLayout(new BoxLayout(rows, BoxLayout.Y_AXIS));
        JScrollPane scroll = Theme.scroll(rows);
        listCard.add(scroll, BorderLayout.CENTER);
        listWrapper.add(listCard, BorderLayout.CENTER);
        add(listWrapper, "list");

        // ----------------------------------------------------------- detail
        detail.setOpaque(false);
        add(detail, "detail");
        cards.show(this, "list");

        NewsService.loadAsync(() -> rebuildRows(), err -> rebuildRows());
        if (!NewsService.items().isEmpty()) rebuildRows();
    }

    private void rebuildRows() {
        // find the rows container
        JScrollPane scroll = (JScrollPane) listCard.getComponent(1);
        JPanel rows = (JPanel) scroll.getViewport().getView();
        rows.removeAll();
        String q = search.getText() == null ? "" : search.getText().trim().toLowerCase();
        var items = NewsService.items();
        ((javax.swing.JLabel) ((JPanel) listCard.getComponent(0)).getComponent(1))
                .setText(items.isEmpty() ? "" : items.size() + " entries");
        for (NewsService.Item item : items) {
            if (!q.isEmpty() && !item.title().toLowerCase().contains(q)
                    && !item.shortText().toLowerCase().contains(q)) continue;
            rows.add(makeRow(item));
            rows.add(Box.createVerticalStrut(12));
        }
        if (rows.getComponentCount() == 0) {
            var empty = new javax.swing.JLabel(items.isEmpty()
                    ? "Could not load news — check your connection."
                    : "No matching entries.");
            empty.setFont(Theme.medium(13f));
            empty.setForeground(Theme.FAINT);
            empty.setBorder(BorderFactory.createEmptyBorder(24, 4, 0, 0));
            empty.setAlignmentX(0f);
            rows.add(empty);
        }
        rows.revalidate();
        rows.repaint();
    }

    private JComponent makeRow(NewsService.Item item) {
        HoverCard card = new HoverCard();
        card.setLayout(new BorderLayout());
        card.setBorder(BorderFactory.createEmptyBorder(12, 14, 12, 18));
        card.onClick(() -> showDetail(item));

        card.add(new RowThumb(item), BorderLayout.WEST);

        var text = Box.createVerticalBox();
        text.setBorder(BorderFactory.createEmptyBorder(2, 16, 2, 0));
        var date = new javax.swing.JLabel(item.formattedDate().toUpperCase() + "  ·  "
                + item.category().toUpperCase());
        date.setFont(Theme.semi(10f));
        date.setForeground(Theme.GREEN_TEXT);
        date.setAlignmentX(0f);
        text.add(date);
        var title = new javax.swing.JLabel("<html><div style='width:600px'>"
                + PlayPanel.escape(item.title()) + "</div></html>");
        title.setFont(Theme.bold(15.5f));
        title.setForeground(Theme.TEXT);
        title.setAlignmentX(0f);
        text.add(title);
        var snippet = new javax.swing.JLabel("<html><div style='width:600px;color:#9aa1ad'>"
                + PlayPanel.escape(PlayPanel.shorten(item.shortText(), 150)) + "</div></html>");
        snippet.setFont(Theme.regular(12.5f));
        snippet.setAlignmentX(0f);
        text.add(snippet);
        card.add(text, BorderLayout.CENTER);
        var wrap = new JPanel(new GridBagLayout());
        wrap.setOpaque(false);
        wrap.setAlignmentX(0f);
        var gc = new GridBagConstraints();
        gc.gridx = 0; gc.weightx = 1; gc.fill = GridBagConstraints.HORIZONTAL;
        gc.insets = new Insets(0, 28, 0, 28);
        wrap.add(card, gc);
        return wrap;
    }

    public void showDetail(NewsService.Item item) {
        detail.removeAll();
        JPanel inner = new JPanel(new GridBagLayout());
        inner.setOpaque(false);

        var gc = new GridBagConstraints();
        gc.gridx = 0; gc.gridy = 0;
        gc.anchor = GridBagConstraints.WEST;
        gc.fill = GridBagConstraints.HORIZONTAL;
        gc.weightx = 1;
        gc.insets = new Insets(18, 28, 8, 28);

        var headerRow = Box.createHorizontalBox();
        RButton back = new RButton("All patch notes", RButton.Kind.GHOST);
        back.setIcon(Icons.glyph(Icons.Glyph.BACK, 13, Theme.DIM));
        back.setFont2(Theme.semi(12f));
        back.setAlignmentY(0.5f);
        back.onClick(() -> cards.show(this, "list"));
        headerRow.add(Box.createHorizontalGlue());
        headerRow.add(back);
        headerRow.add(Box.createHorizontalGlue());
        inner.add(headerRow, gc);

        gc.gridy++;
        gc.insets = new Insets(6, 28, 2, 28);
        var date = new javax.swing.JLabel(item.formattedDate().toUpperCase() + "  ·  "
                + item.category().toUpperCase());
        date.setFont(Theme.semi(10.5f));
        date.setForeground(Theme.GREEN_TEXT);
        inner.add(date, gc);

        gc.gridy++;
        gc.insets = new Insets(2, 28, 14, 28);
        var title = new javax.swing.JLabel(
                "<html><div style='width:760px'>" + PlayPanel.escape(item.title()) + "</div></html>");
        title.setFont(Theme.xbold(24f));
        title.setForeground(Theme.TEXT);
        inner.add(title, gc);

        if (item.imageUrl() != null) {
            gc.gridy++;
            var img = new DetailImage(item);
            gc.insets = new Insets(0, 28, 16, 28);
            inner.add(img, gc);
        }

        gc.gridy++;
        gc.weighty = 1;
        gc.fill = GridBagConstraints.BOTH;
        gc.insets = new Insets(0, 28, 20, 28);
        JEditorPane body = new JEditorPane();
        body.setEditable(false);
        body.setOpaque(false);
        body.setBackground(Theme.BG);
        body.setForeground(Theme.TEXT);
        body.putClientProperty(JEditorPane.HONOR_DISPLAY_PROPERTIES, Boolean.TRUE);
        var kit = new javax.swing.text.html.HTMLEditorKit();
        var sheet = kit.getStyleSheet();
        sheet.addRule("body { font-family: Montserrat; font-size: 12pt; color: #c9ced6; width: 720px }"
                + " a { color: #4daafc } h1,h2,h3 { color: #ebedf2 } p { line-height: 160% }");
        body.setEditorKit(kit);
        body.setText("<html><body>" + item.longText() + "</body></html>");
        body.setCaretPosition(0);
        var bodyScroll = Theme.scroll(body);
        inner.add(bodyScroll, gc);

        detail.add(inner, BorderLayout.CENTER);
        cards.show(this, "detail");
        revalidate();
        repaint();
    }

    /** Rounded row thumbnail. */
    private static class RowThumb extends JComponent {
        private final NewsService.Item item;
        private Image image;

        RowThumb(NewsService.Item item) {
            this.item = item;
            setPreferredSize(new Dimension(168, 94));
            setOpaque(false);
            ImageLoader.load(item.imageUrl(), img -> { image = img; repaint(); });
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
                g.drawImage(img, (getWidth() - (int) (iw * scale)) / 2, (getHeight() - (int) (ih * scale)) / 2,
                        (int) (iw * scale), (int) (ih * scale), null);
            }
            g.setClip(null);
            g.setColor(Theme.withAlpha(Theme.STROKE_SOFT, 140));
            g.draw(shape);
        }
    }

    /** 16:9 detail banner. */
    private static class DetailImage extends JComponent {
        private final NewsService.Item item;
        private Image image;

        DetailImage(NewsService.Item item) {
            this.item = item;
            setPreferredSize(new Dimension(760, 260));
            ImageLoader.load(item.imageUrl(), img -> { image = img; repaint(); });
        }

        @Override protected void paintComponent(Graphics g0) {
            Graphics2D g = (Graphics2D) g0;
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            var shape = new java.awt.geom.RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 12, 12);
            g.setClip(shape);
            Image img = image != null ? image : Icons.newsPlaceholder(getWidth(), getHeight(), item.title());
            int iw = img.getWidth(null), ih = img.getHeight(null);
            if (iw > 0 && ih > 0) {
                double scale = Math.max(getWidth() / (double) iw, getHeight() / (double) ih);
                g.drawImage(img, (getWidth() - (int) (iw * scale)) / 2, (getHeight() - (int) (ih * scale)) / 2,
                        (int) (iw * scale), (int) (ih * scale), null);
            }
            g.setClip(null);
            g.setColor(Theme.withAlpha(Theme.STROKE_SOFT, 160));
            g.draw(shape);
        }
    }
}
