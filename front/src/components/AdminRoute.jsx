import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';

export default function AdminRoute() {
  const { isAuthenticated, isAdmin } = useAuthStore();
  if (!isAuthenticated || !isAdmin) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
