package com.omninode.omnilauncher.util;

import javax.swing.SwingUtilities;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.atomic.AtomicInteger;

/** Small threading facade: pooled background IO + EDT hops. */
public final class Async {

    private static final ExecutorService IO = Executors.newFixedThreadPool(
            Math.max(4, Math.min(12, Runtime.getRuntime().availableProcessors() * 2)),
            named("omni-io"));

    private static final ExecutorService WORK = Executors.newFixedThreadPool(
            Math.max(2, Runtime.getRuntime().availableProcessors()),
            named("omni-work"));

    private Async() {}

    private static ThreadFactory named(String prefix) {
        AtomicInteger n = new AtomicInteger();
        return r -> {
            Thread t = new Thread(r, prefix + "-" + n.incrementAndGet());
            t.setDaemon(true);
            return t;
        };
    }

    /** Run on a shared IO pool (network/disk). */
    public static void io(Runnable r) { IO.submit(wrap(r)); }

    /** Run on the CPU pool (parsing, hashing). */
    public static void work(Runnable r) { WORK.submit(wrap(r)); }

    /** Run on the Swing event dispatch thread (or inline in headless preview mode). */
    public static void ui(Runnable r) {
        if (synchronousUi || SwingUtilities.isEventDispatchThread()) r.run();
        else SwingUtilities.invokeLater(r);
    }

    /** When true, ui() runs callbacks inline (used by the headless preview renderer). */
    public static volatile boolean synchronousUi = false;

    private static Runnable wrap(Runnable r) {
        return () -> {
            try {
                r.run();
            } catch (Throwable t) {
                Log.error("Unhandled error in background task", t);
            }
        };
    }
}
