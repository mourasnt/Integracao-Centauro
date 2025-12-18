import { getSession } from "next-auth/react"

export async function apiFetch(path, options = {}) {
  const base = process.env.NEXT_PUBLIC_API_URL
  const session = await getSession()

  const headers = { 
    "Content-Type": "application/json",
    ...options.headers 
  }

  if (session?.accessToken)
    headers.Authorization = "Bearer " + session.accessToken

  const res = await fetch(base + path, { ...options, headers })

  if (!res.ok) throw new Error("API error: " + res.status)

  return res.json()
}
