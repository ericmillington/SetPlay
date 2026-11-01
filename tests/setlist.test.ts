import { describe, expect, it } from "vitest";
import { toShow, type RawSetlist } from "@/lib/setlistfm";

const raw: RawSetlist = {
  id: "abc",
  eventDate: "23-08-1990",
  url: "https://www.setlist.fm/setlist/aerosmith/1990/x.html",
  artist: { name: "Aerosmith" },
  venue: { name: "Saratoga Performing Arts Center", city: { name: "Saratoga Springs", state: "New York", country: { name: "United States" } } },
  tour: { name: "Pump" },
  sets: {
    set: [
      { song: [{ name: "Intro", tape: true }, { name: "Young Lust" }, { name: "Train Kept A-Rollin'", cover: { name: "Tiny Bradshaw" } }, { name: "" }] },
      { encore: 1, song: [{ name: "Walk This Way" }] },
    ],
  },
};

describe("toShow", () => {
  it("flattens sets, drops tapes and blanks, records the original artist for covers", () => {
    const show = toShow(raw);
    expect(show.songs.map((s) => [s.title, s.artist, s.originalArtist, s.setName])).toEqual([
      ["Young Lust", "Aerosmith", undefined, undefined],
      ["Train Kept A-Rollin'", "Aerosmith", "Tiny Bradshaw", undefined],
      ["Walk This Way", "Aerosmith", undefined, "Encore"],
    ]);
    expect(show.songs[1].isCover).toBe(true);
    expect(show.city).toBe("Saratoga Springs");
  });
});
