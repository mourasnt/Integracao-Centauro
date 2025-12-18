"use client"
import NavButton from "./ui/NavButton"
import { useSidebar } from './SidebarProvider'

export default function Sidebar() {
  const { close } = useSidebar()
  return (
    <nav className="space-y-4">
      <NavButton href="/login" onClick={close}>Login</NavButton>
      <NavButton href="/cargas" onClick={close}>Cargas</NavButton>
    </nav>
  )
}
