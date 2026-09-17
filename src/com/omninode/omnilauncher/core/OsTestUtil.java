package com.omninode.omnilauncher.core;

import com.omninode.omnilauncher.util.Os;

/** Test-only helper so previews/tests can pin platform behavior. */
public final class OsTestUtil {
    private OsTestUtil() {}
    public static Os of(Os.Family family, String arch) { return Os.of(family, arch); }
}
