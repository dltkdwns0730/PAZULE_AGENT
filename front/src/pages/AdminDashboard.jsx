import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, CheckCircle2, Ticket, Users } from 'lucide-react';
import { adminApi } from '../services/adminApi';
import { useAuthStore } from '../store/useAuthStore';

function StatCard({ label, value, icon: Icon }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-black text-slate-950">{value}</p>
        </div>
        <div className="rounded-lg bg-admin-primary/10 p-2 text-admin-primary">
          <Icon size={20} aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const { accessToken } = useAuthStore();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    adminApi
      .getSummary(accessToken)
      .then(setSummary)
      .catch((exc) => setError(exc instanceof Error ? exc.message : 'Failed to load dashboard.'));
  }, [accessToken]);

  return (
    <section className="p-5 md:p-8">
      <div className="mb-6 flex flex-col gap-2">
        <p className="text-sm font-bold text-admin-primary">Operations</p>
        <h2 className="text-2xl font-black text-slate-950">Dashboard</h2>
      </div>

      {error && <p className="rounded-lg bg-red-50 p-4 text-sm font-semibold text-red-600">{error}</p>}

      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Mission Sessions" value={summary?.total_sessions ?? '-'} icon={Activity} />
        <StatCard label="Success Rate" value={`${summary?.success_rate ?? 0}%`} icon={CheckCircle2} />
        <StatCard label="Issued Coupons" value={summary?.issued_coupons ?? '-'} icon={Ticket} />
        <StatCard label="Redeemed" value={summary?.redeemed_coupons ?? '-'} icon={Users} />
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h3 className="text-base font-black">Recent Mission Activity</h3>
          <Link to="/admin/logs" className="text-sm font-bold text-admin-primary">
            View logs
          </Link>
        </div>
        <div className="divide-y divide-slate-100">
          {(summary?.recent_activity || []).map((row) => (
            <Link
              key={row.mission_id}
              to={`/admin/logs/${row.mission_id}`}
              className="grid gap-2 px-5 py-4 text-sm hover:bg-slate-50 md:grid-cols-5"
            >
              <span className="font-bold text-slate-900">{row.mission_id}</span>
              <span>{row.user_id}</span>
              <span>{row.mission_type}</span>
              <span>{row.status}</span>
              <span className="text-slate-500">{row.created_at || '-'}</span>
            </Link>
          ))}
          {summary && summary.recent_activity.length === 0 && (
            <p className="px-5 py-8 text-sm font-semibold text-slate-500">No mission activity yet.</p>
          )}
        </div>
      </div>
    </section>
  );
}
