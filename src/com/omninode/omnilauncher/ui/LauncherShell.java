package com.omninode.omnilauncher.ui;

import java.awt.BorderLayout;
import java.awt.CardLayout;

import javax.swing.JPanel;

import com.omninode.omnilauncher.api.NewsService;

/**
 * The launcher's content root: title bar + nav rail + pages.
 * Reused by the real window and the headless preview renderer.
 */
public class LauncherShell extends JPanel {

    private final TitleBar titleBar;
    private final NavRail navRail = new NavRail();
    private final CardLayout cards = new CardLayout();
    private final JPanel pages = new JPanel(cards);
    public final PlayPanel play;
    public final InstancesPanel instances;
    public final NewsPanel news;
    public final SettingsPanel settings;

    public LauncherShell(javax.swing.JFrame frame) {
        setLayout(new BorderLayout());
        setBackground(Theme.BG);

        titleBar = new TitleBar(frame);
        add(titleBar, BorderLayout.NORTH);
        add(navRail, BorderLayout.WEST);

        play = new PlayPanel(new PlayPanel.Host() {
            @Override public void openAccounts() { LauncherShell.this.openAccounts(); }
            @Override public void showNews(NewsService.Item item) {
                news.showDetail(item);
                navigate(NavRail.Page.NEWS);
            }
            @Override public void showNewsPage() { navigate(NavRail.Page.NEWS); }
        });
        instances = new InstancesPanel();
        news = new NewsPanel();
        settings = new SettingsPanel(this::openAccounts);

        pages.setOpaque(false);
        pages.add(play, NavRail.Page.PLAY.name());
        pages.add(instances, NavRail.Page.INSTANCES.name());
        pages.add(news, NavRail.Page.NEWS.name());
        pages.add(settings, NavRail.Page.SETTINGS.name());
        add(pages, BorderLayout.CENTER);

        navRail.setOnNavigate(this::navigate);
        navRail.setOnAccounts(this::openAccounts);
        titleBar.addMouseListener(new java.awt.event.MouseAdapter() {
            @Override public void mousePressed(java.awt.event.MouseEvent e) {
                titleBar.handleClick(e.getX(), e.getY());
            }
        });

        navigate(NavRail.Page.PLAY);
    }

    public void navigate(NavRail.Page page) {
        cards.show(pages, page.name());
        navRail.setSelected(page);
        switch (page) {
            case PLAY -> play.onShown();
            case INSTANCES -> instances.onShown();
            default -> { }
        }
    }

    public void openAccounts() {
        java.awt.Window w = javax.swing.SwingUtilities.windowForComponent(this);
        new AccountsDialog(w).setVisible(true);
    }

    /** Called when the shell is embedded in a real window. */
    public void onWindowShown() {
        play.onShown();
    }
}
