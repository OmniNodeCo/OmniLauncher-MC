package com.omninode.omnilauncher.ui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.RenderingHints;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.List;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextField;

import com.omninode.omnilauncher.api.VersionManifest;
import com.omninode.omnilauncher.core.Instance;
import com.omninode.omnilauncher.core.InstanceStore;
import com.omninode.omnilauncher.core.LaunchController;
import com.omninode.omnilauncher.ui.components.HoverCard;
import com.omninode.omnilauncher.ui.components.RButton;
import com.omninode.omnilauncher.ui.components.VersionComboBox;

/**
 * Instances page: named installations pinned to one Minecraft version each,
 * with isolated game folders (saves, configs, screenshots).
 */
public class InstancesPanel extends JPanel {

    private final JPanel grid = new JPanel(new GridBagLayout());
    private final JScrollPane scroll;

    public InstancesPanel() {
        setLayout(new BorderLayout());
        setOpaque(false);
        setBorder(BorderFactory.createEmptyBorder(18, 24, 18, 24));

        JPanel top = new JPanel(new BorderLayout());
        top.setOpaque(false);
        JLabel title = new JLabel("Instances");
        title.setFont(Theme.xbold(19f));
        title.setForeground(Theme.TEXT);
        top.add(title, BorderLayout.WEST);

        RButton add = new RButton("+ New instance", RButton.Kind.PRIMARY);
        add.setFont2(Theme.semi(12.5f));
        add.onClick(this::showCreateDialog);
        top.add(add, BorderLayout.EAST);

        JPanel topWrap = new JPanel(new BorderLayout());
        topWrap.setOpaque(false);
        topWrap.add(top, BorderLayout.NORTH);
        JLabel sub = new JLabel("One game folder per instance — versions and settings "
                + "stay separate. Created instances appear here.");
        sub.setFont(Theme.regular(11.5f));
        sub.setForeground(Theme.DIM);
        sub.setBorder(BorderFactory.createEmptyBorder(4, 0, 12, 0));
        topWrap.add(sub, BorderLayout.SOUTH);
        add(topWrap, BorderLayout.NORTH);

        grid.setOpaque(false);
        // anchor content to the top of the viewport instead of centered
        JPanel gridHost = new JPanel(new BorderLayout());
        gridHost.setOpaque(false);
        gridHost.add(grid, BorderLayout.NORTH);
        scroll = Theme.scroll(gridHost);
        scroll.setBorder(null);
        scroll.getVerticalScrollBar().setUnitIncrement(18);
        add(scroll, BorderLayout.CENTER);
    }

    /** Rebuilds the card grid (safe to call often). */
    public void refresh() {
        grid.removeAll();
        var gc = new GridBagConstraints();
        gc.gridx = 0;
        gc.gridy = 0;
        gc.anchor = GridBagConstraints.NORTHWEST;
        gc.insets = new Insets(0, 0, 12, 0);
        gc.fill = GridBagConstraints.HORIZONTAL;
        gc.weightx = 1;

        List<Instance> list = InstanceStore.all();
        for (Instance inst : list) {
            grid.add(makeCard(inst), gc);
            gc.gridy++;
        }
        if (list.isEmpty()) {
            JLabel none = new JLabel("No instances yet — create one to play a "
                    + "version with its own saves and settings.");
            none.setFont(Theme.medium(12.5f));
            none.setForeground(Theme.FAINT);
            none.setBorder(BorderFactory.createEmptyBorder(28, 4, 4, 4));
            grid.add(none, gc);
        }
        revalidate();
        repaint();
    }

    /** Called when the page becomes visible. */
    public void onShown() { refresh(); }

    private JComponent makeCard(Instance inst) {
        HoverCard card = new HoverCard();
        card.setLayout(new BorderLayout(14, 0));
        card.setBorder(BorderFactory.createEmptyBorder(12, 14, 12, 14));

        JLabel icon = new JLabel(new javax.swing.ImageIcon(Icons.avatarFace(inst.id, 48)));
        icon.setBorder(BorderFactory.createEmptyBorder(0, 2, 0, 2));
        card.add(icon, BorderLayout.WEST);

        JPanel mid = new JPanel();
        mid.setOpaque(false);
        mid.setLayout(new BoxLayout(mid, BoxLayout.Y_AXIS));
        JLabel name = new JLabel(inst.name);
        name.setFont(Theme.semi(14f));
        name.setForeground(Theme.TEXT);
        name.setAlignmentX(0f);
        String ver = inst.versionId == null || inst.versionId.isBlank()
                ? "version not set" : inst.versionId;
        JLabel meta = new JLabel(ver + "  ·  " + (inst.lastPlayed == 0
                ? "never played" : "last played " + relTime(inst.lastPlayed)));
        meta.setFont(Theme.regular(11f));
        meta.setForeground(Theme.DIM);
        meta.setAlignmentX(0f);
        mid.add(name);
        mid.add(Box.createVerticalStrut(3));
        mid.add(meta);
        card.add(mid, BorderLayout.CENTER);

        JPanel actions = new JPanel();
        actions.setOpaque(false);
        RButton play = new RButton("Play", RButton.Kind.PRIMARY);
        play.setFont2(Theme.semi(12f));
        play.onClick(() -> launchInstance(inst));
        actions.add(play);
        RButton remove = new RButton("Remove", RButton.Kind.GHOST);
        remove.setFont2(Theme.semi(12f));
        remove.onClick(() -> confirmRemove(inst));
        actions.add(remove);
        card.add(actions, BorderLayout.EAST);

        return card;
    }

