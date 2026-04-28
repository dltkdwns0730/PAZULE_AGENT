import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import PrivateRoute from "./components/PrivateRoute";
import AdminRoute from "./components/AdminRoute";
import AdminLayout from "./components/AdminLayout";
import MissionHome from "./pages/MissionHome";
import WalletOverview from "./pages/WalletOverview";
import Scan from "./pages/Scan";
import PhotoSubmission from "./pages/PhotoSubmission";
import MissionResult from "./pages/MissionResult";
import AdminDashboard from "./pages/AdminDashboard";
import AdminMissionDetail from "./pages/AdminMissionDetail";
import AdminMissionLogs from "./pages/AdminMissionLogs";
import AdminCoupons from "./pages/AdminCoupons";
import AdminUsers from "./pages/AdminUsers";
import CouponSuccess from "./pages/CouponSuccess";
import Onboarding from "./pages/Onboarding";
import Permissions from "./pages/Permissions";
import CouponWallet from "./pages/CouponWallet";
import Profile from "./pages/Profile";
import Map from "./pages/Map";
import Login from "./pages/Login";
import AuthCallback from "./pages/AuthCallback";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route element={<Layout />}>
          <Route path="/login" element={<Login />} />
          <Route path="/admin/login" element={<Login />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/onboarding" element={<Onboarding />} />
        </Route>

        {/* Protected user routes */}
        <Route element={<Layout />}>
          <Route element={<PrivateRoute />}>
            <Route path="/" element={<MissionHome />} />
            <Route path="/map" element={<Map />} />
            <Route path="/wallet" element={<CouponWallet />} />
            <Route path="/scan" element={<Scan />} />
            <Route path="/mission/submit" element={<PhotoSubmission />} />
            <Route path="/mission/result" element={<MissionResult />} />
            <Route path="/permissions" element={<Permissions />} />
            <Route path="/coupon/success" element={<CouponSuccess />} />
            <Route path="/profile" element={<Profile />} />
          </Route>
        </Route>

        {/* Admin routes */}
<Route element={<AdminRoute />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/admin/logs" element={<AdminMissionLogs />} />
            <Route path="/admin/logs/:missionId" element={<AdminMissionDetail />} />
            <Route path="/admin/coupons" element={<AdminCoupons />} />
            <Route path="/admin/users" element={<AdminUsers />} />
          </Route>
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
