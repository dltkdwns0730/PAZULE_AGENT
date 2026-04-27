import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, XCircle } from 'lucide-react';
import { adminApi } from '../services/adminApi';
import { useAuthStore } from '../store/useAuthStore';

export default function AdminMissionDetail() {
  const { missionId } = useParams();
  const { accessToken } = useAuthStore();
  const [mission, setMission] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!missionId) return;
    adminApi
      .getMissionSession(accessToken, missionId)
      .then(setMission)
      .catch((exc) => setError(exc instanceof Error ? exc.message : 'Failed to load mission.'));
  }, [accessToken, missionId]);

  const success = mission?.latest_judgment?.success === true;

  return (
    <section className="p-5 md:p-8">
      <Link to="/admin/logs" className="mb-5 inline-flex items-center gap-2 text-sm font-bold text-admin-primary">
        <ArrowLeft size={16} aria-hidden="true" />
        Mission Logs
      </Link>

      {error && <p className="rounded-lg bg-red-50 p-4 text-sm font-semibold text-red-600">{error}</p>}

      {mission && (
        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <p className="text-sm font-bold text-slate-500">Mission ID</p>
                <h2 className="mt-1 break-all text-2xl font-black text-slate-950">{mission.mission_id}</h2>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-black uppercase text-slate-600">
                {mission.status}
              </span>
            </div>
            <dl className="mt-5 grid gap-4 md:grid-cols-2">
              <div>
                <dt className="text-xs font-bold uppercase text-slate-400">User</dt>
                <dd className="mt-1 text-sm font-semibold">{mission.user_id}</dd>
              </div>
              <div>
                <dt className="text-xs font-bold uppercase text-slate-400">Type</dt>
                <dd className="mt-1 text-sm font-semibold">{mission.mission_type}</dd>
              </div>
              <div>
                <dt className="text-xs font-bold uppercase text-slate-400">Answer</dt>
                <dd className="mt-1 text-sm font-semibold">{mission.answer}</dd>
              </div>
              <div>
                <dt className="text-xs font-bold uppercase text-slate-400">Coupon</dt>
                <dd className="mt-1 text-sm font-semibold">{mission.coupon_code || '-'}</dd>
              </div>
            </dl>
            <div className="mt-6 rounded-lg bg-slate-50 p-4">
              <p className="text-xs font-bold uppercase text-slate-400">Hint</p>
              <p className="mt-1 text-sm text-slate-700">{mission.hint}</p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3">
                {success ? (
                  <CheckCircle2 className="text-green-600" size={24} aria-hidden="true" />
                ) : (
                  <XCircle className="text-slate-400" size={24} aria-hidden="true" />
                )}
                <div>
                  <p className="text-sm font-bold text-slate-500">Latest Judgment</p>
                  <p className="text-xl font-black">{success ? 'Success' : 'Not successful'}</p>
                </div>
              </div>
              <pre className="mt-4 max-h-80 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">
                {JSON.stringify(mission.latest_judgment || {}, null, 2)}
              </pre>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
              <h3 className="border-b border-slate-100 px-5 py-4 text-base font-black">Submissions</h3>
              <div className="divide-y divide-slate-100">
                {(mission.submissions || []).map((row) => (
                  <div key={`${row.submitted_at}-${row.image_hash}`} className="px-5 py-4 text-sm">
                    <p className="font-bold">{row.submitted_at || '-'}</p>
                    <p className="break-all text-xs text-slate-500">{row.image_hash}</p>
                  </div>
                ))}
                {(mission.submissions || []).length === 0 && (
                  <p className="px-5 py-6 text-sm font-semibold text-slate-500">No submissions recorded.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
