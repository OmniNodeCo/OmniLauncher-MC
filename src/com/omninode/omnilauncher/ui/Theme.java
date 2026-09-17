package com.omninode.omnilauncher.ui;

import java.awt.Color;
import java.awt.Font;
import java.awt.FontFormatException;
import java.awt.GraphicsEnvironment;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

import javax.swing.UIManager;

/** Color palette, typography and global Swing styling for the launcher. */
public final class Theme {

    /* ------------------------------------------------------------ colors */

    public static final Color RAIL        = new Color(0x141518);
    public static final Color BG          = new Color(0x1e1f24);
    public static final Color PANEL       = new Color(0x24262c);
    public static final Color CARD        = new Color(0x2b2d34);
    public static final Color CARD_HOVER  = new Color(0x33363e);
    public static final Color INPUT       = new Color(0x181a1f);
    public static final Color STROKE      = new Color(0x3a3d46);
    public static final Color STROKE_SOFT = new Color(0x2e3138);

    public static final Color TEXT   = new Color(0xebedf2);
    public static final Color DIM    = new Color(0x9aa1ad);
    public static final Color FAINT  = new Color(0x6b7280);

    public static final Color GREEN       = new Color(0x3c8527);
    public static final Color GREEN_HOVER = new Color(0x47a02e);
    public static final Color GREEN_PRESS = new Color(0x2f6b1f);
    public static final Color GREEN_TEXT  = new Color(0x8ef07e);
    public static final Color RED         = new Color(0xe5534b);
    public static final Color AMBER       = new Color(0xd29922);
    public static final Color LINK        = new Color(0x4daafc);

    public static final Color CHIP_RELEASE  = new Color(0x3fb950);
    public static final Color CHIP_SNAPSHOT = new Color(0xd29922);
    public static final Color CHIP_OLD      = new Color(0x8957e5);

    /* ----------------------------------------------------------- typography */

    private static Font baseRegular, baseMedium, baseSemiBold, baseBold, baseExtraBold;
    private static final Map<String, Font> CACHE = new HashMap<>();
    public static boolean fontsLoaded;

    private Theme() {}

    public static void init() {
        loadFonts();
        applyUiDefaults();
    }

    private static void loadFonts() {
        baseRegular    = load("/fonts/Montserrat-Regular.ttf");
        baseMedium     = load("/fonts/Montserrat-Medium.ttf");
        baseSemiBold   = load("/fonts/Montserrat-SemiBold.ttf");
        baseBold       = load("/fonts/Montserrat-Bold.ttf");
        baseExtraBold  = load("/fonts/Montserrat-ExtraBold.ttf");
        fontsLoaded = baseRegular != null;
        if (fontsLoaded) {
            try {
                GraphicsEnvironment ge = GraphicsEnvironment.getLocalGraphicsEnvironment();
                for (Font f : new Font[]{baseRegular, baseMedium, baseSemiBold, baseBold, baseExtraBold})
                    ge.registerFont(f);
            } catch (Throwable ignored) {}
        } else {
            baseRegular = baseMedium = baseSemiBold = baseBold = baseExtraBold =
                    new Font(Font.SANS_SERIF, Font.PLAIN, 13);
        }
    }

    private static Font load(String path) {
        try (InputStream in = Theme.class.getResourceAsStream(path)) {
            if (in == null) return null;
            return Font.createFont(Font.TRUETYPE_FONT, in);
        } catch (FontFormatException | java.io.IOException e) {
            return null;
        }
    }

    public static Font regular(float size)   { return derive("r", baseRegular, size, Font.PLAIN); }
    public static Font medium(float size)    { return derive("m", baseMedium, size, Font.PLAIN); }
    public static Font semi(float size)      { return derive("sb", baseSemiBold, size, Font.PLAIN); }
    public static Font bold(float size)      { return derive("b", baseBold, size, Font.BOLD); }
    public static Font xbold(float size)     { return derive("xb", baseExtraBold, size, Font.BOLD); }

