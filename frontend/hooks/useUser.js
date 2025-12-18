import { useSession } from "next-auth/react"

export default function useUser() {
  const { data, status } = useSession()
  return {
    user: data?.user,
    loading: status === "loading"
  }
}
