"use client"
import { signIn } from "next-auth/react"
import { useState } from "react"
import { useRouter } from "next/navigation"
import Input from "../../../components/ui/Input"
import Button from "../../../components/ui/Button"

export default function LoginPage() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)

    const res = await signIn("credentials", {
      redirect: false,
      username,
      password
    })

    setLoading(false)

    if (res?.error) {
      setError(res.error)
      return
    }

    router.push("/")
  }

  return (
    <div className="min-h-[70vh] flex items-center justify-center bg-gradient-to-br from-blue-50 to-slate-100">
      <form onSubmit={handleSubmit} className="w-full max-w-md bg-white p-8 rounded-2xl shadow-xl border border-slate-200">
        <h2 className="text-3xl font-bold mb-6 text-blue-700 text-center">Acesso ao Painel</h2>
        {error && <div className="bg-red-100 text-red-700 p-2 rounded mb-3 text-center font-medium">{error}</div>}
        <Input label="Usuário" value={username} onChange={(e) => setUsername(e.target.value)} />
        <Input label="Senha" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <Button className="mt-6 w-full" disabled={loading}>{loading ? "Entrando..." : "Entrar"}</Button>
      </form>
    </div>
  )
}
