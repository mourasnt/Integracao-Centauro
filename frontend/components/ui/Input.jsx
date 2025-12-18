export default function Input({ label, type = "text", ...props }) {
  return (
    <label className="block mb-4">
      <span className="text-sm font-medium text-slate-700 mb-1 block">{label}</span>
      <input
        type={type}
        className="w-full border border-slate-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-400 transition"
        {...props}
      />
    </label>
  )
}
