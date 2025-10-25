import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import AuthProvider from "./components/AuthProvider";
import { UserAuthProvider } from "./contexts/UserAuthContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "OxY Fx",
  description: "Oxidane Forex Academy - Professional Trading Platform",
  icons: {
    icon: [
      { url: '/favicon.png?v=2025-fixed', type: 'image/png', sizes: '64x64' },
      { url: '/favicon-32.png?v=2025-fixed', type: 'image/png', sizes: '32x32' },
      { url: '/favicon-16.png?v=2025-fixed', type: 'image/png', sizes: '16x16' },
    ],
    apple: [
      { url: '/favicon.png?v=2025-fixed', sizes: '180x180', type: 'image/png' },
    ],
    shortcut: '/favicon.png?v=2025-fixed',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        {/* Fixed PNG favicon with solid background */}
        <link rel="icon" type="image/png" sizes="64x64" href="/favicon.png?v=2025-fixed" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png?v=2025-fixed" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png?v=2025-fixed" />
        <link rel="apple-touch-icon" sizes="180x180" href="/favicon.png?v=2025-fixed" />
        <link rel="shortcut icon" type="image/png" href="/favicon.png?v=2025-fixed" />
        <meta name="msapplication-TileImage" content="/favicon.png?v=2025-fixed" />
        <meta name="theme-color" content="#667eea" />
        <link rel="manifest" href="/manifest.json" />
        <style dangerouslySetInnerHTML={{
          __html: `
            /* Enhanced favicon visibility */
            link[rel*="icon"] {
              image-rendering: -webkit-optimize-contrast;
              image-rendering: crisp-edges;
            }
          `
        }} />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>
          <UserAuthProvider>
            {children}
          </UserAuthProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
