package com.omninode.omnilauncher.ui.components;

import java.awt.Cursor;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.function.IntFunction;

import javax.swing.JComponent;

import com.omninode.omnilauncher.ui.Theme;

/** Custom horizontal slider with a filled rounded track and circular thumb. */
public class RSlider extends JComponent {

    private final int min, max, step;
    private int value;
    private IntFunction<String> labelFn = v -> String.valueOf(v);
    private java.util.function.Consumer<Integer> onChange;
    private boolean dragging;
    private boolean hover;

    public RSlider(int min, int max, int step, int value) {
        this.min = min;
        this.max = max;
        this.step = step;
        this.value = value;
        setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        setOpaque(false);
        MouseAdapter m = new MouseAdapter() {
            @Override public void mousePressed(MouseEvent e) { dragging = true; updateFrom(e); }
            @Override public void mouseReleased(MouseEvent e) { dragging = false; }
            @Override public void mouseDragged(MouseEvent e) { updateFrom(e); }
            @Override public void mouseMoved(MouseEvent e) { hover = true; repaint(); }
            @Override public void mouseEntered(MouseEvent e) { hover = true; repaint(); }
            @Override public void mouseExited(MouseEvent e) { hover = false; repaint(); }
        };
        addMouseListener(m);
        addMouseMotionListener(m);
    }

    public void onChange(java.util.function.Consumer<Integer> c) { onChange = c; }
    public int getValue() { return value; }
    public void setValue(int v, boolean fire) {
        v = snap(v);
        if (v != value) {
            value = v;
            repaint();
            if (fire && onChange != null) onChange.accept(v);
        }
    }
    public void setValueSilently(int v) { value = snap(v); repaint(); }

    public void setLabelFn(IntFunction<String> fn) { labelFn = fn; }

    private int snap(int v) {
        v = Math.max(min, Math.min(max, v));
        v = min + Math.round((v - min) / (float) step) * step;
        return Math.max(min, Math.min(max, v));
    }

    private void updateFrom(MouseEvent e) {
        float frac = (e.getX() - 8) / (float) (getWidth() - 16);
        int v = Math.round(min + frac * (max - min));
        setValue(v, true);
    }

    @Override public Dimension getPreferredSize() { return new Dimension(240, 30); }

    @Override protected void paintComponent(Graphics g0) {
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        int w = getWidth(), h = getHeight();
        int trackY = h / 2 - 3;
        g.setColor(Theme.STROKE_SOFT);
        g.fillRoundRect(0, trackY, w, 6, 6, 6);

        float frac = (value - min) / (float) (max - min);
        int fillW = Math.max(8, Math.round((w - 16) * frac) + 8);
        g.setColor(Theme.GREEN);
        g.fillRoundRect(0, trackY, fillW, 6, 6, 6);

        // thumb
        int tx = Math.round(8 + (w - 16) * frac) - 8;
        g.setColor(hover || dragging ? Theme.GREEN_HOVER : Theme.TEXT);
        g.fillOval(tx, h / 2 - 8, 16, 16);
        g.setColor(Theme.darken(Theme.GREEN, 0.35f));
        g.fillOval(tx + 5, h / 2 - 3, 6, 6);
    }

    @Override protected void paintChildren(Graphics g) {
        super.paintChildren(g);
    }

    /** Small read-only value label renderer helper for tooltips. */
    public String label() { return labelFn.apply(value); }
}
