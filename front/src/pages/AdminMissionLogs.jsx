import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import AdminOrganizationFilter from '../components/AdminOrganizationFilter';
import { adminApi } from '../services/adminApi';
import { useAuthStore } from '../store/useAuthStore';

export default function AdminMissionLogs() {
  const { accessToken } = useAuthStore();
  const [rows, setRows] = useState([]);
  const [organizationId, setOrganizationId] = useState('');
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setError('');
    adminApi
      .getMissionSessions(accessToken, { status, search, organization_id: organizationId })
      .then(setRows)
      .catch((exc) => setError(exc instanceof Error ? exc.message : '미션 로그를 불러오지 못했습니다.'));
  }, [accessToken, organizationId, status, search]);

  return (
    <section className="p-5 md:p-8">
      <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-bold text-admin-primary">운영 관리</p>
          <h2 className="mt-1 text-2xl font-black">미션 로그</h2>
        </div>
        <AdminOrganizationFilter
          accessToken={accessToken}
          value={organizationId}
          onChange={setOrganizationId}
        />
      </div>
      <div className="mb-4 flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 md:flex-row">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="미션, 사용자, 정답 검색"
          className="h-10 flex-1 rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-admin-primary"
        />
        <select
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          className="h-10 rounded-lg border border-slate-200 px-3 text-sm font-semibold outline-none focus:border-admin-primary"
        >
          <option value="">전체 상태</option>
          <option value="created">생성됨</option>
          <option value="submitted">제출됨</option>
          <option value="coupon_issued">쿠폰 발급</option>
          <option value="failed">실패</option>
          <option value="expired">만료</option>
        </select>
      </div>
      {error && <p className="mb-4 rounded-lg bg-red-50 p-4 text-sm font-semibold text-red-600">{error}</p>}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="grid grid-cols-5 gap-3 border-b border-slate-100 bg-slate-50 px-5 py-3 text-xs font-black uppercase text-slate-500">
          <span>ID</span>
          <span>사용자</span>
          <span>유형</span>
          <span>상태</span>
          <span>생성일</span>
        </div>
        {rows.map((row) => (
          <Link
            key={row.mission_id}
            to={`/admin/logs/${row.mission_id}`}
            className="grid grid-cols-1 gap-2 border-b border-slate-100 px-5 py-4 text-sm hover:bg-slate-50 md:grid-cols-5"
          >
            <span className="break-all font-bold">{row.mission_id}</span>
            <span>{row.user_id}</span>
            <span>{row.mission_type}</span>
            <span>{row.status}</span>
            <span className="text-slate-500">{row.created_at || '-'}</span>
          </Link>
        ))}
        {rows.length === 0 && <p className="px-5 py-8 text-sm font-semibold text-slate-500">조회된 미션 로그가 없습니다.</p>}
      </div>
    </section>
  );
}
