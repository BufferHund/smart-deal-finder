import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SmartDeal AI | Intelligent Shopping",
  description: "Experience the future of deal finding with AI-powered insights.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} min-h-screen bg-background text-foreground antialiased selection:bg-purple-500 selection:text-white`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
