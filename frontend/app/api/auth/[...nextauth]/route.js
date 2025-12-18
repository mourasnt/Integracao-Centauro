import NextAuth from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"

const options = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Usuário", type: "text" },
        password: { label: "Senha", type: "password" }
      },
      async authorize(credentials) {
        const res = await fetch(process.env.NEXT_PUBLIC_API_URL + "/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(credentials)
        })

        const data = await res.json().catch(() => null)
        if (!res.ok) throw new Error(data?.detail || "Erro ao autenticar")

        return {
          ...data.user,
          accessToken: data.access_token || data.token
        }
      }
    })
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = user.accessToken
        token.user = user
      }
      return token
    },
    async session({ session, token }) {
      session.user = token.user
      session.accessToken = token.accessToken
      return session
    }
  },
  secret: process.env.NEXTAUTH_SECRET
}

const handler = NextAuth(options)
export { handler as GET, handler as POST }
