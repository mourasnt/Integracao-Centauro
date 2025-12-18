"use client";

import { SessionProvider } from "next-auth/react";

export default function NextAuthProvider({ children }) {
  // Aqui podem entrar outros providers (Theme, Zustand, etc.)
  return <SessionProvider>{children}</SessionProvider>;
}
