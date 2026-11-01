import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SetPlay",
  description: "Turn a concert you saw into a playlist of the studio recordings, in setlist order.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
