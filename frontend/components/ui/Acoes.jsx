"use client";

import Link from "next/link";
import { Eye, Pencil } from "lucide-react";

export default function Acoes({ url_view, url_edit, className = "" }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Visualizar */}
      {url_view && (
        <Link href={url_view}>
          <Eye
            size={20}
            className="text-slate-600 hover:text-blue-600 cursor-pointer transition-colors"
          />
        </Link>
      )}

      {/* Editar */}
      {url_edit && (
        <Link href={url_edit}>
          <Pencil
            size={20}
            className="text-slate-600 hover:text-green-600 cursor-pointer transition-colors"
          />
        </Link>
      )}
    </div>
  );
}
