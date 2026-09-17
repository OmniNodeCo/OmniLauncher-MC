package com.omninode.omnilauncher.ui.components;

import java.awt.Color;
import java.awt.Cursor;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.function.Consumer;

import javax.swing.JComponent;

import com.omninode.omnilauncher.ui.Theme;

/** iOS-style toggle switch. */
public class Toggle extends JComponent {

    private boolean value;
    private boolean hover;
    private Consumer<Boolean> onChange;

    public Toggle(boolean initial) {
        this.value = initial;
        setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        setOpaque(false);
        addMouseListener(new MouseAdapter() {
            @Override public void mouseEntered(MouseEvent e) { hover = true; repaint(); }
            @Override public void mouseExited(MouseEvent e) { hover = false; repaint(); }
            @Override public void mouseReleased(MouseEvent e) {
                if (contains(e.getPoint())) {
                    value = !value;
                    repaint();
                    if (onChange != null) onChange.accept(value);
                }
            }
        });
    }

    public void onChange(Consumer<Boolean> c) { onChange = c; }
    public boolean getValue() { return value; }
    public void setValue(boolean v, boolean fire) {
        value = v;
        repaint();
        if (fire && onChange != null) onChange.accept(v);
    }

    @Override public Dimension getPreferredSize() { return new Dimension(42, 24); }

    @Override protected void paintComponent(Graphics g0) {
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        int w = getWidth(), h = getHeight();
        Color track = value ? Theme.GREEN : (hover ? Theme.CARD_HOVER : Theme.STROKE_SOFT);
        g.setColor(track);
        g.fillRoundRect(0, 0, w, h, h, h);
        int knob = h - 6;
        int x = value ? w - knob - 3 : 3;
        g.setColor(Color.WHITE);
        g.fillOval(x, 3, knob, knob);
    }
}
