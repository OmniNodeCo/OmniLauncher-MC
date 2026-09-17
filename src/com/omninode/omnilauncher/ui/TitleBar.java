package com.omninode.omnilauncher.ui;

import java.awt.Color;
import java.awt.Component;
import java.awt.Cursor;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.Point;
import java.awt.RenderingHints;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

import javax.swing.JComponent;

import com.omninode.omnilauncher.ui.Icons.Glyph;

/** Custom window chrome: draggable title bar with window controls. */
public class TitleBar extends JComponent {

    private final javax.swing.JFrame frame;
    private Point dragStart;

    public TitleBar(javax.swing.JFrame frame) {
        this.frame = frame;
        setOpaque(false);
        MouseAdapter m = new MouseAdapter() {
            @Override public void mousePressed(MouseEvent e) {
                dragStart = e.getLocationOnScreen();
            }
            @Override public void mouseDragged(MouseEvent e) {
                if (dragStart != null && (e.getModifiersEx() & MouseEvent.BUTTON1_DOWN_MASK) != 0) {
                    if (frame.getExtendedState() == java.awt.Frame.MAXIMIZED_BOTH) return;
                    Point now = e.getLocationOnScreen();
                    Point loc = frame.getLocation();
                    frame.setLocation(loc.x + now.x - dragStart.x, loc.y + now.y - dragStart.y);
                    dragStart = now;
                }
            }
            @Override public void mouseReleased(MouseEvent e) { dragStart = null; }
            @Override public void mouseClicked(MouseEvent e) {
                if (e.getClickCount() == 2) toggleMaximize();
            }
        };
        addMouseListener(m);
        addMouseMotionListener(m);
    }

    void toggleMaximize() {
        if (frame.getExtendedState() == java.awt.Frame.MAXIMIZED_BOTH)
            frame.setExtendedState(java.awt.Frame.NORMAL);
        else
            frame.setExtendedState(java.awt.Frame.MAXIMIZED_BOTH);
    }

    @Override public Dimension getPreferredSize() { return new Dimension(100, 42); }

    @Override protected void paintComponent(Graphics g0) {
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(Theme.RAIL);
        g.fillRect(0, 0, getWidth(), getHeight());

        var block = Icons.grassBlock(20);
        g.drawImage(block, 14, 11, 20, 20, null);
        g.setFont(Theme.xbold(11.5f));
        g.setColor(Theme.TEXT);
        g.drawString("OMNILAUNCHER", 42, 26);

        // window controls on the right
        int bw = 44;
        int x = getWidth() - bw * 3;
        for (int i = 0; i < 3; i++) {
            Glyph glyph = i == 0 ? Glyph.MINIMIZE : i == 1 ? Glyph.MAXIMIZE : Glyph.CLOSE;
            boolean over = controlAt(effectiveMousePos()) == i;
            Color bg = over ? (i == 2 ? new Color(0xc0392b) : Theme.CARD_HOVER)
                    : Theme.withAlpha(Theme.CARD, 0);
            if (bg.getAlpha() > 0) g.fillRect(x + i * bw, 0, bw, getHeight());
            Color fg = over ? Theme.TEXT : Theme.DIM;
            Image icon = Icons.glyph(glyph, i == 1 ? 11 : 12, fg);
            g.drawImage(icon, x + i * bw + (bw - 12) / 2, (getHeight() - 12) / 2, 12, 12, null);
        }
    }

    private Point lastMouse;

    private Point effectiveMousePos() {
        return lastMouse != null ? lastMouse : new Point(-1, -1);
    }

    private int controlAt(Point p) {
        int bw = 44;
        if (p.y < 0 || p.y > getHeight()) return -1;
        for (int i = 0; i < 3; i++) {
            int x0 = getWidth() - bw * 3 + i * bw;
            if (p.x >= x0 && p.x < x0 + bw) return i;
        }
        return -1;
    }

    {
        addMouseMotionListener(new MouseAdapter() {
            @Override public void mouseMoved(MouseEvent e) {
                lastMouse = e.getPoint();
                setCursor(controlAt(lastMouse) >= 0
                        ? Cursor.getDefaultCursor()
                        : Cursor.getPredefinedCursor(Cursor.MOVE_CURSOR));
                repaint();
            }
        });
    }

    @Override protected void paintChildren(Graphics g) { super.paintChildren(g); }

    /** Routes clicks on the control zones (called from a click listener installed by the shell). */
    boolean handleClick(Component source, int x, int y) {
        int c = controlAt(new Point(x, y));
        if (c == 0) frame.setState(java.awt.Frame.ICONIFIED);
        else if (c == 1) toggleMaximize();
        else if (c == 2) { frame.dispose(); System.exit(0); }
        return c >= 0;
    }
}
