import { describe, expect, it } from "vitest";
import { venueScore } from "@/lib/venue";

describe("venueScore", () => {
  it("matches acronyms", () => {
    expect(venueScore("SPAC", "Saratoga Performing Arts Center", "Saratoga Springs", "New York")).toBe(1);
  });
  it("matches city names", () => {
    expect(venueScore("Saratoga", "Saratoga Performing Arts Center", "Saratoga Springs")).toBe(1);
  });
  it("matches aliases", () => {
    expect(venueScore("MSG", "Madison Square Garden", "New York")).toBe(1);
  });
  it("scores unrelated venues low", () => {
    expect(venueScore("SPAC", "Great Woods Center for the Performing Arts", "Mansfield")).toBeLessThan(0.5);
  });
});
