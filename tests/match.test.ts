import { describe, expect, it } from "vitest";
import { normalizeTitle, rankCandidates, type RawCandidate } from "@/lib/match";
import type { SetlistSong } from "@/lib/types";

const song: SetlistSong = { title: "Dream On", artist: "Aerosmith", isCover: false };
const c = (id: string, name: string, albumName: string, releaseDate: string, artistName = "Aerosmith"): RawCandidate => ({
  id, name, artistName, albumName, releaseDate,
});

describe("normalizeTitle", () => {
  it("strips remaster and feat. annotations", () => {
    expect(normalizeTitle("Dream On - 2011 Remaster")).toBe("dream on");
    expect(normalizeTitle("Walk This Way (feat. Run-DMC)")).toBe("walk this way");
    expect(normalizeTitle("Rock & Roll")).toBe("rock and roll");
  });
});

describe("rankCandidates", () => {
  it("prefers the original studio album over live, compilation and tribute versions", () => {
    const ranked = rankCandidates(song, [
      c("1", "Dream On (Live)", "Classics Live!", "1986-04-01"),
      c("2", "Dream On", "Greatest Hits", "1980-10-01"),
      c("3", "Dream On", "Aerosmith", "1973-01-05"),
      c("4", "Dream On", "A Tribute to Aerosmith", "2005-01-01", "Various Artists"),
      c("5", "Dream On (Acoustic)", "Unplugged Sessions", "2015-01-01"),
    ]);
    expect(ranked[0].id).toBe("3");
    expect(ranked.at(-1)!.id).toBe("4");
  });

  it("keeps live versions when the setlist song itself is live-titled", () => {
    const s: SetlistSong = { title: "Live and Let Die", artist: "Wings", isCover: false };
    const ranked = rankCandidates(s, [c("1", "Live and Let Die", "Live and Let Die (Soundtrack)", "1973-06-01", "Wings")]);
    expect(ranked[0].score).toBeGreaterThan(70);
  });

  it("ranks by the artist it's asked about", () => {
    const s: SetlistSong = { title: "Train Kept A-Rollin'", artist: "Tiny Bradshaw", isCover: true };
    const ranked = rankCandidates(s, [
      c("1", "Train Kept A Rollin'", "Get Your Wings", "1974-03-01", "Aerosmith"),
      c("2", "The Train Kept A-Rollin'", "Tiny Bradshaw: The Great Composer", "1951-01-01", "Tiny Bradshaw"),
    ]);
    expect(ranked[0].id).toBe("2");
  });
});
