package com.omninode.omnilauncher.ui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GridBagConstraints;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Image;
import java.awt.Insets;
import java.awt.RenderingHints;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.Timer;

import com.omninode.omnilauncher.api.MicrosoftAuth;
import com.omninode.omnilauncher.core.AccountStore;
import com.omninode.omnilauncher.core.Settings;
import com.omninode.omnilauncher.model.Account;
import com.omninode.omnilauncher.ui.components.RButton;
import com.omninode.omnilauncher.ui.components.RTextField;
import com.omninode.omnilauncher.ui.components.Spinner;
import com.omninode.omnilauncher.util.Async;

/**
 * Account manager content: account list, offline login and the Microsoft
 * device-code sign-in flow. Used by {@link AccountsDialog} and the preview.
 */
public class AccountsPanel extends JPanel {

    private enum Mode { LIST, MSA, MSA_CODE, OFFLINE }

    private final JPanel stack = new JPanel();
    private final java.awt.CardLayout cards = new java.awt.CardLayout();
    private final JPanel listPanel = new JPanel(new GridBagLayout());
    private final JPanel msaIntro = new JPanel(new GridBagLayout());
    private final JPanel msaCode = new JPanel(new GridBagLayout());
    private final JPanel offline = new JPanel(new GridBagLayout());

    private final Spinner msaSpinner = new Spinner(26);
    private final JLabel msaStatus = new JLabel(" ");
    private final JLabel codeLabel = new JLabel("···· ····");
    private MicrosoftAuth.DeviceCode pendingCode;
    private Timer pollTimer;
    private final Runnable onClose;

    public AccountsPanel(Runnable onClose) {
        this.onClose = onClose;
        setLayout(new BorderLayout());
        setBackground(Theme.PANEL);

        stack.setLayout(cards);
        stack.setBackground(Theme.PANEL);
        add(stack, BorderLayout.CENTER);

        buildList();
        buildMsaIntro();
        buildMsaCode();
        buildOffline();

        cards.addLayoutComponent(listPanel, "list");
        cards.addLayoutComponent(msaIntro, "msa");
        cards.addLayoutComponent(msaCode, "code");
        cards.addLayoutComponent(offline, "offline");
        stack.add(listPanel, "list");
        stack.add(msaIntro, "msa");
        stack.add(msaCode, "code");
        stack.add(offline, "offline");

        show(Mode.LIST);
    }

    @Override public Dimension getPreferredSize() { return new Dimension(500, 480); }

    private void show(Mode m) {
        cards.show(stack, switch (m) {
            case LIST, OFFLINE -> m == Mode.LIST ? "list" : "offline";
            case MSA -> "msa";
            case MSA_CODE -> "code";
        });
    }

    /* ------------------------------------------------------------ chrome */

    private JPanel header(String title) {
        JPanel p = new JPanel(new FlowLayout(FlowLayout.LEFT, 20, 16));
        p.setOpaque(false);
        p.setBorder(BorderFactory.createMatteBorder(0, 0, 1, 0, Theme.STROKE_SOFT));
        JLabel l = new JLabel(title);
        l.setFont(Theme.xbold(15f));
        l.setForeground(Theme.TEXT);
        p.add(l);
        return p;
    }

    /* -------------------------------------------------------------- list */

    private void buildList() {
        listPanel.setOpaque(false);
        refreshList();
    }

