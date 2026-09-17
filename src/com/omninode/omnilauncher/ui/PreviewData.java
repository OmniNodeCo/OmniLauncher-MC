package com.omninode.omnilauncher.ui;

import com.omninode.omnilauncher.api.NewsService;
import com.omninode.omnilauncher.api.VersionManifest;
import com.omninode.omnilauncher.core.AccountStore;
import com.omninode.omnilauncher.model.Account;

/** Deterministic sample data for --preview screenshots (no network needed). */
final class PreviewData {

    private static final String MANIFEST = """
    {
      "latest": { "release": "1.21.9", "snapshot": "25w45a" },
      "versions": [
        { "id": "25w45a", "type": "snapshot", "url": "https://piston-meta.mojang.com/v1/packages/x/25w45a.json", "time": "2026-08-05T11:22:00+00:00", "releaseTime": "2026-08-05T11:22:00+00:00" },
        { "id": "1.21.9", "type": "release", "url": "https://piston-meta.mojang.com/v1/packages/y/1.21.9.json", "time": "2026-07-28T09:41:00+00:00", "releaseTime": "2026-07-28T09:41:00+00:00" },
        { "id": "1.21.8", "type": "release", "url": "https://piston-meta.mojang.com/v1/packages/z/1.21.8.json", "time": "2026-07-17T10:03:00+00:00", "releaseTime": "2026-07-17T10:03:00+00:00" },
        { "id": "1.21.5", "type": "release", "url": "https://piston-meta.mojang.com/v1/packages/a/1.21.5.json", "time": "2026-03-25T09:00:00+00:00", "releaseTime": "2026-03-25T09:00:00+00:00" },
        { "id": "1.16.5", "type": "release", "url": "https://piston-meta.mojang.com/v1/packages/b/1.16.5.json", "time": "2021-01-15T10:45:00+00:00", "releaseTime": "2021-01-15T10:45:00+00:00" },
        { "id": "b1.7.3", "type": "old_beta", "url": "https://piston-meta.mojang.com/v1/packages/c/b1.7.3.json", "time": "2011-07-08T00:00:00+00:00", "releaseTime": "2011-07-08T00:00:00+00:00" },
        { "id": "a1.2.6", "type": "old_alpha", "url": "https://piston-meta.mojang.com/v1/packages/d/a1.2.6.json", "time": "2010-12-03T00:00:00+00:00", "releaseTime": "2010-12-03T00:00:00+00:00" }
      ]
    }
    """;

    private static final String NEWS = """
    [
      {
        "id": "minecraft-1-21-9",
        "title": "Minecraft: Java Edition 1.21.9 — The Copper Age",
        "date": "2026-07-28T09:41:00+00:00",
        "category": "release",
        "shortText": "Copper golems, copper chests, and shelves arrive together with a bag full of fixes and polish.",
        "longText": "<p>The Copper Age update is here! Copper golems will sort your chests, copper chests expand your storage options, and shelves let you show off your items.</p><p>This release also delivers the usual round of performance improvements and bug fixes.</p>",
        "image": "https://launchercontent.mojang.com/v2/images/copperage.jpg"
      },
      {
        "id": "snapshot-25w45a",
        "title": "Snapshot 25w45a",
        "date": "2026-08-05T11:22:00+00:00",
        "category": "snapshot",
        "shortText": "A fresh batch of experimental features: new villager trades, more ways to find trial chambers, and tweaks.",
        "longText": "<p>This week's snapshot brings experimental changes to villager economics and world generation.</p>",
        "image": "https://launchercontent.mojang.com/v2/images/snapshot.jpg"
      },
      {
        "id": "deep-dive-copper",
        "title": "Deep Dive: Copper Golems",
        "date": "2026-07-02T14:00:00+00:00",
        "category": "deep_dive",
        "shortText": "How we brought the community-voted mob to life — design, oxidation states, and chest sorting AI.",
        "longText": "<p>From mob vote winner to in-game reality: the story of the copper golem.</p>",
        "image": "https://launchercontent.mojang.com/v2/images/golem.jpg"
      }
    ]
    """;

    private PreviewData() {}

    static void install() {
        VersionManifest.parse(MANIFEST);
        NewsService.parse(NEWS);
        AccountStore.load();
        if (AccountStore.selected() == null)
            AccountStore.add(Account.offline("Steve"));
    }
}
