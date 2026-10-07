import type { Metadata, Viewport } from "next";
import Link from "next/link";
import "./globals.css";
export const metadata: Metadata = { title: "Agent Run Explorer", description: "Browse and understand agent runs" };
export const viewport: Viewport = { width: "device-width", initialScale: 1 };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="en"><body><a className="skip" href="#main">Skip to content</a><header className="site-header"><nav><Link href="/runs">Runs</Link><Link href="/dashboard">Dashboard</Link></nav></header><main id="main" className="container">{children}</main></body></html>);
}