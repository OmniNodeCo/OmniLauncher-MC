package com.omninode.omnilauncher.ui.components;

import java.awt.Color;
import java.awt.Cursor;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.RenderingHints;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.ArrayList;
import java.util.List;

import javax.swing.JComponent;

import com.omninode.omnilauncher.ui.Theme;

/** Flat rounded button with hover/press states and optional icon. */
public class RButton extends JComponent {

    public enum Kind { PRIMARY, NEUTRAL, GHOST, DANGER, SUCCESS }

    private String text;
    private Image icon;
    private Kind kind = Kind.NEUTRAL;
    private int radius = 10;
    private Font font = Theme.semi(13f);
    private Color overrideBg;
    private boolean hover;
    private boolean pressed;
    private final List<ActionListener> listeners = new ArrayList<>();
    private String command = "click";

    public RButton(String text) {
        this.text = text;
        setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        setFocusable(false);
        setOpaque(false);
        MouseAdapter m = new MouseAdapter() {
            @Override public void mouseEntered(MouseEvent e) { hover = true; repaint(); }
            @Override public void mouseExited(MouseEvent e) { hover = false; pressed = false; repaint(); }
            @Override public void mousePressed(MouseEvent e) { pressed = true; repaint(); }
            @Override public void mouseReleased(MouseEvent e) {
                boolean wasPressed = pressed;
                pressed = false;
                repaint();
                if (wasPressed && contains(e.getPoint()) && isEnabled())
                    fireAction();
            }
        };
        addMouseListener(m);
    }

    public RButton(String text, Kind kind) { this(text); this.kind = kind; }

    private void fireAction() {
        ActionEvent ev = new ActionEvent(this, ActionEvent.ACTION_PERFORMED, command);
        for (ActionListener l : listeners.toArray(new ActionListener[0])) l.actionPerformed(ev);
    }

    public void addActionListener(ActionListener l) { listeners.add(l); }
    public void onClick(Runnable r) { addActionListener(e -> r.run()); }

    public void setText(String t) { text = t; repaint(); }
    public String getText() { return text; }
    public void setIcon(Image i) { icon = i; repaint(); }
    public void setKind(Kind k) { kind = k; repaint(); }
    public Kind getKind() { return kind; }
    public void setRadius(int r) { radius = r; repaint(); }
    public void setFont2(Font f) { font = f; repaint(); }
    public void setOverrideBg(Color c) { overrideBg = c; repaint(); }
    public void setCommand(String c) { command = c; }

    private Color currentBg() {
        Color base;
        switch (kind) {
            case PRIMARY -> base = Theme.GREEN;
            case SUCCESS -> base = Theme.GREEN_HOVER;
            case DANGER -> base = Theme.RED;
            case GHOST -> base = hover ? Theme.CARD_HOVER : Theme.withAlpha(Theme.CARD, 0);
            default -> base = hover ? Theme.CARD_HOVER : Theme.CARD;
        }
        if (overrideBg != null) base = overrideBg;
        if (pressed) base = Theme.darken(base, 0.18f);
        else if (hover && kind != Kind.GHOST) base = Theme.lighten(base, 0.05f);
        return base;
    }

    @Override protected void paintComponent(Graphics g0) {
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        Color bg = currentBg();
        if (kind == Kind.PRIMARY && !pressed) {
            // soft shadow
            g.setColor(Theme.withAlpha(new Color(0x000000), 70));
            g.fillRoundRect(2, 4, getWidth() - 4, getHeight() - 4, radius, radius);
        }
        if (bg.getAlpha() > 0) {
            g.setColor(bg);
            g.fillRoundRect(0, 0, getWidth(), getHeight(), radius, radius);
            if (kind == Kind.NEUTRAL || kind == Kind.DANGER) {
                g.setColor(Theme.withAlpha(Theme.STROKE, kind == Kind.GHOST ? 0 : 160));
                g.drawRoundRect(0, 0, getWidth() - 1, getHeight() - 1, radius, radius);
            }
        }

        int iconGap = icon != null && text != null && !text.isEmpty() ? 8 : 0;
        Font f = font;
        g.setFont(f);
        var fm = g.getFontMetrics();
        int textW = (text == null || text.isEmpty()) ? 0 : fm.stringWidth(text);
        int iconW = icon != null ? getHeight() / 2 : 0;
        int total = textW + iconW + iconGap;
        int x = (getWidth() - total) / 2;
        int y = (getHeight() - fm.getHeight()) / 2 + fm.getAscent();

        if (!isEnabled()) g.setColor(Theme.withAlpha(Theme.TEXT, 110));
        else g.setColor(kind == Kind.PRIMARY || kind == Kind.SUCCESS || kind == Kind.DANGER ? Color.WHITE : Theme.TEXT);
        if (icon != null) {
            int iy = (getHeight() - iconW) / 2;
            g.drawImage(icon, x, iy, iconW, iconW, null);
            x += iconW + iconGap;
        }
        if (text != null && !text.isEmpty()) g.drawString(text, x, y);
    }

    @Override public java.awt.Dimension getPreferredSize() {
        var fm = getFontMetrics(font);
        int iconW = icon != null ? getHeight() / 2 : 0;
        int w = super.getPreferredSize().width;
        int textW = (text == null ? 0 : fm.stringWidth(text)) + iconW + 28;
        return new java.awt.Dimension(Math.max(w, textW), 34);
    }
}
