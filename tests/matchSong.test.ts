import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { generateKeyPair, exportPKCS8 } from "jose";
import { matchSong } from "@/lib/appleMusic";

const song = (attrs: { name: string; artistName: string; albumName: string; releaseDate: string }, id: string) => ({ id, attributes: attrs });

beforeAll(async () => {
  const { privateKey } = await generateKeyPair("ES256", { extractable: true });
  process.env.APPLE_PRIVATE_KEY = await exportPKCS8(privateKey);
  process.env.APPLE_TEAM_ID = "TEAM";
  process.env.APPLE_KEY_ID = "KEY";
});
afterEach(() => vi.unstubAllGlobals());

function stubCatalog(byTerm: (term: string) => ReturnType<typeof song>[]) {
  const calls: string[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string) => {
    const term = new URL(url).searchParams.get("term")!;
    calls.push(term);
    return new Response(JSON.stringify({ results: { songs: { data: byTerm(term) } } }), { status: 200 });
  }));
  return calls;
}

describe("matchSong for covers", () => {
  it("uses the band's own studio recording when there is one", async () => {
    const calls = stubCatalog(() => [
      song({ name: "Train Kept A Rollin'", artistName: "Aerosmith", albumName: "Get Your Wings", releaseDate: "1974-03-01" }, "1"),
    ]);
    const m = await matchSong({ title: "Train Kept A-Rollin'", artist: "Aerosmith", originalArtist: "Tiny Bradshaw", isCover: true });
    expect(m.best?.id).toBe("1");
    expect(m.confidence).toBe("high");
    expect(calls).toEqual(["Train Kept A-Rollin' Aerosmith"]);
  });

  it("falls back to the original artist when the band never recorded it", async () => {
    stubCatalog((term) =>
      term.includes("Bob Dylan")
        ? [song({ name: "All Along the Watchtower", artistName: "Bob Dylan", albumName: "John Wesley Harding", releaseDate: "1967-12-27" }, "9")]
        : [song({ name: "All Along the Watchtower", artistName: "Some Tribute Band", albumName: "Karaoke Hits", releaseDate: "2010-01-01" }, "2")],
    );
    const m = await matchSong({ title: "All Along the Watchtower", artist: "Aerosmith", originalArtist: "Bob Dylan", isCover: true });
    expect(m.best?.id).toBe("9");
  });
});
