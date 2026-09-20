package com.omninode.omnilauncher.core;

import java.io.IOException;
import java.util.function.Consumer;

import com.omninode.omnilauncher.api.VersionManifest;
import com.omninode.omnilauncher.api.MicrosoftAuth;
import com.omninode.omnilauncher.model.Account;
import com.omninode.omnilauncher.ui.AppState;
import com.omninode.omnilauncher.util.Async;
import com.omninode.omnilauncher.util.Http;
import com.omninode.omnilauncher.util.Log;

/**
 * Orchestrates: refresh account token → install version → launch game.
 * All state changes land in {@link AppState}.
 */
public class LaunchController {

    private static final LaunchController I = new LaunchController();
    public static LaunchController get() { return I; }

    private volatile Http.CancelToken cancelToken;

    /** Fired when the flow needs the UI to open the account dialog. */
    public Consumer<String> onNeedAccount;

    public void play(VersionManifest.Entry entry) {
        play(entry, null);
    }

    /** Plays a launcher instance (pinned version + isolated game folder). */
    public void play(VersionManifest.Entry entry, Instance instance) {
        AppState st = AppState.get();
        if (st.busy()) return;

        Account initialAccount = AccountStore.selected();
        if (initialAccount == null) {
            st.set(AppState.Phase.IDLE, "Sign in to play");
            if (onNeedAccount != null) onNeedAccount.accept("Choose an account to start playing.");
            return;
        }

        cancelToken = Http.newCancelToken();
        Http.CancelToken token = cancelToken;
        st.set(AppState.Phase.PREPARING, "Preparing "
                + (instance != null ? instance.name : "to play " + entry.id()) + "…");
        if (instance != null) Log.info("Launching instance " + instance.name
                + " [" + instance.id + "] on " + entry.id());

        final Account[] holder = {initialAccount};
        Async.io(() -> {
            try {
                Account account = holder[0];
                // refresh Microsoft token when needed
                if (account.isMicrosoft() && account.needsRefresh()) {
                    st.setStatus("Refreshing " + account.getName() + "…");
                    try {
                        Account fresh = MicrosoftAuth.refresh(account);
                        AccountStore.replace(account, fresh);
                        holder[0] = account = fresh;
                    } catch (Exception e) {
                        Log.warn("Token refresh failed: " + e.getMessage());
                        st.set(AppState.Phase.ERROR, "Sign-in expired — sign in again to continue.");
                        if (onNeedAccount != null) onNeedAccount.accept("Your Microsoft sign-in expired. Please sign in again.");
                        return;
                    }
                }

                // install / verify game files
                VersionInstaller.InstalledVersion installed = VersionInstaller.install(entry, (status) -> {
                    st.set(AppState.Phase.INSTALLING, status);
                }, (frac) -> st.setProgress(frac), token);

                // resolve (or download) the right Java runtime
                GameLauncher.JavaRuntime rt;
                try {
                    rt = GameLauncher.resolveRuntime(installed.json(),
                            m -> st.set(AppState.Phase.INSTALLING, m),
                            f -> st.setProgress(f),
                            token);
                } catch (Exception e) {
                    Log.error("Java setup failed", e);
                    st.set(AppState.Phase.ERROR,
                            e.getMessage() == null ? "Java setup failed" : e.getMessage());
                    return;
                }

                // launch
                st.set(AppState.Phase.LAUNCHING, "Launching Minecraft " + entry.id() + "…");
                Account acc = account;
                java.nio.file.Path gameDir = instance != null ? instance.gameDir() : null;
                GameLauncher.launch(installed, acc, rt, gameDir, new GameLauncher.RunListener() {
                    @Override public void started(Process p) {
                        st.setGameProcess(p, entry.id());
                        st.set(AppState.Phase.RUNNING,
                                (instance != null ? instance.name + " — Minecraft " : "Minecraft ")
                                        + entry.id() + " is running");
                        if (instance != null) InstanceStore.touch(instance.id);
                        if (!Settings.get().keepLauncherOpen && p != null) Async.ui(() -> {
                            // window will be minimized by the UI layer listening to phase
                        });
                    }
                    @Override public void exited(int code) {
                        st.setGameProcess(null, null);
                        if (code == 0) st.set(AppState.Phase.IDLE, "Ready to play");
                        else st.set(AppState.Phase.IDLE, "Game exited (code " + code + ")");
                    }
                    @Override public void outputLine(String line) { /* log already captured */ }
                    @Override public void failed(String message) {
                        st.set(AppState.Phase.ERROR, message);
                    }
                });
            } catch (IOException e) {
                if (token.cancelled()) st.set(AppState.Phase.IDLE, "Cancelled");
                else {
                    Log.error("Launch failed", e);
                    st.set(AppState.Phase.ERROR, e.getMessage() == null ? "Install failed" : e.getMessage());
                }
            } catch (Exception e) {
                Log.error("Launch failed", e);
                String msg = e.getMessage();
                st.set(AppState.Phase.ERROR, msg == null || msg.isBlank() ? e.getClass().getSimpleName() : msg);
            }
        });
    }

    public void cancel() {
        Http.CancelToken t = cancelToken;
        if (t != null) t.cancel();
        AppState.get().set(AppState.Phase.IDLE, "Cancelled");
    }
}
