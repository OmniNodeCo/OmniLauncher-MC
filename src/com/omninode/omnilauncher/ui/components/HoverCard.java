package com.omninode.omnilauncher.ui.components;

import java.awt.Cursor;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

import javax.swing.JPanel;

import com.omninode.omnilauncher.ui.Theme;

/** Rounded card panel with optional hover highlight and click handling. */
public class HoverCard extends JPanel {

    private final boolean hoverable;
    private boolean hover;
    private Runnable onClick;

    public HoverCard() { this(true); }

    public HoverCard(boolean hoverable) {
        this.hoverable = hoverable;
        setOpaque(false);
        if (hoverable) {
            setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            addMouseListener(new MouseAdapter() {
                @Override public void mouseEntered(MouseEvent e) { hover = true; repaint(); }
                @Override public void mouseExited(MouseEvent e) { hover = false; repaint(); }
                @Override public void mouseReleased(MouseEvent e) {
                    if (onClick != null && contains(e.getPoint())) onClick.run();
                }
            });
        }
    }

    public void onClick(Runnable r) { onClick = r; }

    @Override protected void paintComponent(Graphics g0) {
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(hover && hoverable ? Theme.CARD_HOVER : Theme.CARD);
        g.fillRoundRect(0, 0, getWidth(), getHeight(), 12, 12);
        if (hover && hoverable) {
            g.setColor(Theme.withAlpha(Theme.GREEN, 60));
            g.drawRoundRect(0, 0, getWidth() - 1, getHeight() - 1, 12, 12);
        }
        super.paintComponent(g0);
    }
}
