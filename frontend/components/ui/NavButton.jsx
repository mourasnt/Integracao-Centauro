"use client"
import Link from "next/link"

export default function NavButton({ href, children, className = "", onClick }) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={`block p-3 rounded-lg font-semibold text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition-colors cursor-pointer ${className}`}
    >
      {children}
    </Link>
  )
}
