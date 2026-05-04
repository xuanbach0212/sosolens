import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  title: "SoSoAlpha — AI Signal Platform",
  description: "Bloomberg Terminal-style AI trading signals powered by SoSoValue",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${jetbrainsMono.variable} h-full`}>
      <body
        className="h-full bg-terminal-bg text-terminal-text"
        style={{ fontFamily: "var(--font-jetbrains-mono), monospace" }}
      >
        {children}
      </body>
    </html>
  );
}