    private void launchInstance(Instance inst) {
        VersionManifest.Entry entry = VersionManifest.resolveSelected(inst.versionId);
        if (entry == null) {
            AppState.get().set(AppState.Phase.ERROR,
                    "Version " + inst.versionId + " not found — refresh the version list.");
            return;
        }
        LaunchController.get().play(entry, inst);
    }

    private void confirmRemove(Instance inst) {
        int res = JOptionPane.showConfirmDialog(this,
                "Remove \"" + inst.name + "\" from the instance list?\n\n"
                        + "Its game folder stays on disk:\n" + inst.gameDir(),
                "Remove instance", JOptionPane.OK_CANCEL_OPTION,
                JOptionPane.PLAIN_MESSAGE);
        if (res == JOptionPane.OK_OPTION) {
            InstanceStore.remove(inst.id);
            refresh();
        }
    }

    private void showCreateDialog() {
        java.awt.Window owner = javax.swing.SwingUtilities.windowForComponent(this);
        javax.swing.JDialog dlg = new javax.swing.JDialog(owner, "New instance",
                javax.swing.JDialog.ModalityType.APPLICATION_MODAL);
        JPanel p = new JPanel(new GridBagLayout());
        p.setBorder(BorderFactory.createEmptyBorder(16, 16, 16, 16));
        var gc = new GridBagConstraints();
        gc.gridx = 0;
        gc.gridy = 0;
        gc.anchor = GridBagConstraints.WEST;
        gc.insets = new Insets(6, 4, 2, 4);

        JLabel nameLabel = new JLabel("Name");
        nameLabel.setFont(Theme.semi(12f));
        p.add(nameLabel, gc);

        JTextField name = new JTextField(22);
        name.setFont(Theme.medium(13f));
        gc.gridy++;
        gc.fill = GridBagConstraints.HORIZONTAL;
        p.add(name, gc);

        JLabel verLabel = new JLabel("Minecraft version");
        verLabel.setFont(Theme.semi(12f));
        gc.gridy++;
        gc.fill = GridBagConstraints.NONE;
        p.add(verLabel, gc);

        VersionComboBox combo = new VersionComboBox();
        combo.setSelected(VersionManifest.resolveSelected(
                com.omninode.omnilauncher.core.Settings.get().lastVersionId), false);
        gc.gridy++;
        gc.fill = GridBagConstraints.HORIZONTAL;
        p.add(combo, gc);

        JLabel err = new JLabel(" ");
        err.setFont(Theme.regular(11f));
        err.setForeground(Theme.RED);
        gc.gridy++;
        p.add(err, gc);

        JPanel buttons = new JPanel(new java.awt.FlowLayout(java.awt.FlowLayout.RIGHT, 8, 8));
        buttons.setOpaque(false);
        RButton cancel = new RButton("Cancel", RButton.Kind.GHOST);
        cancel.onClick(dlg::dispose);
        buttons.add(cancel);
        RButton create = new RButton("Create", RButton.Kind.PRIMARY);
        create.onClick(() -> {
            String n = name.getText().trim();
            if (n.isEmpty()) {
                err.setText("Give the instance a name.");
                return;
            }
            if (InstanceStore.findByName(n) != null) {
                err.setText("An instance with that name already exists.");
                return;
            }
            VersionManifest.Entry sel = combo.getSelected();
            Instance created = InstanceStore.create(n,
                    sel != null ? sel.id() : "");
            if (created == null) {
                err.setText("Could not create the instance.");
                return;
            }
            dlg.dispose();
            refresh();
        });
        buttons.add(create);
        gc.gridy++;
        gc.anchor = GridBagConstraints.EAST;
        p.add(buttons, gc);

        dlg.setContentPane(p);
        dlg.pack();
        dlg.setMinimumSize(new Dimension(440, dlg.getPreferredSize().height));
        dlg.setLocationRelativeTo(owner);
        dlg.setVisible(true);
    }

    private static String relTime(long when) {
        long d = System.currentTimeMillis() - when;
        if (d < 60_000) return "just now";
        if (d < 3_600_000) return (d / 60_000) + " min ago";
        if (d < 86_400_000) return (d / 3_600_000) + " h ago";
        return new java.text.SimpleDateFormat("MMM d, yyyy", java.util.Locale.ENGLISH)
                .format(new java.util.Date(when));
    }
}
