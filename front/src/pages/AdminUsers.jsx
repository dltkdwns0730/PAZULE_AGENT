import { useEffect, useState } from 'react';
import { adminApi } from '../services/adminApi';
import { useAuthStore } from '../store/useAuthStore';

export default function AdminUsers() {
  const { accessToken } = useAuthStore();
  const [rows, setRows] = useState([]);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    adminApi
      .getUsers(accessToken, { search })
      .then(setRows)
      .catch((exc) => setError(exc instanceof Error ? exc.message : 'Failed to load users.'));
  }, [accessToken, search]);

  return (
    <section className="p-5 md:p-8">
      <div className="mb-6">
        <p className="text-sm font-bold text-admin-primary">Operations</p>
        <h2 className="mt-1 text-2xl font-black">Users</h2>
      </div>
      <input
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Search user or email"
        className="mb-4 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm outline-none focus:border-admin-primary md:max-w-md"
      />
      {error && <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm font-semibold text-red-600">{error}</p>}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        {rows.map((row) => (
          <div key={row.user_id} className="grid gap-3 border-b border-slate-100 px-5 py-4 text-sm md:grid-cols-4">
            <span className="break-all font-black">{row.user_id}</span>
            <span>{row.email || row.display_name || '-'}</span>
            <span>{row.total_sessions} sessions</span>
            <span>{row.total_coupons} coupons</span>
          </div>
        ))}
        {rows.length === 0 && <p className="px-5 py-8 text-sm font-semibold text-slate-500">No users found.</p>}
      </div>
    </section>
  );
}
