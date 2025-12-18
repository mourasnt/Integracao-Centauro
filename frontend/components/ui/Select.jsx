"use client"
import React from 'react'

export default function Select({
  label,
  name,
  options = [],
  value = "",
  onChange,
  placeholder = "Selecione...",
  className = "",
  disabled = false,
  id
}) {
  return (
    <label className={`block ${className}`} htmlFor={id || name}>
      {label && <span className="block text-sm font-medium text-slate-700 mb-1">{label}</span>}
      <div className="relative">
        <select
          id={id || name}
          name={name}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          disabled={disabled}
          className={`w-full appearance-none bg-white/60 border border-slate-200 rounded-md py-2 px-3 pr-8 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-300 ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
        >
          {placeholder && <option value="">{placeholder}</option>}
          {options.map((opt) => {
            if (typeof opt === 'string') return <option key={opt} value={opt}>{opt}</option>
            return <option key={opt.value} value={opt.value}>{opt.label}</option>
          })}
        </select>

        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-slate-500">
          <svg width="18" height="18" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
            <path d="M6 7L10 11L14 7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
    </label>
  )
}