    private void refreshList() {
        listPanel.removeAll();
        var gc = new GridBagConstraints();
        gc.gridx = 0; gc.gridy = 0; gc.weightx = 1;
        gc.fill = GridBagConstraints.HORIZONTAL;
        listPanel.add(header("ACCOUNTS"), gc);

        gc.gridy++;
        gc.insets = new Insets(12, 20, 4, 20);
        for (Account acc : AccountStore.all()) {
            listPanel.add(accountRow(acc), gc);
            gc.gridy++;
        }
        if (AccountStore.all().isEmpty()) {
            JLabel empty = new JLabel("<html><div style='width:380px'>No accounts yet. Add a Microsoft "
                    + "account to play online, or create an offline account for singleplayer.</div></html>");
            empty.setFont(Theme.regular(12.5f));
            empty.setForeground(Theme.DIM);
            listPanel.add(empty, gc);
            gc.gridy++;
        }

        JPanel buttons = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 14));
        buttons.setOpaque(false);
        RButton msa = new RButton("Add Microsoft account", RButton.Kind.PRIMARY);
        msa.setIcon(Icons.glyph(Icons.Glyph.PLUS, 12, Color.WHITE));
        msa.onClick(() -> {
            if (Settings.get().msaClientId == null || Settings.get().msaClientId.isBlank()) {
                msaStatus.setText("Set your Azure client ID first (Settings → Accounts & Downloads).");
                show(Mode.MSA);
            } else {
                beginDeviceFlow();
            }
        });
        RButton off = new RButton("Add offline account", RButton.Kind.NEUTRAL);
        off.onClick(() -> show(Mode.OFFLINE));
        RButton close = new RButton("Done", RButton.Kind.GHOST);
        close.onClick(() -> { if (onClose != null) onClose.run(); });
        buttons.add(msa);
        buttons.add(off);
        buttons.add(close);
        gc.gridy++;
        gc.weighty = 1;
        gc.anchor = GridBagConstraints.SOUTHWEST;
        gc.insets = new Insets(0, 12, 14, 12);
        listPanel.add(buttons, gc);
        listPanel.revalidate();
        listPanel.repaint();
    }

    /** Rounded account row with hover highlight. */
    private static final class HoverRow extends JPanel {
        boolean hover;

        HoverRow() {
            super(new FlowLayout(FlowLayout.LEFT, 14, 10));
            setOpaque(false);
            addMouseListener(new java.awt.event.MouseAdapter() {
                @Override public void mouseEntered(java.awt.event.MouseEvent e) {
                    hover = true;
                    repaint();
                }
                @Override public void mouseExited(java.awt.event.MouseEvent e) {
                    hover = false;
                    repaint();
                }
            });
        }

        @Override protected void paintComponent(Graphics g0) {
            Graphics2D g = (Graphics2D) g0;
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setColor(hover ? Theme.CARD_HOVER : Theme.CARD);
            g.fillRoundRect(0, 0, getWidth(), getHeight(), 12, 12);
            super.paintComponent(g0);
        }
    }

    private JPanel accountRow(Account acc) {
        HoverRow row = new HoverRow();
        Image face = acc.getSkinUrl() != null ? SkinFaceCache.faceFor(acc.getSkinUrl()) : null;
        if (acc.getSkinUrl() != null && face == null)
            SkinFaceCache.request(acc.getSkinUrl(), this::refreshList);
        if (face == null) face = Icons.avatarFace(acc.getName(), 36);
        JLabel avatar = new JLabel(new javax.swing.ImageIcon(face));
        row.add(avatar);

        var col = Box.createVerticalBox();
        JLabel name = new JLabel(acc.getName());
        name.setFont(Theme.semi(14f));
        name.setForeground(Theme.TEXT);
        col.add(name);
        JLabel type = new JLabel((acc.isMicrosoft() ? "MICROSOFT" : "OFFLINE")
                + (acc.isMicrosoft() && acc.needsRefresh() ? "  ·  needs re-sign-in" : ""));
        type.setFont(Theme.semi(9.5f));
        type.setForeground(acc.isMicrosoft() ? Theme.GREEN_TEXT : Theme.FAINT);
        col.add(type);
        row.add(col);

        if (acc.equals(AccountStore.selected())) {
            row.add(new JLabel(new javax.swing.ImageIcon(
                    Icons.glyph(Icons.Glyph.CHECK, 15, Theme.GREEN_TEXT))));
        }
        row.addMouseListener(new java.awt.event.MouseAdapter() {
            @Override public void mouseClicked(java.awt.event.MouseEvent e) {
                AccountStore.select(acc);
                refreshList();
            }
        });
        return row;
    }

    /* ---------------------------------------------------------- MSA flow */

    private void buildMsaIntro() {
        msaIntro.setOpaque(false);
        var gc = new GridBagConstraints();
        gc.gridx = 0; gc.gridy = 0; gc.weightx = 1;
        gc.fill = GridBagConstraints.HORIZONTAL;
        msaIntro.add(header("SIGN IN WITH MICROSOFT"), gc);

        gc.insets = new Insets(16, 22, 8, 22);
        JLabel text = new JLabel("<html><div style='width:420px;line-height:160%'>"
                + "A one-time code will be generated. Open <b>microsoft.com/link</b> in your browser, "
                + "enter the code, and sign in with the Microsoft account that owns Minecraft.<br><br>"
                + "<span style='color:#6b7280'>This requires an Azure client ID configured in "
                + "Settings → Accounts &amp; Downloads (see the README for setup).</span></div></html>");
        text.setFont(Theme.regular(12.5f));
        text.setForeground(Theme.DIM);
        msaIntro.add(text, gc);

        gc.gridy++;
        msaStatus.setFont(Theme.medium(12f));
        msaStatus.setForeground(Theme.AMBER);
        msaIntro.add(msaStatus, gc);

        JPanel buttons = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 16));
        buttons.setOpaque(false);
        RButton start = new RButton("Begin sign-in", RButton.Kind.PRIMARY);
        start.onClick(this::beginDeviceFlow);
        RButton back = new RButton("Back", RButton.Kind.GHOST);
        back.onClick(() -> show(Mode.LIST));
        buttons.add(start);
        buttons.add(back);
        gc.gridy++;
        gc.weighty = 1;
        gc.anchor = GridBagConstraints.SOUTHWEST;
        gc.insets = new Insets(0, 12, 14, 12);
        msaIntro.add(buttons, gc);
    }

    private void buildMsaCode() {
        msaCode.setOpaque(false);
        var gc = new GridBagConstraints();
        gc.gridx = 0; gc.gridy = 0; gc.weightx = 1;
        gc.fill = GridBagConstraints.HORIZONTAL;
        msaCode.add(header("ENTER THIS CODE"), gc);

        gc.insets = new Insets(20, 22, 4, 22);
        codeLabel.setFont(new Font(Font.MONOSPACED, Font.BOLD, 30));
        codeLabel.setForeground(Theme.GREEN_TEXT);
        msaCode.add(codeLabel, gc);

        gc.insets = new Insets(8, 22, 8, 22);
        JLabel at = new JLabel("at  microsoft.com/link");
        at.setFont(Theme.medium(14f));
        at.setForeground(Theme.TEXT);
        msaCode.add(at, gc);

        JPanel btnRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 8));
        btnRow.setOpaque(false);
        RButton copy = new RButton("Copy code", RButton.Kind.NEUTRAL);
        copy.setIcon(Icons.glyph(Icons.Glyph.COPY, 12, Theme.DIM));
        copy.onClick(() -> {
            try {
                var cb = java.awt.Toolkit.getDefaultToolkit().getSystemClipboard();
                cb.setContents(new java.awt.datatransfer.StringSelection(
                        pendingCode != null ? pendingCode.userCode() : ""), null);
                msaStatus.setText("Copied to clipboard.");
            } catch (Exception ignored) {}
        });
        RButton openLink = new RButton("Open microsoft.com/link", RButton.Kind.PRIMARY);
        openLink.onClick(() -> com.omninode.omnilauncher.util.Os.openUri(
                pendingCode != null ? pendingCode.verificationUri() : "https://www.microsoft.com/link"));
        btnRow.add(openLink);
        btnRow.add(copy);
        msaCode.add(btnRow, gc);

        JPanel wait = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 10));
        wait.setOpaque(false);
        wait.add(msaSpinner);
        msaStatus.setFont(Theme.medium(12f));
        msaStatus.setForeground(Theme.DIM);
        wait.add(msaStatus);
        gc.gridy++;
        msaCode.add(wait, gc);

        gc.gridy++;
        gc.weighty = 1;
        gc.anchor = GridBagConstraints.SOUTHWEST;
        gc.insets = new Insets(0, 12, 14, 12);
        JPanel cancelRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 8));
        cancelRow.setOpaque(false);
        RButton cancel = new RButton("Cancel sign-in", RButton.Kind.GHOST);
        cancel.onClick(this::stopDeviceFlow);
        cancelRow.add(cancel);
        msaCode.add(cancelRow, gc);
    }

    private void beginDeviceFlow() {
        String clientId = Settings.get().msaClientId;
        if (clientId == null || clientId.isBlank()) {
            msaStatus.setText("Set your Azure client ID first (Settings → Accounts & Downloads).");
            show(Mode.MSA);
            return;
        }
        msaSpinner.start();
        msaStatus.setText("Requesting a sign-in code…");
        Async.io(() -> {
            try {
                pendingCode = MicrosoftAuth.startDeviceCode(clientId);
                Async.ui(() -> {
                    codeLabel.setText(pendingCode.userCode());
                    show(Mode.MSA_CODE);
                    startPolling(clientId);
                });
            } catch (Exception e) {
                Async.ui(() -> {
                    msaSpinner.stop();
                    msaStatus.setText("Could not start sign-in: " + e.getMessage());
                    show(Mode.MSA);
                });
            }
        });
    }

    private void startPolling(String clientId) {
        stopPolling();
        msaSpinner.start();
        msaStatus.setText("Waiting for you to finish in the browser…");
        pollTimer = new Timer(0, e -> {
            pollTimer.stop();
            Async.io(() -> {
                var result = MicrosoftAuth.pollDeviceCode(clientId, pendingCode);
                Async.ui(() -> handlePoll(clientId, result));
            });
        });
        long interval = Math.max(2, pendingCode.interval());
        pollTimer.setInitialDelay((int) interval * 1000);
        pollTimer.start();
    }

    private void handlePoll(String clientId, MicrosoftAuth.PollResult result) {
        switch (result.state()) {
            case PENDING -> startPolling(clientId);
            case SLOW_DOWN -> {
                if (pendingCode != null) pendingCode = new MicrosoftAuth.DeviceCode(
                        pendingCode.userCode(), pendingCode.verificationUri(), pendingCode.deviceCode(),
                        pendingCode.interval() + 3, pendingCode.expiresAt());
                startPolling(clientId);
            }
            case SUCCESS -> {
                stopDeviceFlow();
                Account acc = result.account();
                AccountStore.add(acc);
                refreshList();
                show(Mode.LIST);
                AppState.get().set(AppState.Phase.IDLE, "Signed in as " + acc.getName());
            }
            case EXPIRED -> {
                stopDeviceFlow();
                msaStatus.setText("The code expired. Click Begin sign-in to get a new one.");
                show(Mode.MSA);
            }
            case DECLINED -> {
                stopDeviceFlow();
                msaStatus.setText("Sign-in was declined in the browser.");
                show(Mode.MSA);
            }
            case FAILED -> {
                stopDeviceFlow();
                msaStatus.setText(result.errorDetail());
                show(Mode.MSA);
            }
        }
    }

    private void stopPolling() {
        if (pollTimer != null) pollTimer.stop();
    }

    private void stopDeviceFlow() {
        stopPolling();
        msaSpinner.stop();
        show(Mode.LIST);
        refreshList();
    }

    /* ---------------------------------------------------- offline flow */

    private void buildOffline() {
        offline.setOpaque(false);
        var gc = new GridBagConstraints();
        gc.gridx = 0; gc.gridy = 0; gc.weightx = 1;
        gc.fill = GridBagConstraints.HORIZONTAL;
        offline.add(header("ADD OFFLINE ACCOUNT"), gc);

        gc.insets = new Insets(16, 22, 8, 22);
        JLabel text = new JLabel("<html><div style='width:400px'>Pick a player name. Offline accounts "
                + "work for singleplayer and LAN, but cannot join online servers.</div></html>");
        text.setFont(Theme.regular(12.5f));
        text.setForeground(Theme.DIM);
        offline.add(text, gc);

        gc.insets = new Insets(10, 22, 4, 22);
        RTextField name = new RTextField("Player name");
        name.setFont(Theme.semi(14f));
        name.setPreferredSize(new Dimension(300, 42));
        offline.add(name, gc);

        JPanel buttons = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 16));
        buttons.setOpaque(false);
        RButton add = new RButton("Add account", RButton.Kind.PRIMARY);
        add.onClick(() -> {
            String n = name.getText().trim();
            if (n.isEmpty()) return;
            Account acc = Account.offline(n);
            AccountStore.add(acc);
            refreshList();
            show(Mode.LIST);
            AppState.get().set(AppState.Phase.IDLE, "Ready to play as " + n);
        });
        RButton back = new RButton("Back", RButton.Kind.GHOST);
        back.onClick(() -> show(Mode.LIST));
        buttons.add(add);
        buttons.add(back);
        gc.gridy++;
        gc.weighty = 1;
        gc.anchor = GridBagConstraints.SOUTHWEST;
        gc.insets = new Insets(0, 12, 14, 12);
        offline.add(buttons, gc);
    }

    @Override public void removeNotify() {
        stopPolling();
        super.removeNotify();
        AccountStore.save();
        AppState.get().changed();
    }
}
