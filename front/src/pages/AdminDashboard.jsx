import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, CheckCircle2, Ticket, Users } from 'lucide-react';
import AdminOrganizationFilter from '../components/AdminOrganizationFilter';
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
  const [organizationId, setOrganizationId] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setError('');
    adminApi
      .getSummary(accessToken, { organization_id: organizationId })
      .then(setSummary)
      .catch((exc) => setError(exc instanceof Error ? exc.message : '대시보드를 불러오지 못했습니다.'));
  }, [accessToken, organizationId]);

  return (
    <section className="p-5 md:p-8">
      <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-bold text-admin-primary">운영 관리</p>
          <h2 className="text-2xl font-black text-slate-950">대시보드</h2>
        </div>
        <AdminOrganizationFilter
          accessToken={accessToken}
          value={organizationId}
          onChange={setOrganizationId}
        />
      </div>

      {error && <p className="rounded-lg bg-red-50 p-4 text-sm font-semibold text-red-600">{error}</p>}

      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="미션 세션" value={summary?.total_sessions ?? '-'} icon={Activity} />
        <StatCard label="성공률" value={`${summary?.success_rate ?? 0}%`} icon={CheckCircle2} />
        <StatCard label="발급 쿠폰" value={summary?.issued_coupons ?? '-'} icon={Ticket} />
        <StatCard label="사용 완료" value={summary?.redeemed_coupons ?? '-'} icon={Users} />
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h3 className="text-base font-black">최근 미션 활동</h3>
          <Link to="/admin/logs" className="text-sm font-bold text-admin-primary">
            로그 보기
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
            <p className="px-5 py-8 text-sm font-semibold text-slate-500">아직 미션 활동이 없습니다.</p>
          )}
        </div>
      </div>
    </section>
  );
}
