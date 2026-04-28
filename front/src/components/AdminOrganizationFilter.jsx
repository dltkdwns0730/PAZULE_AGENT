import { useEffect, useState } from 'react';
import { Building2 } from 'lucide-react';
import { adminApi } from '../services/adminApi';

export default function AdminOrganizationFilter({ accessToken, value, onChange }) {
  const [organizations, setOrganizations] = useState([]);

  useEffect(() => {
    if (!accessToken) return;
    adminApi
      .getOrganizations(accessToken)
      .then(setOrganizations)
      .catch(() => setOrganizations([]));
  }, [accessToken]);

  useEffect(() => {
    if (!value && organizations.length === 1) {
      onChange(organizations[0].id);
    }
  }, [onChange, organizations, value]);

  if (organizations.length === 0) return null;

  return (
    <label className="flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-600">
      <Building2 size={16} aria-hidden="true" />
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-full bg-transparent text-sm font-semibold outline-none"
      >
        {organizations.length > 1 && <option value="">전체 컴퍼니</option>}
        {organizations.map((org) => (
          <option key={org.id} value={org.id}>
            {org.name}
          </option>
        ))}
      </select>
    </label>
  );
}
