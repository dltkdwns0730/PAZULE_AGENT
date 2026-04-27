import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  BarChart3,
  ClipboardList,
  LogOut,
  Ticket,
  Users,
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';

const navItems = [
  { to: '/admin', label: 'Dashboard', icon: BarChart3, end: true },
  { to: '/admin/logs', label: 'Mission Logs', icon: ClipboardList },
  { to: '/admin/coupons', label: 'Coupons', icon: Ticket },
  { to: '/admin/users', label: 'Users', icon: Users },
];

export default function AdminLayout() {
  const navigate = useNavigate();
  const { email, clearSession } = useAuthStore();

  const handleLogout = () => {
    clearSession();
    navigate('/admin/login', { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col bg-admin-primary text-white md:flex">
        <div className="p-6">
          <p className="text-xs font-black uppercase tracking-[0.22em] text-admin-secondary">
            PAZULE
          </p>
          <h1 className="mt-2 text-xl font-black">Admin Control</h1>
        </div>
        <nav className="flex flex-1 flex-col gap-1 px-4">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-bold transition-colors ${
                  isActive
                    ? 'bg-white/15 text-white'
                    : 'text-white/70 hover:bg-white/10 hover:text-white'
                }`
              }
            >
              <Icon size={18} aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-white/10 p-4">
          <p className="truncate text-sm font-semibold">{email || 'Admin'}</p>
          <button
            type="button"
            onClick={handleLogout}
            className="mt-3 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold text-white/70 hover:bg-white/10 hover:text-white"
          >
            <LogOut size={16} aria-hidden="true" />
            Logout
          </button>
        </div>
      </aside>
      <main className="min-h-screen md:ml-64">
        <div className="border-b border-slate-200 bg-white px-5 py-4 md:hidden">
          <p className="text-sm font-black text-admin-primary">PAZULE Admin</p>
          <nav className="mt-3 flex gap-2 overflow-x-auto">
            {navItems.map(({ to, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `whitespace-nowrap rounded-lg px-3 py-2 text-xs font-bold ${
                    isActive ? 'bg-admin-primary text-white' : 'bg-slate-100 text-slate-600'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
        <Outlet />
      </main>
    </div>
  );
}
