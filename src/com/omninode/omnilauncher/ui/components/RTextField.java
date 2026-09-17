package com.omninode.omnilauncher.ui.components;

import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.event.FocusAdapter;
import java.awt.event.FocusEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

import javax.swing.JTextField;

import com.omninode.omnilauncher.ui.Theme;

/** Dark text field with rounded border, focus glow and ghost placeholder. */
public class RTextField extends JTextField {

    private String placeholder = "";
    private boolean hover;

    public RTextField() {
        setOpaque(false);
        setBorder(javax.swing.BorderFactory.createEmptyBorder(0, 12, 0, 12));
        setBackground(Theme.INPUT);
        setForeground(Theme.TEXT);
        setCaretColor(Theme.TEXT);
        setSelectionColor(Theme.withAlpha(Theme.GREEN, 90));
        setSelectedTextColor(Theme.TEXT);
        setColumns(12);
        addFocusListener(new FocusAdapter() {
            @Override public void focusGained(FocusEvent e) { repaint(); }
            @Override public void focusLost(FocusEvent e) { repaint(); }
        });
        addMouseListener(new MouseAdapter() {
            @Override public void mouseEntered(MouseEvent e) { hover = true; repaint(); }
            @Override public void mouseExited(MouseEvent e) { hover = false; repaint(); }
        });
    }

    public RTextField(String placeholder) { this(); setPlaceholder(placeholder); }

    public void setPlaceholder(String p) { placeholder = p; repaint(); }
    public String getPlaceholder() { return placeholder; }

    @Override public void setFont(Font f) { super.setFont(f); }

    @Override protected void paintComponent(Graphics g0) {
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        int h = getHeight();
        g.setColor(Theme.INPUT);
        g.fillRoundRect(0, 0, getWidth(), h, 10, 10);
        Color border = isFocusOwner() ? Theme.GREEN : hover ? Theme.STROKE : Theme.STROKE_SOFT;
        g.setColor(border);
        g.drawRoundRect(0, 0, getWidth() - 1, h - 1, 10, 10);

        if (getDocument().getLength() == 0 && !placeholder.isEmpty() && !isFocusOwner()) {
            g.setColor(Theme.FAINT);
            g.setFont(getFont());
            var fm = g.getFontMetrics();
            g.drawString(placeholder, 12, (h - fm.getHeight()) / 2 + fm.getAscent());
        }
        super.paintComponent(g);
    }
}
