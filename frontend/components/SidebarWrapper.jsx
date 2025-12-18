"use client"
import React from 'react'
import Sidebar from './Sidebar'
import { useSidebar } from './SidebarProvider'

export default function SidebarWrapper() {
  const { isOpen, close } = useSidebar()

  return (
    <>
      {/* overlay for small screens when sidebar is open */}
      <div
        className={`sidebar-overlay ${isOpen ? 'open' : ''}`}
        onClick={close}
      />

      <aside className={`sidebar-aside glass p-4 ${isOpen ? 'open' : ''}`}>
        <Sidebar />
      </aside>
    </>
  )
}
