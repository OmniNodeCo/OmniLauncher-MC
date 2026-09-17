package com.omninode.omnilauncher.ui;

import java.awt.Cursor;
import java.awt.Frame;
import java.awt.Point;
import java.awt.Rectangle;
import java.awt.Toolkit;
import java.awt.AWTEvent;
import java.awt.event.MouseEvent;

import javax.swing.SwingUtilities;

/**
 * Edge/corner resizing for undecorated windows using a global AWT listener,
 * so normal component hover/click behavior is untouched. Only pointer
 * activity within {@code EDGE} pixels of the window border initiates a resize.
 */
class WindowResizer {

    private static final int EDGE = 6;
    private static final int MIN_W = 980;
    private static final int MIN_H = 600;

    private final javax.swing.JFrame frame;
    private int dir; // bitmask: 1=N 2=S 4=E 8=W
    private Rectangle startBounds;
    private Point start;

    WindowResizer(javax.swing.JFrame frame) { this.frame = frame; }

    void install() {
        Toolkit.getDefaultToolkit().addAWTEventListener(event -> {
            if (!(event instanceof MouseEvent me)) return;
            if (!frame.isShowing() || frame.getExtendedState() == Frame.MAXIMIZED_BOTH) return;
            int id = me.getID();
            if (id != MouseEvent.MOUSE_MOVED && id != MouseEvent.MOUSE_DRAGGED
                    && id != MouseEvent.MOUSE_PRESSED && id != MouseEvent.MOUSE_RELEASED) return;

            Point p = SwingUtilities.convertPoint(me.getComponent(), me.getPoint(), frame);
            if (id == MouseEvent.MOUSE_RELEASED) {
                dir = 0;
                frame.setCursor(Cursor.getDefaultCursor());
                return;
            }
            int at = dirAt(p);
            if (dir != 0 && id == MouseEvent.MOUSE_DRAGGED) {
                dragTo(p);
                me.consume();
                return;
            }
            if (id == MouseEvent.MOUSE_PRESSED && at != 0) {
                dir = at;
                start = p.getLocation();
                startBounds = frame.getBounds();
                me.consume();
                return;
            }
            if (id == MouseEvent.MOUSE_MOVED) {
                frame.setCursor(cursorFor(at));
            }
        }, AWTEvent.MOUSE_EVENT_MASK | AWTEvent.MOUSE_MOTION_EVENT_MASK);
    }

    private int dirAt(Point p) {
        int w = frame.getWidth(), h = frame.getHeight();
        int d = 0;
        if (p.y <= EDGE) d |= 1;
        else if (p.y >= h - EDGE) d |= 2;
        if (p.x >= w - EDGE) d |= 4;
        else if (p.x <= EDGE) d |= 8;
        return d;
    }

    private static Cursor cursorFor(int d) {
        if (d == 0) return Cursor.getDefaultCursor();
        if (d == 4 || d == 8) return Cursor.getPredefinedCursor(Cursor.E_RESIZE_CURSOR);
        if (d == 1 || d == 2) return Cursor.getPredefinedCursor(Cursor.N_RESIZE_CURSOR);
        if (d == 5 || d == 10) return Cursor.getPredefinedCursor(Cursor.NE_RESIZE_CURSOR);
        if (d == 9 || d == 6) return Cursor.getPredefinedCursor(Cursor.NW_RESIZE_CURSOR);
        return Cursor.getDefaultCursor();
    }

    private void dragTo(Point now) {
        int dx = now.x - start.x, dy = now.y - start.y;
        Rectangle b = new Rectangle(startBounds);
        if ((dir & 4) != 0) b.width = Math.max(MIN_W, startBounds.width + dx);
        if ((dir & 2) != 0) b.height = Math.max(MIN_H, startBounds.height + dy);
        if ((dir & 8) != 0) {
            int newW = Math.max(MIN_W, startBounds.width - dx);
            b.x = startBounds.x + (startBounds.width - newW);
            b.width = newW;
        }
        if ((dir & 1) != 0) {
            int newH = Math.max(MIN_H, startBounds.height - dy);
            b.y = startBounds.y + (startBounds.height - newH);
            b.height = newH;
        }
        frame.setBounds(b);
    }
}
