import { useState, useEffect } from "react"
import { apiFetch } from "../lib/api"

export default function useFetch(endpoint) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch(endpoint)
      .then(setData)
      .finally(() => setLoading(false))
  }, [endpoint])

  return { data, loading }
}
