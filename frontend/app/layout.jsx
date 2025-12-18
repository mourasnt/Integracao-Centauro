import "./globals.css"
import Navbar from "../components/Navbar"
import NextAuthProvider from "./providers/SessionProvider";
import { SidebarProvider } from "../components/SidebarProvider"
import SidebarWrapper from "../components/SidebarWrapper"

export const metadata = {
  title: "Cargas Centauro",
  description: "Painel de cargas",
  icons: {
    icon: [
      { url: "/logo.png", sizes: "32x32", type: "image/png" }
    ]
  }
}

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body className="bg-slate-50 min-h-screen">
        <NextAuthProvider>
          <SidebarProvider>
            <Navbar />
            <SidebarWrapper />
            <main className="pt-16">{children}</main>
          </SidebarProvider>
        </NextAuthProvider>
      </body>
    </html>
  )
}
