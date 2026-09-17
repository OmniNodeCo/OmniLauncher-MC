package com.omninode.omnilauncher.ui;

import java.awt.Window;

import javax.swing.BorderFactory;
import javax.swing.JDialog;

/** Modal wrapper around {@link AccountsPanel}. */
public class AccountsDialog extends JDialog {

    public AccountsDialog(Window owner) {
        super(owner, "Accounts", ModalityType.APPLICATION_MODAL);
        setUndecorated(true);
        setSize(500, 480);
        setLocationRelativeTo(owner);
        getRootPane().setBorder(BorderFactory.createLineBorder(Theme.STROKE, 1));
        setContentPane(new AccountsPanel(this::dispose));
    }
}
