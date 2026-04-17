import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import MissionHome from "./pages/MissionHome";
import WalletOverview from "./pages/WalletOverview";
import Scan from "./pages/Scan";
import PhotoSubmission from "./pages/PhotoSubmission";
import MissionResult from "./pages/MissionResult";
import AdminDashboard from "./pages/AdminDashboard";
import AdminMissionDetail from "./pages/AdminMissionDetail";
import CouponSuccess from "./pages/CouponSuccess";
import Onboarding from "./pages/Onboarding";
import Permissions from "./pages/Permissions";
import CouponWallet from "./pages/CouponWallet";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Mobile App Routes */}
        <Route element={<Layout />}>
          <Route path="/" element={<MissionHome />} />
          <Route path="/wallet" element={<CouponWallet />} />
          <Route path="/scan" element={<Scan />} />
          <Route path="/mission/submit" element={<PhotoSubmission />} />
          <Route path="/mission/result" element={<MissionResult />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/permissions" element={<Permissions />} />
          <Route path="/coupon/success" element={<CouponSuccess />} />

          <Route path="/profile" element={
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-500">
              <span className="material-symbols-outlined text-4xl mb-2">person</span>
              <p>Profile Page (In Progress)</p>
            </div>
          } />
        </Route>

        {/* Admin Routes */}
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/log" element={<AdminMissionDetail />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
