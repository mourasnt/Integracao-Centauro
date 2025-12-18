"use client"
import { useState, useEffect, useMemo } from "react"
import Table from "@/components/ui/Table"
import Input from "@/components/ui/Input"
import Select from "@/components/ui/Select"
import Link from "next/link"
import { useSession } from "next-auth/react"
import Acoes from "@/components/ui/Acoes"
import Button from "@/components/ui/Button"

function StatusBadge({ status }) {
  const color =
    status === "PENDENTE"
      ? "bg-yellow-200 text-yellow-800"
      : status === "EM_TRANSITO"
      ? "bg-blue-200 text-blue-800"
      : status === "FINALIZADO"
      ? "bg-green-200 text-green-800"
      : "bg-gray-200 text-gray-800"

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${color}`}>{status}</span>
  )
}

export default function CargasPage() {
  const { data: session, status } = useSession()

  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [filtroId3zx, setFiltroId3zx] = useState("")
  const [filtroIdCliente, setFiltroIdCliente] = useState("")
  const [filtroUfOrigem, setFiltroUfOrigem] = useState("")
  const [filtroUfDestino, setFiltroUfDestino] = useState("")
  const [filtroMunicipioOrigem, setFiltroMunicipioOrigem] = useState("")
  const [filtroMunicipioDestino, setFiltroMunicipioDestino] = useState("")

  const [page, setPage] = useState(1)
  const itemsPerPage = 10

  useEffect(() => {
    if (status === "loading") return

    if (status === "unauthenticated") {
      setError("Sessão expirada. Faça login novamente.")
      setLoading(false)
      return
    }

    async function load() {
      try {
        setLoading(true)

        const res = await fetch("http://localhost:8000/cargas", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session?.user?.accessToken}`,
          },
          cache: "no-store",
        })

        if (!res.ok) throw new Error("Erro ao buscar cargas")

        const json = await res.json()

        const mapped = json.map((c) => ({
          id: c.id,
          id_3zx: c.id_3zx,
          id_cliente: c.id_cliente,
          origem_uf: c.origem_uf,
          origem_municipio: c.origem_municipio,
          destino_uf: c.destino_uf,
          destino_municipio: c.destino_municipio,
          origem: `${c.origem_uf.uf} - ${c.origem_municipio.municipio}`,
          eta: c.agendamento?.eta_programado
          ? new Date(c.agendamento.eta_programado).toLocaleString("pt-BR", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })
          : "",
          destino: `${c.destino_uf.uf} - ${c.destino_municipio.municipio}`,
          etd: c.agendamento?.etd_programado 
          ? new Date(c.agendamento.etd_programado).toLocaleString("pt-BR", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })
          : "",
          status: <StatusBadge status={c.status.message} />,
          acoes: <Acoes
                  url_view={`/cargas/${c.id}/visualizar`}
                />
        }))

        setData(mapped)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (status === "authenticated") load()
  }, [status, session])

  const filteredData = useMemo(() => {
    return data.filter((item) => {
      return (
        (filtroId3zx === "" || item.id_3zx.toLowerCase().includes(filtroId3zx.toLowerCase())) &&
        (filtroIdCliente === "" || item.id_cliente.toLowerCase().includes(filtroIdCliente.toLowerCase())) &&
        (filtroUfOrigem === "" || item.origem_uf.cod === filtroUfOrigem) &&
        (filtroUfDestino === "" || item.destino_uf.cod === filtroUfDestino) &&
        (filtroMunicipioOrigem === "" || item.origem_municipio.cod === filtroMunicipioOrigem) &&
        (filtroMunicipioDestino === "" || item.destino_municipio.cod === filtroMunicipioDestino)
      )
    })
  }, [
    data,
    filtroId3zx,
    filtroIdCliente,
    filtroUfOrigem,
    filtroUfDestino,
    filtroMunicipioOrigem,
    filtroMunicipioDestino,
  ])

  console.log(data)
  const pageCount = Math.ceil(filteredData.length / itemsPerPage)
  const paginatedData = filteredData.slice((page - 1) * itemsPerPage, page * itemsPerPage)

  const ufsOrigem = [...new Set(data.map((d) => d.origem_uf))]
  const ufsDestino = [...new Set(data.map((d) => d.destino_uf))]
  const municipiosOrigem = [...new Set(data.map((d) => d.origem_municipio))]
  const municipiosDestino = [...new Set(data.map((d) => d.destino_municipio))]

  const columns = [
    { key: "id_cliente", title: "ID Cliente" },
    { key: "origem", title: "Origem" },
    { key: "eta", title: "ETA"},
    { key: "destino", title: "Destino" },
    { key: "etd", title: "ETD"},
    { key: "status", title: "Status"},
    { key: "acoes", title: "Ações"}
  ]

  return (
    <div className="flex min-h-[80vh]">
      <main className="flex-1 p-8 space-y-6">
        <h2 className="text-2xl font-bold">Cargas</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 bg-white p-4 rounded-xl shadow">
          <Input label="ID Cliente" placeholder="Buscar..." value={filtroIdCliente} onChange={(e) => setFiltroIdCliente(e.target.value)} />

          <Select label="UF Origem" value={filtroUfOrigem} onChange={(value) => setFiltroUfOrigem(value)}  options={ufsOrigem.map((uf) => ({ value: uf.cod, label: uf.uf }))}/>
          <Select label="Municipio Origem" value={filtroMunicipioOrigem} onChange={(value) => setFiltroMunicipioOrigem(value)}  options={municipiosOrigem.map((municipio) => ({ value: municipio.cod, label: municipio.municipio }))}/>

          <Select label="UF Destino" value={filtroUfDestino} onChange={(value) => setFiltroUfDestino(value)} options={ufsDestino.map((uf) => ({ value: uf.cod, label: uf.uf }))}/>
          <Select label="Municipio Destino" value={filtroMunicipioDestino} onChange={(value) => setFiltroMunicipioDestino(value)} options={municipiosDestino.map((municipio) => ({ value: municipio.cod, label: municipio.municipio }))}/>
        </div>

        {loading && <p className="text-gray-600">Carregando cargas...</p>}
        {error && <p className="text-red-600">Erro: {error}</p>}

        {!loading && !error && <Table columns={columns} data={paginatedData} />}

        <div className="flex gap-2 mt-4">
          <Button className="text-sm" disabled={page === 1} onClick={() => setPage(page - 1)}>Anterior</Button>
          <Button className="text-sm" disabled={page === pageCount} onClick={() => setPage(page + 1)}>Próxima</Button>
        </div>
      </main>
    </div>
  )
}
