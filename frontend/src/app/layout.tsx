import type { Metadata } from "next";
import localFont from "next/font/local";
import { Big_Shoulders_Display, Archivo, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

const bigShoulders = Big_Shoulders_Display({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["600", "700", "800"],
});

const archivo = Archivo({
  subsets: ["latin"],
  variable: "--font-archivo",
  weight: ["400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "CryptoTrace — Blockchain Forensics & Digital Intelligence",
  description:
    "Enterprise blockchain intelligence and digital forensics platform for multi-hop transaction tracing, anomaly detection, and tamper-evident SHA-256 evidence auditing.",
};

import { AuthProvider } from "@/context/AuthContext";
import { ForensicProvider } from "@/context/ForensicContext";
import { CommandPalette } from "@/components/common/CommandPalette";
import { ToastContainer } from "@/components/common/ToastContainer";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${bigShoulders.variable} ${archivo.variable} ${jetbrainsMono.variable} antialiased bg-[#080909] text-[#F1EEE6] min-h-screen`}
      >
        <AuthProvider>
          <ForensicProvider>
            {children}
            <CommandPalette />
            <ToastContainer />
          </ForensicProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
