import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ThemeProvider from "./theme-provider";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Cladèse",
  description: "Plateforme de formation auto-hébergée",
  // Les conventions `icon.png` / `apple-icon.png` dupliquaient des rendus deja
  // presents dans `public/`. On pointe directement sur ceux-ci : `icon-192`
  // pour le favicon (variante a fond transparent), `icon-maskable-512` pour
  // l'ecran d'accueil iOS, qui exige un visuel plein cadre sans transparence.
  icons: {
    icon: "/icon-192.png",
    apple: "/icon-maskable-512.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
