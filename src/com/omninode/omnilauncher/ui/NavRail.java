package com.omninode.omnilauncher.ui;

import java.awt.Color;
import java.awt.Cursor;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.RenderingHints;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.function.Consumer;

import javax.swing.JComponent;

import com.omninode.omnilauncher.core.AccountStore;
import com.omninode.omnilauncher.model.Account;
import com.omninode.omnilauncher.ui.Icons.Glyph;

/** Left navigation rail: brand mark, page switcher, account button, status dot. */
public class NavRail extends JComponent {

    public static final int WIDTH = 76;

    public enum Page { PLAY, INSTANCES, NEWS, SETTINGS }

    private Page selected = Page.PLAY;
    private Consumer<Page> onNavigate;
    private Runnable onAccounts;
    private boolean avatarHover;

    public NavRail() {
        setOpaque(false);
        setCursor(Cursor.getDefaultCursor());
        MouseAdapter m = new MouseAdapter() {
            @Override public void mouseReleased(MouseEvent e) {
                int i = zoneAt(e.getX(), e.getY());
                if (i == 0 && onNavigate != null) onNavigate.accept(Page.PLAY);
                if (i == 1 && onNavigate != null) onNavigate.accept(Page.INSTANCES);
                if (i == 2 && onNavigate != null) onNavigate.accept(Page.NEWS);
                if (i == 3 && onNavigate != null) onNavigate.accept(Page.SETTINGS);
                if (i == 4 && onAccounts != null) onAccounts.run();
            }
            @Override public void mouseMoved(MouseEvent e) {
                avatarHover = zoneAt(e.getX(), e.getY()) == 4;
                setCursor(avatarHover || zoneAt(e.getX(), e.getY()) >= 0
                        ? Cursor.getPredefinedCursor(Cursor.HAND_CURSOR) : Cursor.getDefaultCursor());
                repaint();
            }
        };
        addMouseListener(m);
        addMouseMotionListener(m);
    }

    public void setOnNavigate(Consumer<Page> c) { onNavigate = c; }
    public void setOnAccounts(Runnable r) { onAccounts = r; }
    public void setSelected(Page p) { selected = p; repaint(); }

    /** 0..3 nav items, 4 = avatar zone, -1 elsewhere. */
    private int zoneAt(int x, int y) {
        if (x < 8 || x > WIDTH - 8) return -1;
        if (y >= 52 && y <= 100) return 0;
        if (y >= 112 && y <= 160) return 1;
        if (y >= 172 && y <= 220) return 2;
        if (y >= 232 && y <= 280) return 3;
        if (y >= getHeight() - 56 && y <= getHeight() - 12) return 4;
        return -1;
    }

    @Override public Dimension getPreferredSize() { return new Dimension(WIDTH, 100); }

    @Override protected void paintComponent(Graphics g0) {
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(Theme.RAIL);
        g.fillRect(0, 0, getWidth(), getHeight());

        // brand block
        g.drawImage(Icons.brandBadge(40), (WIDTH - 40) / 2, 8, 40, 40, null);

        Image[] glyphs = {
                Icons.glyph(Glyph.PLAY, 20, iconColor(0)),
                Icons.glyph(Glyph.FOLDER, 20, iconColor(1)),
                Icons.glyph(Glyph.NEWS, 20, iconColor(2)),
                Icons.glyph(Glyph.GEAR, 20, iconColor(3)),
        };
        int[] y0 = {56, 116, 176, 236};
        for (int i = 0; i < 4; i++) {
            boolean sel = pageOf(i) == selected;
            if (sel) {
                g.setColor(new Color(0x22242a));
                g.fillRoundRect(10, y0[i] - 6, WIDTH - 20, 44, 10, 10);
                g.setColor(Theme.GREEN);
                g.fillRoundRect(0, y0[i] + 2, 3, 28, 3, 3);
            }
            g.drawImage(glyphs[i], (WIDTH - 20) / 2, y0[i], 20, 20, null);
        }

        // running dot
        boolean running = AppState.get().getPhase() == AppState.Phase.RUNNING;
        g.setColor(running ? Theme.GREEN_HOVER : Theme.withAlpha(Theme.STROKE, 200));
        g.fillOval(WIDTH / 2 - 3, getHeight() - 64, 6, 6);

        // avatar
        Account acc = AccountStore.selected();
        if (acc == null) {
            g.setColor(Theme.CARD);
            g.fillRoundRect((WIDTH - 42) / 2, getHeight() - 53, 42, 42, 12, 12);
            g.drawImage(Icons.glyph(Glyph.PLUS, 16, Theme.DIM), (WIDTH - 16) / 2, getHeight() - 38, 16, 16, null);
        } else {
            java.awt.Image face = faceFor(acc);
            int ax = (WIDTH - 36) / 2, ay = getHeight() - 50;
            g.setColor(avatarHover ? Theme.GREEN : Theme.STROKE);
            g.drawRoundRect(ax - 3, ay - 3, 42, 42, 12, 12);
            g.drawImage(face, ax, ay, 36, 36, null);
        }
    }

    private java.awt.Image faceFor(Account acc) {
        if (acc.getSkinUrl() == null) return Icons.avatarFace(acc.getName(), 36);
        java.awt.Image face = SkinFaceCache.faceFor(acc.getSkinUrl());
        if (face == null) SkinFaceCache.request(acc.getSkinUrl(), this::repaint);
        return face != null ? face : Icons.avatarFace(acc.getName(), 36);
    }

    private Color iconColor(int i) {
        return pageOf(i) == selected ? Theme.TEXT : Theme.FAINT;
    }

    private Page pageOf(int i) {
        return switch (i) {
            case 0 -> Page.PLAY;
            case 1 -> Page.INSTANCES;
            case 2 -> Page.NEWS;
            default -> Page.SETTINGS;
        };
    }
}
