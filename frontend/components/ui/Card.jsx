export default function Card({ title, children }) {
  return (
    <div className="glass-card rounded-xl p-5 flex flex-col justify-between min-h-[120px] hover:shadow-lg transition">
      <div>
        {title && <div className="text-sm text-slate-500 mb-2 tracking-wide uppercase">{title}</div>}
        <div className="text-2xl font-semibold text-slate-800">{children}</div>
      </div>
      <div className="text-xs text-slate-400 mt-3">Últimas 24h</div>
    </div>
  )
}
