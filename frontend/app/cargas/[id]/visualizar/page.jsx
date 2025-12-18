"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";
import Button from "@/components/ui/Button"; // seu botão

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between py-2 border-b border-slate-200">
      <span className="font-medium text-slate-600">{label}</span>
      <span className="text-slate-800">{value ?? "-"}</span>
    </div>
  );
}

function StatusBadge({ status }) {
  const color =
    status === "PENDENTE"
      ? "bg-yellow-200 text-yellow-800"
      : status === "EM_TRANSITO"
      ? "bg-blue-200 text-blue-800"
      : status === "FINALIZADO"
      ? "bg-green-200 text-green-800"
      : "bg-gray-200 text-gray-800";

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${color}`}>
      {status}
    </span>
  );
}

export default function CargaVisualizarPage() {
  const { id } = useParams();
  const { data: session, status } = useSession();

  const [carga, setCarga] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ref do input oculto
  const fileInputRef = useRef(null);

  async function handleSendXML(file) {
    const form = new FormData();
    form.append("arquivo", file); // apenas o arquivo no FormData

    const url = `http://localhost:8000/subcontratacao/upload-xml?carga_id=${id}`;

    const res = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session?.user?.accessToken}`,
      },
      body: form,
    });

    const data = await res.json();
    if (!res.ok){
      alert("Erro ao enviar o XML: " + data.detail)
    } else{
      window.location.reload();
    }

  }

  function onFileChange(e) {
    const file = e.target.files?.[0];
    if (file) handleSendXML(file);
  }

  useEffect(() => {
    if (status === "loading") return;

    if (status === "unauthenticated") {
      setError("Sessão expirada. Faça login novamente.");
      setLoading(false);
      return;
    }

    async function load() {
      try {
        setLoading(true);

        const res = await fetch(`http://localhost:8000/cargas/${id}`, {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session?.user?.accessToken}`,
          },
          cache: "no-store",
        });

        if (!res.ok) throw new Error("Erro ao buscar detalhes da carga");

        const json = await res.json();
        setCarga(json);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    if (status === "authenticated") load();
  }, [status, session, id]);

  if (loading)
    return <p className="p-8 text-gray-600">Carregando carga...</p>;

  if (error)
    return <p className="p-8 text-red-600">Erro: {error}</p>;

  if (!carga)
    return <p className="p-8 text-gray-600">Carga não encontrada.</p>;

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">Visualização da Carga</h1>

      {/* Card Principal */}
      <div className="bg-white shadow rounded-xl p-6 space-y-4">
        <InfoRow label="ID Cliente" value={carga.id_cliente} />

        <InfoRow
          label="Origem"
          value={`${carga.origem_uf?.uf ?? ""} - ${carga.origem_municipio?.municipio ?? ""}`}
        />

        <InfoRow
          label="Destino"
          value={`${carga.destino_uf?.uf ?? ""} - ${carga.destino_municipio?.municipio ?? ""}`}
        />

        <InfoRow
          label="ETA Programado"
          value={new Date(carga.agendamento?.eta_programado).toLocaleString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        />

        <InfoRow
          label="ETD Programado"
          value={new Date(carga.agendamento?.etd_programado).toLocaleString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        />

        <div className="flex justify-between py-2">
          <span className="font-medium text-slate-600">Status</span>
          <StatusBadge status={carga.status.message} />
        </div>
      </div>

      {/* CT-es Subcontratação */}
      <div className="bg-white shadow rounded-xl p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold">CT-es Subcontratados</h2>

          {/* BOTÃO ENVIAR XML */}
          <Button onClick={() => fileInputRef.current.click()}>
            Enviar XML
          </Button>

          {/* input oculto */}
          <input
            type="file"
            accept=".xml"
            ref={fileInputRef}
            className="hidden"
            onChange={onFileChange}
          />
        </div>

        {(!carga.ctes_subcontratacao || carga.ctes_subcontratacao.length === 0) && (
          <p className="text-gray-600">Nenhum CT-e vinculado.</p>
        )}

        {carga.ctes_subcontratacao?.length > 0 && (
          <ul className="space-y-2">
            {carga.ctes_subcontratacao.map((cte) => (
              <li
                key={cte.id}
                className="flex justify-between p-2 border rounded-lg"
              >
                <span>{cte.chave}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}