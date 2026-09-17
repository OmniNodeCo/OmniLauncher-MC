package com.omninode.omnilauncher.util;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

/** Tiny logging facility: console + rotating file + in-memory ring for the UI. */
public final class Log {

    private static final DateTimeFormatter TS = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final Deque<String> RING = new ArrayDeque<>(600);
    private static final List<java.util.function.Consumer<String>> SINKS = new ArrayList<>();
    private static final Object LOCK = new Object();
    private static Path file;

    private Log() {}

    public static void init(Path logsDir) {
        String stamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd_HH-mm-ss"));
        file = logsDir.resolve("launcher-" + stamp + ".log");
        try {
            Files.createDirectories(logsDir);
            // keep only the 10 newest logs
            List<Path> logs = new ArrayList<>();
            try (var s = Files.list(logsDir)) {
                s.filter(p -> p.getFileName().toString().startsWith("launcher-"))
                 .filter(p -> p.getFileName().toString().endsWith(".log"))
                 .forEach(logs::add);
            }
            logs.sort(java.util.Comparator.comparingLong(p -> p.toFile().lastModified()));
            while (logs.size() > 10) Files.deleteIfExists(logs.remove(0));
        } catch (IOException ignored) {}
    }

    public static void info(String msg) { log("INFO", msg, null); }
    public static void warn(String msg) { log("WARN", msg, null); }
    public static void error(String msg, Throwable t) { log("ERROR", msg, t); }

    private static void log(String level, String msg, Throwable t) {
        String line = LocalDateTime.now().format(TS) + " [" + level + "] " + msg;
        if (t != null) line += " — " + t.getClass().getSimpleName() + ": " + t.getMessage();
        System.out.println(line);
        synchronized (LOCK) {
            RING.addLast(line);
            while (RING.size() > 500) RING.removeFirst();
            for (var sink : SINKS) {
                try { sink.accept(line); } catch (Throwable ignored) {}
            }
            if (file != null) {
                try {
                    Files.write(file, (line + System.lineSeparator()).getBytes(StandardCharsets.UTF_8),
                            StandardOpenOption.CREATE, StandardOpenOption.APPEND);
                } catch (IOException ignored) {}
            }
        }
    }

    /** Register a live sink (e.g. the game-output console in the UI). */
    public static void addSink(java.util.function.Consumer<String> sink) {
        synchronized (LOCK) { SINKS.add(sink); }
    }

    public static void removeSink(java.util.function.Consumer<String> sink) {
        synchronized (LOCK) { SINKS.remove(sink); }
    }

    public static synchronized List<String> recentLines() {
        synchronized (LOCK) { return new ArrayList<>(RING); }
    }
}
