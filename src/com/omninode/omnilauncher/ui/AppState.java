package com.omninode.omnilauncher.ui;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/** Global observable UI state (single source of truth for the play flow). */
public class AppState {

    public enum Phase { IDLE, PREPARING, INSTALLING, LAUNCHING, RUNNING, ERROR }

    private static final AppState I = new AppState();
    public static AppState get() { return I; }

    private volatile Phase phase = Phase.IDLE;
    private volatile String statusText = "Ready to play";
    private volatile float progress = -1f; // -1 = indeterminate/none
    private volatile Process gameProcess;
    private volatile String runningVersion;

    private final List<Runnable> listeners = new CopyOnWriteArrayList<>();

    private AppState() {}

    public void listen(Runnable r) { listeners.add(r); }
    public void unlisten(Runnable r) { listeners.remove(r); }

    public void changed() {
        for (Runnable r : listeners) com.omninode.omnilauncher.util.Async.ui(r);
    }

    public Phase getPhase() { return phase; }
    public String getStatusText() { return statusText; }
    /** 0..1 while installing, -1 when no progress bar applies. */
    public float getProgress() { return progress; }
    public Process getGameProcess() { return gameProcess; }
    public String getRunningVersion() { return runningVersion; }

    public boolean busy() {
        return phase == Phase.PREPARING || phase == Phase.INSTALLING || phase == Phase.LAUNCHING;
    }

    public void set(Phase phase, String statusText) {
        this.phase = phase;
        this.statusText = statusText;
        if (phase != Phase.INSTALLING) this.progress = -1f;
        changed();
    }

    public void setStatus(String statusText) {
        this.statusText = statusText;
        changed();
    }

    public void setProgress(float p) {
        this.progress = Math.max(0f, Math.min(1f, p));
        changed();
    }

    public void setGameProcess(Process p, String version) {
        this.gameProcess = p;
        this.runningVersion = version;
    }
}
