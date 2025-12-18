"use client"
import Link from "next/link"
import { signOut, useSession } from "next-auth/react"
import Image from "next/image"
import { FiMenu } from 'react-icons/fi'
import { useSidebar } from './SidebarProvider'

export default function Navbar() {
  const { data: session } = useSession()
  const { toggle } = useSidebar()
  return (
    <header className="glass fixed top-0 left-0 right-0 h-16 z-50">
      <div className="max-w-7xl mx-auto h-full flex items-center justify-between px-6">
        <button aria-label="Abrir menu" onClick={toggle} className={"block p-3 rounded-lg font-semibold text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition-colors cursor-pointer"}>
          <span className="text-2xl"><FiMenu /></span>
        </button>
        <Link href="/cargas">
          <Image src="/logo.png" alt="Logo" width={95} height={95} loading="eager"/>
        </Link>

        <div className="flex items-center gap-4"> 
          {session?.user ? (
            <button className="block p-3 rounded-lg font-semibold text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition-colors cursor-pointer" onClick={() => signOut()}>Sair</button>
          ) : (
            <Link href="/login" className="block p-3 rounded-lg font-semibold text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition-colors cursor-pointer">Entrar</Link>
          )}
        </div>
      </div>
    </header>
  )
}
