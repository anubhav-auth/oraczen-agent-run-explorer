import type { Metadata, Viewport } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "Agent Run Explorer", description: "Browse and understand agent runs" };
export const viewport: Viewport = { width: "device-width", initialScale: 1 };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="en"><body><header className="site-header"><nav><a href="/runs">Runs</a><a href="/dashboard">Dashboard</a></nav></header><main className="container">{children}</main></body></html>);
}