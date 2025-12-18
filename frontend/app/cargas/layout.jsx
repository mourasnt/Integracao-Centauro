import SidebarWrapper from "../../components/SidebarWrapper"

export default function DashboardLayout({ children }) {
  return (
    <div className="flex">
      <div className="w-full p-6">
        {children}
      </div>
    </div>
  )
}
