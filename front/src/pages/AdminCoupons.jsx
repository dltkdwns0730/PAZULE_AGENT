import { useEffect, useState } from 'react';
import { adminApi } from '../services/adminApi';
import { useAuthStore } from '../store/useAuthStore';

export default function AdminCoupons() {
  const { accessToken } = useAuthStore();
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  const load = () => {
    adminApi
      .getCoupons(accessToken, { status, search })
      .then(setRows)
      .catch((exc) => setError(exc instanceof Error ? exc.message : 'Failed to load coupons.'));
  };

  useEffect(load, [accessToken, status, search]);

  const redeem = async (code) => {
    setError('');
    try {
      await adminApi.redeemCoupon(accessToken, code);
      load();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Failed to redeem coupon.');
    }
  };

  return (
    <section className="p-5 md:p-8">
      <div className="mb-6">
        <p className="text-sm font-bold text-admin-primary">Operations</p>
        <h2 className="mt-1 text-2xl font-black">Coupon Management</h2>
      </div>
      <div className="mb-4 flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 md:flex-row">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search code, user, answer"
          className="h-10 flex-1 rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-admin-primary"
        />
        <select
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          className="h-10 rounded-lg border border-slate-200 px-3 text-sm font-semibold outline-none focus:border-admin-primary"
        >
          <option value="">All status</option>
          <option value="issued">Issued</option>
          <option value="redeemed">Redeemed</option>
          <option value="expired">Expired</option>
        </select>
      </div>
      {error && <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm font-semibold text-red-600">{error}</p>}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        {rows.map((row) => (
          <div key={row.code} className="grid gap-3 border-b border-slate-100 px-5 py-4 text-sm md:grid-cols-6">
            <span className="font-black">{row.code}</span>
            <span>{row.user_id}</span>
            <span>{row.answer}</span>
            <span>{row.discount_rule}</span>
            <span className="font-semibold">{row.status}</span>
            <button
              type="button"
              disabled={row.status !== 'issued'}
              onClick={() => redeem(row.code)}
              className="rounded-lg bg-admin-primary px-3 py-2 text-xs font-black text-white disabled:bg-slate-200 disabled:text-slate-500"
            >
              Redeem
            </button>
          </div>
        ))}
        {rows.length === 0 && <p className="px-5 py-8 text-sm font-semibold text-slate-500">No coupons found.</p>}
      </div>
    </section>
  );
}
