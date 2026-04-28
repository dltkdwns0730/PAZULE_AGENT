import { useEffect, useState } from 'react';
import AdminOrganizationFilter from '../components/AdminOrganizationFilter';
import { adminApi } from '../services/adminApi';
import { useAuthStore } from '../store/useAuthStore';

export default function AdminUsers() {
  const { accessToken } = useAuthStore();
  const [rows, setRows] = useState([]);
  const [organizationId, setOrganizationId] = useState('');
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setError('');
    adminApi
      .getUsers(accessToken, { search, organization_id: organizationId })
      .then(setRows)
      .catch((exc) => setError(exc instanceof Error ? exc.message : '사용자 목록을 불러오지 못했습니다.'));
  }, [accessToken, organizationId, search]);

  return (
    <section className="p-5 md:p-8">
      <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-bold text-admin-primary">운영 관리</p>
          <h2 className="mt-1 text-2xl font-black">사용자</h2>
        </div>
        <AdminOrganizationFilter
          accessToken={accessToken}
          value={organizationId}
          onChange={setOrganizationId}
        />
      </div>
      <input
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="사용자 또는 이메일 검색"
        className="mb-4 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm outline-none focus:border-admin-primary md:max-w-md"
      />
      {error && <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm font-semibold text-red-600">{error}</p>}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        {rows.map((row) => (
          <div key={row.user_id} className="grid gap-3 border-b border-slate-100 px-5 py-4 text-sm md:grid-cols-4">
            <span className="break-all font-black">{row.user_id}</span>
            <span>{row.email || row.display_name || '-'}</span>
            <span>세션 {row.total_sessions}개</span>
            <span>쿠폰 {row.total_coupons}개</span>
          </div>
        ))}
        {rows.length === 0 && <p className="px-5 py-8 text-sm font-semibold text-slate-500">조회된 사용자가 없습니다.</p>}
      </div>
    </section>
  );
}