    private static Font derive(String key, Font base, float size, int style) {
        String k = key + "@" + size;
        Font f = CACHE.get(k);
        if (f == null) {
            f = base.deriveFont(style, size);
            CACHE.put(k, f);
        }
        return f;
    }

    public static Color lighten(Color c, float amount) {
        return new Color(
                Math.min(255, (int) (c.getRed() + 255 * amount)),
                Math.min(255, (int) (c.getGreen() + 255 * amount)),
                Math.min(255, (int) (c.getBlue() + 255 * amount)));
    }

    public static Color darken(Color c, float amount) {
        return new Color(
                Math.max(0, (int) (c.getRed() * (1 - amount))),
                Math.max(0, (int) (c.getGreen() * (1 - amount))),
                Math.max(0, (int) (c.getBlue() * (1 - amount))));
    }

    public static Color withAlpha(Color c, int alpha) {
        return new Color(c.getRed(), c.getGreen(), c.getBlue(), alpha);
    }

    /* --------------------------------------------------------- swing skins */

    private static void applyUiDefaults() {
        UIManager.put("Panel.background", BG);
        UIManager.put("Label.foreground", TEXT);
        UIManager.put("Label.font", medium(13f));
        UIManager.put("TextField.font", medium(13f));
        UIManager.put("TextField.background", INPUT);
        UIManager.put("TextField.foreground", TEXT);
        UIManager.put("TextArea.font", medium(12f));
        UIManager.put("TextArea.background", INPUT);
        UIManager.put("TextArea.foreground", TEXT);
        UIManager.put("Viewport.background", BG);
        UIManager.put("ScrollPane.background", BG);
        UIManager.put("ScrollPane.border", null);
        UIManager.put("List.background", CARD);
        UIManager.put("List.foreground", TEXT);
        UIManager.put("List.selectionBackground", CARD_HOVER);
        UIManager.put("List.selectionForeground", TEXT);
        UIManager.put("List.font", medium(13f));
        UIManager.put("PopupMenu.background", PANEL);
        UIManager.put("PopupMenu.border", javax.swing.BorderFactory.createLineBorder(STROKE_SOFT, 1));
        UIManager.put("EditorPane.background", BG);
        UIManager.put("EditorPane.foreground", TEXT);
        UIManager.put("EditorPane.font", regular(13f));
        UIManager.put("ToolTip.background", new Color(0x0f1013));
        UIManager.put("ToolTip.foreground", TEXT);
        UIManager.put("ToolTip.border", javax.swing.BorderFactory.createLineBorder(STROKE, 1));
        UIManager.put("ToolTip.font", medium(12f));
        UIManager.put("OptionPane.background", BG);
        UIManager.put("OptionPane.messageForeground", TEXT);
        UIManager.put("OptionPane.messageFont", medium(13f));
        UIManager.put("OptionPane.titleFont", bold(14f));
        UIManager.put("Button.font", semi(13f));
        UIManager.put("Button.background", CARD);
        UIManager.put("Button.foreground", TEXT);
        UIManager.put("CheckBox.font", medium(13f));
        UIManager.put("CheckBox.foreground", TEXT);
        UIManager.put("ProgressBar.background", INPUT);
        UIManager.put("ProgressBar.foreground", GREEN);
        UIManager.put("Separator.foreground", STROKE_SOFT);
        UIManager.put("ScrollBarUI", "javax.swing.plaf.basic.BasicScrollBarUI");
    }

    /** Scroll pane with the modern thin scrollbar and dark background. */
    public static javax.swing.JScrollPane scroll(java.awt.Component view) {
        javax.swing.JScrollPane sp = new javax.swing.JScrollPane(view);
        sp.setBorder(null);
        sp.getVerticalScrollBar().setUI(new com.omninode.omnilauncher.ui.components.ModernScrollBarUi());
        sp.getHorizontalScrollBar().setUI(new com.omninode.omnilauncher.ui.components.ModernScrollBarUi());
        sp.getVerticalScrollBar().setUnitIncrement(18);
        sp.setHorizontalScrollBarPolicy(javax.swing.ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        sp.setBackground(BG);
        sp.getViewport().setBackground(BG);
        return sp;
    }
}
