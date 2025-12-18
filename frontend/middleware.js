import { NextResponse } from "next/server";

export function middleware(req) {
  const url = req.nextUrl;

  // Se o usuário acessar exatamente "/"
  if (url.pathname === "/") {
    url.pathname = "/cargas"; 
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// Define quais rotas o middleware vai observar
export const config = {
  matcher: ["/"], // somente a homepage
};
