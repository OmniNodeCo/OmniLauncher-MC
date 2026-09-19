package com.omninode.omnilauncher.core;

import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.omninode.omnilauncher.model.Account;
import com.omninode.omnilauncher.util.Json;
import com.omninode.omnilauncher.util.Log;
import com.omninode.omnilauncher.util.Os;

/** Persists the account list and the active selection. */
public class AccountStore {

    private static final List<Account> ACCOUNTS = new ArrayList<>();
    private static String selectedUuid;
    private static final Object LOCK = new Object();

    public static void load() {
        synchronized (LOCK) {
            ACCOUNTS.clear();
            selectedUuid = null;
            try {
                var f = Os.accountsFile();
                if (Files.exists(f)) {
                    var root = Json.parseObject(Files.readString(f));
                    selectedUuid = Json.str(root, "selected", null);
                    for (Object o : Json.arr(root, "accounts")) {
                        var m = Json.asMap(o);
                        if (m != null) ACCOUNTS.add(Account.fromMap(m));
                    }
                }
            } catch (Exception e) {
                Log.error("Could not load accounts", e);
            }
        }
    }

    public static void save() {
        synchronized (LOCK) {
            try {
                Map<String, Object> root = new java.util.LinkedHashMap<>();
                root.put("selected", selectedUuid);
                List<Object> arr = new ArrayList<>();
                for (Account a : ACCOUNTS) arr.add(a.toMap());
                root.put("accounts", arr);
                Os.atomicWriteString(Os.accountsFile(), Json.write(root));
            } catch (Exception e) {
                Log.error("Could not save accounts", e);
            }
        }
    }

    public static List<Account> all() {
        synchronized (LOCK) { return new ArrayList<>(ACCOUNTS); }
    }

    public static void add(Account a) {
        synchronized (LOCK) {
            ACCOUNTS.removeIf(x -> x.getUuid().equals(a.getUuid()));
            ACCOUNTS.add(a);
            selectedUuid = a.getUuid();
        }
        save();
    }

    public static void remove(Account a) {
        synchronized (LOCK) {
            ACCOUNTS.removeIf(x -> x.getUuid().equals(a.getUuid()));
            if (a.getUuid().equals(selectedUuid)) {
                selectedUuid = ACCOUNTS.isEmpty() ? null : ACCOUNTS.get(0).getUuid();
            }
        }
        save();
    }

    public static void select(Account a) {
        synchronized (LOCK) { selectedUuid = a == null ? null : a.getUuid(); }
        save();
    }

    public static Account selected() {
        synchronized (LOCK) {
            if (selectedUuid != null) {
                for (Account a : ACCOUNTS) if (a.getUuid().equals(selectedUuid)) return a;
            }
            return ACCOUNTS.isEmpty() ? null : ACCOUNTS.get(0);
        }
    }

    public static Account byUuid(String uuid) {
        synchronized (LOCK) {
            for (Account a : ACCOUNTS) if (a.getUuid().equals(uuid)) return a;
            return null;
        }
    }

    public static void replace(Account oldA, Account newA) {
        synchronized (LOCK) {
            int idx = -1;
            for (int i = 0; i < ACCOUNTS.size(); i++)
                if (ACCOUNTS.get(i).getUuid().equals(oldA.getUuid())) { idx = i; break; }
            if (idx >= 0) ACCOUNTS.set(idx, newA);
            else ACCOUNTS.add(newA);
            if (oldA.getUuid().equals(selectedUuid) || selectedUuid == null) selectedUuid = newA.getUuid();
        }
        save();
    }
}
