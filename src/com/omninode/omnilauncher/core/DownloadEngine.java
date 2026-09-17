package com.omninode.omnilauncher.core;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

import com.omninode.omnilauncher.util.Http;
import com.omninode.omnilauncher.util.Log;

/**
 * Concurrent download engine with dedup, hash/size verification,
 * aggregate byte progress and cancellation.
 */
public class DownloadEngine {

    /** A single file to fetch. */
    public static final class Job {
        public final String url;
        public final Path dest;
        public final String sha1;     // null = no hash check
        public final long size;       // -1 = unknown; used for fast skip of existing files
        public final boolean verifyByHash; // false → existence+size check only (assets)

        public Job(String url, Path dest, String sha1, long size, boolean verifyByHash) {
            this.url = url;
            this.dest = dest;
            this.sha1 = sha1;
            this.size = size;
            this.verifyByHash = verifyByHash;
        }
    }

    public interface Listener {
        void status(String message);
        /** Aggregate progress, both values monotonic (bytesTotal may be -1 early on). */
        void progress(long bytesDone, long bytesTotal);
    }

    /** Runs all jobs; throws on the first failure (after draining the queue). */
    public static void run(List<Job> jobs, Listener listener, Http.CancelToken cancel, int concurrency)
            throws IOException, InterruptedException {
        if (jobs.isEmpty()) return;

        ExecutorService pool = Executors.newFixedThreadPool(Math.max(2, concurrency), new ThreadFactory() {
            private final AtomicInteger n = new AtomicInteger();
            @Override public Thread newThread(Runnable r) {
                Thread t = new Thread(r, "omni-dl-" + n.incrementAndGet());
                t.setDaemon(true);
                return t;
            }
        });

        AtomicLong bytesDone = new AtomicLong();
        long bytesTotal = 0;
        for (Job j : jobs) if (j.size > 0) bytesTotal += j.size;

        AtomicInteger filesDone = new AtomicInteger();
        AtomicInteger filesTotal = new AtomicInteger(jobs.size());
        AtomicReference<IOException> failure = new AtomicReference<>();
        Object listenerLock = new Object();
        long lastReport = System.currentTimeMillis();

        try {
            for (Job job : jobs) {
                pool.submit(() -> {
                    if (failure.get() != null || (cancel != null && cancel.cancelled())) {
                        filesDone.incrementAndGet();
                        return;
                    }
                    try {
                        runJob(job, bytesDone);
                    } catch (IOException e) {
                        failure.compareAndSet(null, e);
                    } finally {
                        filesDone.incrementAndGet();
                    }
                });
            }
            // progress pump
            while (filesDone.get() < filesTotal.get()) {
                Thread.sleep(80);
                if (failure.get() != null && cancel != null && cancel.cancelled()) break;
                synchronized (listenerLock) {
                    long now = System.currentTimeMillis();
                    if (now - lastReport > 90) {
                        lastReport = now;
                        listener.progress(bytesDone.get(), bytesTotal);
                    }
                }
            }
        } finally {
            pool.shutdownNow();
        }

        if (failure.get() != null) throw failure.get();
        listener.progress(bytesDone.get(), Math.max(bytesTotal, bytesDone.get()));
    }

    private static void runJob(Job job, AtomicLong bytesDone) throws IOException {
        if (Files.exists(job.dest)) {
            if (job.verifyByHash && job.sha1 != null) {
                try {
                    if (Http.sha1(job.dest).equalsIgnoreCase(job.sha1)) return; // already good
                } catch (IOException ignored) {
                    // unreadable → re-download
                }
            } else if (!job.verifyByHash && job.size > 0
                    && safeSize(job.dest) == job.size) {
                return; // fast path for the thousands of small asset files
            } else if (job.sha1 == null && job.size <= 0) {
                return;
            } else {
                Log.info("Re-downloading corrupt/changed file: " + job.dest.getFileName());
            }
        }
        long[] before = {0};
        try {
            Http.downloadToFile(job.url, job.dest, job.sha1, (done, total) -> {
                long delta = done - before[0];
                before[0] = done;
                if (delta > 0) bytesDone.addAndGet(delta);
            }, null);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IOException("Interrupted", e);
        }
    }

    private static long safeSize(Path p) {
        try { return Files.size(p); } catch (IOException e) { return -1; }
    }
}
