import { describe, expect, it } from "vitest";
import { parseQuery } from "@/lib/parseQuery";

describe("parseQuery", () => {
  it("handles the classic phrasing", () => {
    expect(parseQuery("I saw Aerosmith at SPAC in 1990")).toEqual({ artist: "Aerosmith", venue: "SPAC", year: "1990" });
  });
  it("handles no lead-in and no 'at'", () => {
    expect(parseQuery("Phish, Saratoga, 1995")).toEqual({ artist: "Phish", venue: "Saratoga", year: "1995" });
  });
  it("parses US dates", () => {
    expect(parseQuery("Pearl Jam at Madison Square Garden on 10/19/2003")).toEqual({
      artist: "Pearl Jam", venue: "Madison Square Garden", year: "2003", date: "19-10-2003",
    });
  });
  it("parses written dates", () => {
    expect(parseQuery("we saw Tom Petty at the Hollywood Bowl August 23rd, 1991")).toMatchObject({
      artist: "Tom Petty", venue: "Hollywood Bowl", date: "23-08-1991",
    });
    expect(parseQuery("Rush at MSG 3 March 1984").date).toBe("03-03-1984");
  });
  it("parses ISO dates", () => {
    expect(parseQuery("Metallica 1986-09-27").date).toBe("27-09-1986");
  });
  it("keeps 'at' inside artist when there is no venue split", () => {
    expect(parseQuery("Aerosmith 1990")).toEqual({ artist: "Aerosmith", year: "1990" });
  });
  it("supports @", () => {
    expect(parseQuery("Dead & Company @ Sphere 2024")).toEqual({ artist: "Dead & Company", venue: "Sphere", year: "2024" });
  });
});
