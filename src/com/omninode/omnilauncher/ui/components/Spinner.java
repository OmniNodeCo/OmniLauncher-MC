package com.omninode.omnilauncher.ui.components;

import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.event.ActionEvent;

import javax.swing.JComponent;
import javax.swing.Timer;

import com.omninode.omnilauncher.ui.Theme;

/** Animated indeterminate spinner. */
public class Spinner extends JComponent {

    private float angle;
    private final Timer timer = new Timer(30, (ActionEvent e) -> {
        angle += 11f;
        if (angle >= 360) angle -= 360;
        repaint();
    });

    public Spinner(int size) {
        setPreferredSize(new Dimension(size, size));
        setOpaque(false);
    }

    public void start() { timer.start(); }
    public void stop() { timer.stop(); }

    @Override public Dimension getPreferredSize() { return super.getPreferredSize(); }

    @Override protected void paintComponent(Graphics g0) {
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        int s = Math.min(getWidth(), getHeight());
        int arc = Math.max(6, s / 4);
        g.setColor(Theme.STROKE);
        g.setStroke(new java.awt.BasicStroke(Math.max(2f, s / 14f), java.awt.BasicStroke.CAP_ROUND,
                java.awt.BasicStroke.JOIN_ROUND));
        int m = arc;
        g.drawArc(m, m, s - 2 * m, s - 2 * m, 0, 360);
        g.setColor(Theme.GREEN_HOVER);
        g.drawArc(m, m, s - 2 * m, s - 2 * m, (int) angle, 100);
    }

    @Override public void removeNotify() {
        timer.stop();
        super.removeNotify();
    }
}
