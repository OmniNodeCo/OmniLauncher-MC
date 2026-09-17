package com.omninode.omnilauncher.ui.components;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.Rectangle;

import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.plaf.basic.BasicScrollBarUI;

import com.omninode.omnilauncher.ui.Theme;

/** Thin rounded scrollbar that fits the dark theme. */
public class ModernScrollBarUi extends BasicScrollBarUI {

    @Override protected void configureScrollBarColors() {
        this.thumbColor = Theme.STROKE;
        this.trackColor = new Color(0, 0, 0, 0);
        this.thumbDarkShadowColor = null;
        this.thumbLightShadowColor = null;
        this.thumbHighlightColor = Theme.CARD_HOVER;
    }

    @Override protected JButton createDecreaseButton(int orientation) { return invisible(); }
    @Override protected JButton createIncreaseButton(int orientation) { return invisible(); }

    private static JButton invisible() {
        JButton b = new JButton();
        b.setPreferredSize(new Dimension(0, 0));
        b.setFocusable(false);
        return b;
    }

    @Override protected void paintTrack(Graphics g, JComponent c, Rectangle r) {
        // invisible track
    }

    @Override protected void paintThumb(Graphics g0, JComponent c, Rectangle r) {
        if (r.width <= 0 || r.height <= 0) return;
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(isThumbRollover() ? Theme.lighten(Theme.STROKE, 0.08f) : Theme.STROKE);
        int pad = 2;
        if (r.width > r.height) g.fillRoundRect(r.x + pad, r.y, r.width - 2 * pad, r.height, 6, 6);
        else g.fillRoundRect(r.x, r.y + pad, r.width, r.height - 2 * pad, 6, 6);
    }

    @Override public Dimension getPreferredSize(JComponent c) {
        return scrollbar.getOrientation() == javax.swing.SwingConstants.HORIZONTAL ? new Dimension(super.getPreferredSize(c).width, 8)
                : new Dimension(8, super.getPreferredSize(c).height);
    }
}
